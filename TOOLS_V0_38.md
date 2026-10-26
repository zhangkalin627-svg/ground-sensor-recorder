# v0.38.0：文本行导入窗口流程冒烟测试

本版扩展 `test_recorder_window.py`：在有 Tk 显示环境时，实际调用 `recorder_lines.LineApp.import_lines()`，用临时文本日志导入一条有效样本和一条格式错误行，并核对窗口状态行显示异常数、回放数据已载入，且生成 `samples.csv`、`anomalies.csv`、`device.json`。测试通过临时目录和文件对话框替身工作，不连接硬件，也不修改仓库中的测试数据。

在带图形环境的机器上运行单项：

```text
python3 -m unittest test_recorder_window
```

在无显示器的 Linux 云机上运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window
```

运行全套测试：

```text
python3 -m unittest discover
```

若系统没有 Tk 或 DISPLAY，窗口测试会标记为跳过；跳过不算通过。当前代码和测试未在此环境运行，以上命令需由管家云服务器或用户电脑执行。模拟日志测试不代表真实传感器、真实测量数据或 Tk 真机验证。
