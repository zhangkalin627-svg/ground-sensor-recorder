# v0.20.x workbench.py 的 channel 和 replay 子命令

本文只描述已提交到 main 的代码。命令按源码核对，本文档提交时未实际运行。管家在云服务器上对提交 96e2853（v0.20.0）运行 python3 -m unittest discover，140 项全部通过，退出码 0（来自他 2026-10-21 22:20 UTC 的回信）。该结果来自干净的云端环境，不含真实数据，Tk 窗口和真实硬件未测。

## 对旧文档的更新

TOOLS_V0_19.md 的"未测试和已知限制"里写到 channel_report.py 未接入 workbench.py。从 v0.20.0 起这句不再成立：workbench.py 有 channel 子命令。replay_session.py 也有 replay 子命令。

## 用法

workbench.py 把子命令后面的参数原样交给对应脚本，不改参数含义，退出码也是对应脚本的退出码。

| 子命令 | 对应脚本 | 说明 |
|---|---|---|
| channel | channel_report.py | 按通道统计采样间隔、缺口、极值、均值、标准差 |
| replay | replay_session.py | 把文本行日志只读导入成采集目录 |

### channel

```
python workbench.py channel samples.csv
python workbench.py channel samples.csv --gap-factor 3
python workbench.py channel samples.csv --expected-interval 0.01
python workbench.py channel samples.csv --expected-interval 0.01 --gap-factor 2 --json report.json
```

参数含义见 TOOLS_V0_19.md：不给参数时间隔大于中位间隔 5 倍算缺口；给 --expected-interval T 时以预期周期为基准，倍数默认 1.5，和 analysis.py 一致；--gap-factor 必须是大于 1 的有限数。

### replay

```
python workbench.py replay input.txt
python workbench.py replay input.txt --out sessions
python workbench.py replay input.txt --out sessions --name 设备名称
```

- 只给 input.txt：只检查并打印摘要，不写任何文件。
- 加 --out：在 sessions 下新建一个带时间戳的目录，写入 samples.csv、anomalies.csv、device.json。
- 源文件只读，不会被修改。坏行记进 anomalies.csv，不会中断导入。
- 没有可用样本、或文件超过 50 MB 时，打印"导入失败"并以退出码 1 结束。

### 两步串联示例

先回放，再对生成的 samples.csv 做通道报告（目录名里的时间戳和随机后缀每次不同，下面用 <目录> 代替）：

```
python workbench.py replay input.txt --out sessions
python workbench.py channel sessions/<目录>/samples.csv --json report.json
```

## 查看帮助

```
python workbench.py --help
python workbench.py channel --help
python workbench.py replay --help
```

后两条由对应脚本的 argparse 给出帮助文字。

## 测试

test_workbench_commands.py 共 4 项，只测路由、参数转交和帮助文字列出新命令。它不运行真实的 channel_report.py 或 replay_session.py。

## 未测试和已知限制

- 本文档里的命令示例没有实际运行过，只按源码核对。
- 两步串联示例里 samples.csv 的路径需要按实际生成的目录替换。
- Tk 窗口、Windows 和真实硬件没有实测。
- realworld_sim 的输入格式说明还没拿到，本版没有接入。
