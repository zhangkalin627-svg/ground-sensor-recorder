# 下次开发从这里开始

当前版本 v0.43.1（未测试）。本版修正 v0.43.0 回读时发现的 `workbench.py` 缩进损坏，恢复正确结构并同步版本；`test_recorder_session_cleanup.py` 新增的两个异常清理测试仍在 main。README.md 与 TOOLS_V0_43_1.md 已更新。

本环境没有运行新增测试或全套测试。命令：

```text
python3 -m unittest test_recorder_session_cleanup
python3 -m unittest discover
python workbench.py --help
```

新增测试不需要 Tk 显示环境；全套测试仍需管家云服务器或用户电脑运行。真实测量数据、真实硬件、硬件在环和 Tk 真机尚未验证。

## 后续开发

1. 管家有新任务时先处理；收到针对当前提交的失败时，按测试名和原始错误优先修复。没有任务或失败时继续迭代，不等待云测结果。
2. 为 `SessionWriter` 补充构造过程部分打开失败、采集追加写入失败时的资源清理测试，检查 `recorder.py` 和 `test_recorder_session_cleanup.py`；若发现未关闭的句柄，再改生产代码。
3. 持续维护 README.md、版本使用说明与本文件，准确说明功能及验证范围。
4. 规划 `realworld_sim` 前先复核管家的仿真说明；仿真结果必须明确标为仿真，不得称为实测或火箭专用模型结果。

未运行测试的提交说明必须标注“未测试”。