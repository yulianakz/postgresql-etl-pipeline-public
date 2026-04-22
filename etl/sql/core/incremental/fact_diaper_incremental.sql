/* core/incremental/fact_diaper_incremental.sql */
WITH last_processed_job_id AS (
    SELECT COALESCE(m.parent_job_id, 0) as last_stg_job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'core'
      AND m.destination_table_name = 'fact_diaper'
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
      AND m.destination_table_name = 'stg_diaper'
      AND m.pipeline_stage = 'extract'
      AND m.status = 'success'
      AND m.job_id > COALESCE((SELECT last_stg_job_id FROM last_processed_job_id), 0)
),
new_diaper_data_to_load AS (
    SELECT DISTINCT ON (s.baby_id, s.change_time)
        s.baby_id,
        s.change_time,
        s.status,
        s.job_id,
        s.loaded_at
    FROM staging.stg_diaper s
    WHERE s.job_id IN (SELECT job_id FROM new_jobs_to_load)
      AND s.change_time IS NOT NULL
      AND s.status IS NOT NULL
    ORDER BY s.baby_id, s.change_time, s.loaded_at DESC
)

INSERT INTO core.fact_diaper (
    baby_sk,
    change_date_sk,
    change_time_sk,
    diaper_status_sk,
    job_id,
    loaded_at
)
SELECT
    COALESCE(c_time.baby_sk, c_curr.baby_sk, -1) AS baby_sk,
    TO_CHAR(ndd.change_time, 'YYYYMMDD')::INTEGER AS change_date_sk,
    (EXTRACT(HOUR FROM ndd.change_time)::INTEGER * 100 +
     EXTRACT(MINUTE FROM ndd.change_time)::INTEGER) AS change_time_sk,
    COALESCE(ndd.status, 'UNKNOWN') AS diaper_status_sk,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at
FROM new_diaper_data_to_load ndd
LEFT JOIN core.dim_baby c_time
    ON c_time.baby_nk = ndd.baby_id
    AND ndd.change_time >= c_time.valid_from
    AND ndd.change_time < c_time.valid_to
LEFT JOIN core.dim_baby c_curr
    ON c_curr.baby_nk = ndd.baby_id
    AND c_curr.is_current = TRUE
ON CONFLICT(baby_sk, change_date_sk, change_time_sk) DO NOTHING;