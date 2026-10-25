# workbench.py 的 drift 子命令（v0.23.0，文档 v0.23.1）

作用：用 workbench.py 一个入口调用 drift_report.py，对比两份 channel_report.py 的 JSON 报告。参数原样转交给 drift_report.py，阈值规则、退出码和输出格式见 TOOLS_V0_22.md。纯标准库，不需要显示器。

## 命令

    python workbench.py drift baseline.json candidate.json
    python workbench.py drift a.json b.json --max-rel-change 0.05 --json drift.json
    python workbench.py drift a.json b.json --max-abs-change 0.5 --strict

等价于直接运行 python drift_report.py 加同样的参数。

## 三个子命令怎么串起来

1. 用 replay 把文本行日志导入成采集目录（samples.csv、anomalies.csv、device.json），用法见 TOOLS_V0_20.md。
2. 用 channel 对 samples.csv 生成按通道统计的 JSON 报告，可加 --expected-interval 和 --gap-factor，用法见 TOOLS_V0_19.md 和 TOOLS_V0_20.md。
3. 对两次采集各生成一份报告，再用 drift 对比，看哪些通道的统计量变化超过阈值。

## 测试

test_workbench_drift.py 共 4 项，只测路由和退出码、帮助文字含 drift 和 v0.23.0、COMMANDS 登记、模块列表。管家在云机上对 60b2deb 运行 python3 -m unittest discover，171 项全部通过（2026-10-25 回信）。本文档提交没有改代码，没有再跑测试。

## 未覆盖

- 没有用真实采集数据跑过 channel 到 drift 的完整串联。
- Tk 窗口和真实硬件仍未实测。
