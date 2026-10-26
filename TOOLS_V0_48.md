# v0.48.0：成功导入与回放一致性

本版在 test_recorder_window.py 新增一项 Tk 冒烟测试，使用临时文本日志（两条有效样本、一条格式错误行）走真实导入路径，核对窗口、samples.csv、anomalies.csv、device.json 的一致性；推进回放到结束后检查完成状态和文件不变。

workbench.py 版本为 0.48.0，README.md 与 NEXT_DEVELOPMENT.md 同步。recorder.py、recorder_lines.py、replay_session.py 和 adapters.py 未修改。

## 运行与未测试范围

仓库根目录运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window
python3 -m unittest discover
python workbench.py --help
```

需要 Python 3.10+。窗口测试需要 tkinter 和可用 DISPLAY；云机可使用 Xvfb。缺少 Tk 或 DISPLAY 时跳过，跳过不代表通过。请报告实际总数、失败数、跳过数、退出码和失败原文。

只对修改的 Python 文件做了 AST 语法解析，没有执行新增测试、全套测试或窗口。测试采用合成日志，不涵盖真实传感器、实测数据、硬件在环或真机显示器。
