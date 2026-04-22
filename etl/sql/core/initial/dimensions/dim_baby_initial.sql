/* core/initial/dimensions/dim_baby_initial.sql */
INSERT INTO core.dim_baby (
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
VALUES (
    -1,
    'Unknown Baby',
    'UTC',
    '1900-01-01',
    '2099-12-31',
    TRUE,
    0,
    CURRENT_TIMESTAMP,
    NULL
);

WITH rank_for_dedup_babies AS (
    SELECT
        s.source_id,
        s.name,
        s.timezone,
        s.loaded_at,
        ROW_NUMBER() OVER (
            PARTITION BY s.source_id
            ORDER BY s.loaded_at DESC
        ) AS rn
    FROM staging.stg_baby s
    WHERE s.source_id IS NOT NULL
)
INSERT INTO core.dim_baby (
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
    r.source_id AS baby_nk,
    r.name AS baby_name,
    r.timezone AS timezone_iana,
    r.loaded_at AS valid_from,
    '2099-12-31 23:59:59'::timestamp AS valid_to,
    TRUE AS is_current,
    :job_id AS job_id,
    CURRENT_TIMESTAMP AS loaded_at,
    NULL AS updated_at
FROM rank_for_dedup_babies r
WHERE r.rn = 1;