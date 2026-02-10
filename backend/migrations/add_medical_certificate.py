"""
Database migration to add medical certificate fields to leave_requests table

Run this migration with:
cd backend
python migrations/add_medical_certificate.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Add medical certificate columns to leave_requests table"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Add medical certificate columns
        try:
            conn.execute(text("""
                ALTER TABLE leave_requests 
                ADD COLUMN IF NOT EXISTS medical_certificate_url TEXT,
                ADD COLUMN IF NOT EXISTS medical_certificate_filename VARCHAR(255),
                ADD COLUMN IF NOT EXISTS medical_certificate_size INTEGER,
                ADD COLUMN IF NOT EXISTS medical_certificate_validation JSON
            """))
            conn.commit()
            print("✅ Successfully added medical certificate columns to leave_requests table")
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    print("Starting migration: Adding medical certificate fields...")
    run_migration()
    print("Migration completed!")
