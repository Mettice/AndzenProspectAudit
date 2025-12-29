-- Migration script to make created_by_id nullable in reports table
-- Run this directly in Railway PostgreSQL database console

ALTER TABLE reports ALTER COLUMN created_by_id DROP NOT NULL;

-- Verify the change
SELECT column_name, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'reports' AND column_name = 'created_by_id';

