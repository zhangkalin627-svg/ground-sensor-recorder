# 下次开发从这里开始

当前版本 v0.24.2（仅文档更新，未测试）。代码状态：channel_report.py 为 0.19.0，drift_report.py 为 0.22.0，workbench.py 为 0.23.0，端到端测试为 v0.24.0，测试修复为 v0.24.1。

管家在云服务器上对提交 `70a9c642eed8e04958a007ccb890c3685dc77cb8` 运行 `python3 -m unittest discover`，178 项全部通过，退出码 0（2026-10-26 06:53 GMT+8）。这是沙箱复跑，不含真实测量数据；Tk 窗口、Windows 和真实硬件仍未实测。

## 已完成

- v0.24.0：新增 `test_pipeline_e2e.py`，7 项无显示器端到端测试，覆盖 `replay_session -> channel_report -> drift_report` 及 `workbench.py` 子进程串联。
- v0.24.1：修复端到端测试的 replay 辅助函数，为每次调用使用唯一输出目录。管家云测 178 项全过。
- v0.24.2：新增 `TOOLS_V0_24.md`，说明三步流程、参数、退出码和测试状态；本次只改文档，未测试。

## 后续开发

1. 继续完善无显示器的真实输入处理流程；接入 `realworld_sim` 前，先对照管家 10-22 的邮件说明，明确仿真输入和结果的标记，不推断为真实测量。
2. 为 `workbench.py` 的 replay、channel、drift 串联流程补充便于重复运行的入口或示例，保持输出不覆盖输入及已有结果。
3. 安排 Tk 窗口检查：导入包含坏行的文本日志，核对异常行状态文字；管家已说明可用 Xvfb 做虚拟显示测试，真实带屏设备仍待实测。

全套测试需在管家云服务器或用户电脑运行：

```text
python3 -m unittest discover
```

文档中的命令依据源码整理，未在本次更新中实际执行。