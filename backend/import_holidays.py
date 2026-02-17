"""
Import Holidays from Excel file to Database
============================================
This script reads holidays from the Excel file and imports them into the holidays table.
It clears all existing holidays first.
"""

import pandas as pd
from datetime import datetime
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.models.models import Holiday, Base

# Excel file path
EXCEL_FILE = r"d:\final_sgp\holidays_2026-02-03 08_01_25.xlsx"


def import_holidays():
    """Import holidays from Excel file to database."""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Read Excel file
    print(f"Reading holidays from: {EXCEL_FILE}")
    df = pd.read_excel(EXCEL_FILE)
    
    print(f"Found {len(df)} holidays in Excel file")
    print(f"Columns: {df.columns.tolist()}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Delete all existing holidays
        deleted_count = db.query(Holiday).delete()
        print(f"\n🗑️  Deleted {deleted_count} existing holidays from database")
        
        # Import new holidays
        imported_count = 0
        skipped_count = 0
        
        for _, row in df.iterrows():
            try:
                # Get the date - use Start Date
                holiday_date = row['Start Date']
                
                # Convert to datetime if it's not already
                if isinstance(holiday_date, str):
                    holiday_date = datetime.strptime(holiday_date, '%Y-%m-%d')
                elif hasattr(holiday_date, 'to_pydatetime'):
                    holiday_date = holiday_date.to_pydatetime()
                
                # Get the occasion/name
                occasion = str(row['Occasion']).strip() if pd.notna(row['Occasion']) else "Holiday"
                
                # Create holiday record
                holiday = Holiday(
                    name=occasion,
                    date=holiday_date,
                    type="PUBLIC",
                    is_active=True
                )
                
                db.add(holiday)
                imported_count += 1
                print(f"  ✓ {holiday_date.strftime('%Y-%m-%d')}: {occasion}")
                
            except Exception as e:
                print(f"  ✗ Error importing row: {row.to_dict()} - {e}")
                skipped_count += 1
        
        # Commit changes
        db.commit()
        
        print(f"\n✅ Import completed!")
        print(f"   - Imported: {imported_count} holidays")
        print(f"   - Skipped: {skipped_count} holidays")
        
        # Show all holidays in database
        print(f"\n📅 All holidays in database:")
        all_holidays = db.query(Holiday).order_by(Holiday.date).all()
        for h in all_holidays:
            print(f"   {h.date.strftime('%Y-%m-%d')}: {h.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_holidays()
