/* core/incremental/fact_sleep_incremental.sql */
WITH last_processed_job_id AS (
    SELECT m.parent_job_id as last_stg_job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'core'
      AND m.destination_table_name = 'fact_sleep'
      AND m.pipeline_stage = 'transform_load'
      AND m.status = 'success'
      AND m.parent_job_id IS NOT NULL
    ORDER BY m.ended_at DESC
    LIMIT 1
),
new_jobs_to_load AS(
    SELECT m.job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'staging'
      AND m.destination_table_name = 'stg_sleep'
      AND m.pipeline_stage = 'extract'
      AND m.status = 'success'
      AND m.job_id > COALESCE((SELECT last_stg_job_id FROM last_processed_job_id),0)
),
new_sleep_data_to_load AS(
    SELECT DISTINCT ON (s.baby_id, s.sleep_start)
        s.sleep_start,
        s.sleep_duration,
        s.baby_id,
        s.job_id,
        s.loaded_at
    FROM staging.stg_sleep AS s
    WHERE s.job_id IN (SELECT job_id FROM new_jobs_to_load)
      AND s.sleep_start IS NOT NULL
      AND s.sleep_duration IS NOT NULL
    ORDER BY s.baby_id, s.sleep_start, s.loaded_at DESC
)

INSERT INTO core.fact_sleep (
    baby_sk,
    sleep_start_date_sk,
    sleep_start_time_sk,
    duration_minutes,
    job_id,
    loaded_at
)
SELECT
    COALESCE(c_time.baby_sk, c_curr.baby_sk, -1) AS baby_sk,
    TO_CHAR(nsl.sleep_start, 'YYYYMMDD')::INTEGER AS sleep_start_date_sk,
    (EXTRACT(HOUR FROM nsl.sleep_start)::INTEGER * 100 +
     EXTRACT(MINUTE FROM nsl.sleep_start)::INTEGER) AS sleep_start_time_sk,
    nsl.sleep_duration AS duration_minutes,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at
FROM new_sleep_data_to_load nsl
LEFT JOIN core.dim_baby c_time
    ON c_time.baby_nk = nsl.baby_id
    AND nsl.sleep_start >= c_time.valid_from
    AND nsl.sleep_start < c_time.valid_to
LEFT JOIN core.dim_baby c_curr
    ON c_curr.baby_nk = nsl.baby_id
    AND c_curr.is_current = TRUE
ON CONFLICT(baby_sk, sleep_start_date_sk, sleep_start_time_sk) DO NOTHING;

