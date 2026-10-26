# v0.53.0 适配器读取预算边界测试说明

本版只增加回归测试和同步文档，不修改 `adapters.py` 的生产逻辑。提交说明标注“未测试”。

## 改动

- `test_adapter_repeated_headers.py` 增加两项边界测试：恰好达到 `MAX_HEADER_SKIPS_PER_READ` 后，下一行留待下一次 `read()`；多一行重复表头时，下一次读取继续跳过剩余表头并取得有效样本。
- `test_adapters.py` 增加空行与坏行共同消耗 `drain(max_reads)` 预算的测试。坏行计入异常，空行不计异常；预算耗尽后后续调用继续处理剩余输入。
- `workbench.py` 更新版本号，`README.md` 与 `NEXT_DEVELOPMENT.md` 同步说明。

## 建议运行

在仓库根目录运行：

```text
python3 -m unittest test_adapter_repeated_headers test_adapters
python3 -m unittest discover
python workbench.py --help
```

本版新增测试、全套测试和窗口测试均未在提交前运行。请在管家云服务器或用户电脑运行，并记录实际提交、测试数、失败数、跳过数、退出码和失败原文。

这些测试使用合成文本输入，不验证真实传感器、实测数据、硬件在环或 Tk 真机环境。窗口测试无 Tk 或 DISPLAY 时跳过，不代表通过。
