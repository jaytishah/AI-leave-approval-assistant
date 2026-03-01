"""
Migration: Add weekly and monthly leave limits to leave_policy table

This migration adds support for calendar-based weekly and monthly leave tracking.
New columns allow HR to set limits on:
- Maximum leave requests per week
- Maximum leave requests per month
- Maximum leave days per week
- Maximum leave days per month

Run this migration after implementing weekly/monthly tracking feature.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def upgrade():
    """Add weekly and monthly limit columns to leave_policy table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        columns_to_add = [
            ("max_leaves_per_week", "INTEGER DEFAULT 2"),
            ("max_leaves_per_month", "INTEGER DEFAULT 5"),
            ("max_days_per_week", "INTEGER DEFAULT 3"),
            ("max_days_per_month", "INTEGER DEFAULT 7")
        ]
        
        for column_name, column_def in columns_to_add:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'leave_policy' 
                AND COLUMN_NAME = :column_name;
            """), {"column_name": column_name})
            
            exists = result.fetchone()[0] > 0
            
            if not exists:
                # Add column
                conn.execute(text(f"""
                    ALTER TABLE leave_policy 
                    ADD COLUMN {column_name} {column_def};
                """))
                print(f"✓ Added {column_name} column to leave_policy table")
            else:
                print(f"⚠ Column {column_name} already exists, skipping")
        
        conn.commit()
        print("\n✓ Migration completed successfully!")


def downgrade():
    """Remove weekly and monthly limit columns from leave_policy table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        columns_to_remove = [
            "max_leaves_per_week",
            "max_leaves_per_month",
            "max_days_per_week",
            "max_days_per_month"
        ]
        
        for column_name in columns_to_remove:
            # Check if column exists
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'leave_policy' 
                AND COLUMN_NAME = :column_name;
            """), {"column_name": column_name})
            
            exists = result.fetchone()[0] > 0
            
            if exists:
                # Remove column
                conn.execute(text(f"""
                    ALTER TABLE leave_policy 
                    DROP COLUMN {column_name};
                """))
                print(f"✓ Removed {column_name} column from leave_policy table")
            else:
                print(f"⚠ Column {column_name} doesn't exist, skipping")
        
        conn.commit()
        print("\n✓ Downgrade completed successfully!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        print("Running downgrade...")
        downgrade()
    else:
        print("Running upgrade...")
        upgrade()
