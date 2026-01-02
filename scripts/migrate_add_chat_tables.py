"""
Migration script to create chat_messages and report_edits tables.
Run this script to update your database schema.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import api modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from api.database import engine, IS_POSTGRES, Base
from api.models.chat import ChatMessage, ReportEdit

def migrate_chat_tables():
    """Create chat_messages and report_edits tables if they don't exist."""
    try:
        # Use Base.metadata.create_all to create tables
        # This is the safest way as it handles both PostgreSQL and SQLite
        Base.metadata.create_all(bind=engine)
        print("✓ Chat tables created/verified successfully")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔄 Running database migration for chat tables...")
    print(f"Database type: {'PostgreSQL' if IS_POSTGRES else 'SQLite'}\n")
    
    success = migrate_chat_tables()
    
    if success:
        print("\n✅ Database migration completed!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the error above.")
        sys.exit(1)

