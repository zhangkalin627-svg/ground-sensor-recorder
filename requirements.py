"""Requirements management 0.4.0 (module 01). Standard library only.

Keeps a requirements table (requirements.csv) for the ground data tools.
It stores and checks text records only; it never touches devices.
"""
from safe_export import export_new
import argparse
import csv
import os
import re
import sys
import tempfile
from dataclasses import dataclass

FIELDS = ('req_id', 'description', 'source', 'status', 'verification_method', 'test_ids')
REQUIRED = ('req_id', 'description', 'source', 'status')
STATUSES = ('草案', '已批准', '已实现', '已验证', '已废弃')
UNKNOWN_SOURCE = '未知'
ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,31}$')
TEST_ID_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}$')
MAX_TEXT = 2000
MAX_ROWS = 10000
DEFAULT_DB = 'requirements.csv'


class RequirementError(ValueError):
    """Carries every problem found, so the user can fix them in one pass."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__('；'.join(self.problems))


@dataclass(frozen=True)
class Requirement:
    req_id: str
    description: str
    source: str
    status: str
    verification_method: str = ''
    test_ids: tuple = ()

    def as_row(self):
        return {'req_id': self.req_id, 'description': self.description,
                'source': self.source, 'status': self.status,
                'verification_method': self.verification_method,
                'test_ids': ';'.join(self.test_ids)}


def _split_tests(text):
    out = []
    for part in re.split(r'[;；]', text):
        part = part.strip()
        if part and part not in out:
            out.append(part)
    return tuple(out)


def check_row(raw, where):
    """Return (Requirement or None, problems). raw is a dict of strings."""
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
            hint = f'；来源不明时请明确写“{UNKNOWN_SOURCE}”' if name == 'source' else ''
            problems.append(f'{where}：缺少必填字段 {name}{hint}')
    if vals['req_id'] and not ID_RE.match(vals['req_id']):
        problems.append(f'{where}：编号 {vals["req_id"]!r} 不合法（字母数字开头，可含 _ . -，最长 32）')
    if vals['status'] and vals['status'] not in STATUSES:
        problems.append(f'{where}：状态 {vals["status"]!r} 非法，可选 {"、".join(STATUSES)}')
    tests = _split_tests(vals['test_ids'])
    for t in tests:
        if not TEST_ID_RE.match(t):
            problems.append(f'{where}：测试编号 {t!r} 不合法')
    if vals['status'] == '已验证' and not (vals['verification_method'] and tests):
        problems.append(f'{where}：状态“已验证”必须填写验证方法和至少一个关联测试编号')
    if problems:
        return None, problems
    return Requirement(vals['req_id'], vals['description'], vals['source'], vals['status'],
                       vals['verification_method'], tests), []


def parse_rows(rows, existing=(), label='行'):
    """Validate every row; raise RequirementError listing all problems, else return new list."""
    seen = {r.req_id.casefold() for r in existing}
    out, problems = [], []
    for i, raw in enumerate(rows, start=1):
        where = f'{label} {i}'
        if None in raw:
            problems.append(f'{where}：字段数多于表头')
        req, probs = check_row(raw, where)
        problems.extend(probs)
        if req is None:
            continue
        key = req.req_id.casefold()
        if key in seen:
            problems.append(f'{where}：编号 {req.req_id} 重复（大小写不区分）')
            continue
        seen.add(key)
        out.append(req)
    if problems:
        raise RequirementError(problems)
    return out


def read_csv(path):
    """Read and validate a requirements CSV. Raises RequirementError on any problem."""
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
                raise RequirementError(problems)
            rows = []
            for raw in reader:
                rows.append(raw)
                if len(rows) > MAX_ROWS:
                    raise RequirementError([f'行数超过上限 {MAX_ROWS}'])
    except (UnicodeDecodeError, csv.Error) as e:
        raise RequirementError([f'无法解析 CSV：{e}'])
    except OSError as e:
        raise RequirementError([f'无法读取文件 {path}：{e}'])
    return parse_rows(rows, label='数据行')


def write_csv(path, reqs):
    """Atomic write: a failure leaves any existing file untouched."""
    path = os.path.abspath(path)
    fd, tmp = tempfile.mkstemp(prefix='.req-', suffix='.tmp', dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, 'w', newline='', encoding='utf-8-sig') as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            for r in reqs:
                w.writerow(r.as_row())
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def filter_status(reqs, status=None):
    if status is None:
        return list(reqs)
    if status not in STATUSES:
        raise RequirementError([f'状态 {status!r} 非法，可选 {"、".join(STATUSES)}'])
    return [r for r in reqs if r.status == status]


class RequirementStore:
    def __init__(self, path=DEFAULT_DB):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return []
        return read_csv(self.path)

    def add(self, **fields):
        existing = self.load()
        new = parse_rows([fields], existing, label='新增')
        write_csv(self.path, existing + new)
        return new[0]

    def import_csv(self, src):
        """All-or-nothing: any problem in src leaves the store unchanged."""
        existing = self.load()
        incoming = read_csv_rows_checked(src, existing)
        write_csv(self.path, existing + incoming)
        return len(incoming)

    def export_csv(self, dest, status=None):
        chosen = filter_status(self.load(), status)
        try:
            export_new(dest, self.path, FIELDS, chosen)
        except (OSError, ValueError) as e:
            raise RequirementError([f"无法导出：{e}"] ) from e
        return len(chosen)

    def unknown_sources(self):
        return [r for r in self.load() if r.source == UNKNOWN_SOURCE]


def read_csv_rows_checked(src, existing):
    """Validate src against existing ids (duplicates across both are rejected)."""
    incoming = read_csv(src)
    seen = {r.req_id.casefold() for r in existing}
    problems = [f'导入文件：编号 {r.req_id} 与已有需求重复' for r in incoming
                if r.req_id.casefold() in seen]
    if problems:
        raise RequirementError(problems)
    return incoming


def _format(reqs):
    lines = []
    for r in reqs:
        flag = ' [来源未知]' if r.source == UNKNOWN_SOURCE else ''
        tests = r.test_ids and ','.join(r.test_ids) or '-'
        lines.append(f'{r.req_id}\t{r.status}\t{r.description}\t来源:{r.source}{flag}\t测试:{tests}')
    return '\n'.join(lines)


def main(argv=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    p = argparse.ArgumentParser(description='需求管理（只处理文本记录，不控制任何设备）')
    p.add_argument('--db', default=DEFAULT_DB, help='需求表路径，默认 requirements.csv')
    sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('add')
    a.add_argument('--id', required=True)
    a.add_argument('--description', required=True)
    a.add_argument('--source', required=True)
    a.add_argument('--status', required=True)
    a.add_argument('--verification', default='')
    a.add_argument('--tests', default='', help='用分号分隔的测试编号')
    l = sub.add_parser('list')
    l.add_argument('--status')
    i = sub.add_parser('import')
    i.add_argument('file')
    e = sub.add_parser('export')
    e.add_argument('file')
    e.add_argument('--status')
    try:
        ns = p.parse_args(argv)
    except SystemExit as x:
        return int(x.code or 0)
    store = RequirementStore(ns.db)
    try:
        if ns.cmd == 'add':
            r = store.add(req_id=ns.id, description=ns.description, source=ns.source,
                          status=ns.status, verification_method=ns.verification,
                          test_ids=ns.tests)
            print(f'已新增 {r.req_id}', file=out)
        elif ns.cmd == 'list':
            reqs = filter_status(store.load(), ns.status)
            print(_format(reqs), file=out)
            print(f'共 {len(reqs)} 条', file=out)
        elif ns.cmd == 'import':
            n = store.import_csv(ns.file)
            print(f'已导入 {n} 条', file=out)
        elif ns.cmd == 'export':
            n = store.export_csv(ns.file, ns.status)
            print(f'已导出 {n} 条', file=out)
    except RequirementError as ex:
        for prob in ex.problems:
            print(f'错误：{prob}', file=err)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
