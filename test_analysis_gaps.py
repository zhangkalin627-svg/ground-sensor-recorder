from pathlib import Path
import tempfile
import unittest
from recorder import Sample,save_csv
from analysis import summarize

class GapTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'samples.csv'
        save_csv(self.path,[Sample(t,v,v,v,v,v,v,100000+v) for t,v in [(0,3),(.1,1),(.25,5),(.6,5)]])

    def test_explicit_threshold_and_extreme_times(self):
        summary=summarize(self.path,.1,2)
        self.assertEqual(summary['gaps']['count'],1)
        self.assertEqual(summary['gaps']['intervals'][0]['start_t_s'],.25)
        channel=summary['channels']['ax_m_s2']
        self.assertEqual(channel['first_minimum_t_s'],.1)
        self.assertEqual(channel['first_maximum_t_s'],.25)

    def test_unspecified_and_single_point(self):
        self.assertIsNone(summarize(self.path)['gaps']['count'])
        save_csv(self.path,[Sample(0,1,1,1,1,1,1,100000)])
        self.assertEqual(summarize(self.path,.1)['gaps']['count'],0)
        self.assertIsNone(summarize(self.path,.1)['sampling_interval_s'])

    def test_invalid_options(self):
        for interval,factor in [(0,2),(-1,2),(float('nan'),2),(.1,1),(.1,float('inf')),(1e308,2)]:
            with self.subTest(interval=interval,factor=factor):
                with self.assertRaises(ValueError): summarize(self.path,interval,factor)

if __name__=='__main__': unittest.main()
