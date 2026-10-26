# v0.35.0：验证并发运行的输出目录保护

本版新增 `test_pipeline_output_concurrency.py`，用两个并发流程尝试写入同一个新输出目录：第一个流程创建目录后暂停，第二个流程必须在 `create_output_directory` 阶段失败；第一个恢复后应完整写出报告和成功运行清单。测试用于验证已实现的独占目录创建不会让后到流程覆盖已有内容。

没有修改流水线业务逻辑。`workbench.py` 入口版本更新为 0.35.0。

运行单项测试：

```text
python3 -m unittest test_pipeline_output_concurrency
```

运行全套测试：

```text
python3 -m unittest discover
```

本版新增 1 项；根据 v0.34.0 文档所列预计 203 项推算，全套预计 204 项。代码和测试均未运行，204 是预计值，不是实测结果。请在管家云服务器或用户电脑运行并报告实际测试总数、退出码和失败原文。无显示环境下 Tk 冒烟测试可能跳过；真实测量、硬件和 Tk 真机仍未验证。
