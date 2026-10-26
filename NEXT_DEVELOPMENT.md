# 下次开发从这里开始

当前 v0.52.0（未测试）。`window_test_preflight.py` 现在把临时窗口关闭失败报告为不可用；`test_window_test_preflight.py` 新增相应替身测试。同步了 `workbench.py`、`README.md` 和本版说明。

未运行新增测试或全套测试。运行：

```text
python3 -m unittest test_window_test_preflight
python3 window_test_preflight.py
xvfb-run -a python3 window_test_preflight.py
xvfb-run -a python3 -m unittest test_recorder_window
python3 -m unittest discover
python workbench.py --help
```

由管家云服务器或用户电脑运行。预检成功不代表窗口功能测试通过；无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前 main 的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 在真实 Xvfb 环境运行预检与 `test_recorder_window.py`，核对完整窗口测试的实际通过、失败、跳过和退出码，并记录测试提交。
3. 对照 `adapters.py` 的有界读取规则，为重复表头上限边界、空行与坏行组合及 `drain(max_reads)` 预算补充回归测试；若发现生产问题，再修改 `adapters.py`。
4. 统一云测命令与结果字段，更新 `README.md`、版本说明和本文件。预计数量不能写成实测结果。

每个未运行过的变更，提交说明写明“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。
