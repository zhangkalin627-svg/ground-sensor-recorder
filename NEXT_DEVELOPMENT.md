# 下次开发从这里开始

当前版本 v0.44.0（未测试）。本版完善 `SessionWriter` 资源清理：部分初始化失败时关闭已打开文件，关闭一个句柄报错时仍尝试关闭另一个，采集追加写入失败时通过 `App.tick()` 停止并收尾。README、`TOOLS_V0_44.md` 和工作台版本号已同步。

本环境没有运行新增测试或全套测试。命令：

```text
python3 -m unittest test_recorder_session_cleanup
python3 -m unittest discover
python workbench.py --help
```

新增测试不需要 Tk 显示环境；全套测试仍需管家云服务器或用户电脑运行。真实测量数据、真实硬件、硬件在环和 Tk 真机尚未验证。

## 后续开发

1. 管家有新任务时先处理；收到针对当前提交的失败时，按测试名和原始错误优先修复。没有任务或失败时继续迭代，不等待云测结果。
2. 继续检查 `SessionWriter` 在事件日志写入失败、目录权限错误和连续停止/关闭时的资源状态，完善 `recorder.py` 与 `test_recorder_session_cleanup.py`。
3. 持续维护 README.md、版本使用说明与本文件，准确说明功能及验证范围。
4. 规划 `realworld_sim` 前先复核管家的仿真说明；仿真结果必须明确标为仿真，不得称为实测或火箭专用模型结果。

未运行测试的提交说明必须标注“未测试”。
