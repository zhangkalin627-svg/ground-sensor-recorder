# v0.25.0：一条命令完成两份日志对比

本版新增 `pipeline_report.py`，并在 `workbench.py` 注册 `pipeline` 子命令。它在无显示器环境按顺序执行：文本日志回放、生成通道统计、比较基准和候选报告。

## 用法

在仓库根目录执行：

```text
python workbench.py pipeline baseline.txt candidate.txt --out run-001 --expected-interval 0.05 --gap-factor 1.5 --max-rel-change 0.10 --strict
```

将 `baseline.txt` 和 `candidate.txt` 换成两份符合 `adapters.LineAdapter` 字段顺序的文本行日志。采样周期由使用者提供，单位为秒；工具不会推测。漂移相对阈值默认 0.10（10%），也可设置 `--max-abs-change`。

`--out` 必须指定一个尚不存在的目录。程序不会覆盖输入文件或已有输出；运行后会生成：

- `baseline_sessions/` 和 `candidate_sessions/`：各自的 replay 采集目录，包含 `samples.csv`、`anomalies.csv`、`device.json`
- `baseline.json` 和 `candidate.json`：通道报告
- `drift.json`：漂移对比报告

缺少有效样本或参数无效时返回 1；正常结束返回 0；有漂移且使用 `--strict` 时返回 2。失败发生在输出目录创建之后时，目录可能留有本次生成的部分文件，换一个新目录重跑即可。

## 测试状态

新增 `test_pipeline_cli.py` 5 项测试，覆盖一键流程、漂移退出码、同数据无漂移、拒绝复用已有输出目录、无效采样周期和 workbench 路由；更新 `test_workbench_drift.py` 的版本及模块入口断言。此次代码和测试均标注“未测试”，需在管家云服务器或用户电脑的仓库根目录运行：

```text
python3 -m unittest discover
```

上一版 v0.24.1 的 178 项云端测试通过；这不是本版测试结果。本版预期全套 183 项。Tk 窗口、真实硬件和真实测量数据仍未验证。
