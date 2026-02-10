from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    HR = "HR"
    ADMIN = "ADMIN"


class LeaveStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    PENDING_REVIEW = "PENDING_REVIEW"


class LeaveType(str, Enum):
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    CASUAL = "CASUAL"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    UNPAID = "UNPAID"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# ========== User Schemas ==========

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = UserRole.EMPLOYEE
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    grade: Optional[str] = None
    level: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[int] = None
    manager_id: Optional[int] = None
    location: Optional[str] = None
    grade: Optional[str] = None
    level: Optional[str] = None
    is_active: Optional[bool] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    tenure_months: int
    is_active: bool
    avatar_url: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithDepartment(UserResponse):
    department_name: Optional[str] = None


# ========== Auth Schemas ==========

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ========== Department Schemas ==========

class DepartmentBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    id: int
    created_at: datetime
    employee_count: int = 0
    
    class Config:
        from_attributes = True


# ========== Leave Balance Schemas ==========

class LeaveBalanceBase(BaseModel):
    leave_type: LeaveType
    year: int
    total_days: float
    used_days: float = 0
    pending_days: float = 0
    remaining_days: float
    accrual_rate_per_month: float = 0


class LeaveBalanceCreate(LeaveBalanceBase):
    employee_id: int


class LeaveBalanceResponse(LeaveBalanceBase):
    id: int
    employee_id: int
    balance_reset_date: Optional[datetime]
    
    class Config:
        from_attributes = True


class LeaveBalanceSummary(BaseModel):
    annual: LeaveBalanceResponse
    sick: LeaveBalanceResponse
    casual: LeaveBalanceResponse


# ========== Leave Request Schemas ==========

class LeaveRequestBase(BaseModel):
    leave_type: LeaveType
    start_date: datetime
    end_date: datetime
    reason_text: Optional[str] = None
    medical_certificate_url: Optional[str] = None
    medical_certificate_filename: Optional[str] = None
    medical_certificate_size: Optional[int] = None


class LeaveRequestCreate(LeaveRequestBase):
    @model_validator(mode='after')
    def validate_medical_certificate(self):
        # Calculate leave duration
        leave_days = (self.end_date - self.start_date).days + 1
        
        # Validate medical certificate is provided for SICK leave > 2 days
        # As per company policy: Medical certificate required for sick leave exceeding 2 consecutive days
        if self.leave_type == LeaveType.SICK and leave_days > 2:
            if not self.medical_certificate_url:
                raise ValueError("Medical certificate is mandatory for sick leave exceeding 2 consecutive days")
            # Validate file size (5MB = 5 * 1024 * 1024 bytes)
            if self.medical_certificate_size and self.medical_certificate_size > 5 * 1024 * 1024:
                raise ValueError("Medical certificate file size must not exceed 5MB")
        
        # If certificate is provided for any sick leave, validate file size
        if self.leave_type == LeaveType.SICK and self.medical_certificate_url:
            if self.medical_certificate_size and self.medical_certificate_size > 5 * 1024 * 1024:
                raise ValueError("Medical certificate file size must not exceed 5MB")
        
        return self


class LeaveRequestUpdate(BaseModel):
    status: Optional[LeaveStatus] = None
    reviewer_comments: Optional[str] = None


class AIEvaluation(BaseModel):
    reason_category: Optional[str] = None
    validity_score: float = 0
    risk_flags: List[str] = []
    recommended_action: str = "MANUAL_REVIEW"
    rationale: Optional[str] = None


class LeaveRequestResponse(LeaveRequestBase):
    id: int
    request_number: str
    employee_id: int
    total_days: float
    status: LeaveStatus
    risk_level: RiskLevel
    medical_certificate_validation: Optional[dict] = None
    ai_validity_score: Optional[float]
    ai_risk_flags: Optional[List[str]]
    ai_recommended_action: Optional[str]
    ai_rationale: Optional[str]
    ai_reason_category: Optional[str]
    decision_engine: Optional[str]
    decision_explanation: Optional[str]
    reviewed_by: Optional[int]
    reviewed_at: Optional[datetime]
    reviewer_comments: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class LeaveRequestWithEmployee(LeaveRequestResponse):
    employee_name: str
    employee_email: str
    employee_department: Optional[str]
    employee_avatar: Optional[str]


class LeaveRequestDetail(LeaveRequestWithEmployee):
    employee_total_balance: Optional[float]
    employee_used_ytd: Optional[float]
    team_coverage: Optional[float]
    team_context: Optional[str]
    historical_pattern: Optional[str]


class EmployeeLeaveBalance(BaseModel):
    """Employee's leave balance for a specific leave type"""
    leave_type: str
    total_days: float
    used_days: float
    pending_days: float
    remaining_days: float
    
    class Config:
        from_attributes = True


class EmployeeLeaveHistory(BaseModel):
    """Past leave request summary"""
    id: int
    request_number: str
    leave_type: str
    start_date: datetime
    end_date: datetime
    total_days: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmployeeLeaveStats(BaseModel):
    """Statistical summary of employee leave patterns"""
    total_leaves_this_year: int
    total_days_taken_this_year: float
    leaves_last_30_days: int
    leaves_last_90_days: int
    most_used_leave_type: Optional[str]
    average_leave_duration: Optional[float]
    pending_requests_count: int


