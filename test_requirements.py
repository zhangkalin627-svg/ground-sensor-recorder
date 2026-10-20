import csv
import io
import os
import tempfile
import unittest

import requirements as rq

HERE = os.path.dirname(os.path.abspath(__file__))


def base(**kw):
    d = dict(req_id='R-1', description='示例需求', source='ADAPTERS.md', status='草案')
    d.update(kw)
    return d


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = os.path.join(self.tmp.name, 'requirements.csv')
        self.store = rq.RequirementStore(self.db)

    def write_src(self, text, name='src.csv'):
        p = os.path.join(self.tmp.name, name)
        with open(p, 'w', newline='', encoding='utf-8-sig') as f:
            f.write(text)
        return p

    def raw(self):
        with open(self.db, 'rb') as f:
            return f.read()

    def leftovers(self):
        return [n for n in os.listdir(self.tmp.name) if n.endswith('.tmp')]


class StoreTests(Base):
    def test_add_and_reload(self):
        self.store.add(**base(verification_method='评审', test_ids='t.a；t.b;t.a'))
        got = self.store.load()
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].test_ids, ('t.a', 't.b'))
        self.assertEqual(got[0].description, '示例需求')

    def test_duplicate_id_rejected_case_insensitive_store_unchanged(self):
        self.store.add(**base())
        before = self.raw()
        with self.assertRaises(rq.RequirementError) as c:
            self.store.add(**base(req_id='r-1'))
        self.assertIn('重复', str(c.exception))
        self.assertEqual(self.raw(), before)

    def test_missing_required_each_flagged(self):
        for name in rq.REQUIRED:
            with self.subTest(name=name):
                with self.assertRaises(rq.RequirementError) as c:
                    self.store.add(**base(**{name: ''}))
                self.assertIn(name, str(c.exception))
        self.assertFalse(os.path.exists(self.db))

    def test_missing_source_hint_mentions_unknown_marker(self):
        with self.assertRaises(rq.RequirementError) as c:
            self.store.add(**base(source=''))
        self.assertIn('未知', str(c.exception))

    def test_unknown_source_is_allowed_and_listed(self):
        self.store.add(**base(source=rq.UNKNOWN_SOURCE))
        self.store.add(**base(req_id='R-2'))
        self.assertEqual([r.req_id for r in self.store.unknown_sources()], ['R-1'])

    def test_illegal_status_and_id_and_newline(self):
        for kw in (dict(status='完成'), dict(req_id='bad id'), dict(req_id='-x'),
                   dict(description='a\nb'), dict(test_ids='bad id')):
            with self.subTest(kw=kw):
                with self.assertRaises(rq.RequirementError):
                    self.store.add(**base(**kw))

    def test_verified_needs_method_and_tests(self):
        with self.assertRaises(rq.RequirementError):
            self.store.add(**base(status='已验证'))
        with self.assertRaises(rq.RequirementError):
            self.store.add(**base(status='已验证', verification_method='测试'))
        self.store.add(**base(status='已验证', verification_method='测试', test_ids='t.x'))

    def test_all_problems_reported_together(self):
        with self.assertRaises(rq.RequirementError) as c:
            self.store.add(req_id='', description='', source='', status='?')
        self.assertGreaterEqual(len(c.exception.problems), 4)

    def test_corrupt_existing_db_is_never_overwritten(self):
        with open(self.db, 'w', encoding='utf-8') as f:
            f.write('req_id,description\nR-1,only two columns\n')
        before = self.raw()
        with self.assertRaises(rq.RequirementError):
            self.store.add(**base(req_id='R-9'))
        self.assertEqual(self.raw(), before)


