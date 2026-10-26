"""Tests for preserving pipeline errors when manifest writes fail."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
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


if __name__ == '__main__':
    unittest.main()
