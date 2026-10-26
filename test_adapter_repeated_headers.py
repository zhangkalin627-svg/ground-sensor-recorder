"""Regression coverage for repeated headers in read-only line adapters."""
import unittest

from adapters import DeviceInfo, LineAdapter, drain
from recorder import FIELDS


class RepeatedHeaderTests(unittest.TestCase):
    def test_many_repeated_headers_are_skipped_without_recursion(self):
        header = ','.join(FIELDS)
        sample_line = '0,0.1,0.2,9.81,1,2,3,101325'
        adapter = LineAdapter([header] * 1500 + [sample_line], DeviceInfo('fixture'))

        samples = drain(adapter, max_reads=10)

        self.assertEqual([sample.t_s for sample in samples], [0.0])
        self.assertTrue(adapter.finished)
        self.assertEqual(adapter.anomalies.total, 0)


if __name__ == '__main__':
    unittest.main()
