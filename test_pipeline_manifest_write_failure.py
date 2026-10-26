"""Tests for preserving pipeline errors and protecting manifest paths (v0.33.0)."""
import contextlib
import io
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


if __name__ == '__main__':
    unittest.main()
