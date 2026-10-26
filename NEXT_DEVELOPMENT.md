# 下次开发从这里开始

当前版本 v0.36.0（未测试）。本版为 `test_pipeline_output_concurrency.py` 增加独立输出目录并行执行测试，两个 pipeline 同步进入回放阶段后都应完成且各自生成报告和成功清单；已有的同目录争用测试继续验证后启动流程不能覆盖先启动流程。没有修改流水线业务逻辑。`workbench.py` 版本为 0.36.0，详见 `TOOLS_V0_36.md`。

v0.35.0 的云端复测结果尚未在本轮收件箱可见页面中找到；最新看到的失败邮件针对旧提交 v0.27.0，旧断言已在 v0.27.1 改为读取 `workbench.VERSION`。本轮未见管家新任务。v0.36.0 代码和测试未运行；按 v0.35.0 的预计 204 项加本版 1 项推算，全套预计 205 项。

运行：

```text
python3 -m unittest test_pipeline_output_concurrency
python3 -m unittest discover
python workbench.py --help
```

## 后续开发

1. 管家有新任务时先处理；收到测试失败时先按测试名和原始错误修复。没有任务或失败时继续迭代，不等待云测结果。
2. 若独立输出目录并行测试通过，可为流水线输入文件在运行期间变化的重试提示补充 CLI 层测试，涉及 `test_pipeline_cli.py`、`TOOLS_V0_37.md` 和本文件；避免改动已验证的输出目录保护逻辑。
3. 为 `recorder_lines.py` 的异常状态行补充 Xvfb 冒烟覆盖，改 `test_recorder_window.py`；没有 Tk/Xvfb 时明确记为跳过，不写成通过。
4. 对照管家给的仿真说明再规划 `realworld_sim` 用法；仿真输出必须标为仿真，不能声称是真实测量或火箭专用模型结果。
5. 维护 `README.md`、版本使用文档和本文件，使当前状态、运行方式和验证范围一致。

全套测试需在管家云服务器或用户电脑运行；本环境没有运行命令行测试。真实测量数据、真实硬件和 Tk 真机仍未验证。
