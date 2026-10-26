# v0.54.0 无限重复表头流的有界读取测试说明

本版只增加一项适配器回归测试并同步文档，没有修改 `adapters.py` 生产逻辑。提交说明标注“未测试”。

## 改动

- `test_adapter_repeated_headers.py` 增加持续产生 CSV 表头的输入测试。调用 `drain(adapter, max_reads=2)` 后应读取不超过两次 `MAX_HEADER_SKIPS_PER_READ` 的表头数，返回空样本，不把仍在运行的流标记为结束，也不记录异常。
- 该边界对应当前读取实现：每次 `LineAdapter.read()` 最多跳过 1000 行重复表头；`drain(max_reads)` 限制调用 `read()` 的次数。因此无限表头输入的一次 drain 最多处理 `1000 × max_reads` 行。
- `workbench.py` 更新版本号，`README.md` 与 `NEXT_DEVELOPMENT.md` 同步版本和测试边界。

## 建议运行

在仓库根目录运行：

```text
python3 -m unittest test_adapter_repeated_headers
python3 -m unittest discover
python workbench.py --help
```

本版新增测试、全套测试和窗口测试均未运行。请在管家云服务器或用户电脑运行，并记录实际提交、测试总数、通过/失败/跳过数、退出码和失败原文。

测试使用合成文本输入，不验证真实传感器、实测数据、硬件在环或 Tk 真机环境。窗口测试无 Tk 或 DISPLAY 时跳过不代表通过。
