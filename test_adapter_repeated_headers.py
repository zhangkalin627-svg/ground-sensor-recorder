"""Regression coverage for bounded repeated-header reads in line adapters."""
import itertools
import unittest

from adapters import (MAX_HEADER_SKIPS_PER_READ, DeviceInfo, LineAdapter, drain)
from recorder import FIELDS


class CountingLines:
    def __init__(self, lines):
        self._lines = iter(lines)
        self.reads = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.reads += 1
        return next(self._lines)


class RepeatedHeaderTests(unittest.TestCase):
    def test_many_repeated_headers_are_skipped_without_recursion(self):
        header = ','.join(FIELDS)
        sample_line = '0,0.1,0.2,9.81,1,2,3,101325'
        adapter = LineAdapter([header] * 1500 + [sample_line], DeviceInfo('fixture'))

        samples = drain(adapter, max_reads=10)

        self.assertEqual([sample.t_s for sample in samples], [0.0])
        self.assertTrue(adapter.finished)
        self.assertEqual(adapter.anomalies.total, 0)

    def test_exact_header_skip_limit_defers_next_line_to_next_read(self):
        header = ','.join(FIELDS)
        sample_line = '0,0.1,0.2,9.81,1,2,3,101325'
        lines = CountingLines([header] * MAX_HEADER_SKIPS_PER_READ + [sample_line])
        adapter = LineAdapter(lines, DeviceInfo('fixture'))

        self.assertIsNone(adapter.read())
        self.assertEqual(lines.reads, MAX_HEADER_SKIPS_PER_READ)
        self.assertFalse(adapter.finished)
        sample = adapter.read()
        self.assertEqual(sample.t_s, 0.0)
        self.assertEqual(lines.reads, MAX_HEADER_SKIPS_PER_READ + 1)
        self.assertEqual(adapter.anomalies.total, 0)

    def test_one_header_over_limit_is_skipped_on_following_read(self):
        header = ','.join(FIELDS)
        sample_line = '0,0.1,0.2,9.81,1,2,3,101325'
        lines = CountingLines([header] * (MAX_HEADER_SKIPS_PER_READ + 1) + [sample_line])
        adapter = LineAdapter(lines, DeviceInfo('fixture'))

        self.assertIsNone(adapter.read())
        self.assertEqual(lines.reads, MAX_HEADER_SKIPS_PER_READ)
        sample = adapter.read()
        self.assertEqual(sample.t_s, 0.0)
        self.assertEqual(lines.reads, MAX_HEADER_SKIPS_PER_READ + 2)
        self.assertEqual(adapter.anomalies.total, 0)

    def test_drain_with_unending_headers_is_bounded_per_tick(self):
        header = ','.join(FIELDS)
        lines = CountingLines(itertools.repeat(header))
        adapter = LineAdapter(lines, DeviceInfo('fixture'))

        self.assertEqual(drain(adapter, max_reads=2), [])
        self.assertEqual(lines.reads, 2 * MAX_HEADER_SKIPS_PER_READ)
        self.assertFalse(adapter.finished)
        self.assertEqual(adapter.anomalies.total, 0)


if __name__ == '__main__':
    unittest.main()
