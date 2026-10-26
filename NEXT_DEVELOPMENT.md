# 下次开发从这里开始

当前 v0.51.0（未测试）。新增 `window_test_preflight.py`，检查 Tk 是否可导入、DISPLAY 是否适用，并尝试初始化和销毁临时窗口；新增 `test_window_test_preflight.py` 覆盖替身环境下的可用、缺失和初始化失败路径。它只检查环境，不运行窗口功能测试。已更新 `workbench.py`、`README.md` 和 `TOOLS_V0_51.md`。

未运行新增测试或全套测试。运行：

```text
python3 -m unittest test_window_test_preflight
python3 window_test_preflight.py
xvfb-run -a python3 window_test_preflight.py
xvfb-run -a python3 -m unittest test_recorder_window
python3 -m unittest discover
python workbench.py --help
```

由管家云服务器或用户电脑运行。无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前 main 的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 在真实 Xvfb 环境确认 `test_recorder_window.py` 的预检和完整窗口测试能区分通过、失败与跳过，更新 `README.md` 和版本说明。
3. 对照 adapters.py 的有界读取规则，继续补充 CSV 头部、异常计数及 drain 边界；若发现生产问题，再修改 `adapters.py` 并增加回归测试。
4. 整理可重复的云测命令和结果字段，更新版本说明与开发记录。预计数量不能写成实测结果。

每个未运行过的变更，提交说明写明“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。
