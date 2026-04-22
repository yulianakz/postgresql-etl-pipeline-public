/* core/initial/dimensions/dim_time_initial.sql */
INSERT INTO core.dim_time (
    time_sk,
    full_time,
    hour,
    minute
)
SELECT
    (t.hour * 100 + t.minute) AS time_sk,
    (LPAD(t.hour::TEXT, 2, '0') || ':' || LPAD(t.minute::TEXT, 2, '0'))::TIME AS full_time,
    t.hour,
    t.minute
FROM (
    SELECT
        h AS hour,
        m AS minute
    FROM generate_series(0, 23) h
    CROSS JOIN generate_series(0, 59) m
) t
ON CONFLICT (time_sk) DO NOTHING;