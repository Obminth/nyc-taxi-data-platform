import argparse
import os
from datetime import date, datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from pyspark.sql import SparkSession, functions as F

from src.transform import clean_trips

ROOT = Path(__file__).resolve().parents[1]


def month_bounds(month):
    first_dt = datetime.strptime(month, "%Y-%m")
    first = date(first_dt.year, first_dt.month, 1)
    if first.month == 12:
        end = date(first.year + 1, 1, 1)
    else:
        end = date(first.year, first.month + 1, 1)
    return first, end


def save_results(month, source_file, start, end,
                 daily_rows, hourly_rows, source_count, clean_count):
    conn = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10,
    )
    try:
        # 同一个数据库事务内更新汇总表和执行记录
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM daily_metrics WHERE pickup_date >= %s AND pickup_date < %s",
                    (start, end),
                )
                cur.execute(
                    "DELETE FROM hourly_metrics WHERE month = %s", (month,)
                )
                execute_values(cur, """
                    INSERT INTO daily_metrics
                    (pickup_date, trip_count, total_amount, avg_distance, avg_duration)
                    VALUES %s
                """, daily_rows)
                execute_values(cur, """
                    INSERT INTO hourly_metrics
                    (month, pickup_hour, trip_count, total_amount)
                    VALUES %s
                """, hourly_rows)
                cur.execute("""
                    INSERT INTO etl_runs
                    (month, source_file, source_rows, clean_rows, rejected_rows, status)
                    VALUES (%s, %s, %s, %s, %s, 'success')
                """, (month, source_file, source_count,
                      clean_count, source_count - clean_count))
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="NYC出租车Spark批处理任务")
    parser.add_argument("--month", default="2024-01")
    parser.add_argument(
        "--input", default="data/raw/yellow_tripdata_2024-01.parquet"
    )
    args = parser.parse_args()
    start, end = month_bounds(args.month)
    source = ROOT / args.input
    if not source.is_file():
        raise FileNotFoundError(f"找不到原始文件：{source}")

    spark = (SparkSession.builder
             .master("local[2]")
             .appName("NYC-Taxi-Batch-ETL")
             .config("spark.driver.memory", "2g")
             .config("spark.sql.session.timeZone", "America/New_York")
             .getOrCreate())
    clean_df = None
    try:
        raw_df = spark.read.parquet(str(source))
        source_count = raw_df.count()
        clean_df = clean_trips(
            raw_df, start.isoformat(), end.isoformat()
        ).cache()
        clean_count = clean_df.count()
        if clean_count == 0:
            raise ValueError("清洗结果为空，请检查数据与清洗规则")

        output = ROOT / "data/processed" / args.month
        clean_df.write.mode("overwrite").parquet(str(output))

        daily_df = (clean_df.groupBy(
            F.to_date("pickup_time").alias("pickup_date")
        ).agg(
            F.count("*").alias("trip_count"),
            F.sum("total_amount").alias("total_amount"),
            F.avg("trip_distance").alias("avg_distance"),
            F.avg("duration_min").alias("avg_duration"),
        ))
        hourly_df = (clean_df.groupBy(
            F.hour("pickup_time").alias("pickup_hour")
        ).agg(
            F.count("*").alias("trip_count"),
            F.sum("total_amount").alias("total_amount"),
        ))

        # 仅将最多31条日汇总和24条小时汇总收回Python
        daily_rows = [
            (r["pickup_date"], int(r["trip_count"]),
             r["total_amount"], float(r["avg_distance"]),
             float(r["avg_duration"]))
            for r in daily_df.collect()
        ]
        hourly_rows = [
            (args.month, int(r["pickup_hour"]),
             int(r["trip_count"]), r["total_amount"])
            for r in hourly_df.collect()
        ]
        save_results(
            args.month, source.name, start, end, daily_rows, hourly_rows,
            source_count, clean_count,
        )
        print("ETL成功完成")
        print(f"原始行数: {source_count:,}")
        print(f"有效行数: {clean_count:,}")
        print(f"筛除行数: {source_count - clean_count:,}")
        print(f"每日汇总: {len(daily_rows)} 行")
        print(f"小时汇总: {len(hourly_rows)} 行")
    finally:
        if clean_df is not None:
            clean_df.unpersist()
        spark.stop()


if __name__ == "__main__":
    main()
