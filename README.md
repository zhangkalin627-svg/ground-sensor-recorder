# 地面实验工具 v0.15.0

一个逐步增加模块的通用地面实验与工程记录工具集。当前提供命令行入口及独立的模拟记录器，使用 Python 标准库；Python 3.10+，记录器需 Tk 与图形桌面。

## 从这里开始

```
python workbench.py --help
python workbench.py modules
python workbench.py record
python workbench.py analyze samples.csv --output summary.json
python workbench.py requirements --help
python workbench.py issues --help
python workbench.py configuration --help
python workbench.py documents --help
python workbench.py results --help
python -m unittest -v
```

子命令的文件路径相对于当前工作目录。record 只生成模拟数据；Windows 可沿用 start.bat。分析读取记录器 CSV，不推断数据是否为真实测量。JSON 分析报告和数据库导出不覆盖已有目标。

## 当前模块状态（v0.11.0）

此表为当前摘要，后面的版本记录仅表示历史交付。

| 模块 | 当前能力 |
|---|---|
| 01 需求管理 | 文本需求、新增、筛选、CSV；已有独立测试结果追踪，状态修改已实现 |
| 02 任务与轨道 | 规划，仅资料管理范围 |
| 03 CAD | 文件索引、SHA-256 与变化检查；无 CAD 内核 |
| 04 结构振动 | 规划，仅外部资料与结果管理范围 |
| 05 CFD | 规划，仅外部资料与结果管理范围 |
| 06 热分析 | 规划 |
| 07 推进 | 规划，仅公开文献管理范围 |
| 08 EDA | 规划，仅通用地面仪器资料管理范围 |
| 09 GNC | 规划，仅学习资料管理范围 |
| 10 软件测试管理 | 测试结果登记、按运行与源码标识追踪；不认证真实执行 |
| 11 数据链验证 | 模拟及部分自动测试，无硬件在环 |
| 12 配置管理 | 零件版本、装配引用、独立快照及直接子项差异 |
| 13 采集分析 | 模拟记录器、离线统计、只读适配器基础；未接入真实仪器 |
| 14 故障管理 | 文本记录、处理和关闭依据；附件真实性未认证 |
| 15 只读展示 | 规划 |

统一入口为命令行 workbench.py，尚无统一图形平台。桌面窗口和真实硬件未实测。

## 数据与校验

配置、资料索引和测试结果读取 JSON 时拒绝重复字段、NaN/Infinity、超过 16 MiB 的文件及过深嵌套。配置和资料索引的 schema_version 必须为整数 1，拒绝布尔值与浮点数。各类记录上限 10000；记录器样本上限仍为 100000。

资料索引使用绝对路径，已支持显式根目录映射迁移。测试和复测依据为用户登记文本，不自动认证执行或附件；源码提交标识不联网验证。需求、问题等数据库更新采用原子替换，但当前未提供多进程并发写入协调。

## 验证

本轮全套 103 项测试通过。图形窗口、Windows 实机和真实硬件未实测；不能将单元测试结果视为硬件验证。

## 开发与历史

- [下次开发入口](NEXT_DEVELOPMENT.md)
- [15 模块路线图](ROADMAP.md)
- [具体开发任务](DEVELOPMENT_TASKS.md)
- [截至 v0.10.0 的原首页与历史用法](HISTORY_THROUGH_V0_10.md)

## v0.12.0 需求状态修改

```
python workbench.py requirements set-status --id R1 --status 已批准
python workbench.py requirements set-status --id R1 --status 已验证 --verification "真实验证方法" --tests "T1;T2"
```

省略 --verification 或 --tests 保留原值；显式提供时替换对应字段。已验证状态仍必须满足原有依据和测试编号规则。状态只是用户登记，不自动确认测试通过。需求编号不区分大小写；未找到、非法状态、缺失依据均拒绝，写入失败保留旧文件。其他需求、来源和描述不变。

新增 test_requirement_status.py，全部 90 项测试通过。CLI 已由现有 workbench requirements 路由支持，无需更改入口。桌面与硬件未实测。

## v0.13.0 资料路径迁移

```
python workbench.py documents migrate --old-root /old/data --new-root /new/data
python workbench.py documents migrate --old-root /old/data --new-root /new/data --apply
```

默认仅预览，显示匹配数量、新旧路径及失败原因。--apply 在所有匹配项校验成功后原子更新索引。新文件必须存在、位于新根目录内且 SHA-256 与登记值一致。按路径层级匹配旧目录，避免 old 错配 older；旧目录可以已经不存在。任一匹配项失败则不写入。无匹配时不写入。

该功能不复制、移动、上传或修改资料文件，不扫描索引以外的用户目录。仅适用于当前系统可解析的本地路径；跨操作系统路径转换尚未实现。验证后到写入之间仍需保持资料文件不被其他程序改动，当前无多进程文件锁。

全部 95 项测试通过，新增 5 项覆盖预览与应用、缺失旧目录、前缀边界、缺失和哈希差异、符号链接越界及失败写入保护。Windows、图形窗口、真实硬件未实测。

## v0.14.0 配置版本差异

```
python workbench.py configuration compare --left-id A1 --left-version 1 --right-id A1 --right-version 2
```

只读比较名称、型号、变更原因及直接子项，向终端输出 JSON，不展开下层 BOM。区分新增、删除、版本集合变化、相同版本的数量变化及编号大小写变化。相同零件存在多个子版本时完整列出前后版本集合，不推断替换对应关系。任一根版本缺失则拒绝。identical_content 表示所比较内容相同，不表示版本号相同或整个递归装配等价。

新增 test_configuration_compare.py；全部 99 项测试通过。数据库未被修改。Windows、图形界面与真实硬件仍未实测。

## v0.15.0 离线 HTML 汇总报告

```
python workbench.py report --requirements requirements.csv --issues issues.csv --configuration configuration.json --documents documents.json --output summary.html
```

四类输入可按需选择，至少一类；明确指定却不存在或损坏的文件报错，不当成空表。生成自包含静态 HTML，显示数量、登记状态与摘要。所有用户文本转义，无 JavaScript、远程资源或设备控制。输出必须是新文件，禁止覆盖输入及已有文件（含链接）。

报告只展示已登记资料，不重新核对文件哈希、证据真实性或测试实际执行。HTML 内包含输入路径和登记文本，分享前自行核对内容。它是离线报告，不是统一交互式图形界面。

新增 summary_report.py、test_summary_report.py，workbench 增加 report 命令。全部 103 项测试通过，覆盖 HTML 转义、四类数据、空表、错误输入及输出保护。浏览器视觉效果、Windows、硬件未实测。
