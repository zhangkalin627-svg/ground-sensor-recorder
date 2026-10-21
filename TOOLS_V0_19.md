# v0.19.0 channel_report.py 的缺口参数

本文只描述已提交到 main 的代码。命令按源码核对，本文档提交时未实际运行。管家在云服务器上对提交 ad8fe05 复跑了 136 项 unittest，全部通过，退出码 0（来自他 2026-10-20 23:00 UTC 的回信）。该结果只来自沙箱，不含真实数据，Tk 窗口未测。

## 对旧文档的更新

TOOLS_V0_16_TO_V0_18.md 第 5 节写到 channel_report.py 的缺口阈值固定为中位数乘 5、命令行不可改。从 v0.19.0 起这句不再成立：可以用下面两个参数修改。不给参数时行为与 v0.18.0 相同。

## 用法

```
python channel_report.py samples.csv
python channel_report.py samples.csv --gap-factor 3
python channel_report.py samples.csv --expected-interval 0.01
python channel_report.py samples.csv --expected-interval 0.01 --gap-factor 2 --json report.json
```

| 参数 | 作用 |
|---|---|
| 不给参数 | 间隔大于中位间隔的 5 倍算缺口（和 v0.18.0 一致） |
| --gap-factor F | 修改倍数，必须是大于 1 的有限数 |
| --expected-interval T | 以预期采样周期 T（秒）为基准，T 必须是大于 0 的有限数；倍数默认 1.5 |

给出 --expected-interval 时，缺口规则和 analysis.py 相同：间隔严格大于 T 乘 1.5 才算缺口。参数不合法时在读取文件之前就报错退出，退出码为 1。

## 报告 JSON 新增字段

intervals 下新增 gap_basis（median 或 expected）、gap_factor、expected_interval_s（未给时为 null）。顶层 version 现在是 0.19.0。

## 测试

test_channel_report_options.py 共 8 项：默认行为不变、中位数模式改倍数、预期周期模式默认倍数 1.5、预期周期加倍数、文字报告出现“预期周期”、过短输入保留参数、非法值被拒绝、main 在读文件前拒绝非法参数。

## 版本字符串

管家复跑时指出，v0.19.0 提交后文件里的版本字符串仍是 0.18.0。这次提交把 channel_report.py 的文档字符串和报告 JSON 的 version 字段改为 0.19.0。其他文件没有独立的版本字符串需要改动，这一点未逐个核对，只确认了 channel_report.py。

## 未测试和已知限制

- 这次提交的字符串改动没有运行过。
- channel_report.py 仍未接入 workbench.py，需单独运行。
- Tk 窗口、Windows 和真实硬件没有实测。
