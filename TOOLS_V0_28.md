# v0.28.0：导入状态行的无显示器检查

`recorder_lines.py` 在导入文本行日志后，会把异常行总数、主要异常类别和行数上限提示留在窗口的状态行中。新版本把状态更新提取为 `LineApp.update_lines_status(result)`，方便在不创建 Tk 窗口的情况下检查显示文本。

测试文件 `test_recorder_lines_status.py` 使用替身变量验证异常行摘要、无异常导入覆盖旧状态，以及达到读取上限时提示剩余行未读取。这些测试不创建真实 Tk 窗口，也不能替代 Xvfb 冒烟测试或带屏实测。

从仓库根目录运行单文件测试：

```text
python3 -m unittest test_recorder_lines_status test_import_status
```

运行全套测试：

```text
python3 -m unittest discover
```

本版代码和测试未在真实仓库运行。以上命令是建议运行方法；测试需要由管家云服务器或用户电脑执行。实际测量数据、真实硬件、Tk 窗口和 Xvfb 环境仍未验证。
