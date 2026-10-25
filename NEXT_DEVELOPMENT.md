# 下次开发从这里开始

当前 v0.24.0（未测试）。代码状态：analysis.py 为 0.17.0，channel_report.py 为 0.19.0，drift_report.py 为 0.22.0，workbench.py 为 0.23.0，recorder_lines.py 窗口标题为 0.21.0。管家在云服务器（InstaBox，python3 -m unittest discover）上对 4c41434（v0.23.1）运行全套 171 项 unittest 全部通过，无 Traceback（2026-10-25 18:36 CST 回信）。v0.24.0 新增 test_pipeline_e2e.py（7 项）还没有人在真实仓库跑过，预期全套 178 项。Tk 窗口、Windows 和真实硬件仍未实测：测试只覆盖不需要显示器的部分，recorder_lines.py 的状态行没有人在有桌面的电脑上打开过。

## 已完成
- v0.16.0：summary_report.py 记录输入文件大小、SHA-256、读取时刻并做前后比对；test_report_traceability.py。
- v0.17.0：analysis.py 支持 --expected-interval 与 --gap-factor，报告每通道首次极值时间；replay_session.py（文本行日志只读导入）、recorder_lines.py（记录器导入按钮）及测试。
- v0.18.0：channel_report.py（按通道统计与缺口）及测试。
- v0.19.0：channel_report.py 增加 --expected-interval 与 --gap-factor，缺口定义与 analysis.py 对齐；版本字符串对齐；TOOLS_V0_19.md。
- v0.20.0：workbench.py 新增子命令 channel 和 replay，参数原样转交；test_workbench_commands.py。v0.20.1：TOOLS_V0_20.md。
- v0.21.0：import_status.py（把导入结果生成一行状态文字，纯标准库）、test_import_status.py（7 项）；recorder_lines.py 导入后保留一行状态文字，显示异常行数和主要类别，失败时显示原因。
- v0.21.2：TOOLS_V0_21.md，说明 import_status.py 的用法和输出格式。
- v0.22.0：drift_report.py，对比两份 channel_report.py JSON 报告并按阈值标出漂移通道。v0.22.1：test_drift_report.py（20 项）、TOOLS_V0_22.md。
- v0.23.0：workbench.py 新增子命令 drift，参数原样转交给 drift_report.py，模块 13 的命令列表加上 drift；test_workbench_drift.py（4 项，只测路由、帮助文字和模块列表）。
- v0.23.1：TOOLS_V0_23.md，说明 workbench.py drift 的用法和 replay、channel、drift 的串联顺序。管家云机 171 项全过。
- v0.24.0：test_pipeline_e2e.py（7 项，不需要显示器）：用合成文本行日志把 replay_session、channel_report、drift_report 串起来，覆盖干净日志无缺口、中间断 1 秒被找到、同一数据无漂移、ax 通道平移被标为漂移（--strict 退出码 2）、坏行不中断、输入不被修改且报告拒绝覆盖，另有一项经 workbench.py 子进程串联。代码没动。

## 下一轮候选
1. v0.24.0 的 7 项测试等管家云机结果；有失败先修（如果失败，先判断是测试写错还是代码有问题，再改）。
2. 需要有桌面的电脑：打开 python recorder_lines.py，导入一份带坏行的文本行日志，确认状态行显示正确。管家已说明 Tk 窗口由他用 Xvfb 虚拟显示代跑，真机带屏实测排在家机恢复后。
3. realworld_sim 输入格式说明已由管家 10-22 回复（Pally 收件箱，主题含“三件事一次回”）；接入方式还没做，做之前先对照原信，不猜格式。
4. 给端到端链路写使用文档（TOOLS_V0_24.md），说明三步串联的命令和退出码约定，等 v0.24.0 测试通过后再写。

保留：浏览器视觉验收、附件核验、多进程协调和跨系统路径转换。专业领域维持既定资料管理范围。
