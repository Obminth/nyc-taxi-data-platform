from datetime import datetime
import pytest
from pyspark.sql import SparkSession
from src.transform import clean_trips


@pytest.fixture(scope="module")
def spark():
    s = (SparkSession.builder.master("local[2]")
         .appName("test-taxi-transform")
         .config("spark.sql.session.timeZone", "America/New_York")
         .getOrCreate())
    yield s
    s.stop()


def test_clean_trips_removes_invalid_and_out_of_month(spark):
    rows = [
        (datetime(2024, 1, 2, 8, 0), datetime(2024, 1, 2, 8, 15), 2.5, 25.0),
        (datetime(2024, 1, 2, 9, 0), datetime(2024, 1, 2, 9, 10), 0.0, 10.0),
        (datetime(2024, 2, 2, 8, 0), datetime(2024, 2, 2, 8, 15), 3.0, 30.0),
    ]
    cols = [
        "tpep_pickup_datetime", "tpep_dropoff_datetime",
        "trip_distance", "total_amount"
    ]
    raw = spark.createDataFrame(rows, cols)
    result = clean_trips(raw, "2024-01-01", "2024-02-01")
    assert result.count() == 1
    first = result.first()
    assert first["trip_distance"] == 2.5
    assert first["duration_min"] == 15.0


def test_missing_required_column_raises(spark):
    bad = spark.createDataFrame([(1,)], ["unrelated_column"])
    with pytest.raises(ValueError, match="缺少必需字段"):
        clean_trips(bad, "2024-01-01", "2024-02-01")
