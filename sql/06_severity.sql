-- Accepted order grain; end-of-day promise; historical source-local times.
SELECT delay_days,count(*) AS orders FROM fact_order WHERE late GROUP BY 1 ORDER BY 1;
