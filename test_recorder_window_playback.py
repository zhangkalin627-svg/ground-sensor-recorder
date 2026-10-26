"""Tk replay completion, pause/resume, and import/session-switch checks.

Run with: xvfb-run -a python3 -m unittest test_recorder_window_playback
"""
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
class RecorderWindowPlaybackTests(unittest.TestCase):
    def _new_app(self):
        import tkinter as tk
        from recorder_lines import LineApp

        root = tk.Tk()
        # Tests drive tick() explicitly and do not run the Tk event loop.
        root.after = lambda *_args: None
        return root, LineApp(root)

    def _write_log(self, path, rows):
        path.write_text('\n'.join(rows) + '\n', encoding='utf-8')

    def _import(self, app, source, output_base):
        from tkinter import filedialog, messagebox

        before = set(output_base.iterdir())
        with patch.object(filedialog, 'askopenfilename',
                          return_value=str(source)), \
             patch.object(filedialog, 'askdirectory',
                          return_value=str(output_base)), \
             patch.object(messagebox, 'showinfo'):
            app.confirm_discard = lambda: True
            app.import_lines()
        created = set(output_base.iterdir()) - before
        self.assertEqual(len(created), 1)
        return next(iter(created))

    def test_replay_completion_sets_final_status(self):
        with TemporaryDirectory() as temp:
            root, app = self._new_app()
            try:
                source = Path(temp) / 'three-samples.txt'
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()
                self._write_log(source, [
                    '0,1,0,9.8,0,0,0,101325',
                    '0.05,2,0,9.7,0,0,0,101324',
                    '0.10,3,0,9.6,0,0,0,101323',
                ])
                self._import(app, source, output_base)
                app.started = 100.0

                with patch('recorder_lines.time.monotonic', return_value=101.0):
                    app.tick()

                self.assertEqual(app.mode, 'idle')
                self.assertEqual(app.index, len(app.replay))
                self.assertEqual(len(app.window), 3)
                self.assertEqual(app.status.get(), '文件回放完成')
            finally:
                root.destroy()

    def test_pause_holds_position_and_resume_finishes_replay(self):
        with TemporaryDirectory() as temp:
            root, app = self._new_app()
            try:
                source = Path(temp) / 'three-samples.txt'
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()
                self._write_log(source, [
                    '0,1,0,9.8,0,0,0,101325',
                    '0.05,2,0,9.7,0,0,0,101324',
                    '0.10,3,0,9.6,0,0,0,101323',
                ])
                self._import(app, source, output_base)
                app.started = 100.0
                app.index = 1
                app.window.append(app.replay[0])

                with patch('recorder_lines.time.monotonic', return_value=100.25):
                    app.stop()
                self.assertEqual(app.mode, 'paused')
                self.assertEqual(app.index, 1)
                self.assertEqual(len(app.window), 1)

                with patch('recorder_lines.time.monotonic', return_value=150.0):
                    app.tick()
                self.assertEqual(app.mode, 'paused')
                self.assertEqual(app.index, 1)
                self.assertEqual(len(app.window), 1)

                with patch('recorder_lines.time.monotonic', return_value=200.0):
                    app.resume()
                self.assertEqual(app.mode, 'replay')
                with patch('recorder_lines.time.monotonic', return_value=200.10):
                    app.tick()

                self.assertEqual(app.mode, 'idle')
                self.assertEqual(app.index, len(app.replay))
                self.assertEqual(len(app.window), 3)
                self.assertEqual(app.status.get(), '文件回放完成')
            finally:
                root.destroy()

    def test_consecutive_import_replaces_view_and_preserves_prior_session(self):
        with TemporaryDirectory() as temp:
            root, app = self._new_app()
            try:
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()
                first_source = Path(temp) / 'first.txt'
                second_source = Path(temp) / 'second.txt'
                self._write_log(first_source, [
                    '0,1,0,9.8,0,0,0,101325',
                ])
                self._write_log(second_source, [
                    '0,4,0,9.5,0,0,0,101322',
                    '0.05,5,0,9.4,0,0,0,101321',
                ])

                first_dir = self._import(app, first_source, output_base)
                first_bytes = {
                    path.name: path.read_bytes() for path in first_dir.iterdir()
                }
                self.assertEqual(len(app.rows), 1)
                self.assertEqual(app.mode, 'replay')

                second_dir = self._import(app, second_source, output_base)

                self.assertNotEqual(first_dir, second_dir)
                self.assertEqual(len(app.rows), 2)
                self.assertEqual(app.rows, app.replay)
                self.assertEqual(app.index, 0)
                self.assertEqual(len(app.window), 0)
                self.assertEqual(app.mode, 'replay')
                self.assertEqual(
                    {path.name: path.read_bytes() for path in first_dir.iterdir()},
                    first_bytes)
                self.assertEqual(
                    {path.name for path in second_dir.iterdir()},
                    {'samples.csv', 'anomalies.csv', 'device.json'})
                self.assertEqual(len(list(output_base.glob('*-lines-*'))), 2)
            finally:
                root.destroy()

    def test_switching_simulated_capture_to_text_replay_closes_capture_session(self):
        from recorder import SessionWriter, simulated

        with TemporaryDirectory() as temp:
            root, app = self._new_app()
            try:
                capture_base = Path(temp) / 'capture'
                capture_base.mkdir()
                session = SessionWriter(capture_base)
                sample = simulated(0.0)
                session.append(sample)
                app.session = session
                app.rows = [sample]
                app.mode = 'sim'

                source = Path(temp) / 'text-log.txt'
                output_base = Path(temp) / 'sessions'
                output_base.mkdir()
                self._write_log(source, [
                    '0,4,0,9.5,0,0,0,101322',
                ])
                self._import(app, source, output_base)

                self.assertIsNone(app.session)
                self.assertTrue(session.data.closed)
                self.assertTrue(session.events.closed)
                self.assertIn('切换到文本行回放',
                              (session.directory / 'events.csv').read_text(
                                  encoding='utf-8-sig'))
                self.assertEqual(app.mode, 'replay')
                self.assertEqual(app.rows, app.replay)
                self.assertEqual(len(app.rows), 1)
            finally:
                root.destroy()


if __name__ == '__main__':
    unittest.main()
