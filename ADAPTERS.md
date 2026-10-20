# 只读采集适配器（开发中，尚未接入界面）

`adapters.py` 为选定硬件后接入真实数据做准备。只读：没有写入、发送命令或控制输出的接口，也没有任何具体硬件协议。

## 内容
- `SensorAdapter`：基类，`read()` 返回一个 `Sample`，没有可用数据（坏行或数据流结束）时返回 `None`，结束后 `finished` 为 True。
- `SimulatedAdapter`：包装现有模拟数据。
- `LineAdapter`：按 `recorder.FIELDS` 顺序解析每行一个样本的 CSV 文本行。传入任何文本行迭代器（文件，或由调用方包装好的串口读取器）。坏行记入异常日志后跳过，不抛异常、不中断。
- `DeviceInfo` 与 `write_device_info`：设备身份写入会话目录的 `device.json`。序列号、固件版本未提供时为“未知”，不猜测。
- `AnomalyLog`：异常记录，最多保留最近 1000 条，超出后总数继续计数；`save` 写入 `anomalies.csv`，被截断时末行注明。
- `drain(adapter, max_reads)`：每次最多读 max_reads 次，供界面定时器分批取数。

异常类型：`field_count`（字段数不对）、`invalid`（非数字、NaN、无穷、时间为负、气压非正）、`time_order`（时间未严格递增）、`line_too_long`（超过 512 字符）。

## 验证与限制
```
python -m unittest -v
```
沙箱已验证上述行为，以及适配器数据写入现有 `SessionWriter` 会话后可由 `load_csv` 读回。尚未接入 `recorder.py` 界面，尚未连接真实硬件，未实现串口打开与波特率设置，也没有校准记录。

## 下一步
- 在 `recorder.py` 中增加“适配器采集”入口，并在会话目录写入 `device.json` 与 `anomalies.csv`。需在 Windows 上实测界面。
- 选定硬件后，依据厂家资料补充串口参数、轴向定义与校准记录。
