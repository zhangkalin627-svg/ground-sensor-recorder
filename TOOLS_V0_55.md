# v0.55.0 LineAdapter 行长度边界测试说明

本版只增加两项适配器边界测试并同步版本说明，没有修改 `adapters.py` 生产逻辑。提交说明标注“未测试”。

## 测试改动

`test_adapter_line_length.py` 新增两项回归测试：

- 构造长度恰为 `MAX_LINE`（512 字符）的有效采样行，确认 `LineAdapter` 仍可解析，且不记异常。
- 构造长度为 `MAX_LINE + 1` 的行，确认它返回 `None`，并将异常计为 `line_too_long`。

这两项测试固定行长度检查的边界，避免后续修改把上限内数据误拒，或让超限行绕过异常记录。

## 建议运行

在仓库根目录运行：

```text
python3 -m unittest test_adapter_line_length
python3 -m unittest discover
python workbench.py --help
```

新增测试、全套测试和 Tk 窗口均未运行。请在管家云服务器或用户电脑执行，并记录实际提交、测试总数、通过/失败/跳过数、退出码和失败原文。

测试只使用合成 CSV 文本，不验证真实传感器、实测数据、硬件在环或 Tk 真机环境。
