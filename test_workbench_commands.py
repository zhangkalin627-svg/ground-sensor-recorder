import contextlib
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import workbench


class WorkbenchNewCommandTests(unittest.TestCase):
    def _route(self, argv):
        with patch('workbench.subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
            code = workbench.main(argv)
        return code, run.call_args.args[0]

    def test_channel_routes_to_channel_report(self):
        code, cmd = self._route(['channel', 'samples.csv', '--gap-factor', '3'])
        self.assertEqual(code, 0)
        self.assertEqual(Path(cmd[1]).name, 'channel_report.py')
        self.assertEqual(cmd[2:], ['samples.csv', '--gap-factor', '3'])

    def test_replay_routes_to_replay_session(self):
        code, cmd = self._route(['replay', 'input.txt', '--out', 'sessions'])
        self.assertEqual(code, 0)
        self.assertEqual(Path(cmd[1]).name, 'replay_session.py')
        self.assertEqual(cmd[2:], ['input.txt', '--out', 'sessions'])

    def test_help_lists_new_commands(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(workbench.main(['--help']), 0)
        self.assertIn('channel', out.getvalue())
        self.assertIn('replay', out.getvalue())

    def test_command_scripts_exist_in_repo_listing(self):
        for name in ('channel_report.py', 'replay_session.py'):
            self.assertIn(name, workbench.COMMANDS.values())


if __name__ == '__main__':
    unittest.main()
