"""Optional Tk window smoke checks; run with xvfb-run on a headless machine."""
import importlib.util
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

_HAS_TK = importlib.util.find_spec('tkinter') is not None
_HAS_DISPLAY = bool(os.environ.get('DISPLAY'))


@unittest.skipUnless(_HAS_TK and _HAS_DISPLAY,
                     'requires Tk and a display; use xvfb-run -a')
class RecorderWindowSmokeTests(unittest.TestCase):
    def test_import_status_is_visible_in_the_window(self):
        import tkinter as tk
        from recorder_lines import LineApp
        from types import SimpleNamespace

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

    def test_import_flow_shows_anomalies_and_writes_session_files(self):
        import tkinter as tk
        from tkinter import filedialog, messagebox
        from recorder_lines import LineApp

        with TemporaryDirectory() as temp:
            root = tk.Tk()
            try:
                app = LineApp(root)
                source = Path(temp) / 'sensor.txt'
                source.write_text(
                    'bad,line\n0,1,0,9.8,0,0,0,101325\n', encoding='utf-8')
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()

                with patch.object(filedialog, 'askopenfilename',
                                  return_value=str(source)), \
                     patch.object(filedialog, 'askdirectory',
                                  return_value=str(output_base)), \
                     patch.object(messagebox, 'showinfo'):
                    app.confirm_discard = lambda: True
                    app.import_lines()

                self.assertEqual(len(app.rows), 1)
                self.assertEqual(app.mode, 'replay')
                self.assertEqual(app.lines_status.get(),
                                 '最近一次导入：异常行 1 条（field_count 1）')
                session_dirs = list(output_base.glob('*-lines-*'))
                self.assertEqual(len(session_dirs), 1)
                for filename in ('samples.csv', 'anomalies.csv', 'device.json'):
                    self.assertTrue((session_dirs[0] / filename).is_file(), filename)
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
