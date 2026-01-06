#!/usr/bin/env python3
"""
Setup Railway PostgreSQL database using the connection URL.
"""
import psycopg2
import os

# Your Railway PostgreSQL connection URL
RAILWAY_DATABASE_URL = "postgresql://postgres:your_password@ballast.proxy.rlwy.net:26799/railway"

def setup_database():
    """Setup Railway database with tables and admin user."""
    
    print("🚀 Setting up Railway PostgreSQL Database")
    print("=" * 50)
    
    try:
        # Connect to Railway PostgreSQL
        print("Connecting to Railway PostgreSQL...")
        conn = psycopg2.connect(RAILWAY_DATABASE_URL)
        cursor = conn.cursor()
        print("✓ Connected successfully")
        
        # Create users table
        print("\nCreating users table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
        """)
        print("✓ Users table created")
        
        # Create audit_reports table
        print("Creating audit_reports table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_reports (
                id SERIAL PRIMARY KEY,
                client_name VARCHAR(100) NOT NULL,
                client_type VARCHAR(20) NOT NULL,
                industry VARCHAR(50) NOT NULL,
                period_days INTEGER NOT NULL,
                auditor_name VARCHAR(100),
                html_filename VARCHAR(255),
                pdf_filename VARCHAR(255),
                word_filename VARCHAR(255),
                status VARCHAR(20) DEFAULT 'pending',
                error_message TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP WITH TIME ZONE,
                created_by VARCHAR(50)
            )
        """)
        print("✓ Audit_reports table created")
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        print("✓ Indexes created")
        
        # Note: This script creates tables only. Use init_railway_db.py for secure admin user creation
        print("⚠️  Admin user creation skipped - use init_railway_db.py for secure admin setup")
        print("   Run: python init_railway_db.py")
        
        # Commit changes
        conn.commit()
        
        # Verify setup
        print("\nVerifying setup...")
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        print(f"✓ Tables created: {[table[0] for table in tables]}")
        
        print("\n🎉 Database tables setup complete!")
        print("\nNext steps:")
        print("1. Run: python init_railway_db.py")
        print("2. This will create a secure admin user with a random password")
        print("3. Save the generated password shown in the output")
        
    except Exception as e:
        print(f"✗ Error setting up database: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

if __name__ == "__main__":
    # Update the RAILWAY_DATABASE_URL with your actual password
    print("Before running this script:")
    print("1. Replace 'your_password' in RAILWAY_DATABASE_URL with your actual Railway PostgreSQL password")
    print("2. Get the password from Railway Dashboard → PostgreSQL service → Variables → POSTGRES_PASSWORD")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    setup_database()