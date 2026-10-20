"""Versioned generic instrument parts and assemblies, v0.6.0."""
import strict_json
import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,31}')

def text(value, label, required=True):
    if not isinstance(value,str) or (required and not value.strip()) or len(value)>2000 or any(ord(c)<32 for c in value):
        raise ValueError(f'{label} 为空、过长或含控制字符')
    return value.strip()

def key(part,version):
    if not isinstance(part,str) or not ID.fullmatch(part) or not isinstance(version,str) or not ID.fullmatch(version):
        raise ValueError('零件编号与版本须为 1–32 位字母数字及 _ . -')
    return part.casefold()+'@'+version.casefold()

def validate(data):
    if not isinstance(data,dict) or set(data)!={'schema_version','parts'} or data['schema_version']!=1 or not isinstance(data['parts'],list):
        raise ValueError('配置文件结构错误')
    strict_json.schema(data['schema_version'])
    if len(data['parts'])>10000: raise ValueError('零件版本超过上限')
    index={}
    for p in data['parts']:
        if not isinstance(p,dict) or set(p)!={'id','version','name','model','reason','children'}: raise ValueError('零件字段错误')
        k=key(p['id'],p['version'])
        if k in index: raise ValueError('零件编号及版本重复')
        for f in ('name','reason'): text(p[f],f)
        text(p['model'],'model',False)
        if not isinstance(p['children'],list): raise ValueError('装配关系应为列表')
        index[k]=p
    for p in index.values():
        seen=set()
        for c in p['children']:
            if not isinstance(c,dict) or set(c)!={'id','version','quantity'}: raise ValueError('装配字段错误')
            k=key(c['id'],c['version'])
            if k not in index: raise ValueError('装配引用了未登记零件版本')
            if k in seen: raise ValueError('同一装配重复引用零件版本')
            seen.add(k)
            if type(c['quantity']) is not int or c['quantity']<=0: raise ValueError('数量须为正整数')
    # Iterative graph traversal avoids recursion limits for deep assemblies.
    done=set()
    for start in index:
        active=set(); stack=[(start,False)]
        while stack:
            node,exit_node=stack.pop()
            if exit_node: active.remove(node); done.add(node); continue
            if node in active: raise ValueError('装配关系存在循环')
            if node in done: continue
            active.add(node); stack.append((node,True))
            for c in index[node]['children']: stack.append((key(c['id'],c['version']),False))
    return index

def load(path):
    if not Path(path).exists(): return {'schema_version':1,'parts':[]}
    with open(path,encoding='utf-8') as f: data=strict_json.read(f)
    validate(data)
    return data

def save(path,data):
    validate(data)
    target=Path(path).absolute()
    fd,tmp=tempfile.mkstemp(dir=target.parent,prefix='.configuration-')
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n')
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def add(path,part_id,version,name,reason,model='',children=()):
    data=copy.deepcopy(load(path))
    data['parts'].append(dict(id=part_id,version=version,name=text(name,'name'),
                              model=text(model,'model',False),reason=text(reason,'reason'),children=list(children)))
    save(path,data)

def snapshot(path,part_id,version,output):
    data=load(path); index=validate(data); root=key(part_id,version)
    if root not in index: raise ValueError('快照根零件版本不存在')
    selected=set(); todo=[root]
    while todo:
        k=todo.pop()
        if k in selected: continue
        selected.add(k)
        todo.extend(key(c['id'],c['version']) for c in index[k]['children'])
    result={'schema_version':1,'root':{'id':part_id,'version':version},
            'parts':[index[k] for k in sorted(selected)]}
    target=Path(output)
    if target.resolve()==Path(path).resolve(): raise ValueError('快照不能覆盖数据库')
    encoded=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    with target.open('x',encoding='utf-8') as f: f.write(encoded)
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description='通用地面仪器零件配置管理 v0.6.0')
    p.add_argument('--db',default='configuration.json')
    sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('add')
    for option in ('id','version','name','reason'): a.add_argument('--'+option,required=True)
    a.add_argument('--model',default='')
    a.add_argument('--child',action='append',default=[],help='零件编号@版本:数量，可重复')
    sub.add_parser('list')
    s=sub.add_parser('snapshot')
    s.add_argument('--id',required=True); s.add_argument('--version',required=True); s.add_argument('--output',required=True)
    ns=p.parse_args(argv)
    try:
        if ns.command=='add':
            children=[]
            for spec in ns.child:
                ref,quantity=spec.rsplit(':',1); part,version=ref.split('@',1)
                children.append(dict(id=part,version=version,quantity=int(quantity)))
            add(ns.db,ns.id,ns.version,ns.name,ns.reason,ns.model,children)
        elif ns.command=='snapshot': snapshot(ns.db,ns.id,ns.version,ns.output)
        else: print(json.dumps(load(ns.db),ensure_ascii=False,indent=2))
    except (ValueError,OSError,UnicodeError) as e:
        print(f'操作失败：{e}',file=sys.stderr); return 2
    return 0

if __name__=='__main__': raise SystemExit(main())
