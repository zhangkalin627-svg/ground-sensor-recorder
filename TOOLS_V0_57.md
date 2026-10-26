# v0.57.0：AnomalyLog 容量与详情长度边界测试

本版为 `test_anomaly_log.py` 增加两项回归测试，没有修改 `adapters.py` 生产逻辑。

- `AnomalyLog(limit=0)` 不保留异常明细，但继续累计 `total` 和各类别计数；保存 `anomalies.csv` 时仍输出截断摘要，数量显示最近保留 0 条及累计总数。
- 异常详情超过 200 字符时，日志条目只保留前 200 字符，与 `adapters.py` 的现有截断行为一致。

本版代码和测试均未运行，提交说明标注“未测试”。请在仓库根目录运行：

```text
python3 -m unittest test_anomaly_log
python3 -m unittest discover
python workbench.py --help
```

Tk 窗口可以在有 Tk 和显示环境时用 Xvfb 运行。无 Tk 或 DISPLAY 时窗口测试跳过不代表通过。单元测试使用合成数据，不替代真实传感器、实测数据、硬件在环或 Tk 真机验证。
