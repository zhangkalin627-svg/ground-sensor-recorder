# v0.21 新增：导入状态行（import_status.py）

状态：未测试（文档）。管家在云服务器上对 7cdf9f7 跑过 147 项 unittest，全部通过；下面的示例输出是对照 import_status.py 源码推出来的，没有实际运行过。

## 它做什么

import_status.py 把一次文本行日志导入的结果压成一行中文状态文字。记录器窗口（recorder_lines.py）导入完成后，会在窗口里保留这一行，这样关掉提示框以后，异常行数还看得见。

只用标准库，不需要显示器，可以在服务器上直接测。

## 函数

1. anomaly_status_text(total, by_kind=None, truncated=False)
   - total：异常行总数。小于等于 0 时输出无异常。
   - by_kind：类别名到数量的字典，可以不给。
   - truncated：导入是否因为行数上限提前停止。
2. status_from_result(result)
   - result 是 replay_session 的导入结果对象，需要有 anomalies.total、anomalies.by_kind 和 truncated 三个属性。

## 输出格式（对照源码推出）

- 无异常：最近一次导入：无异常行
- 有异常、没给类别：最近一次导入：异常行 5 条
- 有异常、有类别：最近一次导入：异常行 5 条（甲类 3，乙类 2）
  - 类别按数量从多到少排，数量相同按名称排。
  - 最多显示 3 类，超过的折叠成 另有 N 类。
- 导入被行数上限截断时，末尾加：；已达行数上限，其余未读取

类别名来自 replay_session.py 记录的异常类别，这里的甲类、乙类只是占位，不是真实类别名。

## 怎么在服务器上测

    python3 -m unittest test_import_status

预期 7 项通过。全套：python3 -m unittest discover。

## 还没人测的部分

- recorder_lines.py 的状态行显示：需要有桌面的电脑，执行 python recorder_lines.py，导入一份带坏行的文本行日志，看窗口里的状态行是否和上面的格式一致。
- 导入失败时窗口显示失败原因：同样需要窗口。
