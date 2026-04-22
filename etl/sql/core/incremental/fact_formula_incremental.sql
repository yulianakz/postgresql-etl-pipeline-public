/* core/incremental/fact_formula_incremental.sql */
WITH last_processed_job_id AS (
    SELECT COALESCE(m.parent_job_id, 0) as last_stg_job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'core'
      AND m.destination_table_name = 'fact_formula_feed'
      AND m.pipeline_stage = 'transform_load'
      AND m.status = 'success'
      AND m.parent_job_id IS NOT NULL
    ORDER BY m.ended_at DESC
    LIMIT 1
),
new_jobs_to_load AS (
    SELECT m.job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'staging'
      AND m.destination_table_name = 'stg_formula'
      AND m.pipeline_stage = 'extract'
      AND m.status = 'success'
      AND m.job_id > COALESCE((SELECT last_stg_job_id FROM last_processed_job_id), 0)
),
new_formula_data_to_load AS (
    SELECT DISTINCT ON (s.baby_id, s.feed_time)
        s.baby_id,
        s.feed_time,
        s.amount_ml,
        s.job_id,
        s.loaded_at
    FROM staging.stg_formula AS s
    WHERE s.job_id IN (SELECT job_id FROM new_jobs_to_load)
      AND s.feed_time IS NOT NULL
      AND s.amount_ml IS NOT NULL
    ORDER BY s.baby_id, s.feed_time, s.loaded_at DESC
)

INSERT INTO core.fact_formula_feed (
    baby_sk,
    f_feeding_date_sk,
    f_feeding_time_sk,
    amount_ml,
    job_id,
    loaded_at
)
SELECT
    COALESCE(c_time.baby_sk, c_curr.baby_sk, -1) AS baby_sk,
    TO_CHAR(nfd.feed_time, 'YYYYMMDD')::INTEGER AS f_feeding_date_sk,
    (EXTRACT(HOUR FROM nfd.feed_time)::INTEGER * 100 +
     EXTRACT(MINUTE FROM nfd.feed_time)::INTEGER) AS f_feeding_time_sk,
    nfd.amount_ml AS amount_ml,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at
FROM new_formula_data_to_load nfd
LEFT JOIN core.dim_baby c_time
    ON c_time.baby_nk = nfd.baby_id
    AND nfd.feed_time >= c_time.valid_from
    AND nfd.feed_time < c_time.valid_to
LEFT JOIN core.dim_baby c_curr
    ON c_curr.baby_nk = nfd.baby_id
    AND c_curr.is_current = TRUE
ON CONFLICT(baby_sk, f_feeding_date_sk, f_feeding_time_sk) DO NOTHING;