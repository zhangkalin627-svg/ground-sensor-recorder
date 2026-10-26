"""No-display checks for the persistent import-status line in LineApp."""
import unittest
from types import SimpleNamespace

import recorder_lines


class FakeStringVar:
    def __init__(self):
        self.value = None

    def set(self, value):
        self.value = value


class RecorderLinesStatusTests(unittest.TestCase):
    def make_app(self):
        app = object.__new__(recorder_lines.LineApp)
        app.lines_status = FakeStringVar()
        return app

    def test_status_keeps_anomaly_count_and_kind_visible(self):
        app = self.make_app()
        result = SimpleNamespace(
            anomalies=SimpleNamespace(total=2, by_kind={'bad_field': 2}),
            truncated=False,
        )
        app.update_lines_status(result)
        self.assertEqual(app.lines_status.value,
                         '最近一次导入：异常行 2 条（bad_field 2）')

    def test_clean_import_clears_previous_anomaly_summary(self):
        app = self.make_app()
        app.lines_status.value = '最近一次导入：异常行 2 条'
        result = SimpleNamespace(
            anomalies=SimpleNamespace(total=0, by_kind={}),
            truncated=False,
        )
        app.update_lines_status(result)
        self.assertEqual(app.lines_status.value, '最近一次导入：无异常行')

    def test_truncated_import_status_warns_about_unread_lines(self):
        app = self.make_app()
        result = SimpleNamespace(
            anomalies=SimpleNamespace(total=0, by_kind={}),
            truncated=True,
        )
        app.update_lines_status(result)
        self.assertTrue(app.lines_status.value.endswith('其余未读取'))


if __name__ == '__main__':
    unittest.main()
