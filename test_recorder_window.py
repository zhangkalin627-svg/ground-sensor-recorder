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
    def _load_valid_import(self, root, temp):
        from tkinter import filedialog, messagebox
        from recorder_lines import LineApp

        source = Path(temp) / 'previous.txt'
        source.write_text(
            '0,1,0,9.8,0,0,0,101325\n', encoding='utf-8')
        output_base = Path(temp) / 'sessions'
        output_base.mkdir()
        app = LineApp(root)
        with patch.object(filedialog, 'askopenfilename',
                          return_value=str(source)), \
             patch.object(filedialog, 'askdirectory',
                          return_value=str(output_base)), \
             patch.object(messagebox, 'showinfo'):
            app.confirm_discard = lambda: True
            app.import_lines()
        session_dirs = list(output_base.glob('*-lines-*'))
        self.assertEqual(len(session_dirs), 1)
        return app, output_base, session_dirs[0]

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

    def test_import_failure_keeps_failure_status_visible(self):
        import tkinter as tk
        from tkinter import filedialog, messagebox
        from recorder_lines import LineApp

        with TemporaryDirectory() as temp:
            root = tk.Tk()
            try:
                app = LineApp(root)
                source = Path(temp) / 'sensor.txt'
                source.write_text('sample\n', encoding='utf-8')
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()

                with patch.object(filedialog, 'askopenfilename',
                                  return_value=str(source)), \
                     patch.object(filedialog, 'askdirectory',
                                  return_value=str(output_base)), \
                     patch.object(messagebox, 'showerror') as showerror, \
                     patch('recorder_lines.replay_session.import_lines',
                           side_effect=OSError('simulated import failure')) as importer:
                    app.confirm_discard = lambda: True
                    app.import_lines()

                self.assertEqual(app.lines_status.get(),
                                 '最近一次导入：失败，simulated import failure')
                showerror.assert_called_once_with(
                    '导入失败', 'simulated import failure')
                importer.assert_called_once_with(str(source), str(output_base))
            finally:
                root.destroy()

    def test_cancelled_file_picker_preserves_previous_replay(self):
        import tkinter as tk
        from tkinter import filedialog

        with TemporaryDirectory() as temp:
            root = tk.Tk()
            try:
                app, output_base, previous_dir = self._load_valid_import(root, temp)
                previous_rows = list(app.rows)
                previous_replay = list(app.replay)
                previous_window = list(app.window)
                previous_status = app.lines_status.get()
                previous_save_status = app.save_status.get()
                previous_files = {
                    path.name: path.read_bytes() for path in previous_dir.iterdir()
                }

                with patch.object(filedialog, 'askopenfilename',
                                  return_value=''), \
                     patch.object(filedialog, 'askdirectory') as askdirectory, \
                     patch('recorder_lines.replay_session.import_lines') as importer, \
                     patch.object(app, 'confirm_discard') as confirm_discard:
                    app.import_lines()

                askdirectory.assert_not_called()
                importer.assert_not_called()
                confirm_discard.assert_not_called()
                self.assertEqual(app.rows, previous_rows)
                self.assertEqual(app.replay, previous_replay)
                self.assertEqual(list(app.window), previous_window)
                self.assertEqual(app.mode, 'replay')
                self.assertEqual(app.lines_status.get(), previous_status)
                self.assertEqual(app.save_status.get(), previous_save_status)
                self.assertEqual(
                    {path.name: path.read_bytes() for path in previous_dir.iterdir()},
                    previous_files)
                self.assertEqual(list(output_base.iterdir()), [previous_dir])
            finally:
                root.destroy()

    def test_failed_reimport_preserves_previous_replay_and_files(self):
        import tkinter as tk
        from tkinter import filedialog, messagebox

        with TemporaryDirectory() as temp:
            root = tk.Tk()
            try:
                app, output_base, previous_dir = self._load_valid_import(root, temp)
                previous_rows = list(app.rows)
                previous_replay = list(app.replay)
                previous_window = list(app.window)
                previous_save_status = app.save_status.get()
                previous_files = {
                    path.name: path.read_bytes() for path in previous_dir.iterdir()
                }
                source = Path(temp) / 'broken.txt'
                source.write_text('bad input\n', encoding='utf-8')

                with patch.object(filedialog, 'askopenfilename',
                                  return_value=str(source)), \
                     patch.object(filedialog, 'askdirectory',
                                  return_value=str(output_base)), \
                     patch.object(messagebox, 'showerror') as showerror, \
                     patch('recorder_lines.replay_session.import_lines',
                           side_effect=OSError('simulated reimport failure')) as importer:
                    app.confirm_discard = lambda: True
                    app.import_lines()

                importer.assert_called_once_with(str(source), str(output_base))
                showerror.assert_called_once_with(
                    '导入失败', 'simulated reimport failure')
                self.assertEqual(app.rows, previous_rows)
                self.assertEqual(app.replay, previous_replay)
                self.assertEqual(list(app.window), previous_window)
                self.assertEqual(app.mode, 'replay')
                self.assertEqual(app.save_status.get(), previous_save_status)
                self.assertEqual(app.lines_status.get(),
                                 '最近一次导入：失败，simulated reimport failure')
                self.assertEqual(
                    {path.name: path.read_bytes() for path in previous_dir.iterdir()},
                    previous_files)
                self.assertEqual(list(output_base.iterdir()), [previous_dir])
            finally:
                root.destroy()



    def test_successful_import_matches_saved_session_after_playback(self):
        import csv
        import json
        import tkinter as tk
        from tkinter import filedialog, messagebox
        from recorder import load_csv
        from recorder_lines import LineApp

        with TemporaryDirectory() as temp:
            root = tk.Tk()
            try:
                source = Path(temp) / 'consistent.txt'
                source.write_text(
                    '0,1,0,9.8,0,0,0,101325\n'
                    'bad,line\n'
                    '1,2,0,9.9,0,0,0,101326\n', encoding='utf-8')
                original = source.read_bytes()
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()
                app = LineApp(root)
                with patch.object(filedialog, 'askopenfilename', return_value=str(source)), \
                     patch.object(filedialog, 'askdirectory', return_value=str(output_base)), \
                     patch.object(messagebox, 'showinfo') as showinfo:
                    app.confirm_discard = lambda: True
                    app.import_lines()
                directories = list(output_base.glob('*-lines-*'))
                self.assertEqual(len(directories), 1)
                directory = directories[0]
                saved = load_csv(directory / 'samples.csv')
                self.assertEqual(len(saved), 2)
                self.assertEqual(app.rows, saved)
                self.assertEqual(app.replay, saved)
                self.assertEqual(app.mode, 'replay')
                self.assertEqual(app.index, 0)
                self.assertEqual(list(app.window), [])
                self.assertIsNone(app.session)
                self.assertEqual(app.save_status.get(), '已保存：' + str(directory))
                self.assertEqual(app.lines_status.get(),
                                 '最近一次导入：异常行 1 条（field_count 1）')
                with (directory / 'anomalies.csv').open(
                        encoding='utf-8-sig', newline='') as handle:
                    anomalies = list(csv.DictReader(handle))
                self.assertEqual(len(anomalies), 1)
                self.assertEqual(anomalies[0]['kind'], 'field_count')
                info = json.loads((directory / 'device.json').read_text(encoding='utf-8'))
                self.assertEqual(info['source'], source.name)
                self.assertEqual(info['serial'], '未知')
                self.assertEqual(info['firmware'], '未知')
                showinfo.assert_called_once()
                before = {p.name: p.read_bytes() for p in directory.iterdir()}
                with patch('recorder.time.monotonic', return_value=app.started + 2):
                    app.tick()
                self.assertEqual(app.index, len(saved))
                self.assertEqual(list(app.window), saved)
                self.assertEqual(app.mode, 'idle')
                self.assertEqual(app.status.get(), '文件回放完成')
                self.assertEqual(app.rows, saved)
                self.assertEqual(source.read_bytes(), original)
                self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()}, before)
            finally:
                root.destroy()

if __name__ == '__main__':
    unittest.main()
