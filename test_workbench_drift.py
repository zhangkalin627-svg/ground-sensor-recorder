import contextlib
import io
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch
import workbench


class WorkbenchDriftCommandTests(unittest.TestCase):
    def test_drift_routes_to_drift_report(self):
        with patch('workbench.subprocess.run', return_value=subprocess.CompletedProcess([], 2)) as run:
            code = workbench.main(['drift', 'a.json', 'b.json', '--max-rel-change', '0.05', '--strict'])
        cmd = run.call_args.args[0]
        self.assertEqual(code, 2)
        self.assertEqual(Path(cmd[1]).name, 'drift_report.py')
        self.assertEqual(cmd[2:], ['a.json', 'b.json', '--max-rel-change', '0.05', '--strict'])

    def test_help_lists_drift_and_version(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(workbench.main(['--help']), 0)
        self.assertIn('drift', out.getvalue())
        self.assertIn('pipeline', out.getvalue())
        self.assertIn('v0.26.0', out.getvalue())

    def test_drift_script_name_is_registered(self):
        self.assertEqual(workbench.COMMANDS['drift'], 'drift_report.py')

    def test_modules_still_fifteen_and_module_13_lists_drift(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(workbench.main(['modules']), 0)
        import json
        rows = json.loads(out.getvalue())
        self.assertEqual(len(rows), 15)
        self.assertIn('drift', rows[12]['command'])
        self.assertIn('pipeline', rows[12]['command'])


if __name__ == '__main__':
    unittest.main()