# v0.30.0：流水线输入边界与预检

`pipeline_report.py` 现在在计算输入 SHA-256、创建输出目录之前检查两份日志是否为普通文件，并套用 `replay_session.py` 的 50 MiB 单文件上限。超过上限、路径不存在或是目录时，在 `preflight` 阶段拒绝运行，不创建输出目录。

输入 SHA-256 仍按 1 MiB 块读取，不把整个文件载入内存。流水线输出目录创建遇到权限错误时，会显示 `create_output_directory` 阶段和原始错误，不会伪称已生成输出。

示例：

```text
python workbench.py pipeline baseline.txt candidate.txt --out run-001 --strict
python3 -m unittest test_pipeline_cli
python3 -m unittest discover
```

新增 4 项边界测试：目录输入、大于 50 MiB 的稀疏文件、跨 1 MiB 哈希块的文件，以及模拟输出目录权限拒绝。测试尚未运行，提交说明标记“未测试”；请在管家云服务器或用户电脑执行全套测试。无显示环境时 Tk 冒烟测试可能跳过，真实硬件和真实测量数据仍未验证。
