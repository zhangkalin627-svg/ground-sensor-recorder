# 地面实验工具 v0.6.0
这是通用地面实验数据软件。本版使用合成的桌面运动数据，不是火箭飞控或 GNC，没有制导、姿态解算、导航、点火或执行机构控制功能。
## 启动
安装带 Tk 支持的 Python 3.10 或更高版本。Windows 安装 Python 时保留 Tcl/Tk 选项。在本目录运行：
```
python recorder.py
```
Windows 也可双击 start.bat。无需安装第三方 Python 包。Linux 若提示缺少 tkinter，需通过系统软件管理器安装对应 Tk 支持；本程序需要图形桌面。
## 使用
1. 点击“新建模拟采集”，选择自动保存目录，每次生成独立子目录。目标每秒采集 20 次。此频率为桌面演示目标，时间由实际单调时钟记录，不是硬实时保证。
2. 下拉选择加速度、角速度或气压通道，查看最近 400 点。纵轴自动缩放。
3. 勾选“模拟数据中断”，等待超过 1 秒显示中断提示，取消勾选恢复采集。
4. 停止后点击“保存 CSV”，自行选择保存位置；停止不清空数据。
5. “载入 CSV 回放”按照文件时间间隔播放；可暂停并继续。导入的数据完整保留，导出不受回放进度影响。拖动回放定位滑块，再点“跳转并暂停”，可定位并继续播放。
模拟采集逐条追加到所选目录的 samples.csv，并刷新 Python 文件缓冲；events.csv 记录开始、停止、中断和恢复。系统断电时仍可能丢失操作系统尚未落盘的数据。写入失败自动停止，内存数据可手动导出。文件回放不会自动另存。最多 100000 条，达到上限自动停止。导入失败不替换已有记录。CSV 严格检查字段顺序、有限数值、非负且严格递增的时间、正气压。不能把这些检查当作实际传感器量程校验。
## CSV 格式
UTF-8（导出带 BOM）。每行一个样本，表头顺序固定：
```
t_s,ax_m_s2,ay_m_s2,az_m_s2,gx_deg_s,gy_deg_s,gz_deg_s,pressure_pa
```
时间单位秒，加速度 m/s²，角速度 °/s，气压 Pa。加速度模拟包含静止重力项。本版不定义实际硬件安装轴向、校准系数或串口协议，选定传感器后依据厂家资料补充。
## 验证与限制
```
python -m unittest -v
```
交付环境已验证 CSV 往返、非法数据、表头、空文件、时间顺序及自动保存与事件日志；未在用户 Windows 电脑启动，也未连接硬件。图形界面需用户电脑实测。
建议首次验收：采集 10 秒、切换通道、模拟中断、保存、载入、暂停继续，确认回放结束且条数一致。
下一步：在选定地面实验硬件后接入已有的只读采集适配器（adapters.py，说明见 ADAPTERS.md，尚未接入记录器界面），并补充校准记录。
## v0.2.0 更新
- 独立采集目录、逐条保存和事件日志。
- 回放定位并暂停，修复重复点暂停导致无法继续的问题。
- 保存错误停止采集，保留内存记录。
- 图形界面和真实硬件尚未实测。
## 平台研发方向
按“一个平台、多个模块”逐步演进。完整的 15 个模块方向、第一代范围、验收要求和当前状态见 [研发路线图](ROADMAP.md)。当前仅地面记录器部分实现，其他规划不代表已经完成。
## 继续开发入口
接手开发先读 [下次开发任务](NEXT_DEVELOPMENT.md)，再按 [15 模块具体开发清单](DEVELOPMENT_TASKS.md) 执行。第 13 模块已新增离线 CSV 分析，第 01 模块已新增命令行需求管理；第 14 模块已有问题管理；下一轮优先第 12 模块配置管理。
## v0.3.0 离线分析
记录器仍为 v0.2.0，本次新增独立命令行分析工具，无第三方依赖。
单文件分析：
```
python analysis.py samples.csv --output summary.json
```
两份记录比较：
```
python analysis.py first.csv second.csv --output comparison.json
```
省略 --output 时在终端输出 JSON。输出文件必须不存在，禁止覆盖输入文件（包含硬链接和符号链接别名）。
报告包含各通道样本数、最小值、最大值、均值、总体标准差，以及时长和采样间隔统计。单样本的间隔为 null。双文件输出“第二份均值减第一份均值”，不对齐时间，不进行信号逐点相减。
输入沿用记录器 CSV。文件本身未含来源标记，不能据此判断模拟或实测。无插值、滤波、导航或控制功能。本轮 9 项单元测试通过；桌面界面与真实硬件仍未实测。
## v0.4.0 需求管理
新增独立命令行工具 requirements.py（第 01 模块），无第三方依赖，记录器仍为 v0.2.0。它只处理文本记录，不控制任何设备。
```
python requirements.py add --id GSR-010 --description 说明 --source 来源 --status 草案
python requirements.py list --status 草案
python requirements.py import other.csv
python requirements.py export out.csv --status 已批准
```
默认需求表为当前目录的 requirements.csv，可用 --db 指定。字段：req_id、description、source、status、verification_method、test_ids（多个用分号分隔）。示例见 example_requirements.csv。
规则：
- 必填 req_id、description、source、status。来源不明须明确写“未知”，留空会被拒绝并提示；列表中来源为“未知”的条目会标出。
- 状态只能是 草案、已批准、已实现、已验证、已废弃。“已验证”必须同时填写验证方法和至少一个关联测试编号。
- 编号不区分大小写，重复会被拒绝，包括导入文件内部重复及与已有需求重复。
- 导入全有或全无：任何一行有问题，已有需求表保持原样。写入先写临时文件再替换；已有需求表若本身损坏，不会被覆盖。
- 导入文件表头含未知列、缺少必填列、字段数过多时被拒绝，不静默丢弃信息。
验证：test_requirements.py 的 22 项测试在交付沙箱通过，覆盖重复编号、缺失字段、非法状态、导入失败保护、导出再导入一致、状态筛选和命令行返回码。test_recorder.py、test_analysis.py 本轮未重新运行；桌面界面与真实硬件仍未实测。
限制：关联测试编号只检查格式，不检查是否真实存在；“已验证”仅表示填写了依据，工具不会自动核实测试结果。

