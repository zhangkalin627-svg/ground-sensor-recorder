# v0.51.0 Tk 环境预检说明

本版新增 `window_test_preflight.py`，用于确认 `tkinter` 可导入并能创建、隐藏和关闭一个临时 Tk 根窗口。它只检查当前运行环境，不会运行 `test_recorder_window.py` 中的窗口测试。

新增 `test_window_test_preflight.py` 的 5 项测试用替身覆盖：

- tkinter 不可导入时返回不可用说明。
- Linux 未设置 DISPLAY 时不尝试创建窗口。
- DISPLAY 可用时创建并关闭临时窗口。
- Tk 初始化失败时返回错误。
- 窗口隐藏失败时仍尝试关闭根窗口。

本版代码和测试未运行，提交说明标注“未测试”。建议先运行预检，再运行 Tk 测试：

```text
python3 -m unittest test_window_test_preflight
python3 window_test_preflight.py
xvfb-run -a python3 window_test_preflight.py
xvfb-run -a python3 -m unittest test_recorder_window
python3 -m unittest discover
python workbench.py --help
```

预检通过只说明 Tk 窗口可以初始化和销毁，不证明窗口导入流程通过。无 Tk 或 DISPLAY 时窗口测试会跳过；跳过不代表通过。测试使用替身和合成数据，不替代真实传感器、实测数据或硬件在环验证。
