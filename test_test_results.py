from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from requirements import Requirement, write_csv
from test_results import add,load,trace,validate

class ResultTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.db=self.root/'results.json'; self.reqs=self.root/'requirements.csv'
        write_csv(self.reqs,[Requirement('R1','说明','未知','草案','方法',('T1','T2')),Requirement('R2','说明','未知','草案')])
        self.row=dict(run_id='RUN1',test_id='T1',status='通过',executed_at='2026-10-20T16:00:00+08:00',commit='abc123',evidence='人工执行记录')

    def test_incomplete_and_pass_fail(self):
        add(self.db,self.row)
        self.assertEqual(trace(self.reqs,self.db,'RUN1','abc123')['requirements'][0]['trace_status'],'未完成')
        add(self.db,{**self.row,'test_id':'T2'})
        result=trace(self.reqs,self.db,'RUN1','abc123')['requirements']
        self.assertEqual(result[0]['trace_status'],'通过'); self.assertEqual(result[1]['trace_status'],'未完成')
        add(self.db,{**self.row,'run_id':'RUN2','status':'失败'})
        self.assertEqual(trace(self.reqs,self.db,'RUN2','abc123')['requirements'][0]['trace_status'],'失败')

    def test_commit_and_run_isolation(self):
        add(self.db,self.row)
        for run,commit in [('RUN2','abc123'),('RUN1','other')]:
            result=trace(self.reqs,self.db,run,commit)
            self.assertEqual(result['requirements'][0]['tests'][0]['status'],'无记录')

    def test_invalid_and_duplicate(self):
        add(self.db,self.row); before=self.db.read_bytes()
        with self.assertRaises(ValueError): add(self.db,self.row)
        for fields in [dict(status='其他'),dict(executed_at='2026-10-20'),dict(evidence=''),dict(commit=''),dict(test_id='')]:
            with self.assertRaises(ValueError): validate([{**self.row,**fields}])
        self.assertEqual(before,self.db.read_bytes())
        validate([{**self.row,'status':'未运行','executed_at':'','evidence':''}])

    def test_failure_preserves_inputs(self):
        add(self.db,self.row); before=self.db.read_bytes(); req=self.reqs.read_bytes()
        with patch('test_results.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError): add(self.db,{**self.row,'test_id':'T2'})
        self.assertEqual(before,self.db.read_bytes())
        trace(self.reqs,self.db,'RUN1','abc123')
        self.assertEqual(req,self.reqs.read_bytes())

if __name__=='__main__': unittest.main()
