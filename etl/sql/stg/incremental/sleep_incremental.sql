/* stg/incremental/sleep_incremental.sql */
SELECT
    p.id,
    p.sleep_start,
    p.sleep_duration,
    p.baby_id
FROM public.sleep_data as p
WHERE :watermark_ts IS NULL
   OR p.sleep_start > :watermark_ts