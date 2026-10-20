import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from requirements import RequirementStore, RequirementError, main

class StatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'requirements.csv'; self.store=RequirementStore(self.path)
        self.store.add(req_id='R1',description='说明',source='未知',status='草案')
        self.store.add(req_id='R2',description='另一个需求',source='资料',status='草案')

    def test_update_preserves_other_fields(self):
        second=self.store.load()[1]
        updated=self.store.set_status('r1','已验证','手动检查','T1;T2')
        self.assertEqual(updated.status,'已验证')
        self.assertEqual(updated.test_ids,('T1','T2'))
        self.assertEqual(updated.source,'未知')
        self.assertEqual(self.store.load()[1],second)
        updated=self.store.set_status('R1','已实现')
        self.assertEqual(updated.verification_method,'手动检查')
        self.assertEqual(updated.test_ids,('T1','T2'))

    def test_invalid_updates_preserve_bytes(self):
        before=self.path.read_bytes()
        for args in [('R9','草案'),('R1','错误'),('R1','已验证')]:
            with self.assertRaises(RequirementError): self.store.set_status(*args)
            self.assertEqual(before,self.path.read_bytes())

    def test_explicit_clear_is_validated(self):
        self.store.set_status('R1','已验证','检查','T1')
        before=self.path.read_bytes()
        with self.assertRaises(RequirementError): self.store.set_status('R1','已验证',test_ids='')
        self.assertEqual(before,self.path.read_bytes())
        r=self.store.set_status('R1','草案',verification_method='',test_ids='')
        self.assertEqual(r.test_ids,())

    def test_io_failure_and_cli(self):
        before=self.path.read_bytes()
        with patch('requirements.os.replace',side_effect=OSError('disk failure')):
            with self.assertRaises(RequirementError): self.store.set_status('R1','已批准')
        self.assertEqual(before,self.path.read_bytes())
        self.assertEqual(list(self.path.parent.glob('.req-*')),[])
        out,err=io.StringIO(),io.StringIO()
        self.assertEqual(main(['--db',str(self.path),'set-status','--id','R1','--status','已批准'],out=out,err=err),0)
        self.assertIn('已批准',out.getvalue())
        self.assertEqual(main(['--db',str(self.path),'set-status','--id','MISSING','--status','草案'],out=out,err=err),2)

if __name__=='__main__': unittest.main()
