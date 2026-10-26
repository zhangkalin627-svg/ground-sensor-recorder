"""Boundary tests for LineAdapter.MAX_LINE."""
import unittest

from adapters import MAX_LINE, DeviceInfo, LineAdapter


def valid_line():
    return '0,0.1,0.2,9.81,1,2,3,101325'


def padded_sample(length):
    sample = valid_line()
    return sample.replace(',', ' ' * (length - len(sample)) + ',', 1)


class LineLengthBoundaryTests(unittest.TestCase):
    def test_exact_limit_is_accepted(self):
        text = padded_sample(MAX_LINE)
        self.assertEqual(len(text), MAX_LINE)
        adapter = LineAdapter([text], DeviceInfo('fixture'))

        sample = adapter.read()

        self.assertIsNotNone(sample)
        self.assertEqual(sample.t_s, 0.0)
        self.assertEqual(adapter.anomalies.total, 0)

    def test_one_character_over_limit_is_logged(self):
        text = padded_sample(MAX_LINE + 1)
        self.assertEqual(len(text), MAX_LINE + 1)
        adapter = LineAdapter([text], DeviceInfo('fixture'))

        self.assertIsNone(adapter.read())
        self.assertEqual(adapter.anomalies.by_kind, {'line_too_long': 1})
        self.assertEqual(adapter.anomalies.total, 1)
        self.assertFalse(adapter.finished)


if __name__ == '__main__':
    unittest.main()
