-- 只读核验：当前示例月份 2024-01；其他月份需调整所有月份条件。
SELECT count(*) AS daily_rows, sum(trip_count) AS daily_trips
FROM daily_metrics WHERE pickup_date >= DATE '2024-01-01' AND pickup_date < DATE '2024-02-01';
SELECT count(*) AS hourly_rows, sum(trip_count) AS hourly_trips
FROM hourly_metrics WHERE month = '2024-01';
WITH latest AS (
    SELECT * FROM etl_runs WHERE month = '2024-01' ORDER BY run_at DESC, id DESC LIMIT 1
), daily AS (
    SELECT sum(trip_count) AS trips, sum(total_amount) AS amount FROM daily_metrics
    WHERE pickup_date >= DATE '2024-01-01' AND pickup_date < DATE '2024-02-01'
), hourly AS (
    SELECT sum(trip_count) AS trips, sum(total_amount) AS amount
    FROM hourly_metrics WHERE month = '2024-01'
)
SELECT latest.run_at, latest.source_rows, latest.clean_rows, latest.rejected_rows,
       latest.status = 'success' AS run_succeeded,
       latest.source_rows = latest.clean_rows + latest.rejected_rows AS source_balanced,
       latest.clean_rows = daily.trips AND daily.trips = hourly.trips AS trips_balanced,
       daily.amount = hourly.amount AS amount_balanced
FROM latest CROSS JOIN daily CROSS JOIN hourly;
