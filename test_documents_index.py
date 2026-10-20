import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from documents_index import register,check,load
from configuration import add

class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.db=self.root/'documents.json'; self.file=self.root/'data.txt'
        self.file.write_bytes(b'abc')

    def register(self,**kw):
        return register(self.db,'DOC-1','1','实验资料','未知',self.file,**kw)

    def test_fingerprint_and_change(self):
        self.assertEqual(self.register()['sha256'],hashlib.sha256(b'abc').hexdigest())
        self.assertEqual(check(self.db)[0]['file_status'],'一致')
        self.file.write_bytes(b'changed')
        self.assertEqual(check(self.db)[0]['file_status'],'已变更')
        self.file.unlink()
        self.assertEqual(check(self.db)[0]['file_status'],'文件缺失')

    def test_duplicate_and_missing_preserve(self):
        self.register(); before=self.db.read_bytes()
        with self.assertRaises(ValueError): self.register()
        with self.assertRaises(FileNotFoundError): register(self.db,'DOC-2','1','资料','未知',self.root/'missing')
        self.assertEqual(before,self.db.read_bytes())

    def test_part_reference(self):
        config=self.root/'config.json'; add(config,'P1','1','零件','初次')
        with self.assertRaises(ValueError): self.register(part_id='P2',part_version='1',configuration=config)
        self.register(part_id='P1',part_version='1')
        self.assertEqual(check(self.db)[0]['part_status'],'未核对')
        self.assertEqual(check(self.db,config)[0]['part_status'],'存在')

    def test_write_failure_preserves(self):
        self.register(); before=self.db.read_bytes(); original=self.file.read_bytes()
        with patch('documents_index.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError): register(self.db,'DOC-2','1','资料','未知',self.file)
        self.assertEqual(before,self.db.read_bytes()); self.assertEqual(original,self.file.read_bytes())
        self.assertEqual(list(self.root.glob('.doc-index-*')),[])

if __name__=='__main__': unittest.main()
