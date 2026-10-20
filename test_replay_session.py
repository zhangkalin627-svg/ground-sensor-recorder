import contextlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import replay_session
from recorder import FIELDS, load_csv


def line(t, p=101325):
    return f'{t},0.1,0.2,9.81,1,2,3,{p}'


def write(d, text, name='log.txt', mode='w'):
    path = Path(d) / name
    if mode == 'wb':
        path.write_bytes(text)
    else:
        path.write_text(text, encoding='utf-8')
    return path


class ReplaySessionTests(unittest.TestCase):
    def test_good_file_saved(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, ','.join(FIELDS) + '\r\n' + '\r\n'.join(line(i / 20) for i in range(10)) + '\r\n')
            r = replay_session.import_lines(src, Path(d) / 'out', name='桌面板')
            self.assertEqual(len(r.samples), 10)
            self.assertEqual(r.anomalies.total, 0)
            self.assertEqual(load_csv(r.directory / 'samples.csv'), r.samples)
            info = json.loads((r.directory / 'device.json').read_text(encoding='utf-8'))
            self.assertEqual((info['name'], info['serial']), ('桌面板', '未知'))
            with (r.directory / 'anomalies.csv').open(encoding='utf-8-sig', newline='') as f:
                self.assertEqual(list(csv.reader(f)), [['local_time', 'kind', 'detail']])

    def test_bad_lines_logged_and_saved(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, '\n'.join([line(0), 'junk', line(0.1, p=0), line(0.0), line(0.2)]))
            r = replay_session.import_lines(src, Path(d) / 'out')
            self.assertEqual([s.t_s for s in r.samples], [0.0, 0.2])
            self.assertEqual(r.anomalies.by_kind, {'field_count': 1, 'invalid': 1, 'time_order': 1})
            with (r.directory / 'anomalies.csv').open(encoding='utf-8-sig', newline='') as f:
                self.assertEqual(len(list(csv.reader(f))), 4)
            self.assertIn('异常行 3 条', replay_session.summary_text(r))

    def test_no_out_base_writes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, line(0) + '\n' + line(1))
            r = replay_session.import_lines(src)
            self.assertIsNone(r.directory)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ['log.txt'])

    def test_no_usable_samples_raises(self):
        with tempfile.TemporaryDirectory() as d:
            for text in ('', 'a,b\n', ','.join(FIELDS) + '\n'):
                with self.assertRaises(ValueError):
                    replay_session.import_lines(write(d, text))

    def test_overlong_line_is_bounded(self):
        with tempfile.TemporaryDirectory() as d:
            data = line(0).encode() + b'\n' + b'9' * 5000 + b'\n' + line(1).encode() + b'\n' + b'8' * 700
            r = replay_session.import_lines(write(d, data, mode='wb'))
            self.assertEqual([s.t_s for s in r.samples], [0.0, 1.0])
            self.assertEqual(r.anomalies.by_kind, {'line_too_long': 2})

    def test_row_limit_and_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, '\n'.join(line(i) for i in range(10)))
            with mock.patch.object(replay_session, 'MAX_ROWS', 3):
                r = replay_session.import_lines(src)
            self.assertEqual(len(r.samples), 3)
            self.assertTrue(r.truncated)
            self.assertEqual(r.anomalies.by_kind, {'row_limit': 1})
            with mock.patch.object(replay_session, 'MAX_FILE_BYTES', 10):
                with self.assertRaises(ValueError):
                    replay_session.import_lines(src)

    def test_source_unchanged(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, line(0) + '\nbad\n' + line(1))
            before = src.read_bytes()
            replay_session.import_lines(src, Path(d) / 'out')
            self.assertEqual(src.read_bytes(), before)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            src = write(d, line(0) + '\n' + line(1))
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(replay_session.main([str(src), '--out', str(Path(d) / 'o')]), 0)
            self.assertIn('有效样本 2 条', out.getvalue())
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(replay_session.main([str(Path(d) / 'missing.txt')]), 1)
            self.assertIn('导入失败', err.getvalue())


if __name__ == '__main__':
    unittest.main()
