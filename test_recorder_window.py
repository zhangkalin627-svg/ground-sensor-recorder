"""Optional Tk window smoke check; run with xvfb-run on a headless machine."""
import importlib.util
import os
import unittest
from types import SimpleNamespace

_HAS_TK = importlib.util.find_spec('tkinter') is not None
_HAS_DISPLAY = bool(os.environ.get('DISPLAY'))


@unittest.skipUnless(_HAS_TK and _HAS_DISPLAY,
                     'requires Tk and a display; use xvfb-run -a')
class RecorderWindowSmokeTests(unittest.TestCase):
    def test_import_status_is_visible_in_the_window(self):
        import tkinter as tk
        from recorder_lines import LineApp

        root = tk.Tk()
        try:
            app = LineApp(root)
            result = SimpleNamespace(
                anomalies=SimpleNamespace(total=1, by_kind={'bad_field': 1}),
                truncated=False,
            )
            app.update_lines_status(result)
            self.assertEqual(app.lines_status.get(),
                             '最近一次导入：异常行 1 条（bad_field 1）')
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
