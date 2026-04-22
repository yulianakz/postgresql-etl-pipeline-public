/* core/initial/facts/fact_diaper_initial.sql */
INSERT INTO core.fact_diaper (
    baby_sk,
    change_date_sk,
    change_time_sk,
    diaper_status_sk,
    job_id,
    loaded_at
)
SELECT DISTINCT ON (s.baby_id, s.change_time)
    COALESCE(db.baby_sk, -1) AS baby_sk,
    TO_CHAR(s.change_time, 'YYYYMMDD')::INTEGER AS change_date_sk,
    (EXTRACT(HOUR FROM s.change_time)::INTEGER * 100 +
     EXTRACT(MINUTE FROM s.change_time)::INTEGER) AS change_time_sk,
    COALESCE(s.status,'UNKNOWN') AS diaper_status_sk,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at
FROM staging.stg_diaper s
LEFT JOIN core.dim_baby db
    ON db.baby_nk = s.baby_id
    AND db.is_current = TRUE
WHERE s.change_time IS NOT NULL
  AND s.status IS NOT NULL
ORDER BY s.baby_id, s.change_time, s.loaded_at DESC
ON CONFLICT(baby_sk, change_date_sk, change_time_sk) DO NOTHING;
