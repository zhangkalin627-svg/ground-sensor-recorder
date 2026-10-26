"""Single command entry for the generic ground engineering tools, v0.31.0."""
import json
from pathlib import Path
import subprocess
import sys

VERSION = '0.31.0'
COMMANDS={'record':'recorder.py','analyze':'analysis.py','requirements':'requirements.py',
          'issues':'issues.py','configuration':'configuration.py','documents':'documents_index.py','results':'test_results.py','report':'summary_report.py',
          'channel':'channel_report.py','replay':'replay_session.py','drift':'drift_report.py',
          'pipeline':'pipeline_report.py'}
MODULES=[
    ('01','需求管理','部分实现','requirements'),
    ('02','任务与轨道资料','规划',''),
    ('03','CAD 文件索引','资料管理基础已实现，无 CAD 内核','documents'),
    ('04','结构与振动资料','规划',''),
    ('05','CFD 资料','规划',''),
    ('06','热分析资料','规划',''),
    ('07','推进系统资料','规划',''),
    ('08','电气电子资料','规划',''),
    ('09','GNC 学习资料','规划',''),
    ('10','软件版本与测试管理','测试证据与需求追踪，文本登记','results'),
    ('11','地面数据链测试','部分测试基础，无硬件在环',''),
    ('12','零件配置管理','第一代文本工具','configuration'),
    ('13','地面采集与离线分析','模拟采集与分析，硬件未实测','record / analyze / channel / replay / drift / pipeline'),
    ('14','问题管理','第一代文本工具','issues'),
    ('15','只读状态展示','规划','')]


def main(argv=None):
    args=list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ('-h','--help','help'):
        print(f'地面工程工具入口 v{VERSION}\n用法：python workbench.py <命令> [原工具参数]\n'
              '命令：modules, '+', '.join(COMMANDS)+'\n'
              '示例：python workbench.py analyze samples.csv --output report.json\n'
              '      python workbench.py channel samples.csv --expected-interval 0.01 --json report.json\n'
              '      python workbench.py replay input.txt --out sessions\n'
              '      python workbench.py drift baseline.json candidate.json --max-rel-change 0.05 --strict\n'
              '      python workbench.py pipeline baseline.txt candidate.txt --out run-001 --strict\n'
              '查看子工具帮助：python workbench.py requirements --help\n'
              'record 打开桌面窗口，需要 Tk 和图形环境。')
        return 0
    command=args.pop(0)
    if command=='modules':
        if args:
            print('modules 不接受其他参数',file=sys.stderr); return 2
        print(json.dumps([dict(id=i,name=n,status=s,command=c or None) for i,n,s,c in MODULES],ensure_ascii=False,indent=2))
        return 0
    if command not in COMMANDS:
        print('未知命令；运行 python workbench.py --help 查看入口',file=sys.stderr); return 2
    script=Path(__file__).resolve().parent/COMMANDS[command]
    try:
        # No shell, preserve arguments and working directory for local data paths.
        return subprocess.run([sys.executable,str(script),*args],check=False).returncode
    except OSError as e:
        print(f'启动失败：{e}',file=sys.stderr); return 2


if __name__ == '__main__':
    raise SystemExit(main())
