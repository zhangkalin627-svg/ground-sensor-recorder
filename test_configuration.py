import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from configuration import add,load,save,snapshot,validate,main

class ConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'configuration.json'
        add(self.path,'P1','1','地面实验零件','初次登记')

    def child(self,part='P1',version='1',quantity=1):
        return dict(id=part,version=version,quantity=quantity)

    def test_duplicate_and_unknown_preserve(self):
        before=self.path.read_bytes()
        for args in [('p1','1',[]),('A','1',[self.child('MISSING')])]:
            with self.assertRaises(ValueError): add(self.path,args[0],args[1],'说明','原因',children=args[2])
        self.assertEqual(before,self.path.read_bytes())

    def test_quantity(self):
        for quantity in (0,-1,True,1.5,'2'):
            with self.subTest(quantity=quantity):
                with self.assertRaises(ValueError): add(self.path,'A','1','装配','原因',children=[self.child(quantity=quantity)])

    def test_cycle(self):
        data=load(self.path)
        data['parts'][0]['children']=[self.child()]
        with self.assertRaises(ValueError): validate(data)
        a={**data['parts'][0],'id':'A','children':[self.child()]}
        data['parts'][0]['children']=[self.child('A')]
        data['parts'].append(a)
        with self.assertRaises(ValueError): validate(data)

    def test_snapshot_pins_versions_and_no_overwrite(self):
        add(self.path,'A','1','装配','初次',children=[self.child(quantity=2)])
        target=self.path.parent/'snapshot.json'
        result=snapshot(self.path,'A','1',target)
        add(self.path,'P1','2','零件第二版','修订')
        self.assertEqual(json.loads(target.read_text()),result)
        self.assertEqual({p['version'] for p in result['parts']},{'1'})
        with self.assertRaises(FileExistsError): snapshot(self.path,'A','1',target)
        with self.assertRaises(ValueError): snapshot(self.path,'A','1',self.path)

    def test_write_failure_preserves_database(self):
        before=self.path.read_bytes()
        with patch('configuration.os.replace',side_effect=OSError('disk failure')):
            with self.assertRaises(OSError): add(self.path,'P2','1','零件','初次')
        self.assertEqual(before,self.path.read_bytes())
        self.assertEqual(list(self.path.parent.glob('.configuration-*')),[])

    def test_cli(self):
        self.assertEqual(main(['--db',str(self.path),'add','--id','A','--version','1','--name','装配','--reason','初次','--child','P1@1:2']),0)
        self.assertEqual(load(self.path)['parts'][1]['children'][0]['quantity'],2)

if __name__=='__main__': unittest.main()
