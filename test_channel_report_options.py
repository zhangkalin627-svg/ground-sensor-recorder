"""Tests for --expected-interval / --gap-factor (added after v0.18.1)."""
import unittest
from types import SimpleNamespace

import channel_report as cr


def make_samples(times):
    return [SimpleNamespace(t_s=t, **{c: float(i) for c in cr.CHANNELS})
            for i, t in enumerate(times)]


def times_with_one_gap():
    t, out = 0.0, []
    for i in range(30):
        out.append(t)
        t += 0.05 if i == 14 else 0.01
    return out


class DefaultsUnchanged(unittest.TestCase):
    def test_default_is_median_x5(self):
        iv = cr.interval_stats(times_with_one_gap())
        self.assertEqual(iv['gap_basis'], 'median')
        self.assertEqual(iv['gap_factor'], 5.0)
        self.assertAlmostEqual(iv['gap_threshold_s'], 0.05, places=9)
        self.assertEqual(iv['gap_count'], 0)  # 0.05 is not > 0.05

    def test_median_mode_factor_override(self):
        iv = cr.interval_stats(times_with_one_gap(), gap_factor=3)
        self.assertEqual(iv['gap_count'], 1)


class ExpectedInterval(unittest.TestCase):
    def test_expected_default_factor_1_5(self):
        iv = cr.interval_stats(times_with_one_gap(), expected_interval=0.01)
        self.assertEqual(iv['gap_basis'], 'expected')
        self.assertEqual(iv['gap_factor'], 1.5)
        self.assertAlmostEqual(iv['gap_threshold_s'], 0.015, places=9)
        self.assertEqual(iv['gap_count'], 1)

    def test_expected_with_factor(self):
        iv = cr.interval_stats(times_with_one_gap(), gap_factor=6, expected_interval=0.01)
        self.assertEqual(iv['gap_count'], 0)

    def test_report_text_mentions_expected(self):
        rep = cr.build_report(make_samples(times_with_one_gap()), expected_interval=0.01)
        self.assertIn('预期周期', cr.report_text(rep))

    def test_short_input_keeps_options(self):
        iv = cr.interval_stats([0.0], expected_interval=0.01)
        self.assertEqual(iv['gap_count'], 0)
        self.assertEqual(iv['gap_basis'], 'expected')


class Validation(unittest.TestCase):
    def test_bad_values_rejected(self):
        for kw in ({'expected_interval': 0}, {'expected_interval': -1},
                   {'expected_interval': float('nan')}, {'gap_factor': 1},
                   {'gap_factor': 0.5}, {'gap_factor': float('inf')}):
            with self.assertRaises(ValueError):
                cr.interval_stats([0.0, 1.0, 2.0], **kw)

    def test_main_rejects_bad_option_before_reading(self):
        self.assertEqual(cr.main(['no_such.csv', '--gap-factor', '1']), 1)
        self.assertEqual(cr.main(['no_such.csv', '--expected-interval', '0']), 1)


if __name__ == '__main__':
    unittest.main()
