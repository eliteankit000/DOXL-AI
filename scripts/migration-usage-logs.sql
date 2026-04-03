-- DocXL AI - Database Migration Script
-- Run this in Supabase SQL Editor to add new action types

-- Update usage_logs table to allow new action types
-- This adds 'upgrade' and 'timeout_refund' to the existing constraint

-- First, check the current constraint
-- SELECT conname, pg_get_constraintdef(oid) 
-- FROM pg_constraint 
-- WHERE conrelid = 'usage_logs'::regclass AND conname LIKE '%action%';

-- Drop old constraint if it exists (update constraint name if different)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'usage_logs_action_check' 
        AND conrelid = 'usage_logs'::regclass
    ) THEN
        ALTER TABLE usage_logs DROP CONSTRAINT usage_logs_action_check;
    END IF;
END $$;

-- Add new constraint with all valid action types
ALTER TABLE usage_logs 
ADD CONSTRAINT usage_logs_action_check 
CHECK (action IN ('process', 'export', 'upload', 'upgrade', 'timeout_refund'));

-- Verify the constraint was added
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'usage_logs'::regclass AND conname = 'usage_logs_action_check';

-- Test the new constraint
-- INSERT INTO usage_logs (user_id, action, credits_used) 
-- VALUES ('00000000-0000-0000-0000-000000000000', 'upgrade', 0);
-- Should succeed

COMMENT ON COLUMN usage_logs.action IS 'Action type: process, export, upload, upgrade, timeout_refund';
