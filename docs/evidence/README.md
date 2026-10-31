# 实际运行证据

这些文本来自本机实际命令输出；为便于 Git 展示统一了换行并移除行末空白，未改写数值或成功失败结果。Spark 进度条中的回车按换行展示。

- `etl-local*-*.txt` 与 `performance.csv`：正式六次端到端测量。
- `pytest.txt`：本地单元测试。
- `sql-verification.txt`：日、小时、执行记录及支付额对账。
- `stop-recovery.txt`：主动停服、连接失败与恢复。
- `compose-status.txt`、`environment.txt`：采集时的状态快照。
- `dashboard-apptest.txt`：页面代码和真实数据库查询验证。
- `hello-world.txt`：Docker 独立运行验证。

截图中的 pytest、Compose 和 SQL 文件页为这些实际输出在 GitHub 上的展示，不是模拟终端。看板截图直接来自本机运行页面。
