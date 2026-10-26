# v0.42.0：采集切换到文本回放时关闭旧会话

本版在 `test_recorder_window_playback.py` 增加一项 Tk 窗口流程测试：模拟采集已有打开的 `SessionWriter` 文件时，导入一份文本日志；验证旧会话写入“切换到文本行回放”事件、采集数据与事件文件句柄均已关闭，窗口进入文本回放模式并显示新样本。

`recorder_lines.py` 与 `workbench.py` 的版本标记更新到 0.42.0。没有改切换生产逻辑。本版新增测试尚未运行，提交说明标注“未测试”。

在仓库根目录运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window_playback
python3 -m unittest discover
python workbench.py --help
```

窗口测试需要 Tk 和显示环境。没有 Tk 或 `DISPLAY` 时会跳过，跳过不算通过。全套测试和窗口测试需要由管家云服务器或用户电脑运行。本测试使用临时文件和模拟样本，不验证真实传感器、真实测量数据、硬件在环或 Tk 真机。
