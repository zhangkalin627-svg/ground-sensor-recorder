# 下次开发从这里开始

当前版本 v0.45.0（未测试）。本版为事件日志写入失败后仍关闭两个文件、以及 SessionWriter 成功关闭后可重复调用增加了测试；没有更改采集或关闭生产逻辑。README、`TOOLS_V0_45.md` 和工作台版本号已同步。

本环境没有运行新增测试或全套测试。命令：

```text
python3 -m unittest test_recorder_session_cleanup
python3 -m unittest discover
python workbench.py --help
```

新增测试不需要 Tk 显示环境；全套测试仍需管家云服务器或用户电脑运行。真实测量数据、真实硬件、硬件在环和 Tk 真机尚未验证。

## 后续开发

1. 管家有新任务时先处理；收到针对当前提交的失败时，按测试名和原始错误优先修复。没有任务或失败时继续迭代，不等待云测结果。
2. 继续检查 `SessionWriter` 在目录创建失败、写 CSV 表头或初始事件失败时的清理与错误保留，完善 `recorder.py` 和 `test_recorder_session_cleanup.py`。
3. 持续维护 README.md、版本使用说明与本文件，准确说明功能及验证范围。
4. 规划 `realworld_sim` 前先复核管家的仿真说明；仿真结果必须明确标为仿真，不得称为实测或火箭专用模型结果。

未运行测试的提交说明必须标注“未测试”。
