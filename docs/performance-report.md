# Spark Local 端到端性能实测

2026-11-01（香港时间），在同一份 2024 年 1 月 TLC Parquet 上运行 2/4 线程各 3 次，交替执行且无并发 ETL 写入。原始 2,964,624 行，有效 2,859,451 行。Driver 设置 2g，WSL 可用 4 个逻辑处理器、约 7.8GiB 内存、2GiB swap。数据库和看板保持运行。

初始探索轮曾与单元测试重叠，未计入本报告；正式测量前已完成测试和镜像构建。使用已缓存的容器镜像、预热的数据与文件系统缓存，未清理系统缓存。Windows、浏览器和系统后台负载未被严格控制，因此仅作为本机小样本实验。

| 配置 | 第 1 次 秒 | 第 2 次 秒 | 第 3 次 秒 | 均值 秒 |
| --- | ---: | ---: | ---: | ---: |
| local[2] | 16.240 | 16.701 | 16.073 | 16.338 |
| local[4] | 14.752 | 15.225 | 14.747 | 14.908 |

本轮 local[4] 平均耗时比 local[2] 低约 **8.75%**。计时通过 Python 单调时钟覆盖整个 `docker compose run --rm etl`，包含容器创建、等待数据库、JVM 启动、Parquet 读写、SQL 写入和退出；不是 Spark 内核纯计算基准。只有三次样本，不能保证其他规模或机器上同样更快，也不是分布式扩容结果。

六次执行均 exit=0，均输出 ETL 成功、相同行数和 31/24 行汇总。重复执行按月覆盖汇总，执行记录追加。原始计时见 [CSV](evidence/performance.csv)，详细 Spark 日志见 `evidence/etl-local2-1.txt` 至 `evidence/etl-local4-3.txt`。

复现（会覆盖本月处理明细和汇总，追加执行记录）：

```bash
python3 scripts/benchmark.py
```

单次命令：

```bash
docker compose run --rm etl python -m src.etl --month 2024-01 --spark-master 'local[2]'
docker compose run --rm etl python -m src.etl --month 2024-01 --spark-master 'local[4]'
```

默认仍为 local[2]，无需修改源代码即可切换；每次运行后应重新执行 `sql/verify.sql`。测量数据来自 `time.perf_counter()`，UTC 时间字段仅用于定位运行。
