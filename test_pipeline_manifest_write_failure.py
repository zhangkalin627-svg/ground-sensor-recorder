"""Tests for preserving pipeline errors and protecting manifest paths (v0.34.0)."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pipeline_report
from recorder import FIELDS


def make_log(path):
    rows = [','.join(FIELDS)]
    for i in range(100):
        t = i * 0.05
        rows.append(f'{t:.3f},0.1,0.2,9.81,1,2,3,101325')
    path = Path(path)
    path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return path


class FailureManifestWriteTests(unittest.TestCase):
    def test_manifest_write_error_does_not_hide_replay_error(self):
        with tempfile.TemporaryDirectory() as d:
            source = make_log(Path(d) / 'input.txt')
            output = Path(d) / 'run'
            stdout, stderr = io.StringIO(), io.StringIO()
            with patch('pipeline_report.replay_session.import_lines',
                       side_effect=ValueError('synthetic replay error')), \
                 patch('pipeline_report.write_manifest',
                       side_effect=OSError('synthetic manifest write error')), \
                 contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                rc = pipeline_report.main([str(source), str(source), '--out', str(output)])

            self.assertEqual(rc, 1)
            self.assertIn('阶段 baseline_replay', stderr.getvalue())
            self.assertIn('synthetic replay error', stderr.getvalue())
            self.assertIn('失败清单未能写入', stderr.getvalue())
            self.assertFalse((output / 'pipeline_manifest.json').exists())

    def test_partial_failure_manifest_is_removed_and_primary_error_remains(self):
        with tempfile.TemporaryDirectory() as d:
            source = make_log(Path(d) / 'input.txt')
            output = Path(d) / 'run'
            stderr = io.StringIO()

            def fail_after_partial_write(value, handle, *args, **kwargs):
                handle.write('{"partial":')
                raise OSError('synthetic manifest serialization failure')

            with patch('pipeline_report.replay_session.import_lines',
                       side_effect=ValueError('synthetic replay error')), \
                 patch('pipeline_report.json.dump', side_effect=fail_after_partial_write), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                rc = pipeline_report.main([str(source), str(source), '--out', str(output)])

            self.assertEqual(rc, 1)
            self.assertIn('阶段 baseline_replay', stderr.getvalue())
            self.assertIn('synthetic replay error', stderr.getvalue())
            self.assertIn('失败清单未能写入', stderr.getvalue())
            self.assertFalse((output / 'pipeline_manifest.json').exists())

    def test_existing_manifest_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'pipeline_manifest.json'
            original = '{"keep": true}\n'
            target.write_text(original, encoding='utf-8')

            with self.assertRaises(FileExistsError):
                pipeline_report.write_manifest({'replace': True}, target)

            self.assertEqual(target.read_text(encoding='utf-8'), original)

    def test_partial_file_is_preserved_when_path_identity_differs(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'pipeline_manifest.json'

            def fail_after_partial_write(value, handle, *args, **kwargs):
                handle.write('{"partial":')
                raise OSError('synthetic interrupted write')

            different_identity = SimpleNamespace(st_dev=123, st_ino=456)
            with patch('pipeline_report.json.dump', side_effect=fail_after_partial_write), \
                 patch('pathlib.Path.lstat', return_value=different_identity):
                with self.assertRaisesRegex(OSError, 'synthetic interrupted write'):
                    pipeline_report.write_manifest({'status': 'complete'}, target)

            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding='utf-8'), '{"partial":')

    def test_permission_denied_open_leaves_no_manifest_file(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / 'pipeline_manifest.json'
            with patch('pipeline_report.os.open',
                       side_effect=PermissionError('synthetic manifest permission denied')):
                with self.assertRaisesRegex(PermissionError, 'synthetic manifest permission denied'):
                    pipeline_report.write_manifest({'status': 'completed'}, target)
            self.assertFalse(target.exists())

    def test_success_manifest_open_failure_is_recorded_as_failed_run(self):
        with tempfile.TemporaryDirectory() as d:
            baseline = make_log(Path(d) / 'baseline.txt')
            candidate = make_log(Path(d) / 'candidate.txt')
            output = Path(d) / 'run'
            stderr = io.StringIO()
            real_open = pipeline_report.os.open
            manifest_attempts = [0]

            def deny_first_manifest_open(path, flags, *args, **kwargs):
                if Path(path).name == 'pipeline_manifest.json':
                    manifest_attempts[0] += 1
                    if manifest_attempts[0] == 1:
                        raise PermissionError('synthetic success manifest permission denied')
                return real_open(path, flags, *args, **kwargs)

            with patch('pipeline_report.os.open', side_effect=deny_first_manifest_open), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                rc = pipeline_report.main([str(baseline), str(candidate), '--out', str(output)])

            self.assertEqual(rc, 1)
            self.assertEqual(manifest_attempts[0], 2)
            self.assertIn('阶段 write_success_manifest', stderr.getvalue())
            self.assertIn('synthetic success manifest permission denied', stderr.getvalue())
            manifest = json.loads((output / 'pipeline_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['status'], 'failed')
            self.assertEqual(manifest['failure_stage'], 'write_success_manifest')
            self.assertEqual(manifest['error_type'], 'PermissionError')
            self.assertEqual(manifest['exit_code'], 1)

    def test_primary_error_remains_when_failure_manifest_open_is_denied(self):
        with tempfile.TemporaryDirectory() as d:
            source = make_log(Path(d) / 'input.txt')
            output = Path(d) / 'run'
            stderr = io.StringIO()
            real_open = pipeline_report.os.open

            def deny_manifest_open(path, flags, *args, **kwargs):
                if Path(path).name == 'pipeline_manifest.json':
                    raise PermissionError('synthetic failure manifest permission denied')
                return real_open(path, flags, *args, **kwargs)

            with patch('pipeline_report.replay_session.import_lines',
                       side_effect=ValueError('synthetic replay error')), \
                 patch('pipeline_report.os.open', side_effect=deny_manifest_open), \
                 contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                rc = pipeline_report.main([str(source), str(source), '--out', str(output)])

            self.assertEqual(rc, 1)
            self.assertIn('阶段 baseline_replay', stderr.getvalue())
            self.assertIn('synthetic replay error', stderr.getvalue())
            self.assertIn('失败清单未能写入', stderr.getvalue())
            self.assertFalse((output / 'pipeline_manifest.json').exists())


if __name__ == '__main__':
    unittest.main()
