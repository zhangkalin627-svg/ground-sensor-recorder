"""Single command entry for the generic ground engineering tools, v0.33.0."""
import json
from pathlib import Path
import subprocess
import sys

VERSION = '0.33.0'
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
    if not args or args[0] in ('-h','--help'):
        print(f'地面实验工具工作台 v{VERSION}')
        print('用法: python workbench.py <命令> [参数...]')
        print('命令: ' + ', '.join(COMMANDS))
        print('      modules  查看 15 个模块的当前状态')
        return 0 if args else 2
    command=args.pop(0)
    if command=='modules':
        for number, name, status, route in MODULES:
            suffix=f' -> {route}' if route else ''
            print(f'{number} {name}: {status}{suffix}')
        return 0
    target=COMMANDS.get(command)
    if not target:
        print(f'未知命令: {command}', file=sys.stderr)
        print('可用命令: ' + ', '.join([*COMMANDS, 'modules']), file=sys.stderr)
        return 2
    return subprocess.call([sys.executable, str(Path(__file__).with_name(target)), *args])


if __name__=='__main__':
    sys.exit(main())
