"""Issue tracking 0.5.0 (module 14). Standard library only.

Keeps a plain-text issue table (issues.csv) for the ground data tools.
It stores and checks text records only; it never touches devices and it is
not a safety or reliability certification.
"""
import argparse
import csv
import os
import re
import sys
import tempfile
from dataclasses import dataclass

FIELDS = ('issue_id', 'title', 'symptom', 'suspected_cause', 'status',
          'req_ids', 'test_ids', 'retest_evidence', 'resolution')
REQUIRED = ('issue_id', 'title', 'symptom', 'status')
STATUSES = ('新建', '分析中', '已处理待复测', '验证关闭', '已拒绝')
CLOSED = '验证关闭'
FIXED = '已处理待复测'
REJECTED = '已拒绝'
NO_CAUSE = '未确认'
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$')
TEST_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$')
MAX_TEXT = 2000
MAX_ROWS = 10000
DEFAULT_DB = 'issues.csv'
DEFAULT_REQS = 'requirements.csv'


class IssueError(ValueError):
    """Carries every problem found, so the user can fix them in one pass."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__('；'.join(self.problems))


@dataclass(frozen=True)
class Issue:
    issue_id: str
    title: str
    symptom: str
    status: str
    suspected_cause: str = ''
    req_ids: tuple = ()
    test_ids: tuple = ()
    retest_evidence: str = ''
    resolution: str = ''

    def as_row(self):
        return {'issue_id': self.issue_id, 'title': self.title,
                'symptom': self.symptom, 'suspected_cause': self.suspected_cause,
                'status': self.status, 'req_ids': ';'.join(self.req_ids),
                'test_ids': ';'.join(self.test_ids),
                'retest_evidence': self.retest_evidence,
                'resolution': self.resolution}


def _split(text):
    out = []
    for part in re.split(r'[;；]', text):
        part = part.strip()
        if part and part not in out:
            out.append(part)
    return tuple(out)


def check_row(raw, where):
    """Return (Issue or None, problems). raw is a dict of strings."""
    problems = []
    vals = {}
    for name in FIELDS:
        v = raw.get(name)
        v = '' if v is None else str(v).strip()
        if any(ord(c) < 32 for c in v):
            problems.append(f'{where}：字段 {name} 含换行或控制字符')
            v = ''
        if len(v) > MAX_TEXT:
            problems.append(f'{where}：字段 {name} 超过 {MAX_TEXT} 字符')
            v = ''
        vals[name] = v
    for name in REQUIRED:
        if not vals[name]:
            problems.append(f'{where}：缺少必填字段 {name}')
    if vals['issue_id'] and not ID_RE.match(vals['issue_id']):
        problems.append(f'{where}：问题编号 {vals["issue_id"]!r} 不合法（字母数字开头，可含 _ . -，最长 32）')
    if vals['status'] and vals['status'] not in STATUSES:
        problems.append(f'{where}：状态 {vals["status"]!r} 非法，可选 {"、".join(STATUSES)}')
    reqs = _split(vals['req_ids'])
    for r in reqs:
        if not ID_RE.match(r):
            problems.append(f'{where}：需求编号 {r!r} 不合法')
    tests = _split(vals['test_ids'])
    for t in tests:
        if not TEST_ID_RE.match(t):
            problems.append(f'{where}：测试编号 {t!r} 不合法')
    status = vals['status']
    if status == CLOSED and not (vals['retest_evidence'] and tests):
        problems.append(f'{where}：状态“{CLOSED}”必须填写复测依据和至少一个关联测试编号')
    if status == FIXED and not vals['resolution']:
        problems.append(f'{where}：状态“{FIXED}”必须填写处理说明 resolution')
    if status == REJECTED and not vals['resolution']:
        problems.append(f'{where}：状态“{REJECTED}”必须在 resolution 写明理由')
    if problems:
        return None, problems
    return Issue(vals['issue_id'], vals['title'], vals['symptom'], status,
                 vals['suspected_cause'], reqs, tests,
                 vals['retest_evidence'], vals['resolution']), []


def parse_rows(rows, existing=(), label='行'):
    """Validate every row; raise IssueError listing all problems, else return new list."""
    seen = {i.issue_id.casefold() for i in existing}
    out, problems = [], []
    for n, raw in enumerate(rows, start=1):
        where = f'{label} {n}'
        if None in raw:
            problems.append(f'{where}：字段数多于表头')
        item, probs = check_row(raw, where)
        problems.extend(probs)
        if item is None:
            continue
        key = item.issue_id.casefold()
        if key in seen:
            problems.append(f'{where}：问题编号 {item.issue_id} 重复（大小写不区分）')
            continue
        seen.add(key)
        out.append(item)
    if problems:
        raise IssueError(problems)
    return out


def read_csv(path):
    """Read and validate an issues CSV. Raises IssueError on any problem."""
    try:
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            problems = []
            for name in REQUIRED:
                if name not in header:
                    problems.append(f'表头缺少列 {name}')
            for name in header:
                if name not in FIELDS:
                    problems.append(f'表头含未知列 {name!r}')
            if problems:
                raise IssueError(problems)
            rows = []
            for raw in reader:
                rows.append(raw)
                if len(rows) > MAX_ROWS:
                    raise IssueError([f'行数超过上限 {MAX_ROWS}'])
    except (UnicodeDecodeError, csv.Error) as e:
        raise IssueError([f'无法解析 CSV：{e}'])
    except OSError as e:
        raise IssueError([f'无法读取文件 {path}：{e}'])
    return parse_rows(rows, label='数据行')


def write_csv(path, items):
    """Atomic write: a failure leaves any existing file untouched."""
    path = os.path.abspath(path)
    fd, tmp = tempfile.mkstemp(prefix='.iss-', suffix='.tmp', dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for i in items:
                w.writerow(i.as_row())
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def filter_status(items, status=None):
    if status is None:
        return list(items)
    if status not in STATUSES:
        raise IssueError([f'状态 {status!r} 非法，可选 {"、".join(STATUSES)}'])
    return [i for i in items if i.status == status]


def read_requirement_ids(path):
    """Return the set of req_id values (casefolded) in a requirements CSV.

    Only the req_id column is read; other columns are not validated here.
    """
    try:
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            if 'req_id' not in (reader.fieldnames or []):
                raise IssueError([f'需求表 {path} 表头缺少列 req_id'])
            return {(row.get('req_id') or '').strip().casefold() for row in reader
                    if (row.get('req_id') or '').strip()}
    except (UnicodeDecodeError, csv.Error) as e:
        raise IssueError([f'无法解析需求表 {path}：{e}'])
    except OSError as e:
        raise IssueError([f'无法读取需求表 {path}：{e}'])


def unknown_req_links(items, known_ids):
    """List (issue_id, req_id) pairs whose requirement id is not in known_ids."""
    return [(i.issue_id, r) for i in items for r in i.req_ids
            if r.casefold() not in known_ids]


class IssueStore:
    def __init__(self, path=DEFAULT_DB, reqs_path=None):
        self.path = path
        self.reqs_path = reqs_path

    def load(self):
        if not os.path.exists(self.path):
            return []
        return read_csv(self.path)

    def _check_reqs(self, items, label):
        if self.reqs_path is None:
            return
        bad = unknown_req_links(items, read_requirement_ids(self.reqs_path))
        if bad:
            raise IssueError([f'{label}：问题 {iid} 关联的需求 {rid} 不在 {self.reqs_path} 中'
                              for iid, rid in bad])

    def add(self, **fields):
        existing = self.load()
        new = parse_rows([fields], existing, label='新增')
        self._check_reqs(new, '新增')
        write_csv(self.path, existing + new)
        return new[0]

    def set_status(self, issue_id, status, retest_evidence=None, resolution=None,
                   test_ids=None):
        """Change one issue's status; the result must satisfy every rule."""
        existing = self.load()
        key = issue_id.casefold()
        for pos, it in enumerate(existing):
            if it.issue_id.casefold() == key:
                break
        else:
            raise IssueError([f'找不到问题 {issue_id}'])
        row = it.as_row()
        row['status'] = status
        if retest_evidence is not None:
            row['retest_evidence'] = retest_evidence
        if resolution is not None:
            row['resolution'] = resolution
        if test_ids is not None:
            merged = list(it.test_ids)
            for t in _split(test_ids):
                if t not in merged:
                    merged.append(t)
            row['test_ids'] = ';'.join(merged)
        updated, probs = check_row(row, f'问题 {it.issue_id}')
        if updated is None:
            raise IssueError(probs)
        existing[pos] = updated
        write_csv(self.path, existing)
        return updated

    def import_csv(self, src):
        """All-or-nothing: any problem in src leaves the store unchanged."""
        existing = self.load()
        incoming = read_csv(src)
        seen = {i.issue_id.casefold() for i in existing}
        problems = [f'导入文件：问题编号 {i.issue_id} 与已有问题重复' for i in incoming
                    if i.issue_id.casefold() in seen]
        if problems:
            raise IssueError(problems)
        self._check_reqs(incoming, '导入文件')
        write_csv(self.path, existing + incoming)
        return len(incoming)

    def export_csv(self, dest, status=None):
        chosen = filter_status(self.load(), status)
        write_csv(dest, chosen)
        return len(chosen)


