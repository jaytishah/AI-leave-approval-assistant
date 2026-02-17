from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core import get_db
from app.models import (
    User, UserRole, LeaveRequest, LeaveStatus, LeaveBalance,
    LeaveAuditLog, Department, LeavePolicy, Holiday, AIConfiguration,
    CompanyPolicy, WeeklyOffType
)
from app.schemas import (
    LeavePolicyCreate, LeavePolicyUpdate, LeavePolicyResponse,
    AIConfigCreate, AIConfigUpdate, AIConfigResponse,
    HolidayCreate, HolidayResponse, AuditLogResponse,
    DashboardStats, EmployeeDashboard, HRDashboard, AdminDashboard,
    LeaveBalanceResponse, LeaveRequestResponse, LeaveRequestWithEmployee,
    CompanyPolicyUpdate, CompanyPolicyResponse
)
from app.api.auth import get_current_user, require_role

router = APIRouter(prefix="/admin", tags=["Administration"])


# ========== Dashboard Routes ==========

@router.get("/dashboard/employee", response_model=EmployeeDashboard)
async def get_employee_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get employee dashboard data"""
    current_year = datetime.now().year
    
    # Get leave balances
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_user.id,
        LeaveBalance.year == current_year
    ).all()
    
    # Get recent requests
    recent_requests = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == current_user.id
    ).order_by(LeaveRequest.created_at.desc()).limit(5).all()
    
    # Get upcoming holidays
    today = datetime.now()
    upcoming_holidays = db.query(Holiday).filter(
        Holiday.date >= today,
        Holiday.is_active == True
    ).order_by(Holiday.date.asc()).limit(5).all()
    
    # Generate AI suggestion
    ai_suggestion = _generate_ai_suggestion(current_user, balances, db)
    
    return EmployeeDashboard(
        leave_balances=[LeaveBalanceResponse.model_validate(b) for b in balances],
        recent_requests=[LeaveRequestResponse.model_validate(r) for r in recent_requests],
        upcoming_holidays=[HolidayResponse.model_validate(h) for h in upcoming_holidays],
        ai_suggestion=ai_suggestion
    )


@router.get("/dashboard/hr", response_model=HRDashboard)
async def get_hr_dashboard(
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get HR dashboard data"""
    # Get pending requests count
    total_pending = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW])
    ).count()
    
    # Get high risk count
    high_risk = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]),
        LeaveRequest.risk_level == "HIGH"
    ).count()
    
    # Calculate week-over-week change
    week_ago = datetime.now() - timedelta(days=7)
    last_week_pending = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]),
        LeaveRequest.created_at < week_ago
    ).count()
    
    pending_change = 0
    if last_week_pending > 0:
        pending_change = ((total_pending - last_week_pending) / last_week_pending) * 100
    
    # Get pending requests with employee info
    pending_requests = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW])
    ).order_by(LeaveRequest.created_at.desc()).limit(20).all()
    
    result_requests = []
    for lr in pending_requests:
        employee = db.query(User).filter(User.id == lr.employee_id).first()
        result_requests.append(LeaveRequestWithEmployee(
            **LeaveRequestResponse.model_validate(lr).model_dump(),
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            employee_email=employee.email if employee else "",
            employee_department=employee.department.name if employee and employee.department else None,
            employee_avatar=employee.avatar_url if employee else None
        ))
    
    return HRDashboard(
        stats=DashboardStats(
            total_pending=total_pending,
            high_risk_flagged=high_risk,
            team_coverage=94.0,  # Calculate based on team availability
            pending_change_percent=round(pending_change, 1)
        ),
        pending_requests=result_requests
    )


