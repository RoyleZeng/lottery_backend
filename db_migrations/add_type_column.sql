-- Add type column to lottery_events table if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns 
        WHERE table_name = 'lottery_events' AND column_name = 'type'
    ) THEN
        ALTER TABLE lottery_events ADD COLUMN type VARCHAR(50) NOT NULL DEFAULT 'general';
    END IF;
END $$;

-- Update existing lottery_events with appropriate types based on their name
UPDATE lottery_events
SET type = 'final_teaching'
WHERE name LIKE '%教學評量%' AND type = 'general';

-- Verify the changes
SELECT id, name, type, status FROM lottery_events; 