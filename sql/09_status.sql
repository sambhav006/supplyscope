-- Accepted order grain; end-of-day promise; historical source-local times.
SELECT status,count(*) AS orders,count(*) FILTER(WHERE promise_at IS NULL) AS missing_promise,count(*) FILTER(WHERE delivered_at IS NULL) AS missing_actual FROM fact_order GROUP BY 1 ORDER BY orders DESC;
