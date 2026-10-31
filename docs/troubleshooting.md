# 故障排查记录：ETL 数据写入失败及数据看板无数据

**项目名称：** NYC Taxi Data Platform（纽约城市出行大数据分析平台）

**故障发生日期：** 2026-10-31

**技术环境：** Windows 11、WSL2 Ubuntu、Docker Compose、PySpark、PostgreSQL 16、Streamlit

## 1. 故障现象

在完成 Docker 镜像构建并启动 Streamlit 数据看板后，浏览器能够正常访问 `http://localhost:8501`，但页面提示：

> 还没有数据。请先执行：docker compose run --rm etl

随后重新执行 ETL 任务，Spark 能够正常启动，数据库连接正常，但数据写入阶段发生异常：

`psycopg2.errors.UndefinedColumn: column "total_amount" of relation "daily_metrics" does not exist`

故障导致 ETL 任务无法正常完成，PostgreSQL 未能写入本次汇总结果，因此看板缺少需要展示的数据。

## 2. 故障排查过程

**第一步：检查 Docker 容器状态**

执行命令：`docker compose ps`

目的：确认 PostgreSQL 和 Streamlit 容器是否正常运行。

检查结果：PostgreSQL 容器显示 Healthy，Streamlit 页面可以正常访问，初步排除容器未启动的问题。

**第二步：检查数据库表结构**

执行命令：

`docker compose exec db psql -U taxi_user -d taxi_analytics -c '\d+ public.daily_metrics'`

以及：

`docker compose exec db psql -U taxi_user -d taxi_analytics -c '\d+ public.hourly_metrics'`

目的：检查两张汇总表的字段名、数据类型和约束。

检查结果：发现数据库中的金额字段拼写为 `total_amonut`，而 ETL 代码使用的是 `total_amount`。

**第三步：检查 ETL 程序**

通过 `nl -ba src/etl.py | sed -n '20,75p'` 检查代码。

确认 ETL 使用 psycopg2 的 `execute_values()` 方法向 PostgreSQL 写入汇总结果，INSERT 语句中的字段名称为 `total_amount`。

进一步在 ETL 容器内部检查数据库连接和 SQL，确认连接目标为 `taxi_analytics` 数据库、`public` 模式，并排除同名表搜索路径问题。

## 3. 根本原因分析

故障的根本原因是数据库字段名称与 ETL 程序中的字段名称不一致。

建表时将正确字段 `total_amount` 错写成了 `total_amonut`，导致 PostgreSQL 无法匹配 INSERT 语句指定的字段。

由于 PostgreSQL 初始化脚本仅在数据目录首次初始化时自动执行，因此后续修改 SQL 文件不会自动修复已经创建的数据库表。

## 4. 故障恢复操作

采用 PostgreSQL 的 `ALTER TABLE ... RENAME COLUMN` 修改字段名称，而不是删除并重新创建数据库。

日汇总表修复命令：

`docker compose exec db psql -U taxi_user -d taxi_analytics -c "ALTER TABLE public.daily_metrics RENAME COLUMN total_amonut TO total_amount;"`

小时汇总表修复命令：

`docker compose exec db psql -U taxi_user -d taxi_analytics -c "ALTER TABLE public.hourly_metrics RENAME COLUMN total_amonut TO total_amount;"`

同时检查并修正 `sql/init.sql` 中的字段名称，避免未来重新初始化数据库时再次出现相同错误。

之后重新执行：

`docker compose run --rm etl`

该方案只修改数据库字段名称，保留原有数据和数据库持久化卷。

## 5. 恢复验证

以下结果应根据实际运行情况填写：

- ETL 是否输出“ETL 成功完成”：待验证
- `daily_metrics` 实际数据行数：待填写
- `hourly_metrics` 实际数据行数：待填写
- Streamlit 页面是否恢复显示图表：待验证
- Docker 容器是否正常运行：待最终复测

验证命令：

`docker compose exec db psql -U taxi_user -d taxi_analytics -c "SELECT COUNT(*) FROM daily_metrics;"`

`docker compose exec db psql -U taxi_user -d taxi_analytics -c "SELECT COUNT(*) FROM hourly_metrics;"`

验证完成后，在 Windows 浏览器中刷新 `http://localhost:8501`，检查图表是否正确显示。

## 6. 故障总结与改进措施

本次故障表明，容器运行正常并不代表整个数据处理链路正常。数据库表结构、ETL 程序以及数据看板之间需要保持一致。

后续计划：

- 在 ETL 执行前增加数据库字段检查。
- 使用自动化测试验证数据库表结构与程序写入字段是否匹配。
- 修改数据库结构时使用明确的数据库迁移 SQL。
- 将 ETL 执行状态、数据库数据量和看板健康状态纳入验收流程。
- 为常见故障建立排查文档，形成可复用的运维处理流程。