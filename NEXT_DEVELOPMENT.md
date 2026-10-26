# 下次开发从这里开始

当前版本 v0.25.0（代码和测试未测试）。代码状态：channel_report.py 为 0.19.0，drift_report.py 为 0.22.0，workbench.py 为 0.25.0，pipeline_report.py 新增两份日志一键对比，test_pipeline_cli.py 新增 5 项流程测试。

管家在云服务器上对提交 `70a9c642eed8e04958a007ccb890c3685dc77cb8` 运行 `python3 -m unittest discover`，178 项全部通过，退出码 0（2026-10-26 06:53 GMT+8）。该结果针对 v0.24.1，不是 v0.25.0；使用沙箱数据，不含真实测量数据。

## 本版改动

- 新增 `pipeline_report.py`，一条命令依次回放基准和候选日志、生成通道 JSON 报告、生成漂移 JSON 报告。输出目录必须是新目录，避免覆盖已有文件。
- `workbench.py` 注册 `pipeline` 命令并更新入口版本为 v0.25.0。
- 新增 `test_pipeline_cli.py` 5 项测试；更新 `test_workbench_drift.py` 的版本、帮助和模块命令断言。
- 新增 `TOOLS_V0_25.md` 说明参数、输出文件和退出码。
- 本版代码、测试和文档均未测试。预期全套 183 项，需在管家云服务器或用户电脑运行 `python3 -m unittest discover`。

## 后续开发

1. 先根据管家对 v0.25.0 的复跑结果修复任何失败项。
2. 继续完善无显示器的真实输入处理；接入 `realworld_sim` 前按管家 10-22 邮件说明标记为仿真，不能称为实测。
3. 安排 Tk 窗口检查：导入含坏行日志并核对异常行状态；管家已说可以用 Xvfb 做虚拟显示测试，真实带屏设备仍待实测。

全套测试命令：

```text
python3 -m unittest discover
```
