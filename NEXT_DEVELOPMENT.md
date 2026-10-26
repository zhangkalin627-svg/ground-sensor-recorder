# 下次开发从这里开始

当前版本 v0.32.0（未测试）。v0.27.0 云测报告为 184/185；失败是 `test_workbench_drift` 对版本号写死为 v0.26.0。v0.27.1（`74ed7d54c51a0c6a964d2a1960d536d653911ef9`）已改为读取 `workbench.VERSION`；该旧报告不能判断修复版失败。v0.27.1 至 v0.31.0 的全套复测结果仍待管家确认。

v0.32.0 更新 `pipeline_report.py`：成功和失败运行清单统一使用独占 JSON 写入器；若序列化或写入失败，只清理本次创建的半成品文件。失败清单写入失败时，命令行仍保留原始业务错误和失败阶段，并提示清单未能写入。新增 `test_pipeline_manifest_write_failure.py` 覆盖模拟部分 JSON 写入后抛错的路径。全套测试预计 198 项，未运行。

在仓库根目录运行：

```text
python3 -m unittest test_pipeline_manifest_write_failure
python3 -m unittest discover
```

无显示环境时 Tk 窗口冒烟测试可能跳过；真实测量数据和真实硬件仍未验证。工作台和离线流水线不提供火箭专用仿真模型。

## 后续开发

1. 读管家对 v0.27.1 至 v0.32.0 的云机复测结果；有失败先按测试名和原始报错修复，管家有新任务先做。
2. 补充运行清单路径权限、已有目标和模拟磁盘写入中断测试，检查错误信息与文件清理边界，改 `pipeline_report.py`、`test_pipeline_manifest_write_failure.py`。
3. 继续完善记录器窗口状态的 Xvfb 冒烟测试，改 `test_recorder_window.py`；把无 Tk/Xvfb 时的 skip 与真机验证分开记录。
4. 保持 `TOOLS_V0_32.md`、README 的功能说明与已验证范围一致，不把沙箱测试写成硬件实测。

测试需在管家云服务器或用户电脑运行；本环境未运行命令行测试。
