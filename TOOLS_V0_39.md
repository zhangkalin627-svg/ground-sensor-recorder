# v0.39.0：文本日志导入失败状态测试

本版在 `test_recorder_window.py` 增加失败路径覆盖：模拟 `replay_session.import_lines()` 抛出 `OSError`，检查窗口状态行保留“最近一次导入：失败，…”提示，并确认错误对话框显示异常信息。`recorder_lines.py` 的失败处理逻辑没有改动；`workbench.py` 与记录器窗口标题更新到 0.39.0。

测试依赖 Tk 和图形显示。带显示环境运行：

```text
python3 -m unittest test_recorder_window
```

无显示器的 Linux 环境运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window
```

全套测试：

```text
python3 -m unittest discover
```

本版代码和测试未在此环境运行，预计全套测试约 208 项，实际数量与结果以管家云服务器运行输出为准。若 Tk 或 DISPLAY 缺失，窗口测试会跳过，跳过不算通过。此测试只模拟导入失败，不连接真实传感器，也不验证真实测量数据或 Tk 真机环境。
