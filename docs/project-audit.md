# 项目第一版验收记录

核验日期：2026-11-01（Asia/Hong_Kong）。范围为指导书第一版单机 WSL2 + Docker 项目；多节点、Kafka、Airflow 和监控平台属于后续版本，不在本次第一版交付范围内。

## 已完成

| 验收项 | 实际结果与证据 |
| --- | --- |
| WSL2 与 Docker | Ubuntu-24.04 为 WSL2；Docker 引擎 29.9.2，Compose v5.6.1；hello-world 实际成功，见 evidence/hello-world.txt |
| 源码与编排 | 三服务编排、清洗、ETL、三张数据库表、看板和 2 个单元测试齐全 |
| 数据 | 49,961,641 字节原始 Parquet；2,964,624 原始行，2,859,451 有效行；明细目录含 _SUCCESS |
| 完整 ETL | 已完成探索轮和正式六次重跑，正式日志见 evidence/etl-local*.txt，全部 exit=0 |
| SQL 质量检查 | 日=小时=有效=2,859,451；原始=有效+筛除；日、小时金额一致，四个验证标志均 t |
| 本地测试 | 2 passed in 11.42s，见 evidence/pytest.txt |
| 看板与导出 | 浏览器显示指标和图表，CSV 实际 31 行，订单和金额合计一致；AppTest 通过 |
| 服务恢复 | 主动停止 dashboard 后连接失败；启动后健康接口 ok、两容器 healthy、页面指标恢复 |
| 性能 | 2/4 线程各 3 次正式测量；均值 16.338/14.908 秒，本轮 4 线程耗时低约 8.75% |
| 工程文档 | README、架构 Mermaid、分析报告、排障记录、性能报告、原始日志与截图齐全 |
| 许可证 | MIT 代码许可证；TLC 数据使用条件另按官方说明 |
| GitHub 仓库 | 已创建 Obminth/nyc-taxi-data-platform 公开仓库；推送和 CI 结果在下节补记 |
| CI 工作流 | .github/workflows/tests.yml；Python 3.12、Java 17，自动运行 pytest；支持手动触发 |

## 发布验证

仓库地址：https://github.com/Obminth/nyc-taxi-data-platform

Actions 地址：https://github.com/Obminth/nyc-taxi-data-platform/actions

本地交付已就绪，等待本次推送后的远程运行结果；远程通过后再补入具体运行链接。

## 环境和边界

原项目 `.env`、原始数据、处理明细仍在本机，未纳入 Git。发布前检查了已有提交历史和待发布文本，未发现本机数据库密码。没有更换用户现有数据库凭据，没有删除数据卷或迁移 WSL。

WSL 资源上限为约 8GB 内存、4 个逻辑处理器、2GB swap。`.wslconfig` 原文件含额外 `[ini]` 标记，未修改全局配置。C 盘空间低于指导书预算；此前核验约余 10.17GiB，镜像操作后进一步减少，后续应先核对存储位置并安排空间，再扩数据或构建更多镜像。未进行自动清理或迁移。

系统是 Spark Local 单机教学平台，无跨系统原子提交、生产高可用或告警。本地测试覆盖范围有限，CI 是单元测试，不等于生产自动部署。性能比较已注明缓存和背景负载限制。

## 证据说明

截图均来自实际浏览器页面。SQL、Compose 和 pytest 以原始命令文本输出留证；如有生成的文本展示截图，会明确标注其来自日志。停服失败页受内置浏览器导出限制未保存图片，实际连接失败由 curl 原始输出留证。没有伪造失败页或测试结果。
