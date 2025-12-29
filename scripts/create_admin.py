"""
Script to create the first admin user.
Run this script to create an admin account for the system.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import init_db, SessionLocal
from api.models.user import User, UserRole
from api.services.auth import get_password_hash

def create_admin(username: str, email: str, password: str):
    """Create an admin user."""
    # Initialize database
    init_db()
    
    db = SessionLocal()
    try:
        # Check if admin already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            print(f"❌ User with username '{username}' or email '{email}' already exists!")
            return False
        
        # Create admin user
        admin_user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"✅ Admin user created successfully!")
        print(f"   Username: {username}")
        print(f"   Email: {email}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   ID: {admin_user.id}")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    import getpass
    
    print("=" * 50)
    print("Create Admin User")
    print("=" * 50)
    
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username cannot be empty!")
        sys.exit(1)
    
    email = input("Enter email: ").strip()
    if not email or "@" not in email:
        print("❌ Invalid email address!")
        sys.exit(1)
    
    password = getpass.getpass("Enter password: ")
    if not password or len(password) < 6:
        print("❌ Password must be at least 6 characters!")
        sys.exit(1)
    
    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        print("❌ Passwords do not match!")
        sys.exit(1)
    
    print("\nCreating admin user...")
    success = create_admin(username, email, password)
    
    if success:
        print("\n✅ Setup complete! You can now login with these credentials.")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

