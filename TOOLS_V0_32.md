# v0.32.0：运行清单写入失败保护

`pipeline_report.py` 的成功与失败运行清单现在都使用同一个独占 JSON 写入器。若创建后序列化或写入中途出错，写入器会核对文件身份，只删除本次创建的半成品；不会覆盖已有文件。

若业务阶段先失败、随后失败清单也写入失败，命令行仍保留并报告原始业务阶段和错误，同时提示失败清单未能写入。半截的 `pipeline_manifest.json` 会被清理。新增测试覆盖模拟写入部分 JSON 后抛错的情况。

运行方法：

```text
python workbench.py pipeline baseline.txt candidate.txt --out run-001 --strict
python3 -m unittest test_pipeline_manifest_write_failure
python3 -m unittest discover
```

本版代码和测试未测试。全套测试预计 198 项，需在管家云服务器或用户电脑运行。真实测量数据、真实硬件和 Tk 真机环境未验证；无显示环境下 Tk 测试可能跳过。
