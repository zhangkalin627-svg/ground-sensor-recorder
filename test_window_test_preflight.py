"""Tests for the Tk environment preflight, without opening a real display."""
import unittest
from unittest.mock import patch

from window_test_preflight import check_tk_environment


class FakeRoot:
    def __init__(self, withdraw_error=None):
        self.withdraw_error = withdraw_error
        self.hidden = False
        self.destroyed = False

    def withdraw(self):
        if self.withdraw_error:
            raise self.withdraw_error
        self.hidden = True

    def destroy(self):
        self.destroyed = True


class FakeTk:
    def __init__(self, root):
        self.root = root
        self.created = 0

    def Tk(self):
        self.created += 1
        return self.root


class TkPreflightTests(unittest.TestCase):
    def test_missing_tkinter_reports_unavailable(self):
        with patch('window_test_preflight.importlib.import_module',
                   side_effect=ImportError('tk is absent')):
            available, message = check_tk_environment(
                environ={'DISPLAY': ':1'}, platform='linux')
        self.assertFalse(available)
        self.assertIn('Tkinter 不可用', message)

    def test_linux_without_display_does_not_create_root(self):
        tk = FakeTk(FakeRoot())
        available, message = check_tk_environment(
            tk_module=tk, environ={}, platform='linux')
        self.assertFalse(available)
        self.assertEqual(tk.created, 0)
        self.assertIn('DISPLAY', message)

    def test_successful_probe_with_display_destroys_root(self):
        root = FakeRoot()
        tk = FakeTk(root)
        available, message = check_tk_environment(
            tk_module=tk, environ={'DISPLAY': ':99'}, platform='linux')
        self.assertTrue(available)
        self.assertTrue(root.hidden)
        self.assertTrue(root.destroyed)
        self.assertIn('可用', message)

    def test_tk_start_failure_is_reported(self):
        class BrokenTk:
            def Tk(self):
                raise RuntimeError('display refused')
        available, message = check_tk_environment(
            tk_module=BrokenTk(), environ={'DISPLAY': ':99'}, platform='linux')
        self.assertFalse(available)
        self.assertIn('display refused', message)

    def test_root_is_destroyed_if_withdraw_fails(self):
        root = FakeRoot(withdraw_error=RuntimeError('withdraw failed'))
        available, message = check_tk_environment(
            tk_module=FakeTk(root), environ={'DISPLAY': ':99'}, platform='linux')
        self.assertFalse(available)
        self.assertTrue(root.destroyed)
        self.assertIn('withdraw failed', message)


if __name__ == '__main__':
    unittest.main()
