from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.core import get_db
from app.models import (
    LeaveRequest, LeaveStatus, LeaveType, LeaveBalance,
    LeaveAuditLog, User, LeavePolicy, RiskLevel
)
from app.schemas import (
    LeaveRequestCreate, LeaveRequestResponse, LeaveRequestUpdate,
    LeaveRequestWithEmployee, LeaveRequestDetail, LeaveBalanceResponse,
    AuditLogResponse, LeaveRequestForHRReview, EmployeeLeaveBalance,
    EmployeeLeaveHistory, EmployeeLeaveStats
)
from app.api.auth import get_current_user, require_role
from app.models import UserRole
from app.services import process_leave_request, generate_request_number, business_days_between
from app.services.email_service import email_service
from app.services.certificate_validator import validate_medical_certificate, ValidationResult

router = APIRouter(prefix="/leaves", tags=["Leave Management"])


@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new leave request"""
    # Generate request number
    request_number = generate_request_number()
    
    # Get policy for holidays
    policy = db.query(LeavePolicy).filter(
        LeavePolicy.is_active == True,
        or_(
            LeavePolicy.department_id == current_user.department_id,
            LeavePolicy.department_id == None
        )
    ).first()
    
    holidays = policy.holidays if policy else []
    
    # Calculate total days
    total_days = business_days_between(
        leave_data.start_date,
        leave_data.end_date,
        holidays
    )
    
    # Validate medical certificate for sick leave
    if leave_data.leave_type == LeaveType.SICK:
        if not leave_data.medical_certificate_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medical certificate is mandatory for sick leave"
            )
        if leave_data.medical_certificate_size and leave_data.medical_certificate_size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medical certificate file size must not exceed 5MB"
            )
        
        # Extract and validate medical certificate content
        try:
            validation_result = validate_medical_certificate(
                file_data=leave_data.medical_certificate_url,
                filename=leave_data.medical_certificate_filename or "certificate.pdf"
            )
            
            # Store validation details for HR review
            certificate_validation = {
                "is_valid": validation_result.is_valid,
                "result": validation_result.result.value,
                "confidence_score": validation_result.confidence_score,
                "detected_fields": validation_result.detected_fields,
                "validation_notes": validation_result.validation_notes,
                "extracted_text_preview": validation_result.extracted_text[:200] if validation_result.extracted_text else None
            }
            
            # If certificate is clearly invalid, reject immediately
            if validation_result.result == ValidationResult.INVALID:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Medical certificate validation failed: {', '.join(validation_result.validation_notes)}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            # Log error but allow submission for manual review
            print(f"Certificate validation error: {e}")
            certificate_validation = {
                "is_valid": None,
                "result": "EXTRACTION_FAILED",
                "error": str(e),
                "validation_notes": ["Certificate will be reviewed manually by HR"]
            }
    else:
        certificate_validation = None
    
    # Create leave request
    leave_request = LeaveRequest(
        request_number=request_number,
        employee_id=current_user.id,
        leave_type=leave_data.leave_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        total_days=total_days,
        reason_text=leave_data.reason_text,
        medical_certificate_url=leave_data.medical_certificate_url,
        medical_certificate_filename=leave_data.medical_certificate_filename,
        medical_certificate_size=leave_data.medical_certificate_size,
        medical_certificate_validation=certificate_validation,
        status=LeaveStatus.PENDING
    )
    
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_request.id,
        action="Request Submitted",
        actor_id=current_user.id,
        actor_type="USER",
        new_status=LeaveStatus.PENDING.value,
        details=f"Leave request submitted for {total_days} days"
    )
    db.add(audit_log)
    db.commit()
    
    # Process the leave request asynchronously
    try:
        await process_leave_request(db, leave_request.id)
        db.refresh(leave_request)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error processing leave request: {e}")
    
    return LeaveRequestResponse.model_validate(leave_request)


@router.get("/", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's leave requests"""
    query = db.query(LeaveRequest).filter(LeaveRequest.employee_id == current_user.id)
    
    if status:
        query = query.filter(LeaveRequest.status == status)
    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()
    
    return [LeaveRequestResponse.model_validate(lr) for lr in leave_requests]


