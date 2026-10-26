# 下次开发从这里开始

当前版本 v0.46.0（未测试）。本版为 `SessionWriter` 初始化失败清理补了三项测试：目录创建失败、样本 CSV 表头写入失败、初始事件写入失败。没有修改会话采集生产逻辑。README、`TOOLS_V0_46.md` 和工作台版本号已同步。

本环境没有运行新增测试或全套测试。命令：

```text
python3 -m unittest test_recorder_session_cleanup
python3 -m unittest discover
python workbench.py --help
```

新增测试不需要 Tk 显示环境；全套测试仍需管家云服务器或用户电脑运行。真实测量数据、真实硬件、硬件在环和 Tk 真机尚未验证。

## 后续开发

1. 管家有新任务时先处理；收到针对当前提交的失败时，按测试名和原始错误优先修复。没有任务或失败时继续迭代，不等待云测结果。
2. 继续测试 `SessionWriter` 初始化清理与错误优先级：第二个文件打开失败且首个文件关闭也失败时保留初始化错误；检查目录创建及表头/初始事件写入异常后所有已打开句柄都关闭，完善 `recorder.py` 和 `test_recorder_session_cleanup.py`。
3. 持续维护 README.md、版本使用说明与本文件，准确说明功能及验证范围。
4. 规划 `realworld_sim` 前先复核管家的仿真说明；仿真结果必须明确标为仿真，不得称为实测或火箭专用模型结果。

未运行测试的提交说明必须标注“未测试”。
