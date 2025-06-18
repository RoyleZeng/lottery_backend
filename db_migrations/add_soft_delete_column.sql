-- Add is_deleted column to lottery_events table for soft delete functionality
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'lottery_events' AND column_name = 'is_deleted'
    ) THEN
        ALTER TABLE lottery_events ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
    END IF;
END $$;

-- Create index for better performance on soft delete queries
CREATE INDEX IF NOT EXISTS idx_lottery_events_is_deleted ON lottery_events(is_deleted);

-- Verify the changes
SELECT id, name, type, status, is_deleted FROM lottery_events LIMIT 5; 