@router.get("/pending", response_model=List[LeaveRequestForHRReview])
async def get_pending_requests(
    risk_level: Optional[RiskLevel] = None,
    department_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all pending leave requests with complete employee data (HR/Admin only)"""
    query = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW])
    )
    
    if risk_level:
        query = query.filter(LeaveRequest.risk_level == risk_level)
    
    if department_id:
        query = query.join(User).filter(User.department_id == department_id)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()
    
    current_year = datetime.now().year
    result = []
    
    for lr in leave_requests:
        employee = db.query(User).filter(User.id == lr.employee_id).first()
        if not employee:
            continue
        
        # Get employee's leave balances (all types)
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == current_year
        ).all()
        
        employee_balances = [
            EmployeeLeaveBalance(
                leave_type=b.leave_type.value,
                total_days=b.total_days,
                used_days=b.used_days,
                pending_days=b.pending_days,
                remaining_days=b.remaining_days
            ) for b in balances
        ]
        
        # Get employee's recent leave history (last 10 completed requests)
        history = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([LeaveStatus.APPROVED, LeaveStatus.REJECTED])
        ).order_by(LeaveRequest.created_at.desc()).limit(10).all()
        
        employee_history = [
            EmployeeLeaveHistory(
                id=h.id,
                request_number=h.request_number,
                leave_type=h.leave_type.value,
                start_date=h.start_date,
                end_date=h.end_date,
                total_days=h.total_days,
                status=h.status.value,
                created_at=h.created_at
            ) for h in history
        ]
        
        # Calculate statistics
        # Total leaves this year
        total_this_year = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar() or 0
        
        # Total days taken this year
        total_days_this_year = db.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar() or 0.0
        
        # Leaves in last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        leaves_30_days = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date >= thirty_days_ago
        ).scalar() or 0
        
        # Leaves in last 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)
        leaves_90_days = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date >= ninety_days_ago
        ).scalar() or 0
        
        # Most used leave type
        most_used = db.query(
            LeaveRequest.leave_type,
            func.count(LeaveRequest.id).label('count')
        ).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).group_by(LeaveRequest.leave_type).order_by(func.count(LeaveRequest.id).desc()).first()
        
        most_used_type = most_used[0].value if most_used else None
        
        # Average leave duration
        avg_duration = db.query(func.avg(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar()
        
        # Pending requests count
        pending_count = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW])
        ).scalar() or 0
        
        employee_stats = EmployeeLeaveStats(
            total_leaves_this_year=total_this_year,
            total_days_taken_this_year=float(total_days_this_year),
            leaves_last_30_days=leaves_30_days,
            leaves_last_90_days=leaves_90_days,
            most_used_leave_type=most_used_type,
            average_leave_duration=float(avg_duration) if avg_duration else None,
            pending_requests_count=pending_count
        )
        
        result.append(LeaveRequestForHRReview(
            **LeaveRequestResponse.model_validate(lr).model_dump(),
            employee_name=f"{employee.first_name} {employee.last_name}",
            employee_email=employee.email,
            employee_department=employee.department.name if employee.department else None,
            employee_avatar=employee.avatar_url,
            employee_leave_balances=employee_balances,
            employee_leave_history=employee_history,
            employee_leave_stats=employee_stats
        ))
    
    return result


@router.get("/all", response_model=List[LeaveRequestWithEmployee])
async def get_all_requests(
    status: Optional[LeaveStatus] = None,
    employee_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all leave requests (HR/Admin only)"""
    query = db.query(LeaveRequest)
    
    if status:
        query = query.filter(LeaveRequest.status == status)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for lr in leave_requests:
        employee = db.query(User).filter(User.id == lr.employee_id).first()
        result.append(LeaveRequestWithEmployee(
            **LeaveRequestResponse.model_validate(lr).model_dump(),
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            employee_email=employee.email if employee else "",
            employee_department=employee.department.name if employee and employee.department else None,
            employee_avatar=employee.avatar_url if employee else None
        ))
    
    return result


@router.get("/balance/me", response_model=List[LeaveBalanceResponse])
async def get_my_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's leave balance"""
    current_year = datetime.now().year
    
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_user.id,
        LeaveBalance.year == current_year
    ).all()
    
    return [LeaveBalanceResponse.model_validate(b) for b in balances]


@router.get("/{leave_id}", response_model=LeaveRequestDetail)
async def get_leave_request(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get leave request details with employee context"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE and leave_request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    employee = db.query(User).filter(User.id == leave_request.employee_id).first()
    
    # Get balance info for this specific leave type
    current_year = datetime.now().year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == leave_request.employee_id,
        LeaveBalance.leave_type == leave_request.leave_type,
        LeaveBalance.year == current_year
    ).first()
    
    # Build historical pattern summary for HR
    historical_pattern = None
    if current_user.role in [UserRole.HR, UserRole.ADMIN]:
        # Get stats for pattern analysis
        total_leaves = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == leave_request.employee_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar() or 0
        
        recent_leaves = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == leave_request.employee_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date >= datetime.now() - timedelta(days=60)
        ).scalar() or 0
        
        historical_pattern = f"{total_leaves} approved leaves this year, {recent_leaves} in last 60 days"
    
    return LeaveRequestDetail(
        **LeaveRequestResponse.model_validate(leave_request).model_dump(),
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
        employee_email=employee.email if employee else "",
        employee_department=employee.department.name if employee and employee.department else None,
        employee_avatar=employee.avatar_url if employee else None,
        employee_total_balance=balance.total_days if balance else None,
        employee_used_ytd=balance.used_days if balance else None,
        team_coverage=None,
        team_context=None,
        historical_pattern=historical_pattern
    )


