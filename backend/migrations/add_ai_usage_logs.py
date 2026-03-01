"""
Migration script to create the ai_usage_logs table.
This table records Gemini API token consumption for each successful AI call.

Run with:
    cd backend
    python migrations/add_ai_usage_logs.py
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:@localhost:3306/leave_management_db")

engine = create_engine(DATABASE_URL)


def upgrade():
    """Create ai_usage_logs table."""
    print("Creating ai_usage_logs table...")

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS ai_usage_logs (
        id              INT AUTO_INCREMENT PRIMARY KEY,
        employee_id     INT          DEFAULT NULL,
        leave_request_id INT         DEFAULT NULL,
        call_type       VARCHAR(50)  NOT NULL COMMENT 'LEAVE_EVALUATION | MEDICAL_CERT',
        leave_type      VARCHAR(50)  DEFAULT NULL COMMENT 'SICK | CASUAL | ANNUAL etc.',
        model_name      VARCHAR(100) DEFAULT NULL,
        prompt_tokens   INT          NOT NULL DEFAULT 0,
        output_tokens   INT          NOT NULL DEFAULT 0,
        total_tokens    INT          NOT NULL DEFAULT 0,
        ai_recommended_action VARCHAR(50) DEFAULT NULL COMMENT 'APPROVE | REJECT | MANUAL_REVIEW',
        created_at      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

        INDEX idx_employee_id     (employee_id),
        INDEX idx_leave_request_id (leave_request_id),
        INDEX idx_created_at      (created_at),

        CONSTRAINT fk_ai_usage_employee
            FOREIGN KEY (employee_id)
            REFERENCES users (id)
            ON DELETE SET NULL,

        CONSTRAINT fk_ai_usage_leave_request
            FOREIGN KEY (leave_request_id)
            REFERENCES leave_requests (id)
            ON DELETE SET NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
      COMMENT='Tracks Gemini API token usage — one row per successful API call';
    """

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

    print("✅ ai_usage_logs table created successfully!")


def downgrade():
    """Drop ai_usage_logs table."""
    print("Dropping ai_usage_logs table...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS ai_usage_logs"))
        conn.commit()
    print("✅ ai_usage_logs table dropped!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AI USAGE LOGS TABLE MIGRATION")
    print("=" * 60)

    try:
        upgrade()
        print("\n✅ Migration completed successfully!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("=" * 60 + "\n")
        raise
