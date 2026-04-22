/* core/incremental/dim_diaper_status_incremental.sql */
WITH last_processed_job_id AS (
    SELECT COALESCE(m.parent_job_id, 0) as last_stg_job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'core'
      AND m.destination_table_name = 'dim_diaper_status'
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
new_status_data AS (
    SELECT DISTINCT
        s.status
    FROM staging.stg_diaper AS s
    WHERE s.job_id IN (SELECT job_id FROM new_jobs_to_load)
      AND s.status IS NOT NULL
)

INSERT INTO core.dim_diaper_status (
    diaper_status_sk,
    diaper_status,
    job_id,
    loaded_at,
    updated_at
)
SELECT
    status AS diaper_status_sk,
    status AS diaper_status,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at,
    NULL AS updated_at
FROM new_status_data
ON CONFLICT (diaper_status_sk) DO NOTHING;