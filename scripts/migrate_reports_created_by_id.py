"""
Migration script to make created_by_id nullable in reports table.
Run this once to update the database schema.

Usage:
    Local: python scripts/migrate_reports_created_by_id.py
    Railway: railway run python scripts/migrate_reports_created_by_id.py
    Or connect to Railway database directly and run the SQL:
        ALTER TABLE reports ALTER COLUMN created_by_id DROP NOT NULL;
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import engine, IS_POSTGRES
from sqlalchemy import text

def migrate():
    """Make created_by_id nullable in reports table."""
    try:
        with engine.begin() as conn:  # Use begin() for automatic transaction management
            if IS_POSTGRES:
                # PostgreSQL: ALTER COLUMN to drop NOT NULL constraint
                # First check if constraint exists
                result = conn.execute(text("""
                    SELECT column_name, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'reports' AND column_name = 'created_by_id';
                """))
                row = result.fetchone()
                
                if not row:
                    print("⚠️  Column 'created_by_id' doesn't exist in reports table.")
                    print("   This is OK if tables haven't been created yet.")
                    return
                
                if row[1] == 'YES':
                    print("✓ Column 'created_by_id' is already nullable")
                    return
                
                # Drop NOT NULL constraint
                conn.execute(text("""
                    ALTER TABLE reports 
                    ALTER COLUMN created_by_id DROP NOT NULL;
                """))
                print("✓ Successfully made created_by_id nullable in reports table (PostgreSQL)")
            else:
                # SQLite: Need to recreate table (SQLite doesn't support ALTER COLUMN)
                print("⚠️  SQLite detected. SQLite doesn't support ALTER COLUMN.")
                print("   The model change will take effect on next table creation.")
                print("   To apply: Drop and recreate the table (this will lose data).")
                print("   Or: The change will apply automatically if you recreate the database.")
        
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg or "no such column" in error_msg:
            print("⚠️  Column or table doesn't exist yet. This is OK if tables haven't been created.")
            print("   The model change will apply when tables are created.")
        elif "already" in error_msg.lower() or "duplicate" in error_msg.lower() or "already nullable" in error_msg.lower():
            print("✓ Column is already nullable (or migration already applied)")
        else:
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    print("🔄 Migrating reports table: making created_by_id nullable...")
    migrate()
    print("✅ Migration complete!")

