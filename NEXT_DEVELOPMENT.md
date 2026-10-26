# 下次开发从这里开始

当前 v0.48.0（未测试）。新增一项 Tk 成功文本导入与回放一致性测试，核对样本、异常、设备来源、窗口状态和回放后文件不变。没有修改记录器或回放生产逻辑。workbench.py、README 与版本说明已同步。

仅对修改 Python 文件做 AST 语法解析，没有运行测试。运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window
python3 -m unittest discover
python workbench.py --help
```

管家云服务器或用户电脑运行；无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前提交的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 为窗口测试补充明确的环境预检和运行说明，涉及 test_recorder_window.py、README.md。
3. 核对 adapters.py、test_adapters.py 的重复表头读取边界，避免递归深度问题；必要时改 adapters.py 并补回归测试。
4. 整理可重复的云测步骤与结果字段，更新版本说明、NEXT_DEVELOPMENT.md。估算数量不能当成实测结果。

未经测试的提交说明标注“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。
