# v0.40.0：导入取消与失败恢复

本版扩展 `test_recorder_window.py`，覆盖文本日志导入时取消文件选择，以及重新导入失败后的状态恢复。测试先成功导入一份日志作为当前有效回放，再尝试取消或触发模拟的 `OSError`；检查当前回放数据、窗口模式、保存状态和已有 `samples.csv`、`anomalies.csv`、`device.json` 保持不变。失败时状态行显示错误，弹出错误对话框。

生产导入流程没有改动。`recorder_lines.py` 窗口标题与 `workbench.py` 版本更新到 0.40.0。

这些测试需要 Tk 和显示环境。Linux 无显示器时可用 Xvfb：

```text
xvfb-run -a python3 -m unittest test_recorder_window
```

在有显示环境时运行：

```text
python3 -m unittest test_recorder_window
```

全套测试：

```text
python3 -m unittest discover
```

本版未测试。按上一版文档的预计 208 项加 2 项新测试，估计全套约 210 项；实际数量与结果以管家云服务器输出为准。没有 Tk 或 DISPLAY 时窗口测试会跳过，跳过不算通过。本测试使用临时文件和模拟错误，不验证真实传感器、真实测量数据或 Tk 真机环境。
