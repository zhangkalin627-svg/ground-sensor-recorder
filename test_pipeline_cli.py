"""Tests for the one-command replay -> channel -> drift workflow (v0.30.0)."""
import contextlib
import hashlib
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
            manifest = json.loads((output / 'pipeline_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['pipeline_version'], pipeline_report.VERSION)
            self.assertEqual(manifest['status'], 'completed')
            self.assertEqual(manifest['inputs']['baseline']['sha256'],
                             hashlib.sha256(baseline.read_bytes()).hexdigest())
            self.assertEqual(manifest['inputs']['candidate']['size_bytes'], candidate.stat().st_size)
            self.assertEqual(manifest['options']['expected_interval_s'], 0.05)
            self.assertEqual(manifest['flagged_channels'], ['ax_m_s2'])
            self.assertEqual(manifest['exit_code'], 2)
            self.assertNotIn(str(Path(d).resolve()), (output / 'pipeline_manifest.json').read_text(encoding='utf-8'))

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
            manifest = json.loads((output / 'pipeline_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'completed')
            self.assertEqual(manifest['exit_code'], 0)

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
            rc, _, err = run(pipeline_report.main, [baseline, candidate, '--out', output,
                                                    '--expected-interval', '0'])
            self.assertEqual(rc, 1)
            self.assertIn('阶段 preflight', err)
            self.assertFalse(output.exists())

    def test_directory_input_is_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d) / 'baseline-directory'
            baseline.mkdir()
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'directory-input-run'
            rc, _, err = run(pipeline_report.main, [baseline, candidate, '--out', output])
            self.assertEqual(rc, 1)
            self.assertIn('阶段 preflight', err)
            self.assertIn('不是普通文件', err)
            self.assertFalse(output.exists())

    def test_oversized_input_is_rejected_before_hashing_or_output_creation(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = Path(d) / 'oversized.txt'
            with baseline.open('wb') as handle:
                handle.truncate(pipeline_report.MAX_INPUT_BYTES + 1)
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'oversized-run'
            rc, _, err = run(pipeline_report.main, [baseline, candidate, '--out', output])
            self.assertEqual(rc, 1)
            self.assertIn('阶段 preflight', err)
            self.assertIn('超过 50 MB 限制', err)
            self.assertFalse(output.exists())

    def test_file_identity_handles_input_larger_than_one_hash_block(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / 'multi-block.bin'
            payload = b'ground-sensor-recorder\n' * 50000
            source.write_bytes(payload)
            identity = pipeline_report.file_identity(source)
            self.assertEqual(identity['size_bytes'], len(payload))
            self.assertEqual(identity['sha256'], hashlib.sha256(payload).hexdigest())

    def test_output_permission_failure_is_reported_without_manifest(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'denied-output'
            original_mkdir = Path.mkdir

            def deny_output(path, *args, **kwargs):
                if path == output:
                    raise PermissionError('synthetic output permission denied')
                return original_mkdir(path, *args, **kwargs)

            with patch.object(Path, 'mkdir', autospec=True, side_effect=deny_output):
                rc, _, err = run(pipeline_report.main, [baseline, candidate, '--out', output])
            self.assertEqual(rc, 1)
            self.assertIn('阶段 create_output_directory', err)
            self.assertIn('synthetic output permission denied', err)
            self.assertFalse(output.exists())

    def test_candidate_replay_failure_records_stage_and_partial_outputs(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'failed-run'
            real_import = pipeline_report.replay_session.import_lines

            def fail_candidate(source, out_dir):
                if Path(source).name == candidate.name:
                    raise ValueError('synthetic candidate failure')
                return real_import(source, out_dir)

            with patch('pipeline_report.replay_session.import_lines', side_effect=fail_candidate):
                rc, _, err = run(pipeline_report.main, [baseline, candidate, '--out', output])
            self.assertEqual(rc, 1)
            self.assertIn('阶段 candidate_replay', err)
            manifest = json.loads((output / 'pipeline_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'failed')
            self.assertEqual(manifest['failure_stage'], 'candidate_replay')
            self.assertEqual(manifest['error_type'], 'ValueError')
            self.assertIn('baseline.json', manifest['partial_outputs'])
            self.assertNotIn('candidate.json', manifest['partial_outputs'])
            self.assertNotIn(str(candidate.resolve()), json.dumps(manifest))

    def test_drift_failure_records_completed_reports(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt', offset=1.0)
            output = Path(d) / 'drift-failed'
            with patch('pipeline_report.drift_report.compare', side_effect=RuntimeError('synthetic drift failure')):
                rc, _, err = run(pipeline_report.main, [baseline, candidate, '--out', output])
            self.assertEqual(rc, 1)
            self.assertIn('阶段 drift_comparison', err)
            manifest = json.loads((output / 'pipeline_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['failure_stage'], 'drift_comparison')
            self.assertEqual(manifest['error_type'], 'RuntimeError')
            self.assertIn('baseline.json', manifest['partial_outputs'])
            self.assertIn('candidate.json', manifest['partial_outputs'])
            self.assertNotIn('drift.json', manifest['partial_outputs'])

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
