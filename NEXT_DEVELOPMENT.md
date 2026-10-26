# 下次开发从这里开始

当前版本 v0.42.0（未测试）。本版在 `test_recorder_window_playback.py` 增加一项 Tk 测试：从已有模拟采集切换到文本日志回放时，确认旧采集事件日志记录切换原因、数据与事件文件都关闭，并切到新回放。`recorder_lines.py`、`workbench.py` 的版本标记同步到 0.42.0；更新 README.md 和 TOOLS_V0_42.md。没有改切换生产逻辑。

本环境没有运行测试。新增 Tk 测试和全套测试均待管家云服务器或用户电脑运行。命令：

```text
xvfb-run -a python3 -m unittest test_recorder_window_playback
python3 -m unittest discover
python workbench.py --help
```

窗口测试需要 Tk 和 DISPLAY；没有显示环境时会跳过，跳过不算通过。真实测量数据、真实硬件与 Tk 真机仍未验证。

## 后续开发

1. 管家有新任务时先处理；收到针对当前提交的测试失败时，按测试名和原始错误优先修复。没有任务或失败时继续迭代，不等待云测结果。
2. 为模拟采集切换到文本导入时的异常路径补充覆盖，重点检查旧采集会话在事件写入或关闭报错时的状态清理，涉及 `recorder.py`、`recorder_lines.py` 和 `test_recorder_window_playback.py`。
3. 依据管家的仿真说明规划 `realworld_sim` 使用流程；仿真输出必须标为仿真，不得声称是真实测量或火箭专用模型结果。
4. 持续维护 README.md、版本使用说明与本文件，清楚写出功能和验证范围。

全套测试需在管家云服务器或用户电脑运行；当前环境未运行命令行测试。
