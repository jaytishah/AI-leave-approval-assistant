"""
Migration: Create medical_certificates table for Step 1 & 2 implementation

This migration creates the medical_certificates table to store:
- File information (path, name, size, type)
- Raw OCR extracted text (NEVER DELETE - for audit)
- Structured extracted fields (mandatory & optional)
- Confidence scores
- AI recommendations
- HR final decision

Run this migration to set up the database schema for the medical certificate
validation pipeline.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings


def run_migration():
    """Create medical_certificates table"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS medical_certificates (
        id INT AUTO_INCREMENT PRIMARY KEY,
        leave_id INT NOT NULL UNIQUE,
        
        -- File information
        file_path VARCHAR(500) NOT NULL,
        file_name VARCHAR(255),
        file_size INT,
        file_type VARCHAR(50),
        
        -- Raw OCR text - NEVER DELETE (for audit)
        extracted_text LONGTEXT,
        
        -- Extracted structured fields - MANDATORY
        doctor_name VARCHAR(255),
        clinic_name VARCHAR(255),
        certificate_date DATETIME,
        medical_keywords_detected BOOLEAN DEFAULT FALSE,
        signature_or_stamp_detected BOOLEAN DEFAULT FALSE,
        
        -- Extracted structured fields - OPTIONAL
        rest_days INT,
        diagnosis TEXT,
        registration_number VARCHAR(100),
        contact_number VARCHAR(50),
        
        -- Confidence engine results
        confidence_score INT DEFAULT 0 COMMENT '0-100 scale',
        confidence_level VARCHAR(20) COMMENT 'HIGH, MEDIUM, LOW',
        requires_hr_review BOOLEAN DEFAULT TRUE,
        
        -- AI recommendation layer
        ai_recommendation VARCHAR(20) COMMENT 'APPROVE, REJECT, REVIEW',
        ai_reason TEXT,
        
        -- HR final decision
        final_status VARCHAR(20) COMMENT 'APPROVED, REJECTED, NULL until HR acts',
        hr_reason TEXT,
        
        -- Timestamps
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        -- Foreign key
        FOREIGN KEY (leave_id) REFERENCES leave_requests(id) ON DELETE CASCADE,
        
        INDEX idx_leave_id (leave_id),
        INDEX idx_final_status (final_status),
        INDEX idx_requires_hr_review (requires_hr_review),
        INDEX idx_confidence_level (confidence_level)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✓ medical_certificates table created successfully")
            print("✓ Migration completed: Medical certificate table with Step 1 & 2 schema")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise


if __name__ == "__main__":
    print("Running migration: add_medical_certificate_table")
    print("=" * 60)
    run_migration()
    print("=" * 60)
    print("Migration complete!")
