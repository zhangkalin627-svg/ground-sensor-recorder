import io
import os
import tempfile
import unittest

import issues as iss

HEAD = ','.join(iss.FIELDS) + '\n'
REQ_HEAD = 'req_id,description,source,status,verification_method,test_ids\n'


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, 'issues.csv')
        self.store = iss.IssueStore(self.db)

    def p(self, name):
        return os.path.join(self.tmp.name, name)

    def write(self, name, text):
        path = self.p(name)
        with open(path, 'w', newline='', encoding='utf-8-sig') as f:
            f.write(text)
        return path

    def raw(self):
        if not os.path.exists(self.db):
            return None
        with open(self.db, 'rb') as f:
            return f.read()

    def add_ok(self, **kw):
        fields = dict(issue_id='ISS-001', title='标题', symptom='现象', status='新建')
        fields.update(kw)
        return self.store.add(**fields)


class AddTests(Base):
    def test_add_and_load_keeps_fields(self):
        self.add_ok(suspected_cause='', req_ids='GSR-001;GSR-002')
        items = self.store.load()
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].req_ids, ('GSR-001', 'GSR-002'))
        self.assertEqual(items[0].suspected_cause, '')

    def test_duplicate_id_rejected_case_insensitive(self):
        self.add_ok()
        before = self.raw()
        with self.assertRaises(iss.IssueError) as cm:
            self.store.add(issue_id='iss-001', title='t', symptom='s', status='新建')
        self.assertTrue(any('重复' in p for p in cm.exception.problems))
        self.assertEqual(self.raw(), before)

    def test_missing_required_fields_listed(self):
        with self.assertRaises(iss.IssueError) as cm:
            self.store.add(issue_id='ISS-002', title='', symptom='', status='')
        text = ' '.join(cm.exception.problems)
        for name in ('title', 'symptom', 'status'):
            self.assertIn(name, text)
        self.assertEqual(self.store.load(), [])

    def test_illegal_status_and_bad_id(self):
        with self.assertRaises(iss.IssueError):
            self.add_ok(status='随便')
        with self.assertRaises(iss.IssueError):
            self.store.add(issue_id='-bad', title='t', symptom='s', status='新建')

    def test_control_character_rejected(self):
        with self.assertRaises(iss.IssueError):
            self.add_ok(symptom='第一行\n第二行')

    def test_closed_requires_retest_evidence_and_test_id(self):
        with self.assertRaises(iss.IssueError):
            self.add_ok(status='验证关闭')
        with self.assertRaises(iss.IssueError):
            self.add_ok(status='验证关闭', retest_evidence='复测记录 R1')
        it = self.add_ok(status='验证关闭', retest_evidence='复测记录 R1', test_ids='T-1')
        self.assertEqual(it.test_ids, ('T-1',))

    def test_fixed_and_rejected_need_text(self):
        with self.assertRaises(iss.IssueError):
            self.add_ok(status='已处理待复测')
        with self.assertRaises(iss.IssueError):
            self.add_ok(status='已拒绝')
        self.add_ok(status='已拒绝', resolution='重复报告')


class StatusTests(Base):
    def setUp(self):
        super().setUp()
        self.add_ok(suspected_cause='未确认')

    def test_close_without_evidence_leaves_file_unchanged(self):
        before = self.raw()
        with self.assertRaises(iss.IssueError):
            self.store.set_status('ISS-001', '验证关闭')
        self.assertEqual(self.raw(), before)

    def test_close_with_evidence_and_test(self):
        it = self.store.set_status('iss-001', '验证关闭', retest_evidence='复测记录 R2', test_ids='T-9')
        self.assertEqual(it.status, '验证关闭')
        self.assertEqual(self.store.load()[0].test_ids, ('T-9',))

    def test_fixed_needs_resolution_on_status_change(self):
        with self.assertRaises(iss.IssueError):
            self.store.set_status('ISS-001', '已处理待复测')
        self.store.set_status('ISS-001', '已处理待复测', resolution='更换接插件')
        self.assertEqual(self.store.load()[0].status, '已处理待复测')

    def test_unknown_id(self):
        with self.assertRaises(iss.IssueError):
            self.store.set_status('ISS-999', '分析中')


