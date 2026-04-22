/* core/initial/dimensions/dim_date_initial.sql */
INSERT INTO core.dim_date (
    date_sk,
    full_date,
    year,
    month,
    day
)
SELECT DISTINCT
    TO_CHAR(d.date_value, 'YYYYMMDD')::INTEGER AS date_sk,
    d.date_value::DATE AS full_date,
    EXTRACT(YEAR FROM d.date_value)::INTEGER AS year,
    EXTRACT(MONTH FROM d.date_value)::INTEGER AS month,
    EXTRACT(DAY FROM d.date_value)::INTEGER AS day
FROM (
    SELECT generate_series(
        '2020-01-01'::DATE,
        '2030-12-31'::DATE,
        '1 day'::INTERVAL
    )::DATE AS date_value
) d
ON CONFLICT (date_sk) DO NOTHING;