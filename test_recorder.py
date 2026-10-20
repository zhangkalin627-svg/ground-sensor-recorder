import csv
import tempfile
import unittest
from pathlib import Path
from recorder import FIELDS, load_csv, save_csv, simulated

class RecorderTests(unittest.TestCase):
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
