# 下次开发从这里开始

当前版本 v0.34.0（未测试）。管家最新可见的云测报告仍是 v0.27.0：184/185，失败是旧的工作台版本断言；该断言已在 v0.27.1 改为读取 `workbench.VERSION`。此后至 v0.33.1 的复测结果尚未在当前收件箱页看到。

v0.33.1 已从 v0.32.0 恢复工作台帮助页和 `modules` JSON 输出，保留 `pipeline` 路由。v0.34.0 新增运行清单打开权限拒绝测试，生产流水线逻辑未改。代码和测试未运行，全套预计 203 项。

运行：

```text
python workbench.py --help
python workbench.py modules
python3 -m unittest test_pipeline_manifest_write_failure
python3 -m unittest discover
```

## 后续开发

1. 收到管家对新提交的云机结果后，有失败先按测试名和原始错误修复；有新任务先处理管家任务。当前无新任务，按卡林指示继续软件升级。
2. 按云测反馈补充流水线输出目录并发、manifest 写入异常和路径权限测试，必要时改 `pipeline_report.py`、`test_pipeline_manifest_write_failure.py`。
3. 完善记录器窗口异常状态的 Xvfb 冒烟测试，改 `test_recorder_window.py`；明确无 Tk/Xvfb 时属于跳过，不代表真机通过。
4. 保持 `TOOLS_V0_34.md`、README 与 `NEXT_DEVELOPMENT.md` 中的能力和验证范围一致，不把沙箱或云机单元测试写成硬件实测。

测试需在管家云服务器或用户电脑运行；本环境没有运行命令行测试。真实测量数据、真实硬件和 Tk 真机仍未验证，工作台也没有火箭专用仿真模型。
