"""Bounded retention and category-count tests for AnomalyLog (v0.57.0)."""
import csv
import tempfile
import unittest

from adapters import AnomalyLog


class AnomalyLogBoundedRetentionTests(unittest.TestCase):
    def make_mixed_log(self):
        log = AnomalyLog(limit=3)
        log.add('field_count', 'wrong field count')
        log.add('invalid', 'invalid sample')
        log.add('line_too_long', '513 characters')
        log.add('field_count', 'another wrong field count')
        log.add('time_order', 'timestamp did not increase')
        return log

    def test_category_counts_continue_after_retention_cap(self):
        log = self.make_mixed_log()

        self.assertEqual(log.total, 5)
        self.assertEqual(log.by_kind, {
            'field_count': 2,
            'invalid': 1,
            'line_too_long': 1,
            'time_order': 1,
        })
        self.assertEqual(
            [entry[1] for entry in log.entries],
            ['line_too_long', 'field_count', 'time_order'],
        )

    def test_saved_csv_has_recent_rows_and_mixed_kind_truncation_summary(self):
        log = self.make_mixed_log()
        with tempfile.TemporaryDirectory() as directory:
            path = log.save(directory)
            with path.open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.reader(stream))

        self.assertEqual(rows[0], ['local_time', 'kind', 'detail'])
        self.assertEqual([row[1] for row in rows[1:4]], [
            'line_too_long', 'field_count', 'time_order',
        ])
        self.assertEqual(
            rows[4][1:],
            ['truncated', '仅保留最近 3 条，共 5 条'],
        )

    def test_zero_retention_keeps_counts_and_writes_truncation_summary(self):
        log = AnomalyLog(limit=0)
        log.add('field_count', 'wrong field count')
        log.add('invalid', 'invalid sample')

        self.assertEqual(list(log.entries), [])
        self.assertEqual(log.total, 2)
        self.assertEqual(log.by_kind, {'field_count': 1, 'invalid': 1})
        with tempfile.TemporaryDirectory() as directory:
            path = log.save(directory)
            with path.open(encoding='utf-8-sig', newline='') as stream:
                rows = list(csv.reader(stream))

        self.assertEqual(rows[0], ['local_time', 'kind', 'detail'])
        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[1][1:],
            ['truncated', '仅保留最近 0 条，共 2 条'],
        )

    def test_detail_is_limited_to_200_characters(self):
        log = AnomalyLog(limit=1)
        detail = 'x' * 250

        log.add('invalid', detail)

        self.assertEqual(len(log.entries[0][2]), 200)
        self.assertEqual(log.entries[0][2], detail[:200])


if __name__ == '__main__':
    unittest.main()
