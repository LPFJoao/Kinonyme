CREATE TABLE IF NOT EXISTS guild_configs (
    guild_id BIGINT PRIMARY KEY,
    welcome_channel BIGINT,
    welcome_message TEXT,
    created_at TIMESTAMP DEFAULT now()
);

ALTER TABLE guild_configs ADD COLUMN IF NOT EXISTS onboarding_category BIGINT;

