-- Lottery events table
CREATE TABLE IF NOT EXISTS lottery_events (
    id VARCHAR PRIMARY KEY,
    academic_year_term VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_date TIMESTAMP NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    type VARCHAR(50) NOT NULL DEFAULT 'general',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Lottery participants table
CREATE TABLE IF NOT EXISTS lottery_participants (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR NOT NULL REFERENCES lottery_events(id) ON DELETE CASCADE,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lottery prizes table
CREATE TABLE IF NOT EXISTS lottery_prizes (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR NOT NULL REFERENCES lottery_events(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Lottery winners table
CREATE TABLE IF NOT EXISTS lottery_winners (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR NOT NULL REFERENCES lottery_events(id) ON DELETE CASCADE,
    prize_id INTEGER NOT NULL REFERENCES lottery_prizes(id) ON DELETE CASCADE,
    participant_id INTEGER NOT NULL REFERENCES lottery_participants(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (event_id, participant_id) -- Ensure a participant can only win once per event
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_lottery_participants_event_id ON lottery_participants(event_id);
CREATE INDEX IF NOT EXISTS idx_lottery_prizes_event_id ON lottery_prizes(event_id);
CREATE INDEX IF NOT EXISTS idx_lottery_winners_event_id ON lottery_winners(event_id);
CREATE INDEX IF NOT EXISTS idx_lottery_winners_prize_id ON lottery_winners(prize_id);
CREATE INDEX IF NOT EXISTS idx_lottery_winners_participant_id ON lottery_winners(participant_id);

-- Create GIN index for JSONB meta field for better query performance
CREATE INDEX IF NOT EXISTS idx_lottery_participants_meta ON lottery_participants USING GIN (meta); 