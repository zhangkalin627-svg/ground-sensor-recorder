# 下次开发从这里开始

当前版本 v0.33.0（未测试）。管家最新可见的旧版云测报告是 v0.27.0：184/185，通过之外有一项旧版本断言失败；v0.27.1 已改为读取 `workbench.VERSION`，但该旧报告不能判断修复版失败。v0.27.1 至 v0.32.0 的完整云测结果仍待确认。

v0.33.0 继续加强 `pipeline_report.py` 运行清单保护：独占写入拒绝覆盖已有文件；失败清理前核对文件身份，不匹配时不删除。`test_pipeline_manifest_write_failure.py` 新增两项相应测试。本版预计全套 200 项，未运行。

运行：

```text
python3 -m unittest test_pipeline_manifest_write_failure
python3 -m unittest discover
```

## 后续开发

1. 读管家对 v0.27.1 至 v0.33.0 的云机复测结果；有失败先按测试名和原始报错修复，管家有新任务先做。
2. 补充运行清单路径权限和模拟磁盘写入中断测试，检查失败信息及部分文件清理边界，改 `pipeline_report.py`、`test_pipeline_manifest_write_failure.py`。
3. 继续完善记录器窗口状态的 Xvfb 冒烟测试，改 `test_recorder_window.py`；区分无 Tk/Xvfb 时的跳过与真机验证。
4. 保持 `TOOLS_V0_33.md`、README 的功能说明与验证范围一致，不把沙箱测试写成硬件实测。

测试需在管家云服务器或用户电脑运行；本环境未运行命令行测试。真实测量数据与硬件仍未验证，工作台也不提供火箭专用仿真模型。