class ImportExportTests(Base):
    HEADER = ','.join(rq.FIELDS) + '\n'

    def test_failed_import_leaves_store_untouched(self):
        self.store.add(**base())
        before = self.raw()
        src = self.write_src(self.HEADER + 'R-2,好,来源,草案,,\nR-3,坏状态,来源,乱写,,\nR-2,重复,来源,草案,,\n')
        with self.assertRaises(rq.RequirementError) as c:
            self.store.import_csv(src)
        self.assertGreaterEqual(len(c.exception.problems), 2)
        self.assertEqual(self.raw(), before)
        self.assertEqual(self.leftovers(), [])

    def test_import_duplicate_of_existing_rejected(self):
        self.store.add(**base())
        src = self.write_src(self.HEADER + 'r-1,同名,来源,草案,,\n')
        with self.assertRaises(rq.RequirementError) as c:
            self.store.import_csv(src)
        self.assertIn('已有', str(c.exception))
        self.assertEqual(len(self.store.load()), 1)

    def test_unknown_column_and_missing_column_rejected(self):
        with self.assertRaises(rq.RequirementError):
            self.store.import_csv(self.write_src('req_id,description,source,status,extra\nR-1,a,b,草案,x\n'))
        with self.assertRaises(rq.RequirementError):
            self.store.import_csv(self.write_src('req_id,description,status\nR-1,a,草案\n'))
        self.assertFalse(os.path.exists(self.db))

    def test_extra_fields_in_row_rejected(self):
        with self.assertRaises(rq.RequirementError):
            self.store.import_csv(self.write_src(self.HEADER + 'R-1,a,b,草案,,,多余\n'))

    def test_missing_file_reports_error(self):
        with self.assertRaises(rq.RequirementError):
            self.store.import_csv(os.path.join(self.tmp.name, 'nope.csv'))

    def test_bad_encoding_reports_error_not_crash(self):
        p = os.path.join(self.tmp.name, 'gbk.csv')
        with open(p, 'wb') as f:
            f.write(self.HEADER.encode() + 'R-1,需求,来源,草案,,\n'.encode('gbk'))
        with self.assertRaises(rq.RequirementError):
            self.store.import_csv(p)

    def test_export_then_import_keeps_everything(self):
        self.store.add(**base(verification_method='评审', test_ids='t.a;t.b'))
        self.store.add(**base(req_id='R-2', source=rq.UNKNOWN_SOURCE, description='含，逗号和"引号"'))
        out = os.path.join(self.tmp.name, 'out.csv')
        self.assertEqual(self.store.export_csv(out), 2)
        other = rq.RequirementStore(os.path.join(self.tmp.name, 'other.csv'))
        self.assertEqual(other.import_csv(out), 2)
        self.assertEqual(other.load(), self.store.load())

    def test_export_filter_by_status(self):
        self.store.add(**base())
        self.store.add(**base(req_id='R-2', status='已批准'))
        out = os.path.join(self.tmp.name, 'o.csv')
        self.assertEqual(self.store.export_csv(out, '已批准'), 1)
        self.assertEqual([r.req_id for r in rq.read_csv(out)], ['R-2'])
        with self.assertRaises(rq.RequirementError):
            self.store.export_csv(out, '乱写')


class FilterAndExampleTests(Base):
    def test_filter_status_exact(self):
        for i, s in enumerate(rq.STATUSES):
            self.store.add(**base(req_id=f'R-{i}', status=s, verification_method='m', test_ids='t.x'))
        for s in rq.STATUSES:
            got = rq.filter_status(self.store.load(), s)
            self.assertEqual([r.status for r in got], [s])
        self.assertEqual(len(rq.filter_status(self.store.load())), len(rq.STATUSES))

    def test_example_file_loads_and_marks_unknown_source(self):
        reqs = rq.read_csv(os.path.join(HERE, 'example_requirements.csv'))
        self.assertEqual(len(reqs), 4)
        self.assertEqual([r.req_id for r in reqs if r.source == rq.UNKNOWN_SOURCE], ['GSR-004'])


class CliTests(Base):
    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        code = rq.main(['--db', self.db, *args], out, err)
        return code, out.getvalue(), err.getvalue()

    def test_add_list_filter_flow(self):
        code, out, _ = self.run_cli('add', '--id', 'R-1', '--description', '甲', '--source', '未知', '--status', '草案')
        self.assertEqual(code, 0)
        code, out, _ = self.run_cli('add', '--id', 'R-2', '--description', '乙', '--source', 'x', '--status', '已批准')
        code, out, _ = self.run_cli('list', '--status', '已批准')
        self.assertEqual(code, 0)
        self.assertIn('R-2', out)
        self.assertNotIn('R-1', out)
        self.assertIn('共 1 条', out)
        code, out, _ = self.run_cli('list')
        self.assertIn('[来源未知]', out)

    def test_cli_errors_return_2_and_message(self):
        code, _, err = self.run_cli('add', '--id', 'R-1', '--description', '甲', '--source', 'x', '--status', '乱写')
        self.assertEqual(code, 2)
        self.assertIn('非法', err)
        code, _, err = self.run_cli('list', '--status', '乱写')
        self.assertEqual(code, 2)

    def test_cli_import_export(self):
        src = self.write_src(','.join(rq.FIELDS) + '\nR-1,甲,x,草案,,\n')
        self.assertEqual(self.run_cli('import', src)[0], 0)
        out = os.path.join(self.tmp.name, 'e.csv')
        self.assertEqual(self.run_cli('export', out)[0], 0)
        self.assertEqual(self.run_cli('import', src)[0], 2)


if __name__ == '__main__':
    unittest.main()
