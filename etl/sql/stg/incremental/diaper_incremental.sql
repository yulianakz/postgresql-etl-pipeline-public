/* stg/incremental/diaper_incremental.sql */
SELECT
    p.id,
    p.change_time,
    p.status,
    p.baby_id
FROM public.diaper_data as p
WHERE :watermark_ts IS NULL
   OR p.change_time > :watermark_ts