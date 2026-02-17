from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta

from app.core import get_db
from app.models import User, UserRole, Department, LeaveBalance, LeaveType
from app.schemas import (
    UserResponse, UserUpdate, UserCreate, UserWithDepartment,
    DepartmentResponse, DepartmentCreate, LeaveBalanceResponse, LeaveBalanceCreate
)
from app.api.auth import get_current_user, require_role, get_password_hash

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/", response_model=List[UserWithDepartment])
async def get_all_users(
    role: Optional[UserRole] = None,
    department_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all users (HR/Admin only)"""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(offset).limit(limit).all()
    
    result = []
    for user in users:
        user_data = UserResponse.model_validate(user).model_dump()
        user_data["department_name"] = user.department.name if user.department else None
        result.append(UserWithDepartment(**user_data))
    
    return result


@router.get("/employees", response_model=List[UserWithDepartment])
async def get_all_employees(
    department_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all employees (HR/Admin only)"""
    query = db.query(User).filter(User.role == UserRole.EMPLOYEE, User.is_active == True)
    
    if department_id:
        query = query.filter(User.department_id == department_id)
    
    users = query.offset(offset).limit(limit).all()
    
    result = []
    for user in users:
        user_data = UserResponse.model_validate(user).model_dump()
        user_data["department_name"] = user.department.name if user.department else None
        result.append(UserWithDepartment(**user_data))
    
    return result


@router.get("/{user_id}", response_model=UserWithDepartment)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    # Employees can only view their own profile
    if current_user.role == UserRole.EMPLOYEE and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = UserResponse.model_validate(user).model_dump()
    user_data["department_name"] = user.department.name if user.department else None
    
    return UserWithDepartment(**user_data)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin only)"""
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=user_data.role,
        department_id=user_data.department_id,
        manager_id=user_data.manager_id,
        location=user_data.location,
        grade=user_data.grade,
        level=user_data.level
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Initialize leave balances for new employee
    if new_user.role == UserRole.EMPLOYEE:
        _initialize_leave_balances(db, new_user.id)
    
    return UserResponse.model_validate(new_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user"""
    # Employees can only update their own profile (limited fields)
    if current_user.role == UserRole.EMPLOYEE and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Employees can only update certain fields
    if current_user.role == UserRole.EMPLOYEE:
        allowed_fields = {"first_name", "last_name", "avatar_url"}
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Deactivate user (Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}


@router.get("/{user_id}/balance", response_model=List[LeaveBalanceResponse])
async def get_user_balance(
    user_id: int,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's leave balance"""
    # Employees can only view their own balance
    if current_user.role == UserRole.EMPLOYEE and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this balance")
    
    target_year = year or datetime.now().year
    
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == user_id,
        LeaveBalance.year == target_year
    ).all()
    
    return [LeaveBalanceResponse.model_validate(b) for b in balances]


@router.post("/{user_id}/balance", response_model=LeaveBalanceResponse)
async def set_user_balance(
    user_id: int,
    balance_data: LeaveBalanceCreate,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Set or update user's leave balance (HR/Admin only)"""
    # Check if balance exists
    existing_balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == user_id,
        LeaveBalance.leave_type == balance_data.leave_type,
        LeaveBalance.year == balance_data.year
    ).first()
    
    if existing_balance:
        # Update existing
        existing_balance.total_days = balance_data.total_days
        existing_balance.used_days = balance_data.used_days
        existing_balance.pending_days = balance_data.pending_days
        existing_balance.remaining_days = balance_data.remaining_days
        existing_balance.accrual_rate_per_month = balance_data.accrual_rate_per_month
        db.commit()
        db.refresh(existing_balance)
        return LeaveBalanceResponse.model_validate(existing_balance)
    
    # Create new balance
    new_balance = LeaveBalance(
        employee_id=user_id,
        leave_type=balance_data.leave_type,
        year=balance_data.year,
        total_days=balance_data.total_days,
        used_days=balance_data.used_days,
        pending_days=balance_data.pending_days,
        remaining_days=balance_data.remaining_days,
        accrual_rate_per_month=balance_data.accrual_rate_per_month
    )
    
    db.add(new_balance)
    db.commit()
    db.refresh(new_balance)
    
    return LeaveBalanceResponse.model_validate(new_balance)


def _initialize_leave_balances(db: Session, employee_id: int):
    """Initialize default leave balances for new employee"""
    current_year = datetime.now().year
    
    default_balances = [
        (LeaveType.ANNUAL, 22, 2.5),
        (LeaveType.SICK, 10, 0),
        (LeaveType.CASUAL, 5, 0),
    ]
    
    for leave_type, total_days, accrual_rate in default_balances:
        balance = LeaveBalance(
            employee_id=employee_id,
            leave_type=leave_type,
            year=current_year,
            total_days=total_days,
            used_days=0,
            pending_days=0,
            remaining_days=total_days,
            accrual_rate_per_month=accrual_rate,
            balance_reset_date=datetime(current_year + 1, 1, 1)
        )
        db.add(balance)
    
    db.commit()


# ========== Department Routes ==========

@router.get("/departments/", response_model=List[DepartmentResponse])
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all departments"""
    departments = db.query(Department).all()
    result = []
    for dept in departments:
        employee_count = db.query(User).filter(
            User.department_id == dept.id,
            User.is_active == True
        ).count()
        dept_data = DepartmentResponse.model_validate(dept).model_dump()
        dept_data["employee_count"] = employee_count
        result.append(DepartmentResponse(**dept_data))
    return result


@router.post("/departments/", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new department (Admin only)"""
    existing = db.query(Department).filter(
        (Department.name == dept_data.name) | (Department.code == dept_data.code)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Department name or code already exists")
    
    department = Department(
        name=dept_data.name,
        code=dept_data.code,
        description=dept_data.description
    )
    
    db.add(department)
    db.commit()
    db.refresh(department)
    
    return DepartmentResponse.model_validate(department)
