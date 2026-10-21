import unittest
from types import SimpleNamespace

import import_status as st


class AnomalyStatusTextTests(unittest.TestCase):
    def test_no_anomalies(self):
        self.assertEqual(st.anomaly_status_text(0, {}), '最近一次导入：无异常行')

    def test_total_and_kinds_sorted_by_count(self):
        text = st.anomaly_status_text(5, {'bad_field': 2, 'line_too_long': 3})
        self.assertEqual(text, '最近一次导入：异常行 5 条（line_too_long 3，bad_field 2）')

    def test_ties_sorted_by_name(self):
        text = st.anomaly_status_text(2, {'b': 1, 'a': 1})
        self.assertIn('（a 1，b 1）', text)

    def test_more_than_three_kinds_are_folded(self):
        kinds = {'a': 4, 'b': 3, 'c': 2, 'd': 1, 'e': 1}
        text = st.anomaly_status_text(11, kinds)
        self.assertIn('a 4，b 3，c 2，另有 2 类', text)
        self.assertNotIn('d 1', text)

    def test_truncated_note(self):
        self.assertTrue(st.anomaly_status_text(0, {}, True).endswith('其余未读取'))

    def test_total_without_kinds(self):
        self.assertEqual(st.anomaly_status_text(2), '最近一次导入：异常行 2 条')

    def test_status_from_result(self):
        result = SimpleNamespace(
            anomalies=SimpleNamespace(total=1, by_kind={'bad_field': 1}),
            truncated=False)
        self.assertEqual(st.status_from_result(result),
                         '最近一次导入：异常行 1 条（bad_field 1）')


if __name__ == '__main__':
    unittest.main()
