"""
Database configuration and session management.
Supports both SQLite (development) and PostgreSQL (Supabase/Production).
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
import os

# Load environment variables first (before reading DATABASE_URL)
load_dotenv()

# Database URL - Supports both SQLite and PostgreSQL
# For Supabase: postgresql://user:password@host:port/database
# For local SQLite: sqlite:///./data/audit.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/audit.db")

# Determine if using PostgreSQL
IS_POSTGRES = DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://")

# Create engine with appropriate settings
if IS_POSTGRES:
    # PostgreSQL/Supabase configuration
    # Add SSL mode for Supabase connections
    connect_args = {}
    if "supabase.co" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL:
        # Supabase requires SSL connections
        connect_args = {
            "sslmode": "require",
            "connect_timeout": 10  # 10 second timeout
        }
        
        # For Railway: Try to force IPv4 if IPv6 is causing issues
        # This is a workaround for Railway's IPv6 connectivity issues
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_ENVIRONMENT_NAME"):
            # Railway may have IPv6 connectivity issues
            # Connection pooling (port 6543) often works better than direct (5432)
            if ":5432" in DATABASE_URL and "pooler" not in DATABASE_URL:
                print("⚠️  WARNING: Using direct connection (port 5432) on Railway.")
                print("   Consider using connection pooling (port 6543) if connection fails.")
                print("   Get it from: Supabase → Settings → Database → Connection string → Connection pooling")
    
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Supabase works better with NullPool
        pool_pre_ping=True,  # Verify connections before using
        connect_args=connect_args,
        echo=False,  # Set to True for SQL query logging
        # Add connection pool settings for better reliability
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
else:
    # SQLite configuration (development)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for getting database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    """
    try:
        if not IS_POSTGRES:
            # Only create data directory for SQLite
            os.makedirs("data", exist_ok=True)
        
        # Test connection first with better error reporting
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()  # Actually fetch to ensure connection works
            print(f"✓ Database connection test successful")
        except Exception as conn_error:
            error_msg = str(conn_error)
            # Provide specific guidance based on error type
            if "Network is unreachable" in error_msg:
                raise ConnectionError(
                    f"❌ Network is unreachable - Railway cannot connect to Supabase.\n"
                    f"   This usually means:\n"
                    f"   1. Supabase project is PAUSED - check dashboard\n"
                    f"   2. Network Restrictions are blocking Railway IPs\n"
                    f"   3. Connection string format is wrong\n\n"
                    f"   Fix: Go to Supabase → Settings → Database → Network Restrictions\n"
                    f"   Ensure 'Your database can be accessed by all IP addresses' is enabled\n"
                    f"   Or add Railway IP range (or 0.0.0.0/0 for testing)\n\n"
                    f"   Current DATABASE_URL: {DATABASE_URL[:50]}...\n"
                    f"   Error: {error_msg}"
                )
            elif "password authentication failed" in error_msg.lower():
                raise ConnectionError(
                    f"❌ Password authentication failed.\n"
                    f"   Check: DATABASE_URL password matches Supabase database password\n"
                    f"   Error: {error_msg}"
                )
            elif "timeout" in error_msg.lower():
                raise ConnectionError(
                    f"❌ Connection timeout.\n"
                    f"   Railway cannot reach Supabase within 10 seconds.\n"
                    f"   Check: Network restrictions and Supabase project status\n"
                    f"   Error: {error_msg}"
                )
            else:
                raise ConnectionError(
                    f"❌ Cannot connect to database.\n"
                    f"   Error: {error_msg}\n"
                    f"   Check: DATABASE_URL, Supabase project status, network restrictions"
                )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print(f"✓ Database initialized ({'PostgreSQL' if IS_POSTGRES else 'SQLite'})")
    except ConnectionError:
        # Re-raise connection errors with our improved messages
        raise
    except Exception as e:
        # Catch any other unexpected errors
        error_msg = str(e)
        raise ConnectionError(
            f"❌ Unexpected database error during initialization.\n"
            f"   Error: {error_msg}\n"
            f"   Check: DATABASE_URL format, database server status"
        )

