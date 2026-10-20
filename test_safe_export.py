from pathlib import Path
import tempfile
import unittest
import issues
import requirements

class ExportTests(unittest.TestCase):
    def test_both_stores_preserve_existing_and_links(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            stores=[requirements.RequirementStore(root/'req.csv'),issues.IssueStore(root/'issues.csv')]
            stores[0].add(req_id='R1',description='说明',source='未知',status='草案')
            stores[1].add(issue_id='I1',title='标题',symptom='现象',status='新建')
            for i,store in enumerate(stores):
                source=Path(store.path); before=source.read_bytes()
                hard=root/f'hard{i}.csv'; hard.hardlink_to(source)
                link=root/f'link{i}.csv'; link.symlink_to(source)
                for target in (source,hard,link):
                    with self.subTest(store=i,target=target.name):
                        with self.assertRaises(ValueError): store.export_csv(target)
                        self.assertEqual(source.read_bytes(),before)
                out=root/f'new{i}.csv'
                self.assertEqual(store.export_csv(out),1)
                with self.assertRaises(ValueError): store.export_csv(out)

if __name__=='__main__': unittest.main()
