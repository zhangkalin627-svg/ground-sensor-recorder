# 下次开发从这里开始

当前 v0.56.0（未测试）。本版新增 `test_anomaly_log.py` 两项测试，覆盖 `AnomalyLog` 在超过保留上限后的多类别累计计数、最近异常条目及 `anomalies.csv` 截断摘要；没有修改 `adapters.py` 生产逻辑。

未运行新增测试或全套测试。运行：

```text
python3 -m unittest test_anomaly_log
python3 -m unittest discover
python workbench.py --help
xvfb-run -a python3 -m unittest test_recorder_window
```

由管家云服务器或用户电脑运行。预检成功不代表窗口功能测试通过；无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前 main 的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 核对管家对最新 main 的云测结果，记录实际测试数量、通过/失败/跳过、退出码和原始失败信息；不要把预计数量写成实测结果。
3. 在 Xvfb 环境运行 `window_test_preflight.py` 与 `test_recorder_window.py`，核对预检和窗口测试的通过、失败、跳过及退出码，保持 `README.md` 与版本说明的环境要求准确。
4. 继续审查 `adapters.py` 的异常保存、CSV 解析和有界读取边界；先增加可复现的回归测试，只有确认生产缺陷后再改适配器逻辑，并同步 README、版本说明和本文件。

每个未运行过的变更，提交说明写明“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。
