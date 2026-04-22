/* core/initial/facts/fact_formula_feed_initial.sql */
INSERT INTO core.fact_formula_feed (
    baby_sk,
    f_feeding_date_sk,
    f_feeding_time_sk,
    amount_ml,
    job_id,
    loaded_at
)
SELECT DISTINCT ON (s.baby_id, s.feed_time)
    COALESCE(db.baby_sk, -1) AS baby_sk,
    TO_CHAR(s.feed_time, 'YYYYMMDD')::INTEGER AS f_feeding_date_sk,
    (EXTRACT(HOUR FROM s.feed_time)::INTEGER * 100 +
     EXTRACT(MINUTE FROM s.feed_time)::INTEGER) AS f_feeding_time_sk,
    s.amount_ml AS amount_ml,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at
FROM staging.stg_formula s
LEFT JOIN core.dim_baby db
    ON db.baby_nk = s.baby_id
    AND db.is_current = TRUE
WHERE s.feed_time IS NOT NULL
  AND s.amount_ml IS NOT NULL
ORDER BY s.baby_id, s.feed_time, s.loaded_at DESC
ON CONFLICT(baby_sk, f_feeding_date_sk, f_feeding_time_sk) DO NOTHING;
