import json
import tempfile
import unittest
from pathlib import Path
from analysis import main, report, summarize, write_report
from recorder import Sample, save_csv

class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root/'source.csv'
        self.rows = [Sample(t,v,v,v,v,v,v,100000+v) for t,v in [(0,1),(1,3),(3,5)]]
        save_csv(self.path, self.rows)

    def test_known_statistics(self):
        summary = summarize(self.path)
        self.assertEqual(summary['sample_count'], 3)
        self.assertEqual(summary['duration_s'], 3)
        self.assertEqual(summary['sampling_interval_s'], dict(minimum=1,maximum=2,mean=1.5))
        for field, channel in summary['channels'].items():
            offset = 100000 if field == 'pressure_pa' else 0
            self.assertEqual(channel['count'], 3)
            self.assertEqual(channel['minimum'], 1+offset)
            self.assertEqual(channel['maximum'], 5+offset)
            self.assertEqual(channel['mean'], 3+offset)
            self.assertAlmostEqual(channel['population_stddev'], (8/3)**.5)

    def test_single_sample(self):
        save_csv(self.path, self.rows[:1])
        summary = summarize(self.path)
        self.assertEqual(summary['duration_s'], 0)
        self.assertIsNone(summary['sampling_interval_s'])
        self.assertEqual(summary['channels']['ax_m_s2']['population_stddev'], 0)

    def test_comparison_and_export(self):
        other = self.root/'other.csv'
        save_csv(other, [Sample(0,5,5,5,5,5,5,100005)])
        original = self.path.read_bytes()
        result = report([self.path, other])
        self.assertEqual(result['mean_difference_second_minus_first']['ax_m_s2']['value'], 2)
        self.assertEqual([r['sample_count'] for r in result['records']], [3,1])
        output = self.root/'report.json'
        self.assertEqual(main([str(self.path),str(other),'--output',str(output)]), 0)
        self.assertEqual(json.loads(output.read_text())['records'][0]['sample_count'], 3)
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(FileExistsError): write_report(output,result,[self.path])

    def test_input_protection(self):
        original = self.path.read_bytes()
        with self.assertRaises(ValueError): write_report(self.path,{},[self.path])
        alias = self.root/'alias.csv'
        alias.hardlink_to(self.path)
        with self.assertRaises(ValueError): write_report(alias,{},[self.path])
        self.assertEqual(original,self.path.read_bytes())

    def test_invalid_data(self):
        original = self.path.read_text(encoding='utf-8-sig')
        for bad in [original.replace('1,1,1,1,1,1', 'nan,1,1,1,1,1'),
                    original.replace('3,5,5,5', '1,5,5,5'), 'wrong\n']:
            self.path.write_text(bad,encoding='utf-8-sig')
            with self.assertRaises(ValueError): summarize(self.path)
        with self.assertRaises(ValueError): report([])

if __name__ == '__main__': unittest.main()
