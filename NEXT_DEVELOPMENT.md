# 下次开发从这里开始

当前 v0.20.0（未测试）。代码状态：analysis.py 为 0.17.0，channel_report.py 为 0.19.0，workbench.py 为 0.20.0。管家在云服务器上对 2fade2c（v0.19.0）运行 136 项 unittest 全部通过，退出码 0。v0.20.0 的改动尚未有人运行。Tk 窗口、Windows 和真实硬件未实测。

## 已完成
- v0.16.0：summary_report.py 记录输入文件大小、SHA-256、读取时刻并做前后比对；test_report_traceability.py。
- v0.17.0：analysis.py 支持 --expected-interval 与 --gap-factor，报告每通道首次极值时间；replay_session.py（文本行日志只读导入）、recorder_lines.py（记录器导入按钮）及测试。
- v0.18.0：channel_report.py（按通道统计与缺口）及测试。
- v0.19.0：channel_report.py 增加 --expected-interval 与 --gap-factor，缺口定义与 analysis.py 对齐；版本字符串对齐；TOOLS_V0_19.md。
- v0.20.0：workbench.py 新增子命令 channel（channel_report.py）和 replay（replay_session.py），参数原样转交；模块表第 13 项命令列同步；新增 test_workbench_commands.py（4 项，只测路由和帮助文字）。

## 下一轮候选
1. 记录器窗口直接读取 recorder_lines.py 的导入结果并显示异常行数。需要在有桌面的电脑上实测。
2. 在 TOOLS_V0_19.md 或 README 里补 workbench.py channel 和 replay 的用法示例（目前只写在 python workbench.py --help 里）。
3. 管家对 v0.20.0 的复跑结果出来后，按结果修正。

保留：浏览器视觉验收、附件核验、多进程协调和跨系统路径转换。专业领域维持既定资料管理范围。
