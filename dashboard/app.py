import os
from contextlib import closing

import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(page_title="NYC Taxi Analytics", page_icon="🚕", layout="wide")
st.title("🚕 NYC 城市出行数据分析平台")
st.caption("PySpark ETL · PostgreSQL · Streamlit · Docker Compose")


@st.cache_data(ttl=60)
def query(sql, params=()):
    with closing(psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=10,
    )) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [c[0] for c in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=cols)


try:
    months = query("SELECT DISTINCT month FROM hourly_metrics ORDER BY month DESC")
    if months.empty:
        st.info("还没有数据。请先执行：docker compose run --rm etl")
        st.stop()

    month = st.selectbox("分析月份", months["month"].tolist())
    daily = query("""
        SELECT pickup_date, trip_count, total_amount,
               avg_distance, avg_duration
        FROM daily_metrics
        WHERE TO_CHAR(pickup_date, 'YYYY-MM') = %s
        ORDER BY pickup_date
    """, (month,))
    hourly = query("""
        SELECT pickup_hour, trip_count, total_amount
        FROM hourly_metrics
        WHERE month = %s ORDER BY pickup_hour
    """, (month,))
    quality = query("""
        SELECT source_rows, clean_rows, rejected_rows
        FROM etl_runs WHERE month = %s
        ORDER BY run_at DESC LIMIT 1
    """, (month,))
except psycopg2.Error:
    st.error("数据库访问失败：请检查 Docker Compose 的 db 服务和日志。")
    st.stop()

if daily.empty:
    st.warning("当前月份没有每日统计结果。")
    st.stop()

daily["pickup_date"] = pd.to_datetime(daily["pickup_date"])
for name in ["total_amount", "avg_distance", "avg_duration"]:
    daily[name] = daily[name].astype(float)

trips = int(daily["trip_count"].sum())
amount = float(daily["total_amount"].sum())
avg_distance = (daily["avg_distance"] * daily["trip_count"]).sum() / trips
avg_duration = (daily["avg_duration"] * daily["trip_count"]).sum() / trips

c1, c2, c3, c4 = st.columns(4)
c1.metric("有效订单数", f"{trips:,}")
c2.metric("乘客总支付额", f"${amount:,.2f}")
c3.metric("平均行驶距离", f"{avg_distance:.2f} 英里")
c4.metric("平均行程时长", f"{avg_duration:.2f} 分钟")

st.subheader("每日订单量趋势")
st.line_chart(daily.set_index("pickup_date")["trip_count"])
st.subheader("各小时订单量分布")
st.bar_chart(hourly.set_index("pickup_hour")["trip_count"])

daily["day_type"] = daily["pickup_date"].dt.dayofweek.map(
    lambda i: "周末" if i >= 5 else "工作日"
)
comparison = daily.groupby("day_type")["trip_count"].mean()
st.subheader("工作日与周末的日均订单量")
st.bar_chart(comparison)

st.subheader("数据质量")
if not quality.empty:
    q = quality.iloc[0]
    rate = q["clean_rows"] / q["source_rows"] * 100 if q["source_rows"] else 0
    st.write(f"原始行数：{q['source_rows']:,}")
    st.write(f"有效行数：{q['clean_rows']:,}")
    st.write(f"筛除行数：{q['rejected_rows']:,}")
    st.write(f"有效比例：{rate:.2f}%")

st.subheader("每日统计表")
st.dataframe(daily, width="stretch")
st.download_button(
    "下载每日汇总CSV",
    data=daily.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"nyc_taxi_daily_{month}.csv",
    mime="text/csv",
)
st.caption("仅为教学规则下的有效样本；不代表全部订单或企业利润。")
