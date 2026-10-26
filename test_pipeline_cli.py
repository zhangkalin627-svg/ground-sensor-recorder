"""Tests for the one-command replay -> channel -> drift workflow (v0.25.0)."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import pipeline_report
import workbench
from recorder import FIELDS


def make_log(path, offset=0.0):
    rows = [','.join(FIELDS)]
    for i in range(100):
        t = i * 0.05
        ax = 0.1 + (i % 10) * 0.01 + offset
        rows.append(f'{t:.3f},{ax:.4f},0.2,9.81,1,2,3,101325')
    Path(path).write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return Path(path)


def run(main, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main([str(arg) for arg in argv])
    return rc, out.getvalue(), err.getvalue()


class PipelineCliTests(unittest.TestCase):
    def test_one_command_builds_reports_and_flags_drift(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt', offset=1.0)
            output = Path(d) / 'run'
            rc, text, err = run(pipeline_report.main, [baseline, candidate, '--out', output,
                                                        '--expected-interval', '0.05', '--strict'])
            self.assertEqual(rc, 2, err)
            self.assertIn('漂移通道：ax_m_s2', text)
            self.assertTrue((output / 'baseline.json').is_file())
            self.assertTrue((output / 'candidate.json').is_file())
            self.assertTrue((output / 'drift.json').is_file())
            self.assertEqual(json.loads((output / 'drift.json').read_text(encoding='utf-8'))
                             ['flagged_channels'], ['ax_m_s2'])
            self.assertEqual(len(list((output / 'baseline_sessions').glob('*/samples.csv'))), 1)
            self.assertEqual(len(list((output / 'candidate_sessions').glob('*/samples.csv'))), 1)

    def test_same_data_returns_clean_status(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'clean-run'
            rc, text, err = run(pipeline_report.main, [baseline, candidate, '--out', output, '--strict'])
            self.assertEqual(rc, 0, err)
            self.assertIn('没有通道超过阈值', text)
            self.assertEqual(json.loads((output / 'drift.json').read_text(encoding='utf-8'))
                             ['flagged_channels'], [])

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'existing'
            output.mkdir()
            marker = output / 'keep.txt'
            marker.write_text('keep', encoding='utf-8')
            rc, _, _ = run(pipeline_report.main, [baseline, candidate, '--out', output])
            self.assertEqual(rc, 1)
            self.assertEqual(marker.read_text(encoding='utf-8'), 'keep')
            self.assertFalse((output / 'baseline.json').exists())

    def test_invalid_sampling_period_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'invalid-run'
            rc, _, _ = run(pipeline_report.main, [baseline, candidate, '--out', output,
                                                  '--expected-interval', '0'])
            self.assertEqual(rc, 1)
            self.assertFalse(output.exists())

    def test_workbench_routes_pipeline_arguments(self):
        args = ['baseline.txt', 'candidate.txt', '--out', 'run-001', '--strict']
        with patch('workbench.subprocess.run',
                   return_value=subprocess.CompletedProcess([], 2)) as child:
            rc = workbench.main(['pipeline', *args])
        command = child.call_args.args[0]
        self.assertEqual(rc, 2)
        self.assertEqual(Path(command[1]).name, 'pipeline_report.py')
        self.assertEqual(command[2:], args)


if __name__ == '__main__':
    unittest.main()