@router.get("/dashboard/admin", response_model=AdminDashboard)
async def get_admin_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get admin dashboard data"""
    # Count totals
    total_employees = db.query(User).filter(User.role == UserRole.EMPLOYEE, User.is_active == True).count()
    total_departments = db.query(Department).count()
    
    # This month's requests
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_requests_month = db.query(LeaveRequest).filter(
        LeaveRequest.created_at >= month_start
    ).count()
    
    # Calculate approval rate
    approved_count = db.query(LeaveRequest).filter(
        LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.created_at >= month_start
    ).count()
    
    approval_rate = 0
    if total_requests_month > 0:
        approval_rate = (approved_count / total_requests_month) * 100
    
    # AI accuracy (mock - would need actual tracking)
    ai_accuracy = 87.5
    
    # Recent audit logs
    recent_logs = db.query(LeaveAuditLog).order_by(
        LeaveAuditLog.created_at.desc()
    ).limit(10).all()
    
    return AdminDashboard(
        total_employees=total_employees,
        total_departments=total_departments,
        total_requests_this_month=total_requests_month,
        approval_rate=round(approval_rate, 1),
        ai_accuracy=ai_accuracy,
        recent_audit_logs=[AuditLogResponse.model_validate(log) for log in recent_logs]
    )


# ========== Policy Management ==========

@router.get("/policies", response_model=List[LeavePolicyResponse])
async def get_policies(
    department_id: Optional[int] = None,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all leave policies"""
    query = db.query(LeavePolicy)
    
    if department_id:
        query = query.filter(LeavePolicy.department_id == department_id)
    
    policies = query.all()
    return [LeavePolicyResponse.model_validate(p) for p in policies]


