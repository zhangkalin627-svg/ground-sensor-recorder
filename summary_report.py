"""Self-contained offline HTML summary of explicitly selected local records."""
import argparse
from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path
import sys
import requirements
import issues
import configuration
import documents_index

def table(headers,rows):
    head=''.join('<th>'+escape(str(h))+'</th>' for h in headers)
    body=''.join('<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in row)+'</tr>' for row in rows)
    return '<div class="scroll"><table><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table></div>' if body else '<p>空表：0 条记录</p>'

def build(selected):
    if not selected: raise ValueError('至少指定一个输入文件')
    sections=[]
    for kind,path in selected.items():
        if not Path(path).is_file(): raise ValueError(f'输入文件不存在：{path}')
        if kind=='requirements':
            records=requirements.read_csv(path)
            rows=[(r.req_id,r.description,r.status,r.source,';'.join(r.test_ids)) for r in records]
            headers=('编号','描述','登记状态','来源','测试编号')
        elif kind=='issues':
            records=issues.read_csv(path)
            rows=[(r.issue_id,r.title,r.symptom,r.suspected_cause,r.status,r.resolution,r.retest_evidence) for r in records]
            headers=('编号','标题','现象','推测原因','登记状态','处理说明','复测依据')
        elif kind=='configuration':
            records=configuration.load(path)['parts']
            rows=[(r['id'],r['version'],r['name'],r['model'],len(r['children']),r['reason']) for r in records]
            headers=('零件编号','版本','名称','型号','直接子项种类数','变更原因')
        elif kind=='documents':
            records=documents_index.load(path)['documents']
            rows=[(r['id'],r['version'],r['title'],r['source'],r['path'],r['sha256']) for r in records]
            headers=('资料编号','版本','标题','来源','登记路径','登记 SHA-256')
        else: raise ValueError('未知资料种类')
        states=Counter(r.status for r in records) if kind in ('requirements','issues') else None
        extra='' if states is None else '<p>状态汇总：'+escape('；'.join(f'{k} {v}' for k,v in sorted(states.items())))+'</p>'
        sections.append('<section><h2>'+escape(kind)+f' · {len(records)} 条</h2><p class="source">输入：'+escape(str(Path(path).absolute()))+'</p>'+extra+table(headers,rows)+'</section>')
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>地面工程记录汇总</title><style>body{font:16px system-ui,sans-serif;background:#f3f6fa;color:#1b2b40;margin:24px auto;max-width:1250px;padding:0 20px}section{background:white;padding:20px;border-radius:12px;margin:20px 0}.scroll{overflow:auto}table{border-collapse:collapse;width:100%}th,td{border:1px solid #dce3ec;padding:10px;text-align:left;vertical-align:top;white-space:pre-wrap;overflow-wrap:anywhere}th{background:#eaf1f8}.source{color:#51647a;overflow-wrap:anywhere}</style></head><body><h1>地面工程记录汇总</h1><p>v0.15.0 · 生成时间：'''+escape(datetime.now().astimezone().isoformat(timespec='seconds'))+'''</p><p>离线静态报告，仅展示登记内容。登记状态与复测依据未经自动认证；资料哈希未在本报告中重新核对。本工具不提供专业求解或设备控制。</p>'''+''.join(sections)+'</body></html>'

def write(output,selected):
    target=Path(output)
    for source in selected.values():
        if target.resolve()==Path(source).resolve() or (target.exists() and target.samefile(source)):
            raise ValueError('输出不能覆盖输入文件')
    html=build(selected)
    with target.open('x',encoding='utf-8') as f: f.write(html)

def main(argv=None):
    p=argparse.ArgumentParser(description='离线只读 HTML 记录汇总 v0.15.0')
    for kind in ('requirements','issues','configuration','documents'): p.add_argument('--'+kind)
    p.add_argument('--output',required=True)
    ns=p.parse_args(argv)
    selected={k:getattr(ns,k) for k in ('requirements','issues','configuration','documents') if getattr(ns,k)}
    try: write(ns.output,selected)
    except (ValueError,OSError,UnicodeError) as e:
        print(f'报告生成失败：{e}',file=sys.stderr); return 2
    return 0

if __name__=='__main__': raise SystemExit(main())
