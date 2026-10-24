import contextlib
import copy
import io
import json
import os
import tempfile
import unittest

import drift_report as dr


def channel(count=100, mean=10.0, std=1.0, lo=5.0, hi=15.0):
    return {'count': count, 'mean': mean, 'std': std, 'min': lo, 'max': hi,
            'peak_to_peak': hi - lo}


def report(**channels):
    if not channels:
        channels = {'temp': channel(), 'pressure': channel(mean=100.0, std=2.0, lo=90.0, hi=110.0)}
    return {'version': '0.19.0', 'sample_count': 100, 'duration_s': 99.0,
            'intervals': {'median_s': 1.0, 'gap_count': 0}, 'channels': channels}


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dr.main(argv)
    return code, out.getvalue(), err.getvalue()


class CompareTests(unittest.TestCase):
    def test_identical_reports_have_no_drift(self):
        result = dr.compare(report(), report())
        self.assertEqual(result['flagged_channels'], [])
        self.assertTrue(all(c['status'] == 'ok' for c in result['channels'].values()))

    def test_relative_threshold_flags_channel(self):
        cand = report()
        cand['channels']['temp']['mean'] = 12.0
        result = dr.compare(report(), cand)
        self.assertEqual(result['flagged_channels'], ['temp'])
        self.assertTrue(result['channels']['temp']['changes']['mean']['drift'])
        self.assertEqual(result['channels']['pressure']['status'], 'ok')

    def test_change_equal_to_threshold_is_not_drift(self):
        cand = report()
        cand['channels']['temp']['mean'] = 11.0
        result = dr.compare(report(), cand, max_rel_change=0.1)
        self.assertFalse(result['channels']['temp']['changes']['mean']['drift'])

    def test_absolute_threshold_flags_small_relative_change(self):
        base = report(a=channel(mean=1000.0))
        cand = report(a=channel(mean=1010.0))
        self.assertEqual(dr.compare(base, cand)['flagged_channels'], [])
        flagged = dr.compare(base, cand, max_abs_change=5)['flagged_channels']
        self.assertEqual(flagged, ['a'])

    def test_zero_baseline_any_change_is_drift(self):
        base = report(a=channel(mean=0.0))
        cand = report(a=channel(mean=0.001))
        result = dr.compare(base, cand)
        self.assertIsNone(result['channels']['a']['changes']['mean']['rel_change'])
        self.assertEqual(result['flagged_channels'], ['a'])

    def test_mismatched_channels_raise(self):
        cand = report()
        del cand['channels']['pressure']
        with self.assertRaises(ValueError) as ctx:
            dr.compare(report(), cand)
        self.assertIn('pressure', str(ctx.exception))

    def test_missing_metric_raises(self):
        cand = report()
        del cand['channels']['temp']['std']
        with self.assertRaises(ValueError):
            dr.compare(report(), cand)

    def test_non_numeric_and_bool_values_raise(self):
        for bad in ('x', True, None, float('nan'), float('inf')):
            cand = report()
            cand['channels']['temp']['mean'] = bad
            with self.assertRaises(ValueError):
                dr.compare(report(), cand)

    def test_bad_options_raise(self):
        for rel, ab in ((-0.1, None), (float('nan'), None), (True, None), (0.1, 0), (0.1, -1), (0.1, 'x')):
            with self.assertRaises(ValueError):
                dr.compare(report(), report(), rel, ab)

    def test_interval_deltas(self):
        cand = report()
        cand['sample_count'] = 150
        cand['intervals']['gap_count'] = 2
        result = dr.compare(report(), cand)
        self.assertEqual(result['intervals']['sample_count']['delta'], 50.0)
        self.assertEqual(result['intervals']['gap_count']['delta'], 2.0)
        self.assertEqual(result['intervals']['median_s']['delta'], 0.0)

    def test_missing_interval_value_gives_none(self):
        cand = report()
        del cand['duration_s']
        result = dr.compare(report(), cand)
        self.assertIsNone(result['intervals']['duration_s']['delta'])

    def test_inputs_not_modified(self):
        base, cand = report(), report()
        cand['channels']['temp']['mean'] = 20.0
        before = copy.deepcopy((base, cand))
        dr.compare(base, cand)
        self.assertEqual((base, cand), before)

    def test_text_mentions_flagged_channel(self):
        cand = report()
        cand['channels']['temp']['mean'] = 20.0
        text = dr.drift_text(dr.compare(report(), cand))
        self.assertIn('漂移通道：temp', text)
        self.assertEqual(dr.drift_text(dr.compare(report(), report())).count('没有通道超过阈值'), 1)


class ValidateTests(unittest.TestCase):
    def test_validate_rejects_bad_shapes(self):
        for bad in ([], {'channels': {}}, {'channels': {}, 'intervals': {}},
                    {'channels': [], 'intervals': {}, 'sample_count': 1}):
            with self.assertRaises(ValueError):
                dr.validate_report(bad)

    def test_validate_accepts_report(self):
        self.assertIs(dr.validate_report(report()) is not None, True)


class CommandLineTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.base = self.write('base.json', report())
        drifted = report()
        drifted['channels']['temp']['mean'] = 20.0
        self.drifted = self.write('cand.json', drifted)

    def write(self, name, data):
        path = os.path.join(self.dir.name, name)
        with open(path, 'w', encoding='utf-8') as handle:
            json.dump(data, handle)
        return path

    def test_no_drift_exit_zero(self):
        code, out, err = run_main([self.base, self.base, '--strict'])
        self.assertEqual(code, 0)
        self.assertIn('没有通道超过阈值', out)

    def test_drift_exit_codes(self):
        self.assertEqual(run_main([self.base, self.drifted])[0], 0)
        self.assertEqual(run_main([self.base, self.drifted, '--strict'])[0], 2)

    def test_json_output_written_and_not_overwritten(self):
        target = os.path.join(self.dir.name, 'drift.json')
        code, out, err = run_main([self.base, self.drifted, '--json', target])
        self.assertEqual(code, 0)
        with open(target, encoding='utf-8') as handle:
            self.assertEqual(json.load(handle)['flagged_channels'], ['temp'])
        with open(target, 'w', encoding='utf-8') as handle:
            handle.write('keep')
        code, out, err = run_main([self.base, self.drifted, '--json', target])
        self.assertEqual(code, 1)
        with open(target, encoding='utf-8') as handle:
            self.assertEqual(handle.read(), 'keep')

    def test_inputs_unchanged(self):
        with open(self.base, 'rb') as handle:
            before = handle.read()
        run_main([self.base, self.drifted])
        with open(self.base, 'rb') as handle:
            self.assertEqual(handle.read(), before)

    def test_missing_file_and_bad_json_fail_with_code_1(self):
        code, out, err = run_main([self.base, os.path.join(self.dir.name, 'nope.json')])
        self.assertEqual(code, 1)
        self.assertIn('失败', err)
        bad = os.path.join(self.dir.name, 'bad.json')
        with open(bad, 'w', encoding='utf-8') as handle:
            handle.write('{not json')
        self.assertEqual(run_main([self.base, bad])[0], 1)


if __name__ == '__main__':
    unittest.main()