@router.get("/policies/{policy_id}", response_model=LeavePolicyResponse)
async def get_policy(
    policy_id: int,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get policy by ID"""
    policy = db.query(LeavePolicy).filter(LeavePolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return LeavePolicyResponse.model_validate(policy)


@router.post("/policies", response_model=LeavePolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    policy_data: LeavePolicyCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new leave policy"""
    policy = LeavePolicy(
        name=policy_data.name,
        department_id=policy_data.department_id,
        location=policy_data.location,
        grade=policy_data.grade,
        annual_leave_days=policy_data.annual_leave_days,
        sick_leave_days=policy_data.sick_leave_days,
        casual_leave_days=policy_data.casual_leave_days,
        maternity_leave_days=policy_data.maternity_leave_days,
        paternity_leave_days=policy_data.paternity_leave_days,
        allow_negative_balance=policy_data.allow_negative_balance,
        reason_mandatory=policy_data.reason_mandatory,
        require_manager_approval=policy_data.require_manager_approval,
        long_leave_threshold_days=policy_data.long_leave_threshold_days,
        min_advance_days_for_long_leave=policy_data.min_advance_days_for_long_leave,
        max_consecutive_leave_days=policy_data.max_consecutive_leave_days,
        max_unplanned_leaves_30_days=policy_data.max_unplanned_leaves_30_days,
        max_leaves_90_days=policy_data.max_leaves_90_days,
        max_pattern_score=policy_data.max_pattern_score,
        history_window_days=policy_data.history_window_days,
        blackout_periods=policy_data.blackout_periods,
        holidays=policy_data.holidays
    )
    
    db.add(policy)
    db.commit()
    db.refresh(policy)
    
    return LeavePolicyResponse.model_validate(policy)


@router.put("/policies/{policy_id}", response_model=LeavePolicyResponse)
async def update_policy(
    policy_id: int,
    policy_data: LeavePolicyUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update a leave policy"""
    policy = db.query(LeavePolicy).filter(LeavePolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    update_data = policy_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
    
    db.commit()
    db.refresh(policy)
    
    return LeavePolicyResponse.model_validate(policy)


# ========== AI Configuration ==========

@router.get("/ai-config", response_model=List[AIConfigResponse])
async def get_ai_configs(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all AI configurations"""
    configs = db.query(AIConfiguration).all()
    return [AIConfigResponse.model_validate(c) for c in configs]


@router.post("/ai-config", response_model=AIConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_config(
    config_data: AIConfigCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create AI configuration"""
    config = AIConfiguration(
        name=config_data.name,
        provider=config_data.provider,
        model_name=config_data.model_name,
        temperature=config_data.temperature,
        min_confidence_to_approve=config_data.min_confidence_to_approve,
        min_confidence_to_auto_reject=config_data.min_confidence_to_auto_reject,
        timeout_ms=config_data.timeout_ms,
        fallback_mode=config_data.fallback_mode
    )
    
    db.add(config)
    db.commit()
    db.refresh(config)
    
    return AIConfigResponse.model_validate(config)


@router.put("/ai-config/{config_id}", response_model=AIConfigResponse)
async def update_ai_config(
    config_id: int,
    config_data: AIConfigUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update AI configuration"""
    config = db.query(AIConfiguration).filter(AIConfiguration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)
    
    db.commit()
    db.refresh(config)
    
    return AIConfigResponse.model_validate(config)


# ========== Holidays ==========

@router.get("/holidays", response_model=List[HolidayResponse])
async def get_holidays(
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get holidays"""
    query = db.query(Holiday).filter(Holiday.is_active == True)
    
    if year:
        query = query.filter(func.year(Holiday.date) == year)
    
    holidays = query.order_by(Holiday.date.asc()).all()
    return [HolidayResponse.model_validate(h) for h in holidays]


@router.post("/holidays", response_model=HolidayResponse, status_code=status.HTTP_201_CREATED)
async def create_holiday(
    holiday_data: HolidayCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a holiday"""
    holiday = Holiday(
        name=holiday_data.name,
        date=holiday_data.date,
        type=holiday_data.type,
        location=holiday_data.location
    )
    
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    
    return HolidayResponse.model_validate(holiday)


@router.delete("/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete a holiday"""
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    holiday.is_active = False
    db.commit()
    
    return {"message": "Holiday deleted successfully"}


# ========== Audit Logs ==========

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    leave_request_id: Optional[int] = None,
    actor_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get audit logs"""
    query = db.query(LeaveAuditLog)
    
    if leave_request_id:
        query = query.filter(LeaveAuditLog.leave_request_id == leave_request_id)
    if actor_id:
        query = query.filter(LeaveAuditLog.actor_id == actor_id)
    
    logs = query.order_by(LeaveAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return [AuditLogResponse.model_validate(log) for log in logs]


@router.get("/system-stats")
async def get_system_stats(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get system statistics for admin dashboard"""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_users = db.query(User).filter(User.is_active == True).count()
    total_departments = db.query(Department).count()
    
    requests_today = db.query(LeaveRequest).filter(
        LeaveRequest.created_at >= today
    ).count()
    
    ai_processed_today = db.query(LeaveRequest).filter(
        LeaveRequest.created_at >= today,
        LeaveRequest.ai_validity_score.isnot(None)
    ).count()
    
    # Calculate auto-approved rate
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    total_requests = db.query(LeaveRequest).filter(
        LeaveRequest.created_at >= month_start
    ).count()
    
    auto_approved = db.query(LeaveRequest).filter(
        LeaveRequest.created_at >= month_start,
        LeaveRequest.status == LeaveStatus.APPROVED,
        LeaveRequest.ai_validity_score >= 80
    ).count()
    
    auto_approved_rate = (auto_approved / total_requests * 100) if total_requests > 0 else 0
    
    return {
        "total_users": total_users,
        "total_departments": total_departments,
        "total_requests_today": requests_today,
        "ai_processed_today": ai_processed_today,
        "auto_approved_rate": round(auto_approved_rate, 1),
        "system_health": "healthy"
    }


@router.get("/calendar-events")
async def get_calendar_events(
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get calendar events for a specific month"""
    from calendar import monthrange
    
    _, last_day = monthrange(year, month)
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    events = []
    
    # Get holidays
    holidays = db.query(Holiday).filter(
        Holiday.date >= start_date,
        Holiday.date <= end_date,
        Holiday.is_active == True
    ).all()
    
    for h in holidays:
        events.append({
            "id": h.id,
            "title": h.name,
            "date": h.date.strftime("%Y-%m-%d"),
            "type": "holiday"
        })
    
    # Get approved leaves (for HR/Admin, show all; for employees, show team)
    leave_query = db.query(LeaveRequest).filter(
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date,
        LeaveRequest.status == LeaveStatus.APPROVED
    )
    
    if current_user.role == UserRole.EMPLOYEE:
        # Only show team members if employee
        if current_user.department_id:
            team_members = db.query(User.id).filter(
                User.department_id == current_user.department_id
            ).all()
            leave_query = leave_query.filter(
                LeaveRequest.employee_id.in_([m.id for m in team_members])
            )
    
    leaves = leave_query.all()
    
    for leave in leaves:
        employee = db.query(User).filter(User.id == leave.employee_id).first()
        events.append({
            "id": leave.id + 10000,  # Offset to avoid ID collision
            "title": f"{leave.leave_type} Leave",
            "date": leave.start_date.strftime("%Y-%m-%d"),
            "type": "leave",
            "employee_name": f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            "leave_type": leave.leave_type
        })
    
    return events


# ========== Helper Functions ==========

def _generate_ai_suggestion(user: User, balances: List[LeaveBalance], db: Session) -> Optional[str]:
    """Generate AI-powered suggestion for employee"""
    # Check for upcoming long weekends
    today = datetime.now()
    
    # Get upcoming holidays in next 30 days
    upcoming_holidays = db.query(Holiday).filter(
        Holiday.date >= today,
        Holiday.date <= today + timedelta(days=30),
        Holiday.is_active == True
    ).all()
    
    for holiday in upcoming_holidays:
        holiday_weekday = holiday.date.weekday()
        
        # If holiday is on Thursday, suggest taking Friday off
        if holiday_weekday == 3:  # Thursday
            return f"You have {holiday.name} coming up on {holiday.date.strftime('%A, %B %d')}. Consider taking Friday off to enjoy a 4-day break!"
        
        # If holiday is on Tuesday, suggest taking Monday off
        if holiday_weekday == 1:  # Tuesday
            return f"You have {holiday.name} coming up on {holiday.date.strftime('%A, %B %d')}. Consider taking Monday off to enjoy a 4-day break!"
    
    # Check if user hasn't taken leave in a while
    last_leave = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == user.id,
        LeaveRequest.status == LeaveStatus.APPROVED
    ).order_by(LeaveRequest.end_date.desc()).first()
    
    if last_leave:
        days_since_leave = (today - last_leave.end_date).days
        if days_since_leave > 45:
            return f"Our AI suggests you've worked {days_since_leave} days without a break. Stress levels might be higher than usual. Consider taking some time off!"
    
    return None


# ========== Company Policy Routes ==========

@router.get("/policy", response_model=CompanyPolicyResponse)
async def get_company_policy(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current company policy settings - accessible to all authenticated users"""
    policy = db.query(CompanyPolicy).order_by(CompanyPolicy.updated_at.desc()).first()
    
    if not policy:
        # Create default policy if none exists
        policy = CompanyPolicy(
            weekly_off_type=WeeklyOffType.SAT_SUN,
            description="Default policy: Saturday and Sunday weekly off",
            effective_from=datetime.now()
        )
        db.add(policy)
        db.commit()
        db.refresh(policy)
    
    return CompanyPolicyResponse(
        id=policy.id,
        weekly_off_type=policy.weekly_off_type.value,
        description=policy.description,
        effective_from=policy.effective_from,
        updated_at=policy.updated_at
    )


@router.put("/policy", response_model=CompanyPolicyResponse)
async def update_company_policy(
    policy_data: CompanyPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update company policy settings - Admin only"""
    # Validate weekly_off_type
    try:
        weekly_off_enum = WeeklyOffType(policy_data.weekly_off_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid weekly_off_type. Must be one of: SUNDAY, SAT_SUN, ALT_SAT"
        )
    
    # Get or create policy
    policy = db.query(CompanyPolicy).order_by(CompanyPolicy.updated_at.desc()).first()
    
    if not policy:
        policy = CompanyPolicy()
        db.add(policy)
    
    policy.weekly_off_type = weekly_off_enum
    policy.description = policy_data.description or f"Weekly off type: {policy_data.weekly_off_type}"
    policy.effective_from = datetime.now()
    
    db.commit()
    db.refresh(policy)
    
    return CompanyPolicyResponse(
        id=policy.id,
        weekly_off_type=policy.weekly_off_type.value,
        description=policy.description,
        effective_from=policy.effective_from,
        updated_at=policy.updated_at
    )


# ========== Working Days Calculation API ==========

@router.post("/calculate-working-days", response_model=dict)
async def calculate_working_days_api(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate working days between two dates based on company policy.
    Returns detailed breakdown of working days, weekends, and holidays.
    """
    from app.services.leave_utils import calculate_working_days_detailed
    from datetime import datetime
    
    # Parse dates
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    
    # Validate dates
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be after end_date"
        )
    
    # Get company policy
    policy = db.query(CompanyPolicy).order_by(CompanyPolicy.updated_at.desc()).first()
    weekly_off_type = policy.weekly_off_type.value if policy else "SAT_SUN"
    
    # Get holidays in the date range
    holidays = db.query(Holiday).filter(
        Holiday.date >= start,
        Holiday.date <= end,
        Holiday.is_active == True
    ).all()
    
    holiday_dates = [h.date for h in holidays]
    
    # Calculate working days
    result = calculate_working_days_detailed(start, end, weekly_off_type, holiday_dates)
    
    # Add policy info
    result["policy"] = {
        "weekly_off_type": weekly_off_type,
        "description": policy.description if policy else "Default: Saturday and Sunday off"
    }
    
    return result
