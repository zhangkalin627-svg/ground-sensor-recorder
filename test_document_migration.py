from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from documents_index import register,migrate,load

class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.old=self.root/'old'; self.new=self.root/'new'
        self.old.mkdir(); self.new.mkdir(); self.db=self.root/'documents.json'
        (self.old/'file.txt').write_bytes(b'original'); (self.new/'file.txt').write_bytes(b'original')
        register(self.db,'D1','1','资料','未知',self.old/'file.txt')

    def test_preview_then_apply(self):
        before=self.db.read_bytes()
        result=migrate(self.db,self.old,self.new)
        self.assertFalse(result['applied']); self.assertEqual(result['matches'],1)
        self.assertEqual(self.db.read_bytes(),before)
        self.assertTrue(migrate(self.db,self.old,self.new,True)['applied'])
        self.assertEqual(load(self.db)['documents'][0]['path'],str(self.new/'file.txt'))
        self.assertEqual((self.old/'file.txt').read_bytes(),b'original')

    def test_prefix_and_removed_old_directory(self):
        other=self.root/'older'; other.mkdir(); (other/'x').write_bytes(b'x')
        register(self.db,'D2','1','资料','未知',other/'x')
        (self.old/'file.txt').unlink(); self.old.rmdir()
        result=migrate(self.db,self.old,self.new,True)
        self.assertEqual(result['matches'],1)
        self.assertEqual(load(self.db)['documents'][1]['path'],str(other/'x'))

    def test_missing_and_hash_mismatch_preserve(self):
        before=self.db.read_bytes()
        (self.new/'file.txt').write_bytes(b'different')
        self.assertTrue(migrate(self.db,self.old,self.new)['failed'])
        with self.assertRaises(ValueError): migrate(self.db,self.old,self.new,True)
        (self.new/'file.txt').unlink()
        with self.assertRaises(ValueError): migrate(self.db,self.old,self.new,True)
        self.assertEqual(self.db.read_bytes(),before)

    def test_link_escape_rejected(self):
        outside=self.root/'outside'; outside.write_bytes(b'original')
        (self.new/'file.txt').unlink(); (self.new/'file.txt').symlink_to(outside)
        result=migrate(self.db,self.old,self.new)
        self.assertTrue(result['failed']); self.assertIn('越出',result['items'][0]['reason'])

    def test_partial_failure_and_replace_failure(self):
        (self.old/'other').write_bytes(b'other')
        register(self.db,'D2','1','资料','未知',self.old/'other')
        before=self.db.read_bytes()
        with self.assertRaises(ValueError): migrate(self.db,self.old,self.new,True)
        self.assertEqual(before,self.db.read_bytes())
        (self.new/'other').write_bytes(b'other')
        with patch('documents_index.os.replace',side_effect=OSError('disk')):
            with self.assertRaises(OSError): migrate(self.db,self.old,self.new,True)
        self.assertEqual(before,self.db.read_bytes())
        self.assertEqual(list(self.root.glob('.doc-migrate-*')),[])

if __name__=='__main__': unittest.main()
