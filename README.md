# 地面实验工具 v0.50.0

一个逐步增加模块的通用地面实验与工程记录工具集。当前提供命令行工作台、模拟记录器、文本日志只读导入、离线分析与流水线工具，主要使用 Python 标准库。要求 Python 3.10+；桌面记录器需要 Tk 和图形环境。

本项目目前是记录和离线分析工具，不是经过飞行或硬件验证的火箭飞控系统。模拟数据不是实测数据；项目不会向传感器或设备发送控制输出。

## 快速开始

```text
python workbench.py --help
python workbench.py modules
python workbench.py record
python workbench.py analyze samples.csv --expected-interval 0.05 --gap-factor 1.5 --output analysis.json
python workbench.py channel samples.csv --expected-interval 0.05 --gap-factor 1.5 --json channel.json
python workbench.py replay input.txt --out sessions
python workbench.py drift baseline.json candidate.json --max-rel-change 0.05
python workbench.py pipeline baseline.txt candidate.txt --out run-001
```

文件路径按当前工作目录解析。`record` 只生成模拟数据，桌面窗口需要 Tk。`replay` 将文本行日志只读导入为采样、异常和设备信息文件。`analyze`、`channel`、`drift` 和 `pipeline` 对记录或报告进行离线处理。运行 `python workbench.py <命令> --help` 查看子工具参数。

## 当前模块状态

| 模块 | 当前能力与边界 |
|---|---|
| 01 需求管理 | 文本需求、新增、筛选、CSV 与状态登记，部分实现 |
| 02 任务与轨道资料 | 规划，仅资料管理范围 |
| 03 CAD 文件索引 | 文件索引、SHA-256 与变化检查；没有 CAD 内核 |
| 04 结构与振动资料 | 规划，仅外部资料与结果管理范围 |
| 05 CFD 资料 | 规划，仅外部资料与结果管理范围 |
| 06 热分析资料 | 规划 |
| 07 推进系统资料 | 规划，当前仅公开文献管理范围 |
| 08 电气电子资料 | 规划，仅通用地面仪器资料管理范围 |
| 09 GNC 学习资料 | 规划，仅学习资料管理范围 |
| 10 软件版本与测试管理 | 登记测试证据与需求追踪；不认证真实执行 |
| 11 地面数据链测试 | 部分测试基础；没有硬件在环验证 |
| 12 零件配置管理 | 文本零件版本、装配引用与快照工具 |
| 13 地面采集与离线分析 | 模拟记录、CSV 回放、只读文本日志导入、通道统计、漂移比较与流水线；未接真实仪器 |
| 14 问题管理 | 文本问题记录、处理和关闭依据；不认证附件真实性 |
| 15 只读状态展示 | 规划 |

统一入口为 `workbench.py`，目前是命令行工作台；记录器窗口是独立的 Tk 界面，并非统一图形平台。

## 测试与验证范围

v0.50.0 新增 `test_adapter_read_bounds.py`，覆盖空行逐次读取、坏行异常计数和长坏行前缀下 `drain(max_reads=...)` 的工作量上限。`LineAdapter.read()` 对空行和坏行每次最多消费一行；调用者可用 `drain` 限制一次处理的读取次数。生产适配器逻辑未修改。

本版未运行新增测试或全套测试，提交说明标注“未测试”。在仓库根目录运行：

```text
python3 -m unittest test_adapter_read_bounds test_adapters test_adapter_repeated_headers
python3 -m unittest discover
python workbench.py --help
```

由管家云服务器或用户电脑运行，报告实际测试总数、失败数、跳过数和退出码。Tk 测试需要 tkinter 和可用 DISPLAY；云机可使用 Xvfb。无 Tk 或 DISPLAY 时跳过，跳过不代表通过。单元测试不能替代真实测量数据、传感器、硬件在环或 Tk 真机验证。

## 文档

- [下次开发入口](NEXT_DEVELOPMENT.md)
- [15 模块路线图](ROADMAP.md)
- [具体开发任务](DEVELOPMENT_TASKS.md)
- [历史记录](HISTORY_THROUGH_V0_10.md)
- [v0.40.0 窗口导入取消与失败恢复](TOOLS_V0_40.md)
- [v0.41.0 首页与回放窗口测试说明](TOOLS_V0_41.md)
- [v0.42.0 采集切换与文本回放测试说明](TOOLS_V0_42.md)
- [v0.43.0 采集会话关闭异常测试说明](TOOLS_V0_43.md)
- [v0.43.1 工作台结构修正说明](TOOLS_V0_43_1.md)
- [v0.44.0 会话文件资源清理说明](TOOLS_V0_44.md)
- [v0.45.0 事件日志失败与重复关闭测试说明](TOOLS_V0_45.md)
- [v0.46.0 会话初始化失败清理测试说明](TOOLS_V0_46.md)
- [v0.47.0 初始化失败时错误优先级测试说明](TOOLS_V0_47.md)
- [v0.48.0 成功导入与回放一致性测试说明](TOOLS_V0_48.md)
- [v0.49.0 连续重复表头读取说明](TOOLS_V0_49.md)
- [v0.50.0 LineAdapter 读取边界测试说明](TOOLS_V0_50.md)
- 各版本功能和测试边界见仓库中的 `TOOLS_V0_*.md` 文件。
