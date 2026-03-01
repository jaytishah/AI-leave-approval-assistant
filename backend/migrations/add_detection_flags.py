"""
Migration: Add Detection Flags to Medical Certificates (ROBUST VERSION)
========================================================================

This migration updates the medical_certificates table to support
detection-based extraction with boolean flags.

CHANGES:
1. Rename doctor_name → doctor_name_text
2. Add doctor_name_detected (BOOLEAN)
3. Rename clinic_name → clinic_name_text
4. Add clinic_name_detected (BOOLEAN)
5. Change certificate_date from DATETIME to VARCHAR(50)
6. Add date_detected (BOOLEAN)

Why VARCHAR for date?
- OCR extracts dates in various formats: "02/02/2026", "2-Feb-2026", "02-02-26"
- Parsing can happen in Step 4 (confidence scoring)
- Storing raw extracted text preserves audit trail

SAFETY:
- No data loss - columns are renamed, not dropped
- Existing extracted_text remains untouched
- New boolean flags default to FALSE
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from app.core.config import settings

def run_migration():
    """Execute the migration"""
    
    # Create database connection
    engine = create_engine(settings.DATABASE_URL)
    
    print("=" * 70)
    print("MIGRATION: Add Detection Flags (ROBUST VERSION)")
    print("=" * 70)
    
    with engine.connect() as conn:
        print("\n1. Checking current table structure...")
        
        # Check if table exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'medical_certificates'
        """))
        
        if result.fetchone()[0] == 0:
            print("❌ Error: medical_certificates table not found!")
            print("   Please run add_medical_certificate.py first.")
            return
        
        print("✓ medical_certificates table exists")
        
        # Check current columns
        result = conn.execute(text("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'medical_certificates'
            AND COLUMN_NAME IN ('doctor_name', 'clinic_name', 'certificate_date', 
                                'doctor_name_text', 'clinic_name_text',
                                'doctor_name_detected', 'clinic_name_detected', 'date_detected')
        """))
        
        existing_columns = {row[0]: row[1] for row in result}
        print(f"\n2. Current columns: {', '.join(existing_columns.keys())}")
        
        # Determine what changes are needed
        changes = []
        
        # Check if old column names exist (need migration)
        if 'doctor_name' in existing_columns and 'doctor_name_text' not in existing_columns:
            changes.append("Rename doctor_name → doctor_name_text")
        
        if 'clinic_name' in existing_columns and 'clinic_name_text' not in existing_columns:
            changes.append("Rename clinic_name → clinic_name_text")
        
        if 'doctor_name_detected' not in existing_columns:
            changes.append("Add doctor_name_detected (BOOLEAN)")
        
        if 'clinic_name_detected' not in existing_columns:
            changes.append("Add clinic_name_detected (BOOLEAN)")
        
        if 'date_detected' not in existing_columns:
            changes.append("Add date_detected (BOOLEAN)")
        
        if 'certificate_date' in existing_columns:
            if existing_columns['certificate_date'] == 'datetime':
                changes.append("Change certificate_date: DATETIME → VARCHAR(50)")
        
        if not changes:
            print("\n✓ Database already has robust detection fields!")
            print("   No migration needed.")
            return
        
        print(f"\n3. Changes to apply:")
        for i, change in enumerate(changes, 1):
            print(f"   {i}. {change}")
        
        # Execute migrations
        print(f"\n4. Executing migrations...")
        
        try:
            # Rename doctor_name to doctor_name_text
            if 'doctor_name' in existing_columns and 'doctor_name_text' not in existing_columns:
                print("   → Renaming doctor_name → doctor_name_text...")
                conn.execute(text("""
                    ALTER TABLE medical_certificates 
                    CHANGE COLUMN doctor_name doctor_name_text VARCHAR(255)
                """))
                conn.commit()
                print("   ✓ Renamed doctor_name")
            
            # Add doctor_name_detected
            if 'doctor_name_detected' not in existing_columns:
                print("   → Adding doctor_name_detected column...")
                conn.execute(text("""
                    ALTER TABLE medical_certificates 
                    ADD COLUMN doctor_name_detected BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("   ✓ Added doctor_name_detected")
            
            # Rename clinic_name to clinic_name_text
            if 'clinic_name' in existing_columns and 'clinic_name_text' not in existing_columns:
                print("   → Renaming clinic_name → clinic_name_text...")
                conn.execute(text("""
                    ALTER TABLE medical_certificates 
                    CHANGE COLUMN clinic_name clinic_name_text VARCHAR(255)
                """))
                conn.commit()
                print("   ✓ Renamed clinic_name")
            
            # Add clinic_name_detected
            if 'clinic_name_detected' not in existing_columns:
                print("   → Adding clinic_name_detected column...")
                conn.execute(text("""
                    ALTER TABLE medical_certificates 
                    ADD COLUMN clinic_name_detected BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("   ✓ Added clinic_name_detected")
            
            # Add date_detected
            if 'date_detected' not in existing_columns:
                print("   → Adding date_detected column...")
                conn.execute(text("""
                    ALTER TABLE medical_certificates 
                    ADD COLUMN date_detected BOOLEAN DEFAULT FALSE
                """))
                conn.commit()
                print("   ✓ Added date_detected")
            
            # Change certificate_date to VARCHAR
            if 'certificate_date' in existing_columns:
                if existing_columns['certificate_date'] == 'datetime':
                    print("   → Changing certificate_date: DATETIME → VARCHAR(50)...")
                    conn.execute(text("""
                        ALTER TABLE medical_certificates 
                        MODIFY COLUMN certificate_date VARCHAR(50)
                    """))
                    conn.commit()
                    print("   ✓ Changed certificate_date type")
            
            print("\n✓ Migration completed successfully!")
            
            # Verify final structure
            print("\n5. Verifying final structure...")
            result = conn.execute(text("""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'medical_certificates'
                AND COLUMN_NAME IN ('doctor_name_text', 'doctor_name_detected',
                                    'clinic_name_text', 'clinic_name_detected',
                                    'certificate_date', 'date_detected',
                                    'medical_keywords_detected', 'signature_or_stamp_detected')
                ORDER BY ORDINAL_POSITION
            """))
            
            print("\n   Final Table Structure (Detection Fields):")
            print("   " + "-" * 60)
            for row in result:
                col_name, data_type, nullable = row
                print(f"   {col_name:30s} {data_type:15s} {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            print("   " + "-" * 60)
            
            print("\n✅ ROBUST VERSION MIGRATION COMPLETE")
            print("\nNEXT STEPS:")
            print("  1. Restart backend server")
            print("  2. Run update script to populate detection flags for existing records")
            print("  3. Test with new medical certificate uploads")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