class ImportTests(Base):
    def test_valid_import_adds_all(self):
        self.add_ok()
        src = self.write('in.csv', HEAD +
                         'ISS-010,标题A,现象A,,新建,,,,\n'
                         'ISS-011,标题B,现象B,,分析中,GSR-001,,,\n')
        self.assertEqual(self.store.import_csv(src), 2)
        self.assertEqual(len(self.store.load()), 3)

    def test_bad_row_leaves_store_unchanged(self):
        self.add_ok()
        before = self.raw()
        src = self.write('bad.csv', HEAD +
                         'ISS-010,标题A,现象A,,新建,,,,\n'
                         'ISS-011,,现象B,,新建,,,,\n')
        with self.assertRaises(iss.IssueError):
            self.store.import_csv(src)
        self.assertEqual(self.raw(), before)

    def test_duplicate_with_existing_rejected(self):
        self.add_ok()
        before = self.raw()
        src = self.write('dup.csv', HEAD + 'iss-001,t,s,,新建,,,,\n')
        with self.assertRaises(iss.IssueError) as cm:
            self.store.import_csv(src)
        self.assertTrue(any('重复' in p for p in cm.exception.problems))
        self.assertEqual(self.raw(), before)

    def test_duplicate_inside_file_rejected(self):
        src = self.write('twice.csv', HEAD + 'ISS-010,a,s,,新建,,,,\nISS-010,b,s,,新建,,,,\n')
        with self.assertRaises(iss.IssueError):
            self.store.import_csv(src)
        self.assertIsNone(self.raw())

    def test_unknown_column_rejected(self):
        src = self.write('col.csv', 'issue_id,title,symptom,status,owner\nISS-010,a,s,新建,x\n')
        with self.assertRaises(iss.IssueError):
            self.store.import_csv(src)
        self.assertIsNone(self.raw())


class ReqLinkTests(Base):
    def setUp(self):
        super().setUp()
        self.reqs = self.write('requirements.csv', REQ_HEAD + 'GSR-001,需求一,未知,草案,,\n')
        self.store = iss.IssueStore(self.db, self.reqs)

    def test_unknown_req_rejected_on_add(self):
        with self.assertRaises(iss.IssueError):
            self.store.add(issue_id='ISS-001', title='t', symptom='s', status='新建', req_ids='GSR-999')
        self.assertIsNone(self.raw())

    def test_known_req_accepted_case_insensitive(self):
        self.store.add(issue_id='ISS-001', title='t', symptom='s', status='新建', req_ids='gsr-001')
        self.assertEqual(len(self.store.load()), 1)


class CliTests(Base):
    def cli(self, *argv, reqs=None):
        out, err = io.StringIO(), io.StringIO()
        args = ['--db', self.db]
        if reqs:
            args += ['--reqs', reqs]
        code = iss.main(args + list(argv), out=out, err=err)
        return code, out.getvalue(), err.getvalue()

    def test_add_list_export_import_roundtrip(self):
        code, _, _ = self.cli('add', '--id', 'ISS-001', '--title', '采样断流',
                              '--symptom', '曲线停止', '--cause', '未确认')
        self.assertEqual(code, 0)
        code, out, _ = self.cli('list')
        self.assertEqual(code, 0)
        self.assertIn('ISS-001', out)
        self.assertIn('共 1 条', out)
        dest = self.p('out.csv')
        code, _, _ = self.cli('export', dest)
        self.assertEqual(code, 0)
        store2 = iss.IssueStore(self.p('db2.csv'))
        store2.import_csv(dest)
        self.assertEqual([i.as_row() for i in store2.load()],
                         [i.as_row() for i in self.store.load()])

    def test_cli_errors_return_2(self):
        code, _, err = self.cli('add', '--id', 'ISS-001', '--title', 't',
                                '--symptom', 's', '--status', '不存在')
        self.assertEqual(code, 2)
        self.assertIn('错误', err)
        code, _, _ = self.cli('set-status', '--id', 'ISS-404', '--status', '分析中')
        self.assertEqual(code, 2)
        code, _, _ = self.cli('list', '--status', '乱写')
        self.assertEqual(code, 2)

    def test_cli_close_needs_evidence(self):
        self.cli('add', '--id', 'ISS-001', '--title', 't', '--symptom', 's')
        code, _, _ = self.cli('set-status', '--id', 'ISS-001', '--status', '验证关闭')
        self.assertEqual(code, 2)
        code, out, _ = self.cli('set-status', '--id', 'ISS-001', '--status', '验证关闭',
                                '--retest', 'R1', '--tests', 'T-1')
        self.assertEqual(code, 0)
        self.assertIn('验证关闭', out)

    def test_check_reports_unknown_requirement(self):
        reqs = self.write('requirements.csv', REQ_HEAD + 'GSR-001,需求一,未知,草案,,\n')
        self.cli('add', '--id', 'ISS-001', '--title', 't', '--symptom', 's', '--req', 'GSR-001;GSR-777')
        code, out, _ = self.cli('check', reqs=reqs)
        self.assertEqual(code, 1)
        self.assertIn('GSR-777', out)

    def test_check_passes_when_all_known(self):
        reqs = self.write('requirements.csv', REQ_HEAD + 'GSR-001,需求一,未知,草案,,\n')
        self.cli('add', '--id', 'ISS-001', '--title', 't', '--symptom', 's', '--req', 'GSR-001')
        code, _, _ = self.cli('check', reqs=reqs)
        self.assertEqual(code, 0)


if __name__ == '__main__':
    unittest.main()
