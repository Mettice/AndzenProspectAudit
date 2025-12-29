#!/usr/bin/env python3
"""
Debug script to check Railway environment and connectivity.
Deploy this to Railway to see exactly what's happening.
"""
import os
import sys
import socket
import psycopg2
from urllib.parse import urlparse

def test_railway_environment():
    """Check Railway-specific environment."""
    print("=== RAILWAY ENVIRONMENT DEBUG ===")
    
    # Check Railway-specific variables
    railway_vars = ['RAILWAY_ENVIRONMENT', 'RAILWAY_ENVIRONMENT_NAME', 'RAILWAY_PROJECT_ID']
    for var in railway_vars:
        print(f"{var}: {os.getenv(var, 'NOT SET')}")
    
    print(f"\nPython version: {sys.version}")
    print(f"Platform: {sys.platform}")
    
    # Check DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print(f"\nDATABASE_URL: {db_url[:50]}...{db_url[-20:]}")
        
        # Parse URL
        try:
            parsed = urlparse(db_url)
            print(f"Host: {parsed.hostname}")
            print(f"Port: {parsed.port}")
            print(f"Database: {parsed.path[1:] if parsed.path else 'None'}")
            print(f"Username: {parsed.username}")
            print(f"Password: {'*' * len(parsed.password) if parsed.password else 'None'}")
        except Exception as e:
            print(f"URL parsing error: {e}")
    else:
        print("\nDATABASE_URL: NOT SET")

def test_dns_resolution():
    """Test DNS resolution for Supabase host."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL to test")
        return
        
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port or 5432
        
        print(f"\n=== DNS RESOLUTION TEST ===")
        print(f"Resolving: {host}")
        
        # Get IP addresses
        import socket
        result = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        
        for family, type, proto, canonname, sockaddr in result:
            family_name = 'IPv4' if family == socket.AF_INET else 'IPv6'
            print(f"{family_name}: {sockaddr[0]}:{sockaddr[1]}")
            
    except Exception as e:
        print(f"DNS resolution failed: {e}")

def test_socket_connection():
    """Test raw socket connection."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL to test")
        return
        
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port or 5432
        
        print(f"\n=== SOCKET CONNECTION TEST ===")
        print(f"Testing: {host}:{port}")
        
        # Try IPv4 first
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            if result == 0:
                print("✓ IPv4 socket connection successful")
            else:
                print(f"✗ IPv4 socket connection failed: {result}")
            sock.close()
        except Exception as e:
            print(f"✗ IPv4 socket error: {e}")
            
        # Try IPv6
        try:
            sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            if result == 0:
                print("✓ IPv6 socket connection successful")
            else:
                print(f"✗ IPv6 socket connection failed: {result}")
            sock.close()
        except Exception as e:
            print(f"✗ IPv6 socket error: {e}")
            
    except Exception as e:
        print(f"Socket test failed: {e}")

def test_psycopg2_connection():
    """Test psycopg2 connection with different settings."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("No DATABASE_URL to test")
        return
        
    print(f"\n=== PSYCOPG2 CONNECTION TEST ===")
    
    # Test variations
    test_urls = [
        (db_url, "Original URL"),
        (db_url + "?sslmode=disable", "SSL disabled"),
        (db_url + "?sslmode=prefer", "SSL prefer"),
        (db_url.replace("postgresql://", "postgres://"), "postgres:// scheme"),
    ]
    
    for url, description in test_urls:
        try:
            print(f"\nTesting: {description}")
            conn = psycopg2.connect(url, connect_timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✓ {description}: Success")
            conn.close()
            break  # Stop on first success
        except Exception as e:
            print(f"✗ {description}: {e}")

if __name__ == "__main__":
    test_railway_environment()
    test_dns_resolution()
    test_socket_connection()
    test_psycopg2_connection()