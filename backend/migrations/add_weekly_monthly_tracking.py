"""
Migration: Add weekly/monthly tracking columns to leave_policies table
Created: 2026-03-01
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()

try:
    print("Adding weekly/monthly tracking columns to leave_policies table...")
    
    # Check if columns exist first
    check_columns_query = text("""
        SELECT COUNT(*) as count
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'leave_policies' 
        AND COLUMN_NAME IN ('max_leaves_per_week', 'max_leaves_per_month', 'max_days_per_week', 'max_days_per_month')
    """)
    
    result = db.execute(check_columns_query).fetchone()
    existing_count = result[0] if result else 0
    
    if existing_count == 4:
        print("✓ All tracking columns already exist. Skipping migration.")
    else:
        print(f"Found {existing_count}/4 columns. Adding missing columns...")
        
        # Check and add each column individually
        columns_to_add = [
            ('max_leaves_per_week', 'INT DEFAULT 2', 'Maximum number of leave requests allowed per week'),
            ('max_leaves_per_month', 'INT DEFAULT 5', 'Maximum number of leave requests allowed per calendar month'),
            ('max_days_per_week', 'INT DEFAULT 3', 'Maximum number of leave days allowed per week'),
            ('max_days_per_month', 'INT DEFAULT 7', 'Maximum number of leave days allowed per calendar month')
        ]
        
        for column_name, column_def, comment in columns_to_add:
            # Check if this specific column exists
            check_query = text(f"""
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'leave_policies' 
                AND COLUMN_NAME = '{column_name}'
            """)
            
            result = db.execute(check_query).fetchone()
            exists = result[0] > 0 if result else False
            
            if not exists:
                migration_sql = text(f"""
                    ALTER TABLE leave_policies 
                    ADD COLUMN {column_name} {column_def}
                    COMMENT '{comment}'
                """)
                db.execute(migration_sql)
                db.commit()
                print(f"✓ Added column: {column_name}")
            else:
                print(f"  Column {column_name} already exists, skipping...")
        
        print("✓ Migration completed successfully!")
        
except Exception as e:
    print(f"✗ Migration failed: {e}")
    db.rollback()
    raise
finally:
    db.close()