## v0.5.0 合并验证记录（2026-10-20）

保留仓库现有 issues.py / test_issues.py 实现，不覆盖为另一种问题表格式。全部新旧测试合并运行 63 项通过，命令为 python -m unittest discover -s platform-v0.5.0 -q（交付测试目录）。仓库根目录可运行 python -m unittest -v。真实硬件与桌面界面仍未实测。

第 14 模块支持编号、标题、现象、推测原因、处理说明、状态、需求和测试关联、复测依据、CSV 导入导出。验证关闭须填写复测依据与测试编号；依据为文本，不自动认证复测附件和执行结果。

使用现有接口：

```
python issues.py add --id ISS-001 --title "数据中断" --symptom "曲线停止" --cause "未确认"
python issues.py set-status --id ISS-001 --status 已处理待复测 --resolution "处理记录"
python issues.py set-status --id ISS-001 --status 验证关闭 --retest "复测记录 R1" --tests T-1
python issues.py --reqs requirements.csv check
```

需求存在性校验只检查编号，不验证需求内容。未配置需求表时显示未校验提示。附件校验和变更历史待后续完善。下一轮优先第 12 模块配置管理。

## v0.6.0 配置管理（第 12 模块）

新增 configuration.py 与 test_configuration.py，管理通用地面仪器的零件版本及装配关系。型号未知可留空，名称与变更原因必填。编号和版本组合不区分大小写且唯一；已登记版本不可原地覆盖，变更时新增版本。

```
python configuration.py add --id P1 --version 1 --name "实验零件" --reason "初次登记"
python configuration.py add --id A1 --version 1 --name "地面实验装配" --reason "初次装配" --child P1@1:2
python configuration.py list
python configuration.py snapshot --id A1 --version 1 --output assembly-v1.json
```

默认数据库 configuration.json，使用全局 --db 指定其他路径。装配项必须引用已登记的零件版本，数量必须正整数，禁止重复子项和循环引用。快照复制根装配及其引用的全部零件版本，供独立复查；目标文件必须不存在。快照为报告格式，不作为数据库直接导入；无加工程序、物理模型或设备控制。

全部新旧测试 69 项通过：在交付目录执行 python -m unittest discover -s platform-v0.6.0 -q；仓库根目录可执行 python -m unittest -v。新增 6 项覆盖重复和未知引用、非法数量、循环关系、快照固定版本及不覆盖、写入失败保护和 CLI。桌面界面与真实硬件仍未实测。本模块为第一代配置记录，尚无差异报告、文件哈希或用户权限管理。
