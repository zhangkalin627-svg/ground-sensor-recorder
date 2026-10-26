# v0.56.0 AnomalyLog 有界保留与多类别摘要测试说明

本版只新增两项 `AnomalyLog` 回归测试，并同步工作台版本和文档，没有修改 `adapters.py` 生产逻辑。GitHub 提交说明标注“未测试”。

## 测试改动

`test_anomaly_log.py` 使用合成异常，验证：

- 超过保留上限后，`total` 和 `by_kind` 仍统计所有新增异常；`entries` 仅保存最近的记录，且包含不同异常类别。
- `anomalies.csv` 写出最近保留的异常记录，并在末尾加入 `truncated` 摘要，准确说明保留条数与累计异常总数。

异常明细有界保留不等同于完整原始异常档案；需要审查完整记录时，应使用未触发截断的运行或其他明确保存方案。

## 建议运行

在仓库根目录运行：

```text
python3 -m unittest test_anomaly_log
python3 -m unittest discover
python workbench.py --help
```

本版新增测试、全套测试和 Tk 窗口均未运行。请在管家云服务器或用户电脑上执行，并报告实际提交、测试总数、通过/失败/跳过数、退出码和失败原文。

这些测试只使用合成数据，不验证真实传感器、实测数据、硬件在环或 Tk 真机环境。
