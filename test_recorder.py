import csv
import tempfile
import unittest
from pathlib import Path
from recorder import SessionWriter, FIELDS, load_csv, save_csv, simulated

class RecorderTests(unittest.TestCase):
    def test_session_persistence(self):
        with tempfile.TemporaryDirectory() as d:
            session = SessionWriter(d)
            rows = [simulated(i/20) for i in range(20)]
            for row in rows: session.append(row)
            self.assertEqual(load_csv(session.directory/"samples.csv"), rows)
            session.event("中断")
            session.event("恢复")
            session.close()
            with (session.directory/"events.csv").open(encoding="utf-8-sig", newline="") as f:
                events = list(csv.reader(f))
            self.assertEqual([r[1] for r in events[1:]], ["模拟采集开始", "中断", "恢复"])
            second = SessionWriter(d)
            self.assertNotEqual(second.directory, session.directory)
            second.close()

    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'data.csv'
            rows = [simulated(i/20) for i in range(200)]
            save_csv(path, rows)
            self.assertEqual(load_csv(path), rows)

    def test_invalid_input(self):
        cases = [('NaN', '1'), ('-1', '1'), ('1', '0'), ('1', '1')]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'bad.csv'
            for first, second in cases:
                with self.subTest(first=first, second=second):
                    with path.open('w', newline='') as f:
                        w = csv.writer(f)
                        w.writerow(FIELDS)
                        for t in (first, second): w.writerow([t, 0, 0, 9.81, 0, 0, 0, 101325])
                    with self.assertRaises(ValueError): load_csv(path)

    def test_headers_and_empty(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'bad.csv'
            for text in ('', 'wrong\n1\n', ','.join(FIELDS)+'\n'):
                path.write_text(text)
                with self.assertRaises(ValueError): load_csv(path)

if __name__ == '__main__': unittest.main()
