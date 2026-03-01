"""
Migration: Add is_emergency field to leave_requests table

This migration adds support for emergency leave requests that can bypass
the 1-day advance notice requirement for Casual Leave.

Run this migration after Phase 1 implementation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def upgrade():
    """Add is_emergency column to leave_requests table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'leave_requests' 
            AND COLUMN_NAME = 'is_emergency';
        """))
        
        exists = result.fetchone()[0] > 0
        
        if not exists:
            # Add is_emergency column with default False
            conn.execute(text("""
                ALTER TABLE leave_requests 
                ADD COLUMN is_emergency BOOLEAN DEFAULT FALSE;
            """))
            print("✓ Added is_emergency column to leave_requests table")
        else:
            print("⚠ Column is_emergency already exists, skipping...")
        
        # Update any existing NULL values to False (safety)
        conn.execute(text("""
            UPDATE leave_requests 
            SET is_emergency = FALSE 
            WHERE is_emergency IS NULL;
        """))
        
        conn.commit()
        
    print("✓ Migration completed: is_emergency field is ready")


def downgrade():
    """Remove is_emergency column from leave_requests table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Check if column exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'leave_requests' 
            AND COLUMN_NAME = 'is_emergency';
        """))
        
        exists = result.fetchone()[0] > 0
        
        if exists:
            conn.execute(text("""
                ALTER TABLE leave_requests 
                DROP COLUMN is_emergency;
            """))
            print("✓ Removed is_emergency column from leave_requests table")
        else:
            print("⚠ Column is_emergency does not exist, skipping...")
        
        conn.commit()
        
    print("✓ Migration rolled back successfully")


if __name__ == "__main__":
    print("Running migration: Add is_emergency field...")
    upgrade()