class LeaveRequestForHRReview(LeaveRequestWithEmployee):
    """Enhanced leave request with complete employee leave data for HR review"""
    # Employee leave balances (all types)
    employee_leave_balances: List[EmployeeLeaveBalance]
    
    # Recent leave history (last 10 requests)
    employee_leave_history: List[EmployeeLeaveHistory]
    
    # Statistical summary
    employee_leave_stats: EmployeeLeaveStats


# ========== Leave Policy Schemas ==========

class LeavePolicyBase(BaseModel):
    name: str
    department_id: Optional[int] = None
    location: Optional[str] = None
    grade: Optional[str] = None
    annual_leave_days: int = 22
    sick_leave_days: int = 10
    casual_leave_days: int = 5
    maternity_leave_days: int = 90
    paternity_leave_days: int = 15
    allow_negative_balance: bool = False
    reason_mandatory: bool = True
    require_manager_approval: bool = True
    long_leave_threshold_days: int = 5
    min_advance_days_for_long_leave: int = 7
    max_consecutive_leave_days: int = 15
    max_unplanned_leaves_30_days: int = 3
    max_leaves_90_days: int = 10
    max_pattern_score: float = 0.7
    history_window_days: int = 180


class LeavePolicyCreate(LeavePolicyBase):
    blackout_periods: List[dict] = []
    holidays: List[str] = []


class LeavePolicyUpdate(BaseModel):
    name: Optional[str] = None
    annual_leave_days: Optional[int] = None
    sick_leave_days: Optional[int] = None
    casual_leave_days: Optional[int] = None
    allow_negative_balance: Optional[bool] = None
    reason_mandatory: Optional[bool] = None
    require_manager_approval: Optional[bool] = None
    long_leave_threshold_days: Optional[int] = None
    min_advance_days_for_long_leave: Optional[int] = None
    max_consecutive_leave_days: Optional[int] = None
    max_unplanned_leaves_30_days: Optional[int] = None
    max_leaves_90_days: Optional[int] = None
    max_pattern_score: Optional[float] = None
    blackout_periods: Optional[List[dict]] = None
    holidays: Optional[List[str]] = None
    is_active: Optional[bool] = None


class LeavePolicyResponse(LeavePolicyBase):
    id: int
    blackout_periods: List[dict]
    holidays: List[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== AI Configuration Schemas ==========

class AIConfigBase(BaseModel):
    name: str
    provider: str = "GEMINI"
    model_name: str = "gemini-2.0-flash"
    temperature: float = 0.3
    min_confidence_to_approve: int = 75
    min_confidence_to_auto_reject: int = 25
    timeout_ms: int = 30000
    fallback_mode: str = "MANUAL_REVIEW"


class AIConfigCreate(AIConfigBase):
    pass


class AIConfigUpdate(BaseModel):
    temperature: Optional[float] = None
    min_confidence_to_approve: Optional[int] = None
    min_confidence_to_auto_reject: Optional[int] = None
    timeout_ms: Optional[int] = None
    fallback_mode: Optional[str] = None
    is_active: Optional[bool] = None


class AIConfigResponse(AIConfigBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Audit Log Schemas ==========

class AuditLogResponse(BaseModel):
    id: int
    leave_request_id: int
    action: str
    actor_id: Optional[int]
    actor_type: Optional[str]
    previous_status: Optional[str]
    new_status: Optional[str]
    details: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Holiday Schemas ==========

class HolidayBase(BaseModel):
    name: str
    date: datetime
    type: str = "PUBLIC"
    location: Optional[str] = None


class HolidayCreate(HolidayBase):
    pass


class HolidayResponse(HolidayBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Dashboard Schemas ==========

class DashboardStats(BaseModel):
    total_pending: int
    high_risk_flagged: int
    team_coverage: float
    pending_change_percent: float


class EmployeeDashboard(BaseModel):
    leave_balances: List[LeaveBalanceResponse]
    recent_requests: List[LeaveRequestResponse]
    upcoming_holidays: List[HolidayResponse]
    ai_suggestion: Optional[str] = None


class HRDashboard(BaseModel):
    stats: DashboardStats
    pending_requests: List[LeaveRequestWithEmployee]


class AdminDashboard(BaseModel):
    total_employees: int
    total_departments: int
    total_requests_this_month: int
    approval_rate: float
    ai_accuracy: float
    recent_audit_logs: List[AuditLogResponse]


# ========== Approval Task Schemas ==========

class ApprovalTaskResponse(BaseModel):
    id: int
    leave_request_id: int
    queue: str
    assignee_id: Optional[int]
    priority: str
    notes: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Stats Schemas ==========

class LeaveStats(BaseModel):
    unplanned_leaves_last_30_days: int = 0
    total_leaves_last_90_days: int = 0
    consecutive_leave_streak_days: int = 0
    monday_leaves_last_90_days: int = 0
    friday_leaves_last_90_days: int = 0
    monday_friday_pattern_score: float = 0
    risk_level: str = "LOW"
