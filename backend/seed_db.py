"""
Database seed script to populate initial data
"""
import sys
sys.path.append(".")

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core import engine, SessionLocal, get_password_hash
from app.models import (
    User, UserRole, Department, LeavePolicy, LeaveBalance, 
    LeaveType, Holiday, AIConfiguration, Base
)


def seed_database():
    """Seed the database with initial data"""
    # Drop all tables and recreate
    print("Dropping existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Seeding database...")
        
        # Create departments
        departments = [
            Department(name="Engineering", code="ENG", description="Software Engineering Team"),
            Department(name="Product Design", code="PD", description="Product Design Team"),
            Department(name="Human Resources", code="HR", description="Human Resources Department"),
            Department(name="Finance", code="FIN", description="Finance Department"),
            Department(name="Customer Success", code="CS", description="Customer Success Team"),
            Department(name="Marketing", code="MKT", description="Marketing Team"),
        ]
        
        for dept in departments:
            db.add(dept)
        db.commit()
        
        print("✓ Departments created")
        
        # Get department IDs
        eng_dept = db.query(Department).filter(Department.code == "ENG").first()
        pd_dept = db.query(Department).filter(Department.code == "PD").first()
        hr_dept = db.query(Department).filter(Department.code == "HR").first()
        fin_dept = db.query(Department).filter(Department.code == "FIN").first()
        cs_dept = db.query(Department).filter(Department.code == "CS").first()
        
        # Create users
        users = [
            # Admin
            User(
                email="admin@leaveai.com",
                hashed_password=get_password_hash("admin123"),
                first_name="System",
                last_name="Admin",
                role=UserRole.ADMIN,
                department_id=hr_dept.id,
                tenure_months=48,
                level="L6",
                is_active=True
            ),
            # HR Users
            User(
                email="sarah.jenkins@leaveai.com",
                hashed_password=get_password_hash("hr123"),
                first_name="Sarah",
                last_name="Jenkins",
                role=UserRole.HR,
                department_id=hr_dept.id,
                tenure_months=36,
                level="L5",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah"
            ),
            User(
                email="jordan.smith@leaveai.com",
                hashed_password=get_password_hash("hr123"),
                first_name="Jordan",
                last_name="Smith",
                role=UserRole.HR,
                department_id=hr_dept.id,
                tenure_months=24,
                level="L4",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Jordan"
            ),
            # Employees
            User(
                email="alex.rivera@leaveai.com",
                hashed_password=get_password_hash("employee123"),
                first_name="Alex",
                last_name="Rivera",
                role=UserRole.EMPLOYEE,
                department_id=eng_dept.id,
                tenure_months=18,
                level="L3",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Alex"
            ),
            User(
                email="alex.johnson@leaveai.com",
                hashed_password=get_password_hash("employee123"),
                first_name="Alex",
                last_name="Johnson",
                role=UserRole.EMPLOYEE,
                department_id=pd_dept.id,
                tenure_months=24,
                level="L4",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=AlexJ"
            ),
            User(
                email="mila.theron@leaveai.com",
                hashed_password=get_password_hash("employee123"),
                first_name="Mila",
                last_name="Theron",
                role=UserRole.EMPLOYEE,
                department_id=pd_dept.id,
                tenure_months=12,
                level="L3",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Mila"
            ),
            User(
                email="jamie.chen@leaveai.com",
                hashed_password=get_password_hash("employee123"),
                first_name="Jamie",
                last_name="Chen",
                role=UserRole.EMPLOYEE,
                department_id=cs_dept.id,
                tenure_months=15,
                level="L3",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Jamie"
            ),
            User(
                email="sophia.martinez@leaveai.com",
                hashed_password=get_password_hash("employee123"),
                first_name="Sophia",
                last_name="Martinez",
                role=UserRole.EMPLOYEE,
                department_id=fin_dept.id,
                tenure_months=30,
                level="L4",
                is_active=True,
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Sophia"
            ),
        ]
        
        for user in users:
            db.add(user)
        db.commit()
        
        print("✓ Users created")
        
        # Set manager relationships
        sarah = db.query(User).filter(User.email == "sarah.jenkins@leaveai.com").first()
        for user in db.query(User).filter(User.role == UserRole.EMPLOYEE).all():
            user.manager_id = sarah.id
        db.commit()
        
        # Create leave policy
        default_policy = LeavePolicy(
            name="Default Policy",
            department_id=None,
            annual_leave_days=22,
            sick_leave_days=10,
            casual_leave_days=5,
            maternity_leave_days=90,
            paternity_leave_days=15,
            allow_negative_balance=False,
            reason_mandatory=True,
            require_manager_approval=True,
            long_leave_threshold_days=5,
            min_advance_days_for_long_leave=7,
            max_consecutive_leave_days=15,
            max_unplanned_leaves_30_days=3,
            max_leaves_90_days=10,
            max_pattern_score=0.7,
            history_window_days=180,
            blackout_periods=[
                {"start_date": "2026-12-20", "end_date": "2026-12-31"}
            ],
            holidays=["2026-01-01", "2026-07-04", "2026-12-25"],
            is_active=True
        )
        db.add(default_policy)
        db.commit()
        
        print("✓ Leave policy created")
        
        # Create leave balances for ALL users (including HR and Admin)
        current_year = datetime.now().year
        all_users = db.query(User).all()
        
        for user in all_users:
            balances = [
                LeaveBalance(
                    employee_id=user.id,
                    leave_type=LeaveType.ANNUAL,
                    year=current_year,
                    total_days=22,
                    used_days=9.5,
                    pending_days=0,
                    remaining_days=12.5,
                    accrual_rate_per_month=2.5,
                    balance_reset_date=datetime(current_year + 1, 1, 1)
                ),
                LeaveBalance(
                    employee_id=user.id,
                    leave_type=LeaveType.SICK,
                    year=current_year,
                    total_days=10,
                    used_days=2,
                    pending_days=0,
                    remaining_days=5,
                    accrual_rate_per_month=0,
                    balance_reset_date=datetime(current_year + 1, 1, 1)
                ),
                LeaveBalance(
                    employee_id=user.id,
                    leave_type=LeaveType.CASUAL,
                    year=current_year,
                    total_days=5,
                    used_days=3,
                    pending_days=0,
                    remaining_days=2,
                    accrual_rate_per_month=0,
                    balance_reset_date=datetime(current_year + 1, 1, 1)
                ),
            ]
            
            for balance in balances:
                db.add(balance)
        
        db.commit()
        print("✓ Leave balances created")
        
        # Create holidays
        holidays = [
            Holiday(name="New Year's Day", date=datetime(2026, 1, 1), type="PUBLIC"),
            Holiday(name="Martin Luther King Jr. Day", date=datetime(2026, 1, 19), type="PUBLIC"),
            Holiday(name="Presidents' Day", date=datetime(2026, 2, 16), type="PUBLIC"),
            Holiday(name="Memorial Day", date=datetime(2026, 5, 25), type="PUBLIC"),
            Holiday(name="Independence Day", date=datetime(2026, 7, 4), type="PUBLIC"),
            Holiday(name="Labor Day", date=datetime(2026, 9, 7), type="PUBLIC"),
            Holiday(name="Thanksgiving", date=datetime(2026, 11, 26), type="PUBLIC"),
            Holiday(name="Christmas Day", date=datetime(2026, 12, 25), type="PUBLIC"),
        ]
        
        for holiday in holidays:
            db.add(holiday)
        db.commit()
        
        print("✓ Holidays created")
        
        # Create AI configuration
        ai_config = AIConfiguration(
            name="Default AI Config",
            provider="GEMINI",
            model_name="gemini-2.0-flash",
            temperature=0.3,
            min_confidence_to_approve=75,
            min_confidence_to_auto_reject=25,
            timeout_ms=30000,
            fallback_mode="MANUAL_REVIEW",
            is_active=True
        )
        db.add(ai_config)
        db.commit()
        
        print("✓ AI configuration created")
        
        print("\n✅ Database seeded successfully!")
        print("\nTest accounts:")
        print("  Admin: admin@leaveai.com / admin123")
        print("  HR: sarah.jenkins@leaveai.com / hr123")
        print("  Employee: alex.rivera@leaveai.com / employee123")
        
    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
