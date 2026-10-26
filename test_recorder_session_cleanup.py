"""Session cleanup status tests for recorder.App.close_session (v0.43.0).

These tests use small stand-ins and need no Tk display.
Run: python3 -m unittest test_recorder_session_cleanup
"""
import unittest
from unittest.mock import Mock

from recorder import App


class Status:
    def __init__(self):
        self.value = ''

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class SessionCleanupTests(unittest.TestCase):
    def _app(self, session):
        app = object.__new__(App)
        app.session = session
        app.save_status = Status()
        return app

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


if __name__ == '__main__':
    unittest.main()
