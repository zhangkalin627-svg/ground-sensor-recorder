# v0.31.0：流水线输入变化与报告写入保护

`pipeline_report.py` 在生成两份通道报告和漂移报告时使用独占创建的 JSON 写入函数。若序列化或写入中途失败，只删除本次调用创建的半成品目标文件；已完成的其他输出保留，并在失败清单中记录仍存在的相对路径。已存在的输出不会覆盖。

全部报告生成后会再次计算输入文件指纹。若输入在运行期间发生变化，流程以 `verify_inputs` 阶段失败，写入失败清单；之前生成的报告保留，供排查使用，不能当作一次成功且一致的分析结果。

输出目录的父路径不可创建时，流水线报告 `create_output_directory` 阶段和原始错误。由于输出目录尚未创建，此时不会有失败清单；已有父路径文件不会被改动。

运行方法：

```text
python workbench.py pipeline baseline.txt candidate.txt --out run-001 --strict
python3 -m unittest test_pipeline_cli
python3 -m unittest discover
```

新增三项边界测试，分别覆盖运行中输入变化、输出父路径是文件、报告 JSON 半写入后的清理。全套测试预计 197 项，尚未运行；请在管家云服务器或用户电脑执行。无显示环境时 Tk 冒烟测试可能跳过。真实测量数据、硬件和 Tk 真机环境仍未验证。
