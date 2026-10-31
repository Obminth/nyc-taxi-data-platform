CREATE TABLE IF NOT EXISTS daily_metrics(
    pickup_date DATE PRIMARY KEY,
    trip_count BIGINT NOT NULL CHECK(trip_count>0),
    total_amount NUMERIC(18,2)NOT NULL,
    avg_distance DOUBLE PRECISION NOT NULL,
    avg_duration DOUBLE PRECISION NOT NULL
);

CREATE TABLE IF NOT EXISTS hourly_metrics(
    month VARCHAR(7) NOT NULL,
    pickup_hour SMALLINT NOT NULL
      CHECK(pickup_hour BETWEEN 0 AND 23),
    trip_count BIGINT NOT NULL CHECK(trip_count >= 0),
    total_amount NUMERIC(18,2) NOT NULL,
    PRIMARY KEY(month,pickup_hour)
);

CREATE TABLE IF NOT EXISTS etl_runs(
    id BIGSERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL,
    run_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_file TEXT NOT NULL,
    source_rows BIGINT NOT NULL,
    clean_rows BIGINT NOT NULL,
    rejected_rows BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'success'
);
