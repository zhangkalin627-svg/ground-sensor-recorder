# v0.33.0：运行清单路径保护测试

`pipeline_report.py` 的成功和失败运行清单均以独占方式创建，不覆盖已有目标。若写入出错，清理逻辑先核对路径当前文件身份；身份不匹配时保留该路径，避免误删并发替换后出现的其他文件。

本版在 `test_pipeline_manifest_write_failure.py` 新增两项测试：已有清单保持原内容；模拟部分写入后路径身份不匹配时保留文件。代码和测试未测试。

运行：

```text
python3 -m unittest test_pipeline_manifest_write_failure
python3 -m unittest discover
```

上一版全套测试预计 198 项，本版新增 2 项，预计 200 项；这是预计数，不是实际测试结果。请在管家云服务器或用户电脑运行。真实测量数据、真实硬件和 Tk 真机仍未验证；无显示环境下 Tk 测试可能跳过。
