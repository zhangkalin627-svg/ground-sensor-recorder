from pathlib import Path
import tempfile
import unittest
from configuration import add,compare

class CompareTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.db=Path(self.tmp.name)/'config.json'
        for part,version in [('P','1'),('P','2'),('Q','1')]: add(self.db,part,version,part,'初次')

    def child(self,part='P',version='1',quantity=1): return dict(id=part,version=version,quantity=quantity)

    def test_same_and_read_only(self):
        before=self.db.read_bytes()
        self.assertTrue(compare(self.db,'P','1','P','1')['identical_content'])
        self.assertEqual(before,self.db.read_bytes())

    def test_attributes_added_removed_quantity(self):
        add(self.db,'A','1','装配','初次',children=[self.child(),self.child('Q')])
        add(self.db,'A','2','装配新版','调整',model='已确认型号',children=[self.child(quantity=3)])
        result=compare(self.db,'A','1','A','2')
        self.assertEqual(set(result['attributes']),{'name','reason','model'})
        changes={r['part_id']:r['changes'] for r in result['children']}
        self.assertEqual(changes,{'p':['数量变化'],'q':['删除']})
        self.assertIn('新增',compare(self.db,'A','2','A','1')['children'][1]['changes'])

    def test_versions_no_ambiguous_matching(self):
        add(self.db,'A','1','装配','初次',children=[self.child()])
        add(self.db,'A','2','装配','调整',children=[self.child(),self.child(version='2')])
        delta=compare(self.db,'A','1','A','2')['children'][0]
        self.assertEqual(delta['changes'],['版本集合变化'])
        self.assertEqual(len(delta['after']),2)

    def test_missing_version(self):
        before=self.db.read_bytes()
        with self.assertRaises(ValueError): compare(self.db,'P','1','P','99')
        self.assertEqual(before,self.db.read_bytes())

if __name__=='__main__': unittest.main()
