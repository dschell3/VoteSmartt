-- Maintenance note: Manual FK correction for legacy DBs; consider moving to managed migrations; remove after all environments are updated.
-- Safety: only run if current FK points to `choices`

-- Inspect current FK
-- SELECT kcu.constraint_name, kcu.referenced_table_name
-- FROM information_schema.key_column_usage kcu
-- WHERE kcu.table_schema=DATABASE() AND kcu.table_name='vote' AND kcu.column_name='vote_option_id' AND kcu.referenced_table_name IS NOT NULL;

ALTER TABLE vote DROP FOREIGN KEY fk_vote_option1;
ALTER TABLE vote
  ADD CONSTRAINT fk_vote_option1
  FOREIGN KEY (vote_option_id)
  REFERENCES `option` (option_id)
  ON DELETE CASCADE;
