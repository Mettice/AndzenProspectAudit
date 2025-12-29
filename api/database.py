"""
Database configuration and session management.
Supports both SQLite (development) and PostgreSQL (Supabase/Production).
"""
from sqlalchemy import create_engine
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
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Supabase works better with NullPool
        pool_pre_ping=True,  # Verify connections before using
        echo=False  # Set to True for SQL query logging
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
    if not IS_POSTGRES:
        # Only create data directory for SQLite
        os.makedirs("data", exist_ok=True)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"✓ Database initialized ({'PostgreSQL' if IS_POSTGRES else 'SQLite'})")

