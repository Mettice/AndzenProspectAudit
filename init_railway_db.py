#!/usr/bin/env python3
"""
Initialize Railway PostgreSQL database with tables and admin user.
Run this script to set up your Railway PostgreSQL database.

Note: This script works with Railway PostgreSQL (or any PostgreSQL database).
Make sure DATABASE_URL is set in your environment or .env file.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from api.database import init_db, get_db, SessionLocal
from api.models import User
from api.models.user import UserRole
from api.services.auth import get_password_hash

def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        init_db()
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def create_admin_user():
    """Create initial admin user."""
    print("\nCreating admin user...")
    
    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(User.username == "admin").first()
        if existing_user:
            print("✓ Admin user already exists")
            return True
        
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),  # Change this password!
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        print("✓ Admin user created successfully")
        print("   Username: admin")
        print("   Password: admin123")
        print("   ⚠️  CHANGE THIS PASSWORD AFTER FIRST LOGIN!")
        return True
        
    except Exception as e:
        print(f"✗ Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main initialization function."""
    print("🚀 Initializing Railway PostgreSQL Database")
    print("=" * 50)
    
    # Check database connection
    print("Testing database connection...")
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("Make sure DATABASE_URL is set correctly")
        sys.exit(1)
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    # Create admin user
    if not create_admin_user():
        sys.exit(1)
    
    print("\n🎉 Database initialization complete!")
    print("\nYou can now:")
    print("1. Access your app at: https://your-railway-app.railway.app/ui")
    print("2. Login with username: admin, password: admin123")
    print("3. Change the admin password immediately!")

if __name__ == "__main__":
    main()