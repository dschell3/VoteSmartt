-- Migration: Add reset_token and reset_token_expires columns to user table
ALTER TABLE user
  ADD COLUMN reset_token VARCHAR(128) NULL,
  ADD COLUMN reset_token_expires DATETIME NULL;

-- Optional: add an index to speed lookups by reset_token (if you store token hash elsewhere)
-- CREATE INDEX idx_user_reset_token ON user (reset_token);
