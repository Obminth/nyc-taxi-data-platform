from pyspark.sql import functions as F

REQUIRED_COLUMNS = {
    "tpep_pickup_datetime",
    "tpep_dropoff_datetime",
    "trip_distance",
    "total_amount",
}


def clean_trips(raw_df, start_date, end_date):
    """清洗出租车行程记录；start/end为YYYY-MM-DD字符串，右端不包含。"""
    missing = REQUIRED_COLUMNS - set(raw_df.columns)
    if missing:
        raise ValueError(f"缺少必需字段: {sorted(missing)}")

    df = raw_df.select(
        F.col("tpep_pickup_datetime").alias("pickup_time"),
        F.col("tpep_dropoff_datetime").alias("dropoff_time"),
        F.col("trip_distance").cast("double").alias("trip_distance"),
        F.col("total_amount").cast("decimal(14,2)").alias("total_amount"),
    )

    df = df.withColumn(
        "duration_min",
        F.timestamp_diff("SECOND", F.col("pickup_time"), F.col("dropoff_time")) / 60.0,
    )

    return df.filter(
        F.col("pickup_time").isNotNull()
        & F.col("dropoff_time").isNotNull()
        & (F.col("pickup_time") >= F.lit(start_date).cast("timestamp"))
        & (F.col("pickup_time") < F.lit(end_date).cast("timestamp"))
        & F.col("trip_distance").between(0.1, 100.0)
        & F.col("total_amount").between(0.01, 500.0)
        & F.col("duration_min").between(1.0, 240.0)
    )
