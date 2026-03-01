"""
Import Company Holidays to Database
====================================
This script clears all existing holidays and imports the company's official holidays
for 2024, 2025, 2026, and 2027.
"""

from datetime import datetime
import sys
import os

# Add the app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, SessionLocal
from app.models.models import Holiday, Base


# Company holidays data from official calendar
COMPANY_HOLIDAYS = [
    # 2024 Holidays
    {"date": "2024-04-11", "name": "Ramzan/Eid-ul-Fitr"},
    {"date": "2024-08-15", "name": "Independence Day Festival"},
    {"date": "2024-08-19", "name": "Rakshabandhan Festival"},
    {"date": "2024-08-26", "name": "Janmashtami Festival"},
    {"date": "2024-10-12", "name": "Dussehra Festival"},
    {"date": "2024-10-31", "name": "Diwali Festival"},
    {"date": "2024-11-01", "name": "Diwali New Year Festival"},
    {"date": "2024-11-02", "name": "Bhai Duj Festival"},
    {"date": "2024-12-25", "name": "Christmas Festival"},
    
    # 2025 Holidays
    {"date": "2025-01-14", "name": "Makar Sankranti"},
    {"date": "2025-01-26", "name": "Republic Day"},
    {"date": "2025-03-14", "name": "Dhuleti"},
    {"date": "2025-03-31", "name": "Ramjan-Eid (Eid-Ul-Fitra)"},
    {"date": "2025-08-09", "name": "Rakshabandhan Festival"},
    {"date": "2025-08-15", "name": "Independence Day Festival"},
    {"date": "2025-08-16", "name": "Janmashtami Festival"},
    {"date": "2025-10-02", "name": "Dussehra Festival"},
    {"date": "2025-10-20", "name": "Diwali Festival"},
    {"date": "2025-10-22", "name": "Diwali New Year Festival"},
    {"date": "2025-10-23", "name": "Bhai Duj Festival"},
    {"date": "2025-11-05", "name": "Guru Nanak Jayanti"},
    {"date": "2025-12-25", "name": "Christmas Festival"},
    
    # 2026 Holidays
    {"date": "2026-01-14", "name": "Makar Sankranti Festival"},
    {"date": "2026-01-26", "name": "Republic Day Festival"},
    {"date": "2026-03-04", "name": "Dhuleti Festival"},
    {"date": "2026-03-21", "name": "Ramzan/Eid-ul-Fitr"},
    {"date": "2026-08-15", "name": "Independence Day Festival"},
    {"date": "2026-08-28", "name": "Rakshabandhan Festival"},
    {"date": "2026-09-04", "name": "Janmashtami Festival"},
    {"date": "2026-10-20", "name": "Dussehra Festival"},
    {"date": "2026-11-08", "name": "Diwali Festival"},
    {"date": "2026-11-10", "name": "Diwali New Year Festival"},
    {"date": "2026-11-11", "name": "Bhai Duj Festival"},
    {"date": "2026-11-24", "name": "Guru Nanak Jayanti"},
    {"date": "2026-12-25", "name": "Christmas Festival"},
    
    # 2027 Holidays
    {"date": "2027-01-14", "name": "Makar Sankranti Festival"},
    {"date": "2027-01-26", "name": "Republic Day Festival"},
    {"date": "2027-03-09", "name": "Ramzan/Eid-ul-Fitr"},
    {"date": "2027-03-22", "name": "Dhuleti Festival"},
]


def import_company_holidays():
    """Clear all existing holidays and import company holidays."""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Delete all existing holidays
        deleted_count = db.query(Holiday).delete()
        print(f"\n🗑️  Deleted {deleted_count} existing holidays from database")
        
        # Import company holidays
        imported_count = 0
        
        print(f"\n📥 Importing {len(COMPANY_HOLIDAYS)} company holidays...\n")
        
        for holiday_data in COMPANY_HOLIDAYS:
            try:
                # Parse date
                holiday_date = datetime.strptime(holiday_data["date"], "%Y-%m-%d")
                
                # Create holiday record
                holiday = Holiday(
                    name=holiday_data["name"],
                    date=holiday_date,
                    type="PUBLIC",
                    is_active=True
                )
                
                db.add(holiday)
                imported_count += 1
                print(f"  ✓ {holiday_date.strftime('%Y-%m-%d')}: {holiday_data['name']}")
                
            except Exception as e:
                print(f"  ✗ Error importing {holiday_data}: {e}")
        
        # Commit all changes
        db.commit()
        
        print(f"\n✅ Import completed successfully!")
        print(f"   - Total holidays imported: {imported_count}")
        
        # Show summary by year
        print(f"\n📊 Holidays by year:")
        for year in [2024, 2025, 2026, 2027]:
            count = len([h for h in COMPANY_HOLIDAYS if h["date"].startswith(str(year))])
            print(f"   - {year}: {count} holidays")
        
        # Display all holidays
        print(f"\n📅 All holidays in database:")
        all_holidays = db.query(Holiday).order_by(Holiday.date).all()
        current_year = None
        for h in all_holidays:
            year = h.date.year
            if year != current_year:
                print(f"\n   {year}:")
                current_year = year
            print(f"     • {h.date.strftime('%Y-%m-%d')}: {h.name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("  COMPANY HOLIDAYS IMPORT")
    print("=" * 60)
    import_company_holidays()
    print("\n" + "=" * 60)
