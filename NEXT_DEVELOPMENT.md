# 下次开发从这里开始

当前版本 v0.41.0（未测试）。本版更新 README.md 的版本、命令、15 模块状态和验证边界；新增 test_recorder_window_playback.py，覆盖文本回放结束、暂停后保持进度并继续，以及连续导入时替换当前视图并保留旧会话目录。workbench.py 与 recorder_lines.py 的版本标记同步到 0.41.0，没有改回放生产逻辑。

本环境没有运行测试。预计新增 3 项 Tk 窗口测试；全套实际数量和结果待管家云服务器或用户电脑运行确认。测试命令：

```text
xvfb-run -a python3 -m unittest test_recorder_window_playback
python3 -m unittest discover
python workbench.py --help
```

窗口测试需要 Tk 和 DISPLAY；没有显示环境时会跳过，跳过不算通过。真实测量数据、真实硬件与 Tk 真机仍未验证。

## 后续开发

1. 管家有新任务时先处理；收到针对当前提交的测试失败时，按测试名和原始错误优先修复。没有任务或失败时继续迭代，不等待云测结果。
2. 为 `recorder_lines.py` 补充运行中模拟采集切换到文本回放的状态与旧采集文件关闭边界测试，涉及 `test_recorder_window_playback.py`，必要时再改 `recorder_lines.py`。
3. 依据管家的仿真说明规划 `realworld_sim` 使用流程；仿真输出必须标为仿真，不得声称是真实测量或火箭专用模型结果。
4. 持续维护 README.md、版本使用说明与本文件，清楚写出功能和验证范围。

全套测试需在管家云服务器或用户电脑运行；当前环境未运行命令行测试。
