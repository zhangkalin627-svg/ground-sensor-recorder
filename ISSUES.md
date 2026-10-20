# 问题追踪 v0.5.0（第 14 模块）

新增独立命令行工具 issues.py，无第三方依赖。它只处理文本记录，不控制任何设备，不构成安全或可靠性认证。记录器仍为 v0.2.0，未接入图形界面。

```
python issues.py add --id ISS-001 --title 采样断流 --symptom 曲线停止 --cause 未确认 --req GSR-001
python issues.py set-status --id ISS-001 --status 验证关闭 --retest 复测记录R1 --tests T-1
python issues.py list --status 新建
python issues.py check --reqs requirements.csv
python issues.py export out.csv
python issues.py import other.csv
```

默认问题表为当前目录的 issues.csv，可用 --db 指定。字段：issue_id、title、symptom（观察到的现象）、suspected_cause（推测原因，未确认时留空或写“未确认”）、status、req_ids、test_ids、retest_evidence、resolution。多个编号用分号分隔。

规则：
- 必填 issue_id、title、symptom、status。编号不区分大小写，重复会被拒绝。
- 状态只能是 新建、分析中、已处理待复测、验证关闭、已拒绝。
- “验证关闭”必须同时填写复测依据和至少一个测试编号。“已处理待复测”和“已拒绝”必须填写 resolution。推测原因不计入证据，不能替代复测。
- 导入全有或全无：任何一行有问题，已有问题表保持原样。写入先写临时文件再替换。
- 关联的需求编号只有在指定 --reqs 时才校验（add、import 和 check）；工具不检查测试编号是否真实存在。
