"""Session cleanup tests for recorder.SessionWriter and recorder.App.tick (v0.48.0).

These tests use in-memory file objects and stand-ins; no Tk display is needed.
Run: python3 -m unittest test_recorder_session_cleanup
"""
import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from recorder import App, SessionWriter


class Status:
    def __init__(self, value=''):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class MemoryFile(io.StringIO):
    def __init__(self):
        super().__init__()
        self.fail_next_write = False

    def write(self, text):
        if self.fail_next_write:
            self.fail_next_write = False
            raise OSError('sample write failed')
        return super().write(text)


class FailOnSecondWriteFile(MemoryFile):
    def __init__(self):
        super().__init__()
        self.write_calls = 0

    def write(self, text):
        self.write_calls += 1
        if self.write_calls == 2:
            raise OSError('initial event write failed')
        return super().write(text)


class CloseErrorFile(MemoryFile):
    def close(self):
        super().close()
        raise OSError('first close failed')


class WriteAndCloseErrorFile(MemoryFile):
    def __init__(self):
        super().__init__()
        self.fail_next_write = True

    def close(self):
        super().close()
        raise OSError('header cleanup close failed')


class FailOnSecondWriteAndCloseFile(FailOnSecondWriteFile):
    def close(self):
        super().close()
        raise OSError('event cleanup close failed')


class SessionCleanupTests(unittest.TestCase):
    def _app(self, session):
        app = object.__new__(App)
        app.session = session
        app.save_status = Status()
        return app

    def _session(self, base, data_file=None, events_file=None):
        data_file = data_file or MemoryFile()
        events_file = events_file or MemoryFile()
        with patch.object(Path, 'open', side_effect=[data_file, events_file]):
            session = SessionWriter(base)
        return session, data_file, events_file

    def test_event_write_error_still_closes_and_clears_session(self):
        session = Mock()
        session.event.side_effect = OSError('event disk error')
        app = self._app(session)

        app.close_session('切换到文本行回放')

        self.assertIsNone(app.session)
        session.close.assert_called_once_with()
        self.assertEqual(app.save_status.get(), '事件日志写入失败；请检查磁盘')

    def test_close_error_still_clears_session_and_reports_status(self):
        session = Mock()
        session.close.side_effect = OSError('close disk error')
        app = self._app(session)

        app.close_session('切换到文本行回放')

        self.assertIsNone(app.session)
        session.event.assert_called_once_with('切换到文本行回放')
        session.close.assert_called_once_with()
        self.assertEqual(app.save_status.get(), '关闭文件失败；请检查磁盘')

    def test_partial_initialization_closes_already_opened_data_file(self):
        data_file = MemoryFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, OSError('events open failed')]) as open_file:
                with self.assertRaisesRegex(OSError, 'events open failed'):
                    SessionWriter(base)

        self.assertEqual(open_file.call_count, 2)
        self.assertTrue(data_file.closed)

    def test_open_error_is_preserved_when_open_file_close_fails(self):
        data_file = CloseErrorFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, OSError('events open failed')]) as open_file:
                with self.assertRaisesRegex(OSError, 'events open failed'):
                    SessionWriter(base)

        self.assertEqual(open_file.call_count, 2)
        self.assertTrue(data_file.closed)

    def test_header_write_error_does_not_mask_close_error_and_closes_events_file(self):
        data_file = WriteAndCloseErrorFile()
        events_file = MemoryFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, events_file]):
                with self.assertRaisesRegex(OSError, 'sample write failed'):
                    SessionWriter(base)

        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)

    def test_initial_event_write_error_does_not_mask_close_error_and_closes_data_file(self):
        data_file = MemoryFile()
        events_file = FailOnSecondWriteAndCloseFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, events_file]):
                with self.assertRaisesRegex(OSError, 'initial event write failed'):
                    SessionWriter(base)

        self.assertEqual(events_file.write_calls, 2)
        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)

    def test_directory_creation_error_does_not_open_session_files(self):
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'mkdir', side_effect=OSError('directory denied')):
                with patch.object(Path, 'open') as open_file:
                    with self.assertRaisesRegex(OSError, 'directory denied'):
                        SessionWriter(base)

        open_file.assert_not_called()

    def test_csv_header_write_error_closes_both_open_files(self):
        data_file = MemoryFile()
        data_file.fail_next_write = True
        events_file = MemoryFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, events_file]):
                with self.assertRaisesRegex(OSError, 'sample write failed'):
                    SessionWriter(base)

        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)

    def test_initial_event_write_error_closes_both_open_files(self):
        data_file = MemoryFile()
        events_file = FailOnSecondWriteFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, events_file]):
                with self.assertRaisesRegex(OSError, 'initial event write failed'):
                    SessionWriter(base)

        self.assertEqual(events_file.write_calls, 2)
        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)

    def test_close_attempts_events_file_after_data_close_error(self):
        writer = SessionWriter.__new__(SessionWriter)
        data_file = CloseErrorFile()
        events_file = MemoryFile()
        writer.data = data_file
        writer.events = events_file

        with self.assertRaisesRegex(OSError, 'first close failed'):
            writer.close()

        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)
        self.assertIsNone(writer.events)

    def test_append_write_error_stops_and_closes_both_session_files(self):
        data_file = MemoryFile()
        events_file = MemoryFile()
        with tempfile.TemporaryDirectory() as base:
            with patch.object(Path, 'open', side_effect=[data_file, events_file]):
                session = SessionWriter(base)

        data_file.fail_next_write = True
        app = object.__new__(App)
        app.mode = 'sim'
        app.interrupted = False
        app.drop = Status(False)
        app.started = time.monotonic() - 1
        app.last_rx = None
        app.session = session
        app.rows = []
        app.replay = []
        app.save_status = Status()
        app.status = Status()
        app.count = Status()
        app.root = Mock()

        app.tick()

        self.assertEqual(app.mode, 'idle')
        self.assertIsNone(app.session)
        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)
        self.assertEqual(app.save_status.get(), 'sample write failed')
        app.root.after.assert_called_once_with(50, app.tick)

    def test_real_event_log_write_error_still_closes_both_files(self):
        data_file = MemoryFile()
        events_file = MemoryFile()
        with tempfile.TemporaryDirectory() as base:
            session, data_file, events_file = self._session(base, data_file, events_file)
        events_file.fail_next_write = True
        app = self._app(session)

        app.close_session('停止采集')

        self.assertIsNone(app.session)
        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)
        self.assertEqual(app.save_status.get(), '事件日志写入失败；请检查磁盘')

    def test_successful_close_can_be_called_more_than_once(self):
        with tempfile.TemporaryDirectory() as base:
            session, data_file, events_file = self._session(base)

        session.close()
        session.close()

        self.assertTrue(data_file.closed)
        self.assertTrue(events_file.closed)
        self.assertIsNone(session.data)
        self.assertIsNone(session.events)


if __name__ == '__main__':
    unittest.main()
