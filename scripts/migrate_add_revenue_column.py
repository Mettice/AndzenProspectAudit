#!/usr/bin/env python3
"""
Migration script to add total_revenue and attributed_revenue columns to reports table.
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from api.database import engine, IS_POSTGRES, SessionLocal

def migrate_add_revenue_columns():
    """Add revenue columns to reports table."""
    print("🔄 Running migration to add revenue columns...")
    print(f"Database type: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}\n")
    
    db = SessionLocal()
    try:
        # Check if columns already exist
        if IS_POSTGRES:
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='reports' AND column_name='total_revenue'
            """)
        else:
            check_query = text("PRAGMA table_info(reports)")
        
        result = db.execute(check_query)
        
        if IS_POSTGRES:
            exists = result.fetchone() is not None
        else:
            columns = [row[1] for row in result.fetchall()]
            exists = 'total_revenue' in columns
        
        if exists:
            print("✓ Revenue columns already exist")
            return True
        
        # Add columns
        print("Adding total_revenue and attributed_revenue columns...")
        
        if IS_POSTGRES:
            db.execute(text("ALTER TABLE reports ADD COLUMN total_revenue NUMERIC(15, 2) DEFAULT 0;"))
            db.execute(text("ALTER TABLE reports ADD COLUMN attributed_revenue NUMERIC(15, 2) DEFAULT 0;"))
        else:
            db.execute(text("ALTER TABLE reports ADD COLUMN total_revenue REAL DEFAULT 0;"))
            db.execute(text("ALTER TABLE reports ADD COLUMN attributed_revenue REAL DEFAULT 0;"))
        
        db.commit()
        print("✓ Revenue columns added successfully")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = migrate_add_revenue_columns()
    if success:
        print("\n✅ Migration completed!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed")
        sys.exit(1)

