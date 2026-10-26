# 下次开发从这里开始

当前版本 v0.28.0（未测试）。`workbench.py` 的 `VERSION` 常量驱动帮助页版本文字。v0.27.0 云测为 184/185，唯一失败是 `test_workbench_drift` 将帮助页版本写死为 v0.26.0；v0.27.1（`74ed7d54c51a0c6a964d2a1960d536d653911ef9`）改为从 `workbench.VERSION` 断言并动态显示版本，已请管家复跑，结果尚未收到。

v0.28.0 为 `recorder_lines.py` 的导入状态行提取了无显示器可测的方法，新增 `test_recorder_lines_status.py` 的 3 项检查，更新工作台版本及 `TOOLS_V0_28.md`。这 3 项及全套测试均未运行；按 v0.27.0 的 185 项云测基数，预计全套 188 项。请在管家云服务器或用户电脑运行 `python3 -m unittest discover`。

## 已完成版本

- v0.25.0：新增 `pipeline_report.py`，依次回放基准和候选日志、生成通道 JSON 报告及漂移报告；`workbench.py` 注册 `pipeline` 命令；增加流程测试。
- v0.26.0：为流程增加 `pipeline_manifest.json`，记录输入文件名、大小、SHA-256、运行参数、输出名称、漂移通道、退出码和 UTC 时间；不记录绝对路径或输入内容。
- v0.27.0：失败时尽力写运行清单，记录失败阶段、错误类型和部分输出路径；云测发现帮助页版本测试断言过期。
- v0.27.1：版本常量改为单一来源，帮助页和测试都读取当前版本。
- v0.28.0：提取文本行导入状态更新方法并新增免显示器单元测试；不等同于真实 Tk 测试。

## 后续开发

1. 先修复管家云测发现的任何失败，并确认 v0.27.1、v0.28.0 的全套测试结果。
2. 为 `recorder_lines.py` 编写 Xvfb 窗口冒烟测试；真实带屏设备仍需单独实测。
3. 补充流水线失败清单写入失败等边界测试，改 `pipeline_report.py` 和 `test_pipeline_cli.py`。
4. `realworld_sim` 相关工作按管家 10-22 邮件说明标记为仿真，不得称为实测。

全套测试命令：

```text
python3 -m unittest discover
```
