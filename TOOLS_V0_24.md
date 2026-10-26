# replay、channel、drift 三步流程（v0.24.0，文档 v0.24.2）

这三个工具可在无显示器的环境运行。输入文件只读；输出目录或文件要使用新路径，程序不会覆盖已有输出。

## 1. 把文本行日志导入为采集目录

```text
python workbench.py replay baseline.txt --out sessions
```

将 `baseline.txt` 换成待导入日志。输入遵循 `adapters.LineAdapter` 的记录字段顺序。程序会打印生成目录，目录名带时间和随机后缀，里面有 `samples.csv`、`anomalies.csv`、`device.json`。坏行会记入异常文件；没有有效样本时导入失败。省略 `--out` 只检查、不写文件。

候选数据也用相同方式导入，使用不同的输入文件和输出目录：

```text
python workbench.py replay candidate.txt --out sessions
```

## 2. 分别生成基准和候选通道报告

把下面的 `<基准目录>` 和 `<候选目录>` 替换为 replay 输出中显示的实际目录：

```text
python workbench.py channel <基准目录>/samples.csv --expected-interval 0.05 --gap-factor 1.5 --json baseline.json
python workbench.py channel <候选目录>/samples.csv --expected-interval 0.05 --gap-factor 1.5 --json candidate.json
```

`--expected-interval` 单位为秒，必须由使用者提供已知采样周期；工具不会替你猜。缺口定义为间隔严格大于 `预期周期 × gap-factor`。给出预期周期时，`--gap-factor` 默认 1.5；省略预期周期时，缺口按“间隔大于间隔中位数 × 5”判定。`baseline.json`、`candidate.json` 必须是尚不存在的新文件。

## 3. 对比两份报告

```text
python workbench.py drift baseline.json candidate.json --max-rel-change 0.10 --strict --json drift.json
```

默认相对变化阈值为 10%。可用 `--max-abs-change 0.5` 加入绝对变化阈值。只要相对阈值或已指定的绝对阈值任一超限，就将通道标为漂移；基准值为 0 时，任何非零变化都算漂移。完整规则见 `TOOLS_V0_22.md`。`--strict` 让存在漂移通道时退出码为 2。结果写入 `drift.json`，文件必须不存在。

## 测试与限制

在仓库根目录运行全套测试：

```text
python3 -m unittest discover
```

管家于 2026-10-26 06:53 GMT+8 在云服务器上对提交 `70a9c642eed8e04958a007ccb890c3685dc77cb8` 运行了该命令，178 项全部通过，退出码 0。测试使用沙箱数据，不含真实测量数据；Tk 窗口、真实硬件和 Windows 环境仍未实测。

本说明根据脚本源码和已有测试整理，命令未在本次文档更新中实际运行；本次仅改文档，未测试。