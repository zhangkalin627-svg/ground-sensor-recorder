"""Read-only local document fingerprints for generic engineering records."""
import strict_json
import argparse
import hashlib
import json
from pathlib import Path
import sys
from configuration import key, text, validate as validate_configuration
import os
import tempfile

FIELDS={'id','version','title','source','path','sha256','part_id','part_version'}

def fingerprint(path):
    digest=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): digest.update(block)
    return digest.hexdigest()

def load(path):
    if not Path(path).exists(): return {'schema_version':1,'documents':[]}
    with open(path,encoding='utf-8') as f: data=strict_json.read(f)
    if not isinstance(data,dict) or set(data)!={'schema_version','documents'} or data['schema_version']!=1 or not isinstance(data['documents'],list):
        raise ValueError('资料索引格式错误')
    strict_json.schema(data['schema_version'])
    strict_json.records(data['documents'])
    seen=set()
    for row in data['documents']:
        if not isinstance(row,dict) or set(row)!=FIELDS: raise ValueError('资料字段错误')
        k=key(row['id'],row['version'])
        if k in seen: raise ValueError('资料编号版本重复')
        seen.add(k)
        for field in FIELDS: text(row[field],field,field not in ('part_id','part_version'))
        if len(row['sha256'])!=64 or any(c not in '0123456789abcdef' for c in row['sha256']): raise ValueError('哈希格式错误')
        if bool(row['part_id'])!=bool(row['part_version']): raise ValueError('零件编号版本须同时提供')
        if row['part_id']: key(row['part_id'],row['part_version'])
    return data

def part_status(row,configuration=None):
    if not row['part_id']: return '无关联'
    if configuration is None: return '未核对'
    with open(configuration,encoding='utf-8') as f: data=strict_json.read(f)
    index=validate_configuration(data)
    return '存在' if key(row['part_id'],row['part_version']) in index else '未知'

def register(db,doc_id,version,title,source,path,part_id='',part_version='',configuration=None):
    data=load(db); k=key(doc_id,version)
    if any(key(r['id'],r['version'])==k for r in data['documents']): raise ValueError('资料编号版本重复')
    if bool(part_id)!=bool(part_version): raise ValueError('零件编号版本须同时提供')
    if part_id: key(part_id,part_version)
    path=Path(path).resolve(strict=True)
    if not path.is_file(): raise ValueError('资料必须是文件')
    if path==Path(db).resolve(): raise ValueError('不能将索引本身登记为资料')
    row=dict(id=doc_id,version=version,title=text(title,'title'),source=text(source,'source'),
             path=str(path),sha256=fingerprint(path),part_id=part_id,part_version=part_version)
    if part_status(row,configuration)=='未知': raise ValueError('关联零件版本不存在')
    if len(data['documents'])>=strict_json.MAX_RECORDS: raise ValueError('资料记录已达到 10000 条上限')
    data['documents'].append(row)
    target=Path(db).absolute(); fd,tmp=tempfile.mkstemp(dir=target.parent,prefix='.doc-index-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return row

def check(db,configuration=None):
    results=[]
    for row in load(db)['documents']:
        try: status='一致' if fingerprint(row['path'])==row['sha256'] else '已变更'
        except FileNotFoundError: status='文件缺失'
        except OSError: status='无法读取'
        results.append(dict(id=row['id'],version=row['version'],file_status=status,
                            part_status=part_status(row,configuration),source=row['source']))
    return results

def migrate(db, old_root, new_root, apply=False):
    """Map registered paths only. Preview by default; all-or-nothing update."""
    data=load(db)
    old=Path(old_root).absolute()
    new=Path(new_root).resolve(strict=True)
    if not new.is_dir(): raise ValueError('新根路径必须是目录')
    plan=[]
    for row in data['documents']:
        try: relative=Path(row['path']).relative_to(old)
        except ValueError: continue
        proposed=new/relative
        item=dict(id=row['id'],version=row['version'],old_path=row['path'],new_path=str(proposed),status='可迁移')
        try:
            target=proposed.resolve(strict=True)
            if not target.is_relative_to(new): raise ValueError('目标链接越出新根目录')
            if not target.is_file(): raise ValueError('目标不是文件')
            if target==Path(db).resolve(): raise ValueError('目标不能是索引本身')
            if fingerprint(target)!=row['sha256']: raise ValueError('目标哈希不一致')
            item['new_path']=str(target)
        except (OSError,ValueError) as e:
            item['status']='失败'; item['reason']=str(e)
        plan.append(item)
    failed=any(item['status']=='失败' for item in plan)
    if apply and failed: raise ValueError('迁移校验失败，索引未修改；请先运行预览查看失败项')
    if apply and plan:
        mapping={(item['id'],item['version']):item['new_path'] for item in plan}
        for row in data['documents']:
            row['path']=mapping.get((row['id'],row['version']),row['path'])
        target=Path(db).absolute()
        fd,tmp=tempfile.mkstemp(dir=target.parent,prefix='.doc-migrate-')
        try:
            with os.fdopen(fd,'w',encoding='utf-8') as f:
                json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,target)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    return dict(applied=bool(apply and plan),failed=failed,matches=len(plan),items=plan)

def main(argv=None):
    p=argparse.ArgumentParser(description='通用资料索引 v0.7.0')
    p.add_argument('--db',default='documents.json'); p.add_argument('--configuration')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('add')
    for option in ('id','version','title','source','file'): a.add_argument('--'+option,required=True)
    a.add_argument('--part-id',default=''); a.add_argument('--part-version',default='')
    sub.add_parser('list'); sub.add_parser('check')
    m=sub.add_parser('migrate')
    m.add_argument('--old-root',required=True); m.add_argument('--new-root',required=True)
    m.add_argument('--apply',action='store_true',help='校验全部成功后更新索引，默认仅预览')
    ns=p.parse_args(argv)
    try:
        if ns.cmd=='add': register(ns.db,ns.id,ns.version,ns.title,ns.source,ns.file,ns.part_id,ns.part_version,ns.configuration)
        elif ns.cmd=='migrate':
            result=migrate(ns.db,ns.old_root,ns.new_root,ns.apply)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            if result['failed']: return 1
        else:
            result=check(ns.db,ns.configuration) if ns.cmd=='check' else load(ns.db)
            print(json.dumps(result,ensure_ascii=False,indent=2))
            if ns.cmd=='check' and any(r['file_status']!='一致' or r['part_status']=='未知' for r in result): return 1
    except (ValueError,OSError,UnicodeError) as e:
        print(f'操作失败：{e}',file=sys.stderr); return 2
    return 0

if __name__=='__main__': raise SystemExit(main())
