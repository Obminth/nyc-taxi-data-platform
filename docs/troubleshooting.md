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

2026-11-01（香港时间）复测已有恢复结果。第 1～4 节是原有的历史故障记录，本次未重新制造字段拼写错误，也未重复执行字段重命名或完整 ETL。

| 验证项目 | 实际结果 |
| --- | --- |
| 历史 ETL 完成状态 | etl_runs 存在两次 success，最近一次香港时间为 2026-11-01 01:37:34 |
| 日汇总行数 | 31 |
| 小时汇总行数 | 24 |
| 有效订单数对账 | 日汇总 = 小时汇总 = clean_rows = 2,859,451 |
| 原始行数对账 | 2,964,624 = 2,859,451 + 105,173 |
| 金额字段 | 当前两张汇总表均为 total_amount；未见 total_amonut |
| 容器状态 | 启动已有 db 后，db 和 dashboard 均 healthy |
| 看板健康接口 | Windows 请求返回 HTTP 200，正文 ok |
| 页面代码验证 | AppTest 显示四个指标，无 exception/error；尚未保存浏览器截图 |
| 自动化测试 | 2 passed in 9.96s |

只读复查命令（在 WSL 项目目录执行）：

```bash
docker compose ps -a
docker compose exec -T db sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < sql/verify.sql
docker compose run --rm etl python -m pytest -q
curl -fsS http://localhost:8501/_stcore/health
```

本次核验证实已有汇总可供看板读取。历史运行的终端成功输出未另行保存，不能将当前数据库记录写成此次重跑 ETL 的日志。浏览器视觉效果仍需打开页面检查并截图。

## 6. 故障总结与改进措施

本次故障表明，容器运行正常并不代表整个数据处理链路正常。数据库表结构、ETL 程序以及数据看板之间需要保持一致。

后续计划：

- 在 ETL 执行前增加数据库字段检查。
- 使用自动化测试验证数据库表结构与程序写入字段是否匹配。
- 修改数据库结构时使用明确的数据库迁移 SQL。
- 将 ETL 执行状态、数据库数据量和看板健康状态纳入验收流程。
- 为常见故障建立排查文档，形成可复用的运维处理流程。
## 7. 本次核验发现数据库已停止

2026-11-01 检查时，`docker compose ps` 只显示运行中的看板，执行数据库查询返回 `service "db" is not running`。这说明当时 db 容器没有运行；停止原因没有足够证据，不能推断为数据库损坏。

执行 `docker compose start db` 启动已有容器，随后健康检查通过，现有表与汇总可查询。没有删除容器数据卷，也未重新初始化数据库。若新环境根本没有 db 容器，应使用 `docker compose up -d db` 创建并启动。

复测结果见第 5 节。看板查询有 60 秒缓存，页面暂时仍有数据显示不能单独证明 db 可用。本次属于恢复检查时发现的停止状态，不等于已完成指导书 13.2 的“主动停止看板 → 观察访问失败 → 启动看板 → 复测”全流程实验，后续已完成该实验并保存证据，见第 11 节。

## 8. 环境变量示例与新环境复现

核验发现 `.env.example` 首行含 `[ini]`，且写有具体密码。本次移除格式标记，并将密码改为 `CHANGE_ME_BEFORE_RUNNING`，避免将具体密码作为公开示例。没有修改运行中的 `.env` 或数据库用户密码。

首次使用时复制示例并设置自己的密码。已有 pgdata 卷时，修改 `.env` 的密码不会自动改变 PostgreSQL 中已创建用户的密码；遇到认证失败，先核对实际数据库配置，不要以删除卷作为修复方法。

## 9. 尚未实际演练的常见问题

以下为排查方法，不是本次发生过的故障：

- 找不到原始文件：检查当前目录和 `data/raw/yellow_tripdata_2024-01.parquet`，核对 `--month` 与 `--input` 是否匹配。
- Docker 命令不可用或无法连接引擎：检查 Windows Docker Desktop 和 Ubuntu WSL Integration，不另装第二套引擎。
- 页面显示无数据：检查 `hourly_metrics` 是否为空、ETL 是否成功，结合执行记录和 SQL 对账定位。
- 修改初始化 SQL 后表结构未变化：已有数据卷不会重新执行首次初始化脚本，需检查实际表结构并做有针对性的迁移。
- 本机端口或页面异常：检查 `docker compose ps -a`、日志及健康接口，再检查 Windows 浏览器。
## 10. GitHub 推送认证与远程仓库不存在

2026-11-01，首次 HTTPS 推送提示 `Password authentication is not supported for Git operations`。网页登录密码不能作为 Git HTTPS 密码，应使用 GitHub CLI 浏览器授权或访问令牌。用户已通过 `gh auth login` 成功登录 Obminth。

随后推送变为 `Repository not found`。检查 `gh api user --jq .login` 确认账号为 Obminth；`gh repo view Obminth/nyc-taxi-data-platform` 无法找到仓库；账号仓库列表为空。原因是远程仓库尚未创建，`git remote add origin` 仅保存地址，不会在 GitHub 新建仓库。

完成本地核验后，通过 `gh repo create Obminth/nyc-taxi-data-platform --public` 创建同名仓库，再由 `git push -u origin main` 推送。发布结果和 Actions 验证见项目核对记录。

## 11. 主动看板停服与恢复实验

2026-11-01 实际执行 `docker compose stop dashboard`。容器变为 Exited，健康请求出现 curl 连接错误 7；浏览器重新加载也返回连接被拒绝。随后 `docker compose start dashboard`，健康接口恢复为 `ok`，db 与 dashboard 均 healthy；新浏览器标签重新显示 2,859,451 条订单等四项指标。

原始状态输出见 `docs/evidence/stop-recovery.txt`，恢复截图见 `docs/screenshots/dashboard-restored.png`。内置浏览器未能导出失败页截图，因此不提供伪造的错误页图片。本实验保留了数据库卷和汇总结果。初轮停止曾观察到退出码 137，后续正式留证实验为退出码 0；退出码应结合当时操作和日志判断，不能单独推断为内存不足。

## 12. 看板弃用提示

AppTest 曾提示 `use_container_width` 将弃用。本次将 `st.dataframe` 改为 `width="stretch"`，重新构建并部署看板，浏览器恢复验证通过。
