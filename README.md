# NYC Taxi Data Analytics Platform

基于 PySpark、PostgreSQL、Streamlit 和 Docker Compose 的城市出行数据平台。

## 项目目标
- 完成真实出行数据读取、清洗、质量统计和业务聚合
- 通过Streamlit展示每日趋势、小时分布、工作日/周末差异
- 使用Docker Compose可重复部署并检查服务健康

## 技术栈
Python · PySpark 4.2.1 · PostgreSQL 16 · Streamlit · Docker · WSL2

## 数据来源
NYC TLC 官方页面：
https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
使用 Yellow Taxi 2024年1月数据。

## 运行步骤
1. 在Windows安装WSL2 Ubuntu、Docker Desktop并启用WSL Integration。
2. 在WSL项目根目录复制 `.env.example` 为 `.env` 并设置强密码。
3. 下载官方Parquet文件到 `data/raw/`。
4. 运行 `docker compose up -d db`。
5. 运行 `docker compose build etl dashboard`。
6. 运行 `docker compose run --rm etl`。
7. 运行 `docker compose up -d dashboard`。
8. 在Windows浏览器打开 http://localhost:8501 。

## 测试
`docker compose run --rm etl python -m pytest -q`

## 已知限制
- 使用Spark Local，并非真实分布式集群
- 数据清洗阈值为教学假设，不等同于TLC官方质量标准
- Parquet与PostgreSQL之间没有跨系统原子事务
- 尚无Airflow调度和Prometheus/Grafana告警

