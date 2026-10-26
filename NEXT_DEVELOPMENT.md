# 下次开发从这里开始

当前 v0.50.0（未测试）。本版新增 `test_adapter_read_bounds.py`，覆盖空行和坏行的逐次读取、异常计数，以及 `drain(max_reads=...)` 的读取预算。没有修改 `adapters.py` 生产逻辑。已更新 `workbench.py`、`README.md` 和 `TOOLS_V0_50.md`。

未运行新增测试或全套测试。运行：

```text
python3 -m unittest test_adapter_read_bounds test_adapters test_adapter_repeated_headers
python3 -m unittest discover
python workbench.py --help
```

由管家云服务器或用户电脑运行；无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前 main 的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 为窗口测试补充明确的环境预检和运行说明，涉及 `test_recorder_window.py`、`README.md`。
3. 继续检查适配器连续表头、空行和坏行的有界读取边界；若发现生产问题再改 `adapters.py`，并在 `test_adapters.py` 补回归测试。
4. 整理可重复的云测步骤与结果字段，更新版本说明、`README.md`、`NEXT_DEVELOPMENT.md`。估算数量不能当成实测结果。

未经测试的提交说明标注“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。
