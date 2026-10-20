# v0.16.0 到 v0.18.0 新增工具说明

本文只描述已提交到 main 的文件。命令按源码核对，本文档提交时未实际运行。管家在云服务器上对提交 3909986 运行了 128 项测试并全部通过（来自他的回信），该提交包含下列全部文件。Tk 窗口、Windows 和真实硬件未实测。

## 1. summary_report.py（v0.16.0）

入口：python workbench.py report，用法见 README 的 v0.15.0 小节。v0.16.0 的变化：每个输入文件在报告中记录大小、SHA-256 和读取时刻；生成前后比对，文件在生成期间变化则拒绝输出。测试：test_report_traceability.py。

## 2. replay_session.py（v0.17.0）：文本行日志导入

```
python replay_session.py input.txt --out sessions
python replay_session.py input.txt
```

- 只读打开输入文件，不修改，不向任何设备写入。
- 按 adapters.LineAdapter 的字段顺序解析，坏行记入 anomalies.csv，不中断导入。
- 加 --out 时在该目录下新建一个带时间戳和随机后缀的子目录，写入 samples.csv、anomalies.csv、device.json。省略 --out 只检查并打印摘要，不写文件。
- 文件上限 50 MB，样本上限沿用记录器的 MAX_ROWS，超过的部分不读取并记入 anomalies。
- 没有可用样本时报错退出。
- 可选 --name 设置设备名称；设备身份注明为离线回放，序列号与固件未知。
- 测试：test_replay_session.py。

## 3. recorder_lines.py（v0.17.0）：记录器窗口加导入按钮

```
python recorder_lines.py
```

在记录器窗口上多一个按钮“导入文本行日志并回放（只读）”，内部调用 replay_session.import_lines，并在图表中回放。需要 Tk 与图形桌面，未实测。回退办法：继续使用原来的 recorder.py，本文件没有改动它。

## 4. channel_report.py（v0.18.0）：按通道统计

```
python channel_report.py samples.csv --json report.json
```

- 输入为记录器导出的 samples.csv，只读。
- 输出采样间隔（中位、均值、最小、最大）、缺口、每个通道的最小值及时刻、最大值及时刻、均值、总体标准差和峰峰值。
- --json 指定的文件必须不存在，已存在则拒绝覆盖。
- 时间必须严格递增，否则报错。数据含 NaN 或无穷值时报错。
- 最多列出 50 个缺口。
- 测试：test_channel_report.py。

## 5. 两套缺口定义的区别

| | analysis.py（workbench.py analyze） | channel_report.py |
|---|---|---|
| 基准 | 用户用 --expected-interval 明确给出的采样周期 | 数据自身间隔的中位数 |
| 阈值 | 周期乘 --gap-factor，默认 1.5，实际间隔严格大于阈值才算缺口 | 中位数乘 5（代码常量 GAP_FACTOR，命令行不可改） |
| 未给周期时 | 不判断缺口，gaps.assessed=false、count=null | 总是判断 |
| 适用 | 已知设计采样周期，想检查是否丢样 | 不知道周期，想快速看哪里有明显中断 |

两者结果可能不同：采样本来就不均匀时，中位数法可能漏报小缺口，周期法在周期填错时会大量误报。比较两个文件时，analysis.py 应对两份文件使用相同参数；channel_report.py 的阈值随各文件自己的中位数变化。

## 6. 未测试和已知限制

- Tk 窗口（recorder_lines.py 的导入按钮）、Windows、真实硬件都没有实测。
- 管家 128 项测试覆盖命令行和单元测试，不覆盖上面几项。
- channel_report.py 尚未接入 workbench.py，需单独运行。
