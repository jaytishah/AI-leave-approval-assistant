from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from app.models import (
    LeaveRequest, LeaveStatus, LeaveBalance, LeavePolicy,
    LeaveAuditLog, ApprovalTask, User, RiskLevel
)
from app.services.leave_utils import (
    business_days_between, compute_leave_stats, check_rule_violations,
    is_blocking_violation, build_explanation, compute_priority,
    generate_request_number, calculate_working_days
)
from app.models import CompanyPolicy
from app.services.ai_service import evaluate_leave_with_ai
from app.services.email_service import email_service
from app.core.config import settings


class LeaveProcessingService:
    """
    Main service for processing leave requests according to the pseudo code.
    Implements the complete leave request workflow with rules engine and AI evaluation.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def process_leave_request(self, leave_request_id: int) -> str:
        """
        Main function to process a leave request.
        Implements the ProcessLeaveRequest function from pseudo code.
        """
        # 1) Load request + employee + policies
        leave_req = self.db.query(LeaveRequest).filter(LeaveRequest.id == leave_request_id).first()
        if not leave_req:
            return "NOT_FOUND"
        
        employee = self.db.query(User).filter(User.id == leave_req.employee_id).first()
        if not employee:
            return "EMPLOYEE_NOT_FOUND"
        
        # Check if already processed
        if leave_req.status in [LeaveStatus.APPROVED, LeaveStatus.REJECTED, LeaveStatus.CANCELLED]:
            return "NO_ACTION"
        
        # Get policy
        org_policy = self._get_leave_policy(employee)
        
        # Basic date validation
        if leave_req.start_date > leave_req.end_date:
            await self._update_and_exit(leave_req, LeaveStatus.REJECTED, "Invalid date range")
            return "REJECTED"
        
        # Get company policy for weekly off configuration
        company_policy = self.db.query(CompanyPolicy).order_by(CompanyPolicy.updated_at.desc()).first()
        weekly_off_type = company_policy.weekly_off_type.value if company_policy else "SAT_SUN"
        
        # Calculate requested days using proper working days calculation
        holidays = org_policy.holidays if org_policy else []
        requested_days = calculate_working_days(
            leave_req.start_date,
            leave_req.end_date,
            weekly_off_type,
            holidays
        )
        leave_req.total_days = requested_days
        
        # 2) Fetch past data (history + patterns)
        history_window_days = org_policy.history_window_days if org_policy else 180
        leave_history = self._get_leave_history(employee.id, history_window_days)
        balance = self._get_leave_balance(employee.id, leave_req.leave_type.value)
        
        # 3) Hard rules engine
        stats = compute_leave_stats(leave_history, org_policy) if org_policy else {}
        
        violations = check_rule_violations(
            leave_req,
            org_policy,
            balance.remaining_days if balance else 0,
            requested_days,
            stats
        ) if org_policy else []
        
        # If hard-rule violations are blocking
        if violations and is_blocking_violation(violations, org_policy):
            explanation = build_explanation(violations)
            await self._update_and_exit(leave_req, LeaveStatus.REJECTED, explanation, engine="RULES")
            await self._notify_employee(employee, LeaveStatus.REJECTED, explanation, leave_req)
            return "REJECTED"
        
        # 4) AI evaluation
        ai_result = await self._evaluate_with_ai(leave_req, requested_days, org_policy, stats, employee)
        
        # Store AI results
        leave_req.ai_validity_score = ai_result.get("validity_score")
        leave_req.ai_risk_flags = ai_result.get("risk_flags", [])
        leave_req.ai_recommended_action = ai_result.get("recommended_action")
        leave_req.ai_rationale = ai_result.get("rationale")
        leave_req.ai_reason_category = ai_result.get("reason_category")
        
        # Handle AI errors
        if ai_result.get("error"):
            fallback_mode = settings.AI_FALLBACK_MODE
            if fallback_mode == "RULES_ONLY" and not violations:
                # Rules passed, AI failed - approve or manual review
                return await self._approve_or_manual_by_rules(leave_req, employee, stats, org_policy, "AI unavailable")
            else:
                return await self._route_to_manual_review(leave_req, employee, "AI evaluation failed")
        
        # 5) Final decision logic
        decision = await self._make_final_decision(
            leave_req, employee, org_policy, stats, ai_result, requested_days, violations
        )
        
        return decision
    
    def _get_leave_policy(self, employee: User) -> Optional[LeavePolicy]:
        """Get applicable leave policy for employee"""
        # Try to find most specific policy first
        policy = self.db.query(LeavePolicy).filter(
            LeavePolicy.is_active == True,
            LeavePolicy.department_id == employee.department_id
        ).first()
        
        if not policy:
            # Fall back to default policy
            policy = self.db.query(LeavePolicy).filter(
                LeavePolicy.is_active == True,
                LeavePolicy.department_id == None
            ).first()
        
        return policy
    
    def _get_leave_history(self, employee_id: int, days: int):
        """Get leave history for employee"""
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        return self.db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.created_at >= cutoff_date,
            LeaveRequest.status.in_([
                LeaveStatus.APPROVED,
                LeaveStatus.PENDING,
                LeaveStatus.PENDING_REVIEW
            ])
        ).all()
    
    def _get_leave_balance(self, employee_id: int, leave_type: str) -> Optional[LeaveBalance]:
        """Get leave balance for employee and leave type"""
        from app.models import LeaveType as LeaveTypeEnum
        current_year = datetime.now().year
        
        # Convert string to enum for comparison
        try:
            leave_type_enum = LeaveTypeEnum(leave_type)
        except ValueError:
            leave_type_enum = leave_type
        
        return self.db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type_enum,
            LeaveBalance.year == current_year
        ).first()
    
    async def _evaluate_with_ai(
        self,
        leave_req: LeaveRequest,
        requested_days: float,
        policy: LeavePolicy,
        stats: dict,
        employee: User
    ) -> dict:
        """Evaluate leave request with AI"""
        policy_dict = {
            "reason_mandatory": policy.reason_mandatory if policy else True,
            "long_leave_threshold_days": policy.long_leave_threshold_days if policy else 5,
            "max_unplanned_leaves_30_days": policy.max_unplanned_leaves_30_days if policy else 3
        }
        
        employee_context = {
            "tenure_months": employee.tenure_months,
            "role_level": employee.level,
            "department": employee.department.name if employee.department else "Unknown"
        }
        
        ai_config = {
            "temperature": 0.3,
            "timeout_ms": settings.AI_TIMEOUT_MS
        }
        
        return await evaluate_leave_with_ai(
            leave_type=leave_req.leave_type.value,
            start_date=leave_req.start_date.strftime("%Y-%m-%d"),
            end_date=leave_req.end_date.strftime("%Y-%m-%d"),
            requested_days=requested_days,
            reason_text=leave_req.reason_text,
            policy=policy_dict,
            history_stats=stats,
            employee_context=employee_context,
            ai_config=ai_config
        )
    
    async def _make_final_decision(
        self,
        leave_req: LeaveRequest,
        employee: User,
        policy: LeavePolicy,
        stats: dict,
        ai_result: dict,
        requested_days: float,
        violations: list
    ) -> str:
        """Make final decision based on rules + AI + thresholds"""
        decision = LeaveStatus.PENDING_REVIEW
        explanation_parts = []
        
        if violations:
            explanation_parts.append("Rule warnings: " + "; ".join(violations))
        else:
            explanation_parts.append("Rules check: PASSED")
        
        ai_score = ai_result.get("validity_score", 0)
        explanation_parts.append(f"AI validity_score={ai_score}")
        
        if ai_result.get("risk_flags"):
            explanation_parts.append("AI flags: " + ", ".join(ai_result["risk_flags"]))
        
        risk_level = stats.get("risk_level", "LOW")
        leave_req.risk_level = RiskLevel(risk_level)
        
        # Decision thresholds
        min_approve = settings.AI_MIN_CONFIDENCE_TO_APPROVE
        min_reject = settings.AI_MIN_CONFIDENCE_TO_REJECT
        
        if ai_score >= min_approve and risk_level != "HIGH":
            decision = LeaveStatus.APPROVED
        elif ai_score <= min_reject and risk_level == "HIGH":
            decision = LeaveStatus.REJECTED
        else:
            decision = LeaveStatus.PENDING_REVIEW
        
        # Guardrails
        if policy:
            if requested_days >= policy.long_leave_threshold_days:
                decision = LeaveStatus.PENDING_REVIEW
            
            if policy.require_manager_approval:
                decision = LeaveStatus.PENDING_REVIEW
        
        explanation = " | ".join(explanation_parts)
        
        # 6) Persist outcome + audit trail
        audit_meta = {
            "engine": "RULES+AI",
            "ai_provider": "GEMINI",
            "ai_model": settings.GEMINI_MODEL,
            "ai_validity_score": ai_score,
            "ai_recommended_action": ai_result.get("recommended_action"),
            "history_window_days": policy.history_window_days if policy else 180,
            "computed_stats": stats
        }
        
        if decision == LeaveStatus.APPROVED:
            await self._finalize_decision(leave_req, employee, decision, explanation, audit_meta)
            return "APPROVED"
        
        if decision == LeaveStatus.REJECTED:
            await self._finalize_decision(leave_req, employee, decision, explanation, audit_meta)
            return "REJECTED"
        
        # Manual review
        await self._finalize_decision(leave_req, employee, LeaveStatus.PENDING_REVIEW, explanation, audit_meta)
        self._create_approval_task(leave_req, stats, requested_days, explanation)
        return "MANUAL_REVIEW"
    
    async def _finalize_decision(
        self,
        leave_req: LeaveRequest,
        employee: User,
        status: LeaveStatus,
        explanation: str,
        audit_meta: dict
    ):
        """Finalize decision with database update and notifications"""
        leave_req.status = status
        leave_req.decision_explanation = explanation
        leave_req.decision_engine = audit_meta.get("engine", "RULES+AI")
        
        # Create audit log
        self._create_audit_log(
            leave_req.id,
            f"Decision: {status.value}",
            actor_type="SYSTEM",
            new_status=status.value,
            details=explanation,
            metadata=audit_meta
        )
        
        self.db.commit()
        
        # Send notification
        await self._notify_employee(employee, status, explanation, leave_req)
    
    async def _update_and_exit(
        self,
        leave_req: LeaveRequest,
        status: LeaveStatus,
        explanation: str,
        engine: str = "RULES"
    ):
        """Update leave request and exit"""
        leave_req.status = status
        leave_req.decision_explanation = explanation
        leave_req.decision_engine = engine
        
        self._create_audit_log(
            leave_req.id,
            f"Decision: {status.value}",
            actor_type="SYSTEM",
            new_status=status.value,
            details=explanation,
            metadata={"engine": engine}
        )
        
        self.db.commit()
    
    async def _notify_employee(
        self,
        employee: User,
        status: LeaveStatus,
        explanation: str,
        leave_req: LeaveRequest
    ):
        """Send notification to employee"""
        try:
            if status == LeaveStatus.APPROVED:
                await email_service.send_leave_approved(
                    to_email=employee.email,
                    employee_name=f"{employee.first_name} {employee.last_name}",
                    leave_type=leave_req.leave_type.value,
                    start_date=leave_req.start_date.strftime("%Y-%m-%d"),
                    end_date=leave_req.end_date.strftime("%Y-%m-%d"),
                    total_days=leave_req.total_days,
                    reason_text=leave_req.reason_text,
                    explanation=explanation
                )
            elif status == LeaveStatus.REJECTED:
                await email_service.send_leave_rejected(
                    to_email=employee.email,
                    employee_name=f"{employee.first_name} {employee.last_name}",
                    leave_type=leave_req.leave_type.value,
                    start_date=leave_req.start_date.strftime("%Y-%m-%d"),
                    end_date=leave_req.end_date.strftime("%Y-%m-%d"),
                    total_days=leave_req.total_days,
                    reason=explanation,
                    employee_reason=leave_req.reason_text
                )
            elif status == LeaveStatus.PENDING_REVIEW:
                await email_service.send_leave_pending_review(
                    to_email=employee.email,
                    employee_name=f"{employee.first_name} {employee.last_name}",
                    leave_type=leave_req.leave_type.value,
                    start_date=leave_req.start_date.strftime("%Y-%m-%d"),
                    end_date=leave_req.end_date.strftime("%Y-%m-%d"),
                    total_days=leave_req.total_days,
                    reason_text=leave_req.reason_text
                )
        except Exception as e:
            # Log but don't fail the process
            print(f"Failed to send email notification: {e}")
    
    async def _route_to_manual_review(
        self,
        leave_req: LeaveRequest,
        employee: User,
        note: str
    ) -> str:
        """Route to manual review queue"""
        leave_req.status = LeaveStatus.PENDING_REVIEW
        leave_req.decision_explanation = note
        leave_req.decision_engine = "FALLBACK"
        
        self._create_audit_log(
            leave_req.id,
            "Routed to manual review",
            actor_type="SYSTEM",
            new_status=LeaveStatus.PENDING_REVIEW.value,
            details=note,
            metadata={"engine": "FALLBACK"}
        )
        
        self._create_approval_task(leave_req, {}, leave_req.total_days, note, priority="HIGH")
        
        self.db.commit()
        
        await self._notify_employee(employee, LeaveStatus.PENDING_REVIEW, note, leave_req)
        
        return "MANUAL_REVIEW"
    
    async def _approve_or_manual_by_rules(
        self,
        leave_req: LeaveRequest,
        employee: User,
        stats: dict,
        policy: LeavePolicy,
        note: str
    ) -> str:
        """Approve or route to manual based on rules only"""
        # If rules passed and low risk, approve
        if stats.get("risk_level", "LOW") == "LOW":
            leave_req.status = LeaveStatus.APPROVED
            leave_req.decision_explanation = f"{note} - Approved by rules only"
            leave_req.decision_engine = "RULES_ONLY"
            
            self._create_audit_log(
                leave_req.id,
                "Approved by rules (AI unavailable)",
                actor_type="SYSTEM",
                new_status=LeaveStatus.APPROVED.value,
                details=note,
                metadata={"engine": "RULES_ONLY"}
            )
            
            self.db.commit()
            await self._notify_employee(employee, LeaveStatus.APPROVED, note, leave_req)
            return "APPROVED"
        else:
            return await self._route_to_manual_review(leave_req, employee, note)
    
    def _create_audit_log(
        self,
        leave_request_id: int,
        action: str,
        actor_id: int = None,
        actor_type: str = None,
        previous_status: str = None,
        new_status: str = None,
        details: str = None,
        metadata: dict = None
    ):
        """Create audit log entry"""
        audit_log = LeaveAuditLog(
            leave_request_id=leave_request_id,
            action=action,
            actor_id=actor_id,
            actor_type=actor_type,
            previous_status=previous_status,
            new_status=new_status,
            details=details,
            metadata=metadata
        )
        self.db.add(audit_log)
    
    def _create_approval_task(
        self,
        leave_req: LeaveRequest,
        stats: dict,
        requested_days: float,
        notes: str,
        priority: str = None
    ):
        """Create approval task for HR queue"""
        if not priority:
            priority = compute_priority(stats, requested_days)
        
        task = ApprovalTask(
            leave_request_id=leave_req.id,
            queue="HR_MANAGER_QUEUE",
            priority=priority,
            notes=notes,
            status="OPEN"
        )
        self.db.add(task)


async def process_leave_request(db: Session, leave_request_id: int) -> str:
    """Convenience function to process a leave request"""
    service = LeaveProcessingService(db)
    return await service.process_leave_request(leave_request_id)
