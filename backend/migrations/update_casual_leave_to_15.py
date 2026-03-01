"""
Migration: Update Casual Leave to 15 days/year (Company Policy Compliance)

This migration updates all leave policies to reflect the company policy:
- Casual Leave: 15 days/year (was 5 days in some configs)

Run this after Phase 1 implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def upgrade():
    """Update casual_leave_days to 15 for all policies"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check current values
        result = conn.execute(text("""
            SELECT id, name, casual_leave_days 
            FROM leave_policies
        """))
        
        policies = result.fetchall()
        
        if not policies:
            print("⚠ No leave policies found in database")
            return
        
        print("\nCurrent Casual Leave Configuration:")
        print("="*60)
        for policy in policies:
            print(f"Policy: {policy[1]} (ID: {policy[0]}) - Current: {policy[2]} days")
        
        # Update all policies to 15 days
        result = conn.execute(text("""
            UPDATE leave_policies 
            SET casual_leave_days = 15
            WHERE casual_leave_days != 15
        """))
        
        updated_count = result.rowcount
        conn.commit()
        
        if updated_count > 0:
            print(f"\n✓ Updated {updated_count} policy/policies to 15 days casual leave")
        else:
            print("\n✓ All policies already have 15 days casual leave")
        
        # Verify the update
        result = conn.execute(text("""
            SELECT id, name, casual_leave_days 
            FROM leave_policies
        """))
        
        policies = result.fetchall()
        
        print("\nUpdated Casual Leave Configuration:")
        print("="*60)
        for policy in policies:
            print(f"Policy: {policy[1]} (ID: {policy[0]}) - New: {policy[2]} days")
        
    print("\n✓ Migration completed: Casual Leave is now 15 days/year (Company Policy)")


def downgrade():
    """Revert casual_leave_days to 5 for all policies"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE leave_policies 
            SET casual_leave_days = 5
            WHERE casual_leave_days = 15
        """))
        
        conn.commit()
        
    print("✓ Migration rolled back: Casual Leave reverted to 5 days")


if __name__ == "__main__":
    print("Running migration: Update Casual Leave to 15 days/year...")
    upgrade()
