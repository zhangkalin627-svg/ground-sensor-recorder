import csv
import tempfile
import unittest
from pathlib import Path

from adapters import (AnomalyLog, DeviceInfo, LineAdapter, SensorAdapter, SimulatedAdapter,
                      drain, read_device_info, write_device_info)
from recorder import FIELDS, SessionWriter, load_csv, simulated


def line(t, p=101325):
    return f'{t},0.1,0.2,9.81,1,2,3,{p}'


class AdapterTests(unittest.TestCase):
    def test_simulated_uses_clock(self):
        ticks = iter([10.0, 10.5, 11.0])
        a = SimulatedAdapter(clock=lambda: next(ticks))
        self.assertEqual(a.read(), simulated(0.5))
        self.assertEqual(a.read(), simulated(1.0))
        self.assertEqual(a.info.name, '模拟数据')

    def test_good_lines_header_blank_bytes(self):
        lines = [','.join(FIELDS) + '\n', '\n', line(0.0), line(0.05).encode(), '\ufeff' + ','.join(FIELDS)]
        a = LineAdapter(lines, DeviceInfo('测试设备'))
        got = drain(a)
        self.assertEqual([s.t_s for s in got], [0.0, 0.05])
        self.assertTrue(a.finished)
        self.assertEqual(a.anomalies.total, 0)

    def test_bad_lines_logged_not_raised(self):
        lines = [line(0), '1,2,3', line(0.1, p=0), 'a,b,c,d,e,f,g,h', line(0.0),
                 line(0.2) + ',9', 'x' * 600, line('nan'), b'\xff\xfe,1,1,1,1,1,1,1', line(0.3)]
        a = LineAdapter(lines, DeviceInfo('测试设备'))
        got = drain(a)
        self.assertEqual([s.t_s for s in got], [0.0, 0.3])
        kinds = a.anomalies.by_kind
        self.assertEqual(kinds['field_count'], 2)
        self.assertEqual(kinds['invalid'], 4)
        self.assertEqual(kinds['line_too_long'], 1)
        self.assertEqual(kinds['time_order'], 1)
        self.assertEqual(a.anomalies.total, 8)

    def test_equal_time_rejected_and_state_kept(self):
        a = LineAdapter([line(1), line(1), line(2)], DeviceInfo('d'))
        self.assertEqual([s.t_s for s in drain(a)], [1.0, 2.0])
        self.assertEqual(a.anomalies.by_kind, {'time_order': 1})

    def test_drain_is_bounded(self):
        a = LineAdapter((line(i) for i in range(1000)), DeviceInfo('d'))
        self.assertEqual(len(drain(a, 100)), 100)
        self.assertFalse(a.finished)
        self.assertEqual(len(drain(a, 5000)), 900)
        self.assertTrue(a.finished)
        self.assertIsNone(a.read())

    def test_adapter_has_no_write_path(self):
        for cls in (SensorAdapter, SimulatedAdapter, LineAdapter):
            for name in ('write', 'send', 'command', 'set_output'):
                self.assertFalse(hasattr(cls, name), (cls, name))
        with self.assertRaises(NotImplementedError):
            SensorAdapter().read()

    def test_device_info_roundtrip_unknown_stays_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            info = DeviceInfo('桌面 IMU 板', note='未校准')
            write_device_info(d, info)
            self.assertEqual(read_device_info(d), info)
            self.assertEqual(info.serial, '未知')
            self.assertIn('桌面 IMU 板', (Path(d) / 'device.json').read_text(encoding='utf-8'))

    def test_anomaly_log_cap_and_save(self):
        log = AnomalyLog(limit=3)
        for i in range(5):
            log.add('invalid', f'第 {i} 条')
        self.assertEqual((len(log.entries), log.total), (3, 5))
        with tempfile.TemporaryDirectory() as d:
            path = log.save(d)
            with path.open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.reader(f))
        self.assertEqual(rows[0], ['local_time', 'kind', 'detail'])
        self.assertEqual([r[2] for r in rows[1:4]], ['第 2 条', '第 3 条', '第 4 条'])
        self.assertEqual(rows[4][1:], ['truncated', '仅保留最近 3 条，共 5 条'])

    def test_adapter_into_session(self):
        with tempfile.TemporaryDirectory() as d:
            a = LineAdapter([line(0), 'bad', line(0.05), line(0.1)], DeviceInfo('测试设备', serial='SN-1'))
            session = SessionWriter(d)
            write_device_info(session.directory, a.info)
            for s in drain(a):
                session.append(s)
            session.event('适配器流结束')
            session.close()
            a.anomalies.save(session.directory)
            self.assertEqual([s.t_s for s in load_csv(session.directory / 'samples.csv')], [0.0, 0.05, 0.1])
            self.assertEqual(read_device_info(session.directory).serial, 'SN-1')
            self.assertTrue((session.directory / 'anomalies.csv').exists())


if __name__ == '__main__':
    unittest.main()
