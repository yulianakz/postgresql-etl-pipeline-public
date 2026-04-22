BEGIN;

UPDATE staging.stg_baby
SET job_id = 1
WHERE row_hash = '55459d53f5401f6f6d9909b923c858fb1fd071b798e4c1f76023638295a86261'
  AND source_id = 1
  AND name = 'Adriana'
  AND timezone = 'Europe/Chisinau'
  AND job_id = 12
  AND loaded_at = '2026-04-21 19:35:38.176525+00';

-- 1) STG BABY: timezone change loaded in April (SCD2 trigger)
-- Adriana source_id = 1
INSERT INTO staging.stg_baby (row_hash, source_id, name, timezone, job_id, loaded_at) VALUES
('f4f5f6f701111111111111111111111111111111111111111111111111111111', 1, 'Adriana', 'Europe/Berlin', 12, '2026-04-24T09:00:00+00:00');

-- 2) STG SLEEP: two April rows for Adriana
-- Both are < your mentioned last watermark 2026-04-23 12:45:00+00
-- to test late-arriving event behavior with new stg job_id.
INSERT INTO staging.stg_sleep (row_hash, source_id, sleep_start, sleep_duration, baby_id, job_id, loaded_at) VALUES
('a111111111111111111111111111111111111111111111111111111111111111', 83001, '2026-04-23T10:30:00+00:00', 70, 1, 1302, '2026-04-24T09:05:00+00:00'),
('b222222222222222222222222222222222222222222222222222222222222222', 83002, '2026-04-23T11:50:00+00:00', 55, 1, 1302, '2026-04-24T09:06:00+00:00');

COMMIT;