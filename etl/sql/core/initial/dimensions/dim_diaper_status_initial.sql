/* core/initial/dimensions/dim_diaper_status_initial.sql */
-- Step 1: Insert UNKNOWN diaper status (placeholder for orphaned fact records)
INSERT INTO core.dim_diaper_status (
    diaper_status_sk,
    diaper_status,
    job_id,
    loaded_at,
    updated_at
)VALUES(
    'UNKNOWN',
    'UNKNOWN STATUS',
    0,
    CURRENT_TIMESTAMP,
    NULL
)
ON CONFLICT(diaper_status_sk) DO NOTHING;

-- Step 2: Insert all real data from stg
INSERT INTO core.dim_diaper_status (
    diaper_status_sk,
    diaper_status,
    job_id,
    loaded_at,
    updated_at
)
SELECT DISTINCT ON(s.status)
    s.status AS diaper_status_sk,
    s.status AS diaper_status,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at,
    NULL AS updated_at
FROM staging.stg_diaper AS s
WHERE status IS NOT NULL
ORDER BY s.status, s.loaded_at DESC
ON CONFLICT (diaper_status_sk) DO NOTHING;
