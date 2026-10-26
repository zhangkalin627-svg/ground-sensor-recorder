# v0.26.0：一键流程的输入指纹清单

本版在 v0.25.0 的 `pipeline_report.py` 输出中新增 `pipeline_manifest.json`。清单记录流程版本、UTC 生成时间、基准和候选输入文件名、字节数、SHA-256、使用参数、报告相对路径、漂移通道和退出码。清单不保存输入文件内容或绝对路径。开始和结束时会计算输入指纹；发现输入在运行期间变化时，不生成 manifest 并报错。

## 用法

```text
python workbench.py pipeline baseline.txt candidate.txt --out run-001 --expected-interval 0.05 --gap-factor 1.5 --max-rel-change 0.10 --strict
```

`--out` 必须是尚不存在的新目录。流程生成 `baseline_sessions/`、`candidate_sessions/`、`baseline.json`、`candidate.json`、`drift.json` 和 `pipeline_manifest.json`。不得复用已有输出目录。运行中失败可能留下部分结果；检查后使用新的输出目录重跑。

退出码：无漂移或未启用 `--strict` 时为 0；启用 `--strict` 且发现漂移时为 2；参数、输入或文件写入错误时为 1。

## 测试状态

本版在原有 5 项 `test_pipeline_cli.py` 断言中增加 manifest 字段、输入 SHA-256、退出码及不泄露绝对路径的检查；共 5 项测试，代码和测试未测试。请在仓库根目录运行：

```text
python3 -m unittest discover
```

全套预计 183 项。v0.24.1 的 178 项通过结果不代表 v0.26.0 已测试；真实测量数据、硬件和 Tk 窗口仍未验证。
