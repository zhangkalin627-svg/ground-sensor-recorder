# v0.47.0：初始化失败时保留原始错误

## 改动

- `test_recorder_session_cleanup.py` 新增三项无 Tk 回归测试，覆盖文件初始化失败后清理也抛出 `OSError` 的情况。
- 第二个会话文件打开失败时，如果已打开的样本文件关闭也失败，构造过程应保留第二个文件打开失败的原始错误。
- CSV 表头写入失败且样本文件关闭失败时，仍尝试关闭事件文件，并保留表头写入错误。
- 初始事件日志写入失败且事件文件关闭失败时，仍尝试关闭样本文件，并保留初始事件写入错误。
- `workbench.py` 版本更新至 0.47.0；同步更新 README 和 `NEXT_DEVELOPMENT.md`。
- 没有修改 `recorder.py` 的会话采集逻辑。

## 运行与测试

在仓库根目录运行：

```text
python3 -m unittest test_recorder_session_cleanup
python3 -m unittest discover
python workbench.py --help
```

本版新增测试和全套测试均未运行，提交说明标注“未测试”；请由管家云服务器或用户电脑复测。新测试使用内存文件对象，不需要 Tk 显示环境。

## 边界

这些测试检查文件初始化异常和清理异常的优先级，不验证真实传感器、实测数据、硬件在环或 Tk 真机环境。
