# v0.49.0：连续重复 CSV 表头

`LineAdapter.read()` 以前遇到表头行时递归调用自身。输入中表头重复过多会超过 Python 递归深度。

本版改为循环跳过表头，每次 `read()` 最多忽略 1000 个连续表头后返回 `None`，避免递归，并保持单次调用有界。后续 `drain()` 继续读取，直到有效样本或流结束。

新增 `test_adapter_repeated_headers.py`：在 1500 个重复表头后放一条有效样本，确认样本读取成功、没有异常记录且迭代结束。没有修改硬件协议或生产控制路径。

## 运行与未测试范围

```text
python3 -m unittest test_adapter_repeated_headers test_adapters
python3 -m unittest discover
python workbench.py --help
```

本版没有运行测试，提交说明标注“未测试”。请以管家云服务器或用户电脑的实际输出为准。输入使用合成 CSV 行，不替代真实传感器或实测数据验证。
