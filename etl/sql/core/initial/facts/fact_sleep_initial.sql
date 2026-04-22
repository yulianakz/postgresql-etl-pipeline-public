/* core/initial/facts/fact_sleep_initial.sql */
INSERT INTO core.fact_sleep (
    baby_sk,
    sleep_start_date_sk,
    sleep_start_time_sk,
    duration_minutes,
    job_id,
    loaded_at
)
SELECT DISTINCT ON (s.baby_id, s.sleep_start)
    COALESCE(db.baby_sk, -1) AS baby_sk,
    TO_CHAR(s.sleep_start, 'YYYYMMDD')::INTEGER AS sleep_start_date_sk,
    (EXTRACT(HOUR FROM s.sleep_start)::INTEGER * 100 +
     EXTRACT(MINUTE FROM s.sleep_start)::INTEGER) AS sleep_start_time_sk,
    s.sleep_duration AS duration_minutes,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at
FROM staging.stg_sleep s
LEFT JOIN core.dim_baby db
    ON db.baby_nk = s.baby_id
    AND db.is_current = TRUE
WHERE s.sleep_start IS NOT NULL
  AND s.sleep_duration IS NOT NULL
ORDER BY s.baby_id, s.sleep_start, s.loaded_at DESC
ON CONFLICT(baby_sk, sleep_start_date_sk, sleep_start_time_sk) DO NOTHING;
