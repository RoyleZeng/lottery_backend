-- Remove old tables that are no longer needed
DROP TABLE IF EXISTS final_teaching_comments CASCADE;
DROP TABLE IF EXISTS student CASCADE;

-- Ensure lottery_participants table has the correct structure
-- This will recreate the table if it doesn't have the meta column
DO $$
BEGIN
    -- Check if meta column exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'lottery_participants' 
        AND column_name = 'meta'
    ) THEN
        -- Add meta column if it doesn't exist
        ALTER TABLE lottery_participants ADD COLUMN meta jsonb DEFAULT '{}'::jsonb NOT NULL;
    END IF;
    
    -- Remove student_id column if it exists
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'lottery_participants' 
        AND column_name = 'student_id'
    ) THEN
        ALTER TABLE lottery_participants DROP COLUMN student_id;
    END IF;
END $$;

-- Create GIN index for JSONB meta field for better query performance
CREATE INDEX IF NOT EXISTS idx_lottery_participants_meta ON lottery_participants USING GIN (meta);

-- Update any existing data to have proper meta structure (if needed)
-- This is a safety measure for existing installations
UPDATE lottery_participants 
SET meta = '{}'::jsonb 
WHERE meta IS NULL OR meta = 'null'::jsonb; 