@router.put("/{leave_id}/approve")
async def approve_leave_request(
    leave_id: int,
    comments: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Approve a leave request (HR/Admin only)"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status not in [LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="Leave request cannot be approved")
    
    previous_status = leave_request.status.value
    leave_request.status = LeaveStatus.APPROVED
    leave_request.reviewed_by = current_user.id
    leave_request.reviewed_at = datetime.now()
    leave_request.reviewer_comments = comments
    
    # Update leave balance
    employee = db.query(User).filter(User.id == leave_request.employee_id).first()
    if employee:
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type == leave_request.leave_type,
            LeaveBalance.year == datetime.now().year
        ).first()
        
        if balance:
            balance.used_days += leave_request.total_days
            balance.pending_days = max(0, balance.pending_days - leave_request.total_days)
            balance.remaining_days = balance.total_days - balance.used_days
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_id,
        action="Approved",
        actor_id=current_user.id,
        actor_type="USER",
        previous_status=previous_status,
        new_status=LeaveStatus.APPROVED.value,
        details=comments or "Leave request approved by HR"
    )
    db.add(audit_log)
    db.commit()
    
    # Send email notification to employee
    if employee and employee.email:
        try:
            await email_service.send_leave_approved(
                to_email=employee.email,
                employee_name=f"{employee.first_name} {employee.last_name}",
                leave_type=leave_request.leave_type.value,
                start_date=leave_request.start_date.strftime("%Y-%m-%d"),
                end_date=leave_request.end_date.strftime("%Y-%m-%d"),
                total_days=leave_request.total_days,
                reason_text=leave_request.reason_text,
                explanation=comments
            )
        except Exception as e:
            # Log but don't fail the approval
            print(f"Failed to send approval email: {e}")
    
    return {"message": "Leave request approved", "status": "APPROVED"}


@router.put("/{leave_id}/reject")
async def reject_leave_request(
    leave_id: int,
    reason: str,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Reject a leave request (HR/Admin only)"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status not in [LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="Leave request cannot be rejected")
    
    previous_status = leave_request.status.value
    leave_request.status = LeaveStatus.REJECTED
    leave_request.reviewed_by = current_user.id
    leave_request.reviewed_at = datetime.now()
    leave_request.reviewer_comments = reason
    
    # Get employee for email
    employee = db.query(User).filter(User.id == leave_request.employee_id).first()
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_id,
        action="Rejected",
        actor_id=current_user.id,
        actor_type="USER",
        previous_status=previous_status,
        new_status=LeaveStatus.REJECTED.value,
        details=reason
    )
    db.add(audit_log)
    db.commit()
    
    # Send email notification to employee
    if employee and employee.email:
        try:
            await email_service.send_leave_rejected(
                to_email=employee.email,
                employee_name=f"{employee.first_name} {employee.last_name}",
                leave_type=leave_request.leave_type.value,
                start_date=leave_request.start_date.strftime("%Y-%m-%d"),
                end_date=leave_request.end_date.strftime("%Y-%m-%d"),
                total_days=leave_request.total_days,
                reason=reason,
                employee_reason=leave_request.reason_text
            )
        except Exception as e:
            # Log but don't fail the rejection
            print(f"Failed to send rejection email: {e}")
    
    return {"message": "Leave request rejected", "status": "REJECTED"}


@router.put("/{leave_id}/cancel")
async def cancel_leave_request(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a leave request (only by the employee who created it)"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
    
    if leave_request.status not in [LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="Leave request cannot be cancelled")
    
    previous_status = leave_request.status.value
    leave_request.status = LeaveStatus.CANCELLED
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_id,
        action="Cancelled",
        actor_id=current_user.id,
        actor_type="USER",
        previous_status=previous_status,
        new_status=LeaveStatus.CANCELLED.value,
        details="Leave request cancelled by employee"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Leave request cancelled", "status": "CANCELLED"}


@router.get("/{leave_id}/audit", response_model=List[AuditLogResponse])
async def get_leave_audit_trail(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit trail for a leave request"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE and leave_request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this audit trail")
    
    audit_logs = db.query(LeaveAuditLog).filter(
        LeaveAuditLog.leave_request_id == leave_id
    ).order_by(LeaveAuditLog.created_at.asc()).all()
    
    return [AuditLogResponse.model_validate(log) for log in audit_logs]
