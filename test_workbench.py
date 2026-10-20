import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
import workbench

class WorkbenchTests(unittest.TestCase):
    def test_modules(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out): self.assertEqual(workbench.main(['modules']),0)
        rows=json.loads(out.getvalue())
        self.assertEqual(len(rows),15)
        self.assertIsNone(rows[8]['command'])
        self.assertIn('CAD 内核',rows[2]['status'])

    def test_route_arguments_and_return_code(self):
        with patch('workbench.subprocess.run',return_value=subprocess.CompletedProcess([],7)) as run:
            self.assertEqual(workbench.main(['analyze','file with spaces.csv','--output','out.json']),7)
        call=run.call_args
        self.assertEqual(call.args[0][0],sys.executable)
        self.assertEqual(Path(call.args[0][1]).name,'analysis.py')
        self.assertEqual(call.args[0][2:],['file with spaces.csv','--output','out.json'])
        self.assertNotIn('shell',call.kwargs)

    def test_unknown_and_extra_arguments(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(workbench.main(['gnc']),2)
            self.assertEqual(workbench.main(['modules','extra']),2)

    def test_real_child_help(self):
        result=subprocess.run([sys.executable,str(Path(workbench.__file__)),'requirements','--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0)
        self.assertIn('--db',result.stdout)

if __name__=='__main__': unittest.main()
