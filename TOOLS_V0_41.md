# v0.41.0：README 更新与回放窗口交互测试

本版将 README.md 的首页版本、15 模块状态、工作台命令和验证边界同步到当前仓库实现。README 明确区分模拟记录、离线处理与尚未验证的真实仪器/硬件。

新增 `test_recorder_window_playback.py`，用 Tk 窗口流程覆盖三项行为：

- 回放消费完所有样本后进入 idle 并显示“文件回放完成”。
- 暂停后位置不前进，继续后可完成回放。
- 连续导入时，第二份样本替换窗口中的当前回放，第一份会话目录及其文件保留。

`workbench.py`、`recorder_lines.py` 的版本标记更新到 0.41.0；没有改回放生产逻辑。

测试需要 Tk 和显示环境。Linux 无显示器时可运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window_playback
python3 -m unittest discover
python workbench.py --help
```

本版未测试，新增窗口测试与全套测试均须由管家云服务器或用户电脑运行。没有 Tk 或 DISPLAY 时测试会跳过，跳过不算通过。临时文件和模拟样本不验证真实传感器、真实测量数据或 Tk 真机环境。
