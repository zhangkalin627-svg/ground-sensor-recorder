# v0.34.0：运行清单打开权限失败测试

本版给 `pipeline_manifest.json` 的独占创建补充权限拒绝场景的测试，没有改变流水线业务逻辑：

- 直接写运行清单时，模拟 `os.open` 因权限不足而失败，确认没有留下空文件。
- 成功流程的最终清单被拒绝打开时，确认命令以失败退出，并尽力写出 `failure_stage=write_success_manifest` 的失败清单。
- 业务阶段已经失败、随后失败清单也因权限拒绝无法打开时，确认原始业务错误仍显示，且不会留下清单文件。

`workbench.py` 入口版本更新为 0.34.0。运行：

```text
python3 -m unittest test_pipeline_manifest_write_failure
python3 -m unittest discover
python workbench.py --help
```

代码和测试未测试。上一版全套测试预计 200 项，本版新增 3 项，预计 203 项；这是推算值，不是实测结果。请在管家云服务器或用户电脑运行。无显示环境下 Tk 冒烟测试可能跳过；真实测量数据、真实硬件及 Tk 真机仍未验证。
