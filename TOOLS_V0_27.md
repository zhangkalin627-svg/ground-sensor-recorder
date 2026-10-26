# v0.27.0：流水线失败记录

`pipeline_report.py` 仍通过一个命令依次回放两份文本日志、生成通道报告并比较漂移。v0.27.0 为运行清单增加完成/失败状态；发生错误时记录失败阶段、异常类型、预期输出、失败时已存在的相对路径，以及退出码 1。

## 运行

```text
python workbench.py pipeline baseline.txt candidate.txt --out run-001 --expected-interval 0.05 --strict
```

`--out` 必须是尚不存在的目录。已有目录不会被覆盖。输入校验失败发生在创建输出目录之前，因此不会留下运行清单。输出目录创建后发生失败时，工具会尽力写入 `pipeline_manifest.json`，其中 `status` 为 `failed`，`failure_stage` 标出阶段，例如 `candidate_replay` 或 `drift_comparison`，`partial_outputs` 列出失败时输出目录中已有的路径。若失败清单自身无法写入，错误信息会指出输出目录需要人工检查。

成功时 `status` 为 `completed`，正常退出码为 0；使用 `--strict` 且发现漂移时退出码为 2。失败阶段标记及部分输出记录尚未在本环境运行，需在管家云服务器或用户电脑执行：

```text
python3 -m unittest discover
```
