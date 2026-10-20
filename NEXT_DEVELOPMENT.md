# 下次开发从这里开始

当前 v0.18.1（仅文档）。代码状态：analysis.py 为 0.17.0，channel_report.py 为 0.18.0。管家在云服务器上对提交 3909986 运行 128 项测试全部通过。Tk 窗口、Windows 和真实硬件未实测。

## 已完成
- v0.16.0：summary_report.py 记录输入文件大小、SHA-256、读取时刻并做前后比对；test_report_traceability.py。
- v0.17.0：analysis.py 支持 --expected-interval 与 --gap-factor，报告每通道首次极值时间；replay_session.py（文本行日志只读导入）、recorder_lines.py（记录器导入按钮）及测试。原计划的“通用只读文本流采集”已由 replay_session.py 完成。
- v0.18.0：channel_report.py（按通道统计与缺口，中位数 5 倍法）及测试。
- v0.18.1：用法说明见 TOOLS_V0_16_TO_V0_18.md，含两套缺口定义的对比。

## 下一轮候选
1. 统一缺口定义：channel_report.py 增加 --expected-interval 与 --gap-factor，与 analysis.py 一致；不给周期时保留中位数法并在输出中标明所用方法。改 channel_report.py、test_channel_report.py、TOOLS_V0_16_TO_V0_18.md。
2. 把 channel_report.py 和 replay_session.py 接入 workbench.py 子命令。需先读 workbench.py 的带缩进原文。
3. 记录器窗口直接读取 recorder_lines.py 的导入结果并显示异常行数。需要在有桌面的电脑上实测。

保留：浏览器视觉验收、附件核验、多进程协调和跨系统路径转换。专业领域维持既定资料管理范围。
