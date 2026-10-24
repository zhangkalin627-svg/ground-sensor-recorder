# drift_report.py 用法（v0.22.0，文档 v0.22.1）

作用：对比两份 channel_report.py 的 JSON 报告，按阈值标出统计量变化过大的通道。纯标准库，不需要显示器，只读两份输入。

## 命令

    python drift_report.py baseline.json candidate.json
    python drift_report.py a.json b.json --max-rel-change 0.05 --json drift.json
    python drift_report.py a.json b.json --max-abs-change 0.5 --strict

参数：
- --max-rel-change：相对变化阈值，默认 0.1（10%）。必须是不小于 0 的有限数。
- --max-abs-change：绝对变化阈值，默认不启用。给出后，变化量绝对值超过它也算漂移。必须大于 0。
- --json 路径：把结果写成 JSON。文件已存在则拒绝覆盖，退出码 1。
- --strict：有漂移通道时退出码为 2，方便脚本判断。

## 判定规则

对每个通道比较 count、mean、std、min、max、peak_to_peak 六项。任一项满足下面之一，该通道记为漂移：
- 相对变化的绝对值大于相对阈值（恰好等于阈值不算）。
- 给了绝对阈值，且变化量绝对值大于它。
- 基准值为 0 时相对变化无定义，任何非零变化都算漂移。

两份报告的通道名必须完全一致，否则报错，错误里会列出哪边缺哪个通道。报告必须有 channels、intervals 和 sample_count。

另外会列出 sample_count、duration_s、median_s、gap_count 的变化，这四项只显示，不参与漂移判定。

## 退出码

- 0：正常（没加 --strict 时，有漂移也是 0）。
- 1：读文件、JSON 格式、通道不一致、数值非法或输出文件已存在。错误信息以“失败：”开头，写到标准错误。
- 2：加了 --strict 且有漂移通道。

## 输出示例

下面是沙箱里用合成数据跑出的一次结果（temp 通道 mean 从 10 变到 12，样本数从 100 变到 120）：

    阈值 相对 +10.00%，绝对 —
    sample_count: 100 -> 120（+20，+20.00%）
    duration_s: 99 -> 99（+0，+0.00%）
    median_s: 1 -> 1（+0，+0.00%）
    gap_count: 0 -> 0（+0，—）
    漂移通道：temp
    temp: mean 10 -> 12（+2，+20.00%）

## 测试

测试在 test_drift_report.py，共 20 项。在仓库目录运行：

    python3 -m unittest discover

预期全套 167 项（之前 147 项加这 20 项）。未在真实仓库里跑过，需要云机复跑。
