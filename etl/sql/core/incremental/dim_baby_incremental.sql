/* core/incremental/dim_baby_incremental.sql */
-- Step 1: compute general tem table
CREATE TEMP TABLE tmp_find_changes AS
WITH last_processed_job_id AS (
    SELECT
        COALESCE(m.parent_job_id, 0) as last_stg_job_id
    FROM metadata.etl_job AS m
    WHERE m.destination_schema = 'core'
      AND m.destination_table_name = 'dim_baby'
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
      AND m.destination_table_name = 'stg_baby'
      AND m.pipeline_stage = 'extract'
      AND m.status = 'success'
      AND m.job_id > COALESCE((SELECT last_stg_job_id FROM last_processed_job_id),0)
),
new_baby_data_to_load AS(
    SELECT DISTINCT ON (s.source_id, s.timezone)
        s.source_id,
        s.name,
        s.timezone,
        s.job_id,
        s.loaded_at
    FROM staging.stg_baby AS s
    WHERE s.job_id IN (SELECT job_id FROM new_jobs_to_load)
      AND s.source_id IS NOT NULL
      AND s.timezone IS NOT NULL
      AND s.name IS NOT NULL
    ORDER BY s.source_id, s.timezone, s.job_id
),
nbd_with_timezone_history AS (
    SELECT
        source_id,
        name,
        timezone,
        job_id,
        loaded_at,
        LAG(timezone) OVER (PARTITION BY source_id ORDER BY job_id, loaded_at) AS prev_timezone
    FROM new_baby_data_to_load
),
nbd_with_tz_history_filtered AS(
    SELECT
        source_id,
        name,
        timezone,
        job_id,
        loaded_at,
        prev_timezone
    FROM nbd_with_timezone_history
    WHERE prev_timezone IS DISTINCT FROM timezone
        OR prev_timezone IS NULL
),
find_changes_in_baby_data AS (
    SELECT
        n.job_id,
        n.source_id,
        c.baby_nk,
        n.name,
        n.loaded_at,
        n.timezone,
        n.prev_timezone,
        c.timezone_iana AS current_timezone
    FROM nbd_with_tz_history_filtered n
    LEFT JOIN core.dim_baby c
      ON c.baby_nk = n.source_id
     AND c.is_current = TRUE
)
SELECT * FROM find_changes_in_baby_data;

-- Step 2: expire old records for babies whose timezone has changed
WITH changed_babies AS (
    SELECT
        source_id,
        MIN(loaded_at) AS stg_loaded_at
    FROM tmp_find_changes
    WHERE baby_nk IS NOT NULL
      AND current_timezone IS DISTINCT FROM timezone
    GROUP BY source_id
)
UPDATE core.dim_baby d
SET
    valid_to   = c.stg_loaded_at,
    is_current = FALSE,
    updated_at = CURRENT_TIMESTAMP
FROM changed_babies c
WHERE d.baby_nk = c.source_id
  AND d.is_current = TRUE;

-- Step 3: insert new SCD2 rows for babies whose timezone has changed
WITH changed_babies AS (
    SELECT
        source_id,
        name,
        timezone,
        job_id,
        loaded_at,
        prev_timezone
    FROM tmp_find_changes
    WHERE baby_nk IS NOT NULL
      AND current_timezone IS DISTINCT FROM timezone
),
changed_babies_with_rn AS (
    SELECT
        source_id,
        name,
        timezone,
        job_id,
        loaded_at AS stg_loaded_at,
        ROW_NUMBER() OVER (PARTITION BY source_id ORDER BY job_id DESC) AS rn_desc
    FROM changed_babies
),
insert_changed_babies AS (
    SELECT
         source_id AS baby_nk,
         name AS baby_name,
         timezone AS timezone_iana,
         stg_loaded_at AS valid_from,
         CASE
            WHEN rn_desc = 1 THEN '2099-12-31 23:59:59'::timestamptz
            ELSE LEAD(stg_loaded_at) OVER (PARTITION BY source_id ORDER BY job_id)
         END AS valid_to,
         CASE
            WHEN rn_desc = 1 THEN TRUE
            ELSE FALSE
         END AS is_current,
         :job_id AS job_id,
         CURRENT_TIMESTAMP AS loaded_at,
         CASE
            WHEN rn_desc = 1 THEN NULL
            ELSE CURRENT_TIMESTAMP
         END AS updated_at
    FROM changed_babies_with_rn
)
INSERT INTO core.dim_baby(
    baby_nk,
    baby_name,
    timezone_iana,
    valid_from,
    valid_to,
    is_current,
    job_id,
    loaded_at,
    updated_at
)
SELECT
    baby_nk,
    baby_name,
    timezone_iana,
    valid_from,
    valid_to,
    is_current,
    job_id,
    loaded_at,
    updated_at
FROM insert_changed_babies;

-- Step 4: insert brand new babies that don't exist in core yet
WITH brand_new_babies_rows AS (
    SELECT
        source_id,
        name,
        timezone,
        loaded_at
    FROM tmp_find_changes
    WHERE baby_nk IS NULL
)
INSERT INTO core.dim_baby(
    baby_nk,
    baby_name,
    timezone_iana,
    valid_from,
    valid_to,
    is_current,
    job_id,
    loaded_at,
    updated_at
)
SELECT
    source_id AS baby_nk,
    name AS baby_name,
    timezone AS timezone_iana,
    loaded_at AS valid_from,
    '2099-12-31 23:59:59'::timestamptz AS valid_to,
    TRUE AS is_current,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at,
    NULL AS updated_at
FROM brand_new_babies_rows;
