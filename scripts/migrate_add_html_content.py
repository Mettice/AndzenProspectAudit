"""
Migration script to add html_content and llm_config columns to reports table.
Run this script to update your database schema.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from api.database import engine, IS_POSTGRES

def migrate_reports_table():
    """Add html_content and llm_config columns to reports table."""
    try:
        with engine.connect() as conn:
            # Check if columns already exist
            if IS_POSTGRES:
                # PostgreSQL
                check_html = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='reports' AND column_name='html_content'
                """))
                check_llm_config = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='reports' AND column_name='llm_config'
                """))
                html_exists = check_html.fetchone() is not None
                llm_config_exists = check_llm_config.fetchone() is not None
            else:
                # SQLite
                check_html = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='reports'
                """))
                if check_html.fetchone():
                    # Check columns in SQLite
                    pragma = conn.execute(text("PRAGMA table_info(reports)"))
                    columns = [row[1] for row in pragma.fetchall()]
                    html_exists = 'html_content' in columns
                    llm_config_exists = 'llm_config' in columns
                else:
                    html_exists = False
                    llm_config_exists = False
            
            # Add html_content column if it doesn't exist
            if not html_exists:
                if IS_POSTGRES:
                    conn.execute(text("""
                        ALTER TABLE reports 
                        ADD COLUMN html_content TEXT
                    """))
                else:
                    conn.execute(text("""
                        ALTER TABLE reports 
                        ADD COLUMN html_content TEXT
                    """))
                print("✓ Added html_content column to reports table")
            else:
                print("✓ html_content column already exists")
            
            # Add llm_config column if it doesn't exist
            if not llm_config_exists:
                if IS_POSTGRES:
                    conn.execute(text("""
                        ALTER TABLE reports 
                        ADD COLUMN llm_config JSONB
                    """))
                else:
                    conn.execute(text("""
                        ALTER TABLE reports 
                        ADD COLUMN llm_config TEXT
                    """))
                print("✓ Added llm_config column to reports table")
            else:
                print("✓ llm_config column already exists")
            
            conn.commit()
            print("\n✅ Migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔄 Running database migration...")
    print(f"Database type: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}\n")
    
    success = migrate_reports_table()
    
    if success:
        print("\n✅ Database migration completed!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the error above.")
        sys.exit(1)

