# v0.37.0：输入变化时的 CLI 提示

本版为流水线输入身份校验的命令行提示增加了专门测试。`pipeline_report.py` 在流程结束前复核输入指纹；若文件在运行期间发生变化，命令以失败状态结束，并提示检查输入后使用新的输出目录重跑。测试通过可控替身模拟指纹变化，不修改真实输入文件。

运行单项测试：

```text
python3 -m unittest test_pipeline_cli_retry
```

运行全套测试：

```text
python3 -m unittest discover
```

工作台入口版本已更新为 0.37.0：

```text
python workbench.py --help
```

本版代码和测试未在此环境运行，以上命令需由管家云服务器或用户电脑执行。测试不覆盖真实测量数据、真实硬件或 Tk 真机环境。
