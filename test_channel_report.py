import json
import math
import os
import tempfile
import unittest
from collections import namedtuple

import channel_report as cr

S = namedtuple('S', 't_s ax_m_s2 ay_m_s2 az_m_s2 gx_deg_s gy_deg_s gz_deg_s pressure_pa')


def make(times, f=lambda t: 1.0):
    return [S(t, f(t), 0.0, 9.81, 0.0, 0.0, 0.0, 101325.0) for t in times]


class IntervalTests(unittest.TestCase):
    def test_uniform_has_no_gaps(self):
        iv = cr.interval_stats([i * 0.05 for i in range(100)])
        self.assertEqual(iv['gap_count'], 0)
        self.assertAlmostEqual(iv['median_s'], 0.05)

    def test_gap_detected(self):
        times = [i * 0.05 for i in range(10)] + [2.0 + i * 0.05 for i in range(10)]
        iv = cr.interval_stats(times)
        self.assertEqual(iv['gap_count'], 1)
        self.assertAlmostEqual(iv['gaps'][0]['start_s'], 0.45)
        self.assertAlmostEqual(iv['gaps'][0]['duration_s'], 1.55)

    def test_non_increasing_rejected(self):
        with self.assertRaises(ValueError):
            cr.interval_stats([0.0, 0.1, 0.1])

    def test_single_sample(self):
        self.assertEqual(cr.interval_stats([0.0])['gap_count'], 0)

    def test_gap_list_is_bounded(self):
        times, t = [], 0.0
        for i in range(400):
            t += 10.0 if i % 4 == 3 else 0.1
            times.append(t)
        iv = cr.interval_stats(times)
        self.assertEqual(len(iv['gaps']), cr.MAX_GAPS_LISTED)
        self.assertGreater(iv['gap_count'], cr.MAX_GAPS_LISTED)


class ChannelTests(unittest.TestCase):
    def test_extremes_mean_std(self):
        st = cr.channel_stats([0, 1, 2, 3], [1.0, 5.0, -2.0, 4.0])
        self.assertEqual(st['min'], -2.0)
        self.assertEqual(st['min_t_s'], 2)
        self.assertEqual(st['max'], 5.0)
        self.assertEqual(st['max_t_s'], 1)
        self.assertAlmostEqual(st['mean'], 2.0)
        self.assertAlmostEqual(st['peak_to_peak'], 7.0)
        self.assertAlmostEqual(st['std'], math.sqrt(((-1) ** 2 + 3 ** 2 + (-4) ** 2 + 2 ** 2) / 4))

    def test_rejects_nan_and_empty_and_mismatch(self):
        with self.assertRaises(ValueError):
            cr.channel_stats([0, 1], [1.0, float('nan')])
        with self.assertRaises(ValueError):
            cr.channel_stats([], [])
        with self.assertRaises(ValueError):
            cr.channel_stats([0], [1.0, 2.0])


class ReportTests(unittest.TestCase):
    def test_report_and_text(self):
        rep = cr.build_report(make([i * 0.05 for i in range(50)], lambda t: math.sin(t)))
        self.assertEqual(rep['sample_count'], 50)
        self.assertEqual(set(rep['channels']), set(cr.CHANNELS))
        self.assertIn('ax_m_s2', cr.report_text(rep))

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            cr.build_report([])

    def test_json_roundtrip_and_no_overwrite(self):
        rep = cr.build_report(make([i * 0.1 for i in range(5)]))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'r.json')
            cr.write_json(rep, p)
            with open(p, encoding='utf-8') as f:
                self.assertEqual(json.load(f)['sample_count'], 5)
            with self.assertRaises(FileExistsError):
                cr.write_json(rep, p)


if __name__ == '__main__':
    unittest.main()