def _format(items, checked):
    lines = []
    for i in items:
        cause = i.suspected_cause or NO_CAUSE
        reqs = ','.join(i.req_ids) or '-'
        mark = '' if checked or not i.req_ids else ' [需求未校验]'
        tests = ','.join(i.test_ids) or '-'
        lines.append(f'{i.issue_id}\t{i.status}\t{i.title}\t现象:{i.symptom}\t'
                     f'推测原因:{cause}\t需求:{reqs}{mark}\t测试:{tests}')
    return '\n'.join(lines)


def main(argv=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    p = argparse.ArgumentParser(description='问题追踪（只处理文本记录，不控制任何设备，不构成安全或可靠性认证）')
    p.add_argument('--db', default=DEFAULT_DB, help='问题表路径，默认 issues.csv')
    p.add_argument('--reqs', default=None,
                   help='需求表路径（如 requirements.csv）；给出后关联的需求编号必须存在')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add')
    a.add_argument('--id', required=True)
    a.add_argument('--title', required=True)
    a.add_argument('--symptom', required=True, help='观察到的现象')
    a.add_argument('--cause', default='', help='推测原因（未确认时留空）')
    a.add_argument('--status', default='新建')
    a.add_argument('--req', default='', help='用分号分隔的需求编号')
    a.add_argument('--tests', default='', help='用分号分隔的测试编号')
    a.add_argument('--retest', default='', help='复测依据')
    a.add_argument('--resolution', default='', help='处理说明')
    s = sub.add_parser('set-status')
    s.add_argument('--id', required=True)
    s.add_argument('--status', required=True)
    s.add_argument('--retest', default=None)
    s.add_argument('--resolution', default=None)
    s.add_argument('--tests', default=None, help='追加的测试编号，分号分隔')
    l = sub.add_parser('list')
    l.add_argument('--status')
    i = sub.add_parser('import')
    i.add_argument('file')
    e = sub.add_parser('export')
    e.add_argument('file')
    e.add_argument('--status')
    sub.add_parser('check', help='对照需求表检查关联的需求编号是否存在（需要 --reqs 或默认 requirements.csv）')
    try:
        ns = p.parse_args(argv)
    except SystemExit as x:
        return int(x.code or 0)
    store = IssueStore(ns.db, ns.reqs)
    try:
        if ns.cmd == 'add':
            it = store.add(issue_id=ns.id, title=ns.title, symptom=ns.symptom,
                           suspected_cause=ns.cause, status=ns.status, req_ids=ns.req,
                           test_ids=ns.tests, retest_evidence=ns.retest,
                           resolution=ns.resolution)
            print(f'已新增 {it.issue_id}', file=out)
        elif ns.cmd == 'set-status':
            it = store.set_status(ns.id, ns.status, ns.retest, ns.resolution, ns.tests)
            print(f'{it.issue_id} 状态已改为 {it.status}', file=out)
        elif ns.cmd == 'list':
            items = filter_status(store.load(), ns.status)
            print(_format(items, ns.reqs is not None), file=out)
            print(f'共 {len(items)} 条', file=out)
        elif ns.cmd == 'import':
            n = store.import_csv(ns.file)
            print(f'已导入 {n} 条', file=out)
        elif ns.cmd == 'export':
            n = store.export_csv(ns.file, ns.status)
            print(f'已导出 {n} 条', file=out)
        elif ns.cmd == 'check':
            path = ns.reqs or DEFAULT_REQS
            bad = unknown_req_links(store.load(), read_requirement_ids(path))
            for iid, rid in bad:
                print(f'未知需求：问题 {iid} 关联的 {rid} 不在 {path} 中', file=out)
            print(f'共 {len(bad)} 处未知需求关联（只检查编号是否存在，不检查需求内容）', file=out)
            if bad:
                return 1
    except IssueError as ex:
        for prob in ex.problems:
            print(f'错误：{prob}', file=err)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
