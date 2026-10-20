"""User-declared ground software test evidence, not automatic certification."""
import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
from requirements import ID_RE, TEST_ID_RE, read_csv

STATES=('未运行','通过','失败')
FIELDS={'run_id','test_id','status','executed_at','commit','evidence'}

def validate(rows):
    if not isinstance(rows,list): raise ValueError('测试记录须为列表')
    seen=set()
    for row in rows:
        if not isinstance(row,dict) or set(row)!=FIELDS: raise ValueError('测试记录字段错误')
        if any(not isinstance(v,str) or len(v)>2000 or any(ord(c)<32 for c in v) for v in row.values()): raise ValueError('字段须为单行文本')
        if not ID_RE.fullmatch(row['run_id']) or not TEST_ID_RE.fullmatch(row['test_id']): raise ValueError('运行编号或测试编号非法')
        key=(row['run_id'].casefold(),row['test_id'].casefold())
        if key in seen: raise ValueError('重复运行及测试编号')
        seen.add(key)
        if row['status'] not in STATES: raise ValueError('测试状态非法')
        if not row['commit'].strip(): raise ValueError('必须记录源码提交标识')
        if row['status']!='未运行':
            if not row['evidence'].strip(): raise ValueError('已执行测试须提供证据说明')
            try: stamp=datetime.fromisoformat(row['executed_at'])
            except ValueError: raise ValueError('执行时间须为 ISO 8601')
            if stamp.utcoffset() is None: raise ValueError('执行时间必须带时区')
        elif row['executed_at']: raise ValueError('未运行记录不能填写执行时间')
    return rows

def load(path):
    if not Path(path).exists(): return []
    with open(path,encoding='utf-8') as f: return validate(json.load(f))

def add(path,record):
    rows=validate(load(path)+[record]); target=Path(path).absolute()
    fd,tmp=tempfile.mkstemp(dir=target.parent,prefix='.results-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(rows,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def trace(requirements,results,run_id,commit):
    if not run_id.strip() or not commit.strip(): raise ValueError('追踪须指定运行编号和源码提交标识')
    rows=load(results)
    selected={r['test_id'].casefold():r for r in rows if r['run_id'].casefold()==run_id.casefold() and r['commit']==commit}
    output=[]
    for req in read_csv(requirements):
        tests=[dict(test_id=t,status=selected.get(t.casefold(),{}).get('status','无记录')) for t in req.test_ids]
        states=[t['status'] for t in tests]
        state='失败' if '失败' in states else '通过' if states and all(s=='通过' for s in states) else '未完成'
        output.append(dict(req_id=req.req_id,declared_requirement_status=req.status,tests=tests,trace_status=state))
    return dict(run_id=run_id,commit=commit,requirements=output,
                limitation='仅汇总用户登记的执行结果，不运行测试、不验证证据真实性，也不修改需求状态。')

def main(argv=None):
    p=argparse.ArgumentParser(description='通用软件测试证据与需求追踪 v0.9.0')
    p.add_argument('--db',default='test_results.json')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('add')
    for opt in ('run-id','test-id','status','commit'): a.add_argument('--'+opt,required=True)
    a.add_argument('--executed-at',default=''); a.add_argument('--evidence',default='')
    t=sub.add_parser('trace')
    t.add_argument('--requirements',required=True); t.add_argument('--run-id',required=True); t.add_argument('--commit',required=True)
    ns=p.parse_args(argv)
    try:
        if ns.cmd=='add': add(ns.db,{k:getattr(ns,k) for k in FIELDS})
        else: print(json.dumps(trace(ns.requirements,ns.db,ns.run_id,ns.commit),ensure_ascii=False,indent=2))
    except (OSError,ValueError,UnicodeError) as e:
        print(f'操作失败：{e}',file=sys.stderr); return 2
    return 0

if __name__=='__main__': raise SystemExit(main())
