"""Bounded-read edge coverage for LineAdapter (v0.50.0)."""
import unittest

from adapters import DeviceInfo, LineAdapter, drain
from recorder import FIELDS


def line(t):
    return f'{t},0.1,0.2,9.81,1,2,3,101325'


class AdapterReadBoundsTests(unittest.TestCase):
    def test_blank_line_consumes_one_read_and_does_not_hide_sample(self):
        adapter = LineAdapter(['\n', line(0.0)], DeviceInfo('fixture'))

        self.assertIsNone(adapter.read())
        self.assertFalse(adapter.finished)
        sample = adapter.read()
        self.assertEqual(sample.t_s, 0.0)
        self.assertEqual(adapter.anomalies.total, 0)

    def test_bad_lines_are_counted_once_per_read(self):
        adapter = LineAdapter(['bad,1', 'still,bad', line(0.0)], DeviceInfo('fixture'))

        self.assertIsNone(adapter.read())
        self.assertEqual(adapter.anomalies.by_kind['field_count'], 1)
        self.assertIsNone(adapter.read())
        self.assertEqual(adapter.anomalies.by_kind['field_count'], 2)
        self.assertEqual(adapter.read().t_s, 0.0)
        self.assertEqual(adapter.anomalies.total, 2)

    def test_drain_read_budget_handles_long_bad_prefix(self):
        bad = 'bad,1'
        adapter = LineAdapter([bad] * 1001 + [line(0.0)], DeviceInfo('fixture'))

        self.assertEqual(drain(adapter, max_reads=100), [])
        self.assertEqual(adapter.anomalies.by_kind['field_count'], 100)
        self.assertFalse(adapter.finished)

        self.assertEqual(drain(adapter, max_reads=900), [])
        self.assertEqual(adapter.anomalies.by_kind['field_count'], 1000)
        self.assertFalse(adapter.finished)

        samples = drain(adapter, max_reads=10)
        self.assertEqual([sample.t_s for sample in samples], [0.0])
        self.assertEqual(adapter.anomalies.by_kind['field_count'], 1001)
        self.assertTrue(adapter.finished)


if __name__ == '__main__':
    unittest.main()
