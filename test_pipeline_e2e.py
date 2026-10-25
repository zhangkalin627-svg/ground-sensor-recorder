"""End-to-end chain without a display: replay_session -> channel_report -> drift_report (v0.24.0).

Uses only temporary files. Each step runs through its own main(), and one test
runs the same chain through workbench.py in subprocesses.
"""
import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import channel_report
import drift_report
import replay_session
from recorder import FIELDS

HERE = Path(__file__).resolve().parent


def line(t, ax=0.1, p=101325):
    return f'{t},{ax},0.2,9.81,1,2,3,{p}'


def clean_times(n=100):
    return [round(i * 0.05, 3) for i in range(n)]


def make_log(d, name, times, ax_offset=0.0, extra=()):
    rows = [','.join(FIELDS)]
    for i, t in enumerate(times):
        rows.append(line(t, ax=round(0.1 + (i % 10) * 0.01 + ax_offset, 4)))
    rows.extend(extra)
    path = Path(d) / name
    path.write_text('\n'.join(rows) + '\n', encoding='utf-8')
    return path


def run(main, argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main([str(a) for a in argv])
    return rc, out.getvalue(), err.getvalue()


def replay(d, log):
    sessions = Path(d) / ('s_' + log.stem)
    rc, out, err = run(replay_session.main, [log, '--out', sessions])
    assert rc == 0, err
    found = list(sessions.glob('*/samples.csv'))
    assert len(found) == 1, found
    return found[0], out


def report(d, csv_path, name, *extra):
    path = Path(d) / f'{name}.json'
    rc, out, err = run(channel_report.main, [csv_path, '--json', path, *extra])
    assert rc == 0, err
    return path, json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PipelineE2ETests(unittest.TestCase):
    def test_clean_log_has_no_gaps(self):
        with tempfile.TemporaryDirectory() as d:
            csv_path, out = replay(d, make_log(d, 'a.txt', clean_times()))
            self.assertIn('有效样本 100 条', out)
            _, rep = report(d, csv_path, 'a', '--expected-interval', '0.05')
            self.assertEqual(rep['sample_count'], 100)
            self.assertEqual(rep['intervals']['gap_count'], 0)
            self.assertEqual(set(rep['channels']), set(channel_report.CHANNELS))

    def test_gap_in_log_is_found(self):
        with tempfile.TemporaryDirectory() as d:
            times = clean_times(50) + [round(3.45 + i * 0.05, 3) for i in range(50)]
            csv_path, _ = replay(d, make_log(d, 'gap.txt', times))
            _, rep = report(d, csv_path, 'gap', '--expected-interval', '0.05')
            self.assertEqual(rep['intervals']['gap_count'], 1)
            self.assertAlmostEqual(rep['intervals']['gaps'][0]['duration_s'], 1.0, places=6)
            _, median_rep = report(d, csv_path, 'gap_median')
            self.assertEqual(median_rep['intervals']['gap_count'], 1)

    def test_same_data_shows_no_drift(self):
        with tempfile.TemporaryDirectory() as d:
            log = make_log(d, 'a.txt', clean_times())
            base, _ = report(d, replay(d, log)[0], 'base')
            cand, _ = report(d, replay(d, log)[0], 'cand')
            result = Path(d) / 'drift.json'
            rc, out, err = run(drift_report.main, [base, cand, '--strict', '--json', result])
            self.assertEqual(rc, 0, err)
            self.assertEqual(json.loads(result.read_text(encoding='utf-8'))['flagged_channels'], [])
            self.assertIn('没有通道超过阈值', out)

    def test_shifted_channel_is_flagged(self):
        with tempfile.TemporaryDirectory() as d:
            base, _ = report(d, replay(d, make_log(d, 'a.txt', clean_times()))[0], 'base')
            cand, _ = report(d, replay(d, make_log(d, 'b.txt', clean_times(), ax_offset=1.0))[0], 'cand')
            result = Path(d) / 'drift.json'
            rc, out, err = run(drift_report.main, [base, cand, '--strict', '--json', result])
            self.assertEqual(rc, 2, err)
            self.assertEqual(json.loads(result.read_text(encoding='utf-8'))['flagged_channels'], ['ax_m_s2'])
            self.assertIn('ax_m_s2', out)
            rc, _, _ = run(drift_report.main, [base, cand])
            self.assertEqual(rc, 0)

    def test_bad_lines_do_not_stop_the_chain(self):
        with tempfile.TemporaryDirectory() as d:
            log = make_log(d, 'bad.txt', clean_times(), extra=('junk', line(99.0, p=0)))
            csv_path, out = replay(d, log)
            self.assertIn('异常行 2 条', out)
            self.assertTrue((csv_path.parent / 'anomalies.csv').exists())
            _, rep = report(d, csv_path, 'bad')
            self.assertEqual(rep['sample_count'], 100)

    def test_inputs_are_not_modified_and_report_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            log = make_log(d, 'a.txt', clean_times())
            log_hash = sha(log)
            csv_path, _ = replay(d, log)
            csv_hash = sha(csv_path)
            path, _ = report(d, csv_path, 'r')
            report_hash = sha(path)
            rc, _, err = run(channel_report.main, [csv_path, '--json', path])
            self.assertEqual(rc, 1)
            self.assertIn('失败', err)
            self.assertEqual((sha(log), sha(csv_path), sha(path)), (log_hash, csv_hash, report_hash))

    def test_chain_through_workbench(self):
        def wb(*args):
            return subprocess.run([sys.executable, str(HERE / 'workbench.py'), *[str(a) for a in args]],
                                  capture_output=True, text=True, cwd=d, timeout=120)
        with tempfile.TemporaryDirectory() as d:
            logs = [make_log(d, 'a.txt', clean_times()),
                    make_log(d, 'b.txt', clean_times(), ax_offset=1.0)]
            reports = []
            for log in logs:
                r = wb('replay', log, '--out', Path(d) / ('s_' + log.stem))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn('有效样本 100 条', r.stdout)
                csv_path = next((Path(d) / ('s_' + log.stem)).glob('*/samples.csv'))
                out = Path(d) / (log.stem + '.json')
                r = wb('channel', csv_path, '--json', out)
                self.assertEqual(r.returncode, 0, r.stderr)
                reports.append(out)
            r = wb('drift', reports[0], reports[1], '--strict')
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn('漂移通道：ax_m_s2', r.stdout)


if __name__ == '__main__':
    unittest.main()
