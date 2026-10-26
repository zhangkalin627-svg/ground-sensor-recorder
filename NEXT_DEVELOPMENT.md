# 下次开发从这里开始

当前 v0.53.0（未测试）。本版仅增加适配器边界回归测试并同步文档，没有改 `adapters.py` 生产逻辑：覆盖重复表头达到及超过单次跳过上限的情况，以及空行、坏行消耗 `drain(max_reads)` 预算的情况。

未运行新增测试或全套测试。运行：

```text
python3 -m unittest test_adapter_repeated_headers test_adapters
python3 -m unittest discover
python workbench.py --help
xvfb-run -a python3 -m unittest test_recorder_window
```

由管家云服务器或用户电脑运行。预检成功不代表窗口功能测试通过；无 Tk / DISPLAY 时跳过不代表通过。真实传感器、实测数据、硬件在环和 Tk 真机未验证。

## 后续开发

1. 管家有新任务先做；收到当前 main 的失败按测试名和错误原文先修。没有任务或失败就继续，不等云测结果。
2. 核对管家对最新 main 的云测结果，记录实际测试数量、通过/失败/跳过、退出码和原始失败信息；不要把预计数量写成实测结果。
3. 在 Xvfb 环境运行 `window_test_preflight.py` 与 `test_recorder_window.py`，核对预检和窗口测试的通过、失败、跳过及退出码，保持 `README.md` 与版本说明的环境要求准确。
4. 继续审查 `adapters.py` 的有界读取和文本解析边界；先增加可复现的回归测试，只有确认生产缺陷后再改适配器逻辑，并同步 README、版本说明和本文件。

每个未运行过的变更，提交说明写明“未测试”；提交后邮件通知管家，抄送卡林，不发凭据。