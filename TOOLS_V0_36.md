# v0.36.0：验证不同输出目录的并行流水线

本版在 `test_pipeline_output_concurrency.py` 增加一个并行测试：两次 pipeline 流程使用各自独立的输出目录，并在回放阶段同步启动；两边都应完成并生成各自的 baseline、candidate、drift 报告和成功运行清单。它与同文件已有的“争用同一目录时后启动流程失败”测试互补。

没有修改流水线业务逻辑。`workbench.py` 入口版本更新为 0.36.0。

运行单项测试：

```text
python3 -m unittest test_pipeline_output_concurrency
```

运行全套测试：

```text
python3 -m unittest discover
```

本版新增 1 项。根据 v0.35.0 文档的预计 204 项推算，全套预计 205 项；这是预计数，不是测试结果。本次代码和测试未运行，请在管家云服务器或用户电脑上执行并回报实际数量、退出码和失败原文。无 Tk/Xvfb 的环境可能跳过窗口冒烟测试；真实测量数据、硬件和 Tk 真机仍未验证。
