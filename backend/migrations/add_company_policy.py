"""
Migration script to add company_policy table for weekly off configuration
Run this script to create the company_policy table in your database
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Enum as SQLEnum, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/leave_management_db")

Base = declarative_base()
engine = create_engine(DATABASE_URL)


def upgrade():
    """Create company_policy table"""
    print("Creating company_policy table...")
    
    # Create table using raw SQL to ensure it works
    with engine.connect() as conn:
        # Drop table if exists (for development/testing)
        conn.execute(text("DROP TABLE IF EXISTS company_policy"))
        conn.commit()
        
        # Create table
        create_table_sql = """
        CREATE TABLE company_policy (
            id INT AUTO_INCREMENT PRIMARY KEY,
            weekly_off_type ENUM('SUNDAY', 'SAT_SUN', 'ALT_SAT') NOT NULL DEFAULT 'SAT_SUN',
            description VARCHAR(255) DEFAULT NULL,
            effective_from DATE DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_updated_at (updated_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        conn.execute(text(create_table_sql))
        conn.commit()
        
        # Insert default policy
        insert_default_sql = """
        INSERT INTO company_policy (weekly_off_type, description, effective_from)
        VALUES ('SAT_SUN', 'Default policy: Saturday and Sunday weekly off', CURDATE())
        """
        
        conn.execute(text(insert_default_sql))
        conn.commit()
        
    print("✅ company_policy table created successfully!")
    print("✅ Default policy (SAT_SUN) inserted!")


def downgrade():
    """Drop company_policy table"""
    print("Dropping company_policy table...")
    
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS company_policy"))
        conn.commit()
        
    print("✅ company_policy table dropped!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  COMPANY POLICY TABLE MIGRATION")
    print("=" * 60)
    
    try:
        upgrade()
        print("\n✅ Migration completed successfully!")
        print("\nYou can now configure weekly off days from Admin dashboard.")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("=" * 60 + "\n")
        raise
