from hashlib import sha256
from pathlib import Path
from unittest import mock
import tempfile
import unittest
import requirements
from summary_report import build,write,fingerprint
class TraceabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.req=self.root/'requirements.csv'
        requirements.write_csv(self.req,[requirements.Requirement('R1','描述','未知','草案')])
    def test_fingerprint_matches_file(self):
        data=self.req.read_bytes()
        self.assertEqual(fingerprint(self.req),(len(data),sha256(data).hexdigest()))
    def test_page_shows_size_hash_and_snapshot_note(self):
        page=build({'requirements':self.req})
        size,digest=fingerprint(self.req)
        self.assertIn(digest,page)
        self.assertIn(f'{size} 字节',page)
        self.assertIn('不是实时状态',page)
    def test_change_during_build_rejected_no_output(self):
        real=requirements.read_csv
        def read_and_modify(path):
            result=real(path)
            Path(path).write_text(Path(path).read_text(encoding='utf-8-sig')+'\n',encoding='utf-8')
            return result
        out=self.root/'report.html'
        with mock.patch.object(requirements,'read_csv',read_and_modify):
            with self.assertRaises(ValueError): write(out,{'requirements':self.req})
        self.assertFalse(out.exists())
    def test_stable_input_unchanged_after_write(self):
        before=self.req.read_bytes(); out=self.root/'report.html'
        write(out,{'requirements':self.req})
        self.assertTrue(out.exists())
        self.assertEqual(self.req.read_bytes(),before)
if __name__=='__main__': unittest.main()
