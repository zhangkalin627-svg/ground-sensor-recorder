# 下次开发从这里开始

当前 v0.49.0（未测试）。`LineAdapter.read()` 将重复表头处理改为有界循环，避免连续表头触发递归深度错误；新增 test_adapter_repeated_headers.py 覆盖 1500 个连续表头后的有效样本。已同步 workbench.py、README.md 和版本说明。

未运行新增测试或全套测试。运行：

```text
python3 -m unittest test_adapter_repeated_headers test_adapters
python3 -m unittest discover
python workbench.py --help
```

由管家云服务器或用户电脑运行；无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前提交的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 为窗口测试补充明确的环境预检和运行说明，涉及 test_recorder_window.py、README.md。
3. 检查 LineAdapter 对大量坏行或空行的单次读取和错误计数边界，涉及 adapters.py、test_adapter_repeated_headers.py；保持单次工作有界。
4. 整理可重复的云测步骤与结果字段，更新版本说明、README.md、NEXT_DEVELOPMENT.md。估算数量不能当成实测结果。

未经测试的提交说明标注“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。
