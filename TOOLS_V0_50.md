# v0.50.0 LineAdapter 读取边界测试说明

本版只新增 `test_adapter_read_bounds.py`，没有改动 `adapters.py` 的生产逻辑。测试 `LineAdapter.read()` 对空行和坏行的逐次消费，以及 `drain(adapter, max_reads=...)` 如何限制一次处理的读取次数。

覆盖范围：

- 空行调用一次 `read()` 后返回 `None`，后续有效样本仍可读取。
- 两条坏行分别由两次 `read()` 处理，`field_count` 异常计数分别增加。
- 1001 条坏行后跟有效样本时，`drain` 的 100、900、10 读取预算逐步限制工作量，并最终读到样本。

本版代码和测试未运行，提交说明标注“未测试”。请在仓库根目录运行：

```text
python3 -m unittest test_adapter_read_bounds
python3 -m unittest test_adapter_read_bounds test_adapters test_adapter_repeated_headers
python3 -m unittest discover
python workbench.py --help
```

请回报实际执行的提交号、测试总数、失败数、跳过数、退出码和失败原文。合成日志测试不代表真实传感器或实测数据验证。
