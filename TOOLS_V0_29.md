# v0.29.0：虚拟显示冒烟与失败清单边界测试

新增 `test_recorder_window.py`，在 Tk 和 `DISPLAY` 可用时创建一次记录器窗口，并检查导入状态摘要能写入窗口变量。无显示环境下该测试会跳过。若机器安装 Xvfb，可单独运行：

```text
xvfb-run -a python3 -m unittest test_recorder_window
```

新增 `test_pipeline_manifest_write_failure.py`，模拟回放失败且失败清单写入也出错，检查命令保留原始失败阶段和原因，并提示清单未写入。

建议运行全部测试：

```text
python3 -m unittest discover
```

本版未运行测试。按 v0.28.0 预计 188 项的基数，本版增加 2 项，预计全套 190 项；无显示环境下虚拟窗口冒烟项会报告跳过。真实测量数据和硬件仍未验证，Xvfb 测试需要在具备 Tk/Xvfb 的云服务器或用户电脑执行。
