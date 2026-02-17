from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    HR = "HR"
    ADMIN = "ADMIN"


class LeaveStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    PENDING_REVIEW = "PENDING_REVIEW"


class LeaveType(str, enum.Enum):
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    CASUAL = "CASUAL"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    UNPAID = "UNPAID"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WeeklyOffType(str, enum.Enum):
    SUNDAY = "SUNDAY"
    SAT_SUN = "SAT_SUN"
    ALT_SAT = "ALT_SAT"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    location = Column(String(100), nullable=True)
    grade = Column(String(50), nullable=True)
    level = Column(String(50), nullable=True)
    tenure_months = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="employees")
    manager = relationship("User", remote_side=[id], backref="direct_reports")
    leave_requests = relationship("LeaveRequest", back_populates="employee", foreign_keys="LeaveRequest.employee_id")
    leave_balances = relationship("LeaveBalance", back_populates="employee")


class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    employees = relationship("User", back_populates="department")
    leave_policies = relationship("LeavePolicy", back_populates="department")


class LeavePolicy(Base):
    __tablename__ = "leave_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    location = Column(String(100), nullable=True)
    grade = Column(String(50), nullable=True)
    
    # Leave allocations per year
    annual_leave_days = Column(Integer, default=22)
    sick_leave_days = Column(Integer, default=10)
    casual_leave_days = Column(Integer, default=5)
    maternity_leave_days = Column(Integer, default=90)
    paternity_leave_days = Column(Integer, default=15)
    
    # Policy rules
    allow_negative_balance = Column(Boolean, default=False)
    reason_mandatory = Column(Boolean, default=True)
    require_manager_approval = Column(Boolean, default=True)
    long_leave_threshold_days = Column(Integer, default=5)
    min_advance_days_for_long_leave = Column(Integer, default=7)
    max_consecutive_leave_days = Column(Integer, default=15)
    max_unplanned_leaves_30_days = Column(Integer, default=3)
    max_leaves_90_days = Column(Integer, default=10)
    max_pattern_score = Column(Float, default=0.7)
    history_window_days = Column(Integer, default=180)
    
    # Blackout periods (JSON array of {start_date, end_date})
    blackout_periods = Column(JSON, default=[])
    
    # Holidays (JSON array of dates)
    holidays = Column(JSON, default=[])
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="leave_policies")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(20), unique=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_days = Column(Float, nullable=False)
    reason_text = Column(Text, nullable=True)
    
    # Medical certificate for sick leave
    medical_certificate_url = Column(String(500), nullable=True)
    medical_certificate_filename = Column(String(255), nullable=True)
    medical_certificate_size = Column(Integer, nullable=True)  # Size in bytes
    medical_certificate_validation = Column(JSON, nullable=True)  # Validation results
    
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    
    # AI Evaluation Results
    ai_validity_score = Column(Float, nullable=True)
    ai_risk_flags = Column(JSON, nullable=True)
    ai_recommended_action = Column(String(50), nullable=True)
    ai_rationale = Column(Text, nullable=True)
    ai_reason_category = Column(String(100), nullable=True)
    
    # Risk Assessment
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    
    # Decision metadata
    decision_engine = Column(String(50), nullable=True)  # RULES, AI, RULES+AI, MANUAL
    decision_explanation = Column(Text, nullable=True)
    
    # Reviewer info
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer_comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", back_populates="leave_requests", foreign_keys=[employee_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    audit_logs = relationship("LeaveAuditLog", back_populates="leave_request")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    year = Column(Integer, nullable=False)
    total_days = Column(Float, default=0)
    used_days = Column(Float, default=0)
    pending_days = Column(Float, default=0)
    remaining_days = Column(Float, default=0)
    accrual_rate_per_month = Column(Float, default=0)
    last_accrual_date = Column(DateTime, nullable=True)
    balance_reset_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    employee = relationship("User", back_populates="leave_balances")


class LeaveAuditLog(Base):
    __tablename__ = "leave_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    leave_request_id = Column(Integer, ForeignKey("leave_requests.id"), nullable=False)
    action = Column(String(50), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_type = Column(String(50), nullable=True)  # SYSTEM, USER, AI
    previous_status = Column(String(50), nullable=True)
    new_status = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    leave_request = relationship("LeaveRequest", back_populates="audit_logs")
    actor = relationship("User")


class AIConfiguration(Base):
    __tablename__ = "ai_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    provider = Column(String(50), default="GEMINI")
    model_name = Column(String(100), default="gemini-2.0-flash")
    temperature = Column(Float, default=0.3)
    min_confidence_to_approve = Column(Integer, default=75)
    min_confidence_to_auto_reject = Column(Integer, default=25)
    timeout_ms = Column(Integer, default=30000)
    fallback_mode = Column(String(50), default="MANUAL_REVIEW")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    date = Column(DateTime, nullable=False)
    type = Column(String(50), default="PUBLIC")  # PUBLIC, REGIONAL, OPTIONAL
    location = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ApprovalTask(Base):
    __tablename__ = "approval_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    leave_request_id = Column(Integer, ForeignKey("leave_requests.id"), nullable=False)
    queue = Column(String(50), default="HR_MANAGER_QUEUE")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    priority = Column(String(20), default="NORMAL")
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="OPEN")  # OPEN, IN_PROGRESS, COMPLETED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    leave_request = relationship("LeaveRequest")
    assignee = relationship("User")


class CompanyPolicy(Base):
    __tablename__ = "company_policy"
    
    id = Column(Integer, primary_key=True, index=True)
    weekly_off_type = Column(Enum(WeeklyOffType), default=WeeklyOffType.SAT_SUN, nullable=False)
    description = Column(String(255), nullable=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
