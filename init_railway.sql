-- Initialize Railway PostgreSQL Database
-- Run this SQL in Railway PostgreSQL Query interface

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create audit_reports table
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
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_audit_reports_created_at ON audit_reports(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_reports_status ON audit_reports(status);

-- Insert admin user (password hash for "admin123")
-- Note: This is a bcrypt hash of "admin123" - CHANGE THIS PASSWORD!
INSERT INTO users (username, email, password_hash, role, is_active) 
VALUES ('admin', 'admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBNSMhF2fAH9TW', 'admin', true)
ON CONFLICT (username) DO NOTHING;

-- Verify tables were created
SELECT 'Tables created successfully:' as message;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- Verify admin user was created
SELECT 'Admin user created:' as message;
SELECT username, email, role, is_active, created_at FROM users WHERE username = 'admin';