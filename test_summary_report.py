from pathlib import Path
import tempfile
import unittest
import requirements
import issues
import configuration
from summary_report import build,write

class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.req=self.root/'requirements.csv'
        requirements.write_csv(self.req,[requirements.Requirement('R1','<script>alert(1)</script>','未知','草案')])

    def test_escape_and_offline(self):
        page=build({'requirements':self.req})
        self.assertNotIn('<script>',page)
        self.assertIn('&lt;script&gt;',page)
        self.assertIn('default-src',page)
        self.assertNotIn('src="http',page)

    def test_all_tables_and_empty(self):
        issue=self.root/'issues.csv'; issues.write_csv(issue,[])
        config=self.root/'config.json'; configuration.save(config,{'schema_version':1,'parts':[]})
        docs=self.root/'documents.json'; docs.write_text('{"schema_version":1,"documents":[]}')
        page=build({'requirements':self.req,'issues':issue,'configuration':config,'documents':docs})
        self.assertEqual(page.count('<section>'),4)
        self.assertIn('空表',page)

    def test_protection(self):
        before=self.req.read_bytes(); selected={'requirements':self.req}
        with self.assertRaises(ValueError): write(self.req,selected)
        alias=self.root/'alias'; alias.hardlink_to(self.req)
        with self.assertRaises(ValueError): write(alias,selected)
        out=self.root/'report.html'; write(out,selected)
        with self.assertRaises(FileExistsError): write(out,selected)
        self.assertEqual(self.req.read_bytes(),before)

    def test_invalid_inputs_no_output(self):
        out=self.root/'report.html'
        for selected in ({},{'configuration':self.root/'missing'}):
            with self.assertRaises(ValueError): write(out,selected)
            self.assertFalse(out.exists())
        self.req.write_text('wrong\n')
        with self.assertRaises(ValueError): write(out,{'requirements':self.req})
        self.assertFalse(out.exists())

if __name__=='__main__': unittest.main()
