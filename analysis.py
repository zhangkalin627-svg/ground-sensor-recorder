"""Offline ground experiment CSV statistics. Does not modify source data."""
import argparse
import csv
import json
import statistics
import math
import sys
from pathlib import Path
from recorder import FIELDS, load_csv

UNITS = dict(zip(FIELDS[1:], ['m/s²']*3 + ['deg/s']*3 + ['Pa']))

def summarize(path, expected_interval_s=None, gap_factor=1.5):
    if expected_interval_s is not None and (not math.isfinite(expected_interval_s) or expected_interval_s<=0):
        raise ValueError('预期采样周期须为有限正数')
    if not math.isfinite(gap_factor) or gap_factor<=1:
        raise ValueError('缺口倍数须为大于 1 的有限数值')
    rows = load_csv(path)
    intervals = [b.t_s-a.t_s for a, b in zip(rows, rows[1:])]
    channels = {}
    for field in FIELDS[1:]:
        values = [getattr(row, field) for row in rows]
        channels[field] = dict(unit=UNITS[field], count=len(values), minimum=min(values),
                               maximum=max(values), mean=statistics.mean(values),
                               population_stddev=statistics.pstdev(values))
        channels[field]['first_minimum_t_s']=rows[values.index(min(values))].t_s
        channels[field]['first_maximum_t_s']=rows[values.index(max(values))].t_s
    threshold=None if expected_interval_s is None else expected_interval_s*gap_factor
    if threshold is not None and not math.isfinite(threshold): raise ValueError('缺口阈值超出有限范围')
    gaps=[] if threshold is None else [dict(start_t_s=rows[i].t_s,end_t_s=rows[i+1].t_s,interval_s=dt)
                                      for i,dt in enumerate(intervals) if dt>threshold]
    return dict(source=str(Path(path).resolve()), sample_count=len(rows),
                gaps=dict(assessed=threshold is not None,expected_interval_s=expected_interval_s,
                          gap_factor=gap_factor,threshold_s=threshold,count=None if threshold is None else len(gaps),
                          intervals=gaps,note='仅标记间隔超过阈值，不估算丢失样本数量；未指定周期则不判定缺口。'),
                duration_s=rows[-1].t_s-rows[0].t_s,
                sampling_interval_s=None if not intervals else dict(
                    minimum=min(intervals), maximum=max(intervals), mean=statistics.mean(intervals)),
                channels=channels)

def report(paths, expected_interval_s=None, gap_factor=1.5):
    if len(paths) not in (1, 2):
        raise ValueError('需要一份或两份 CSV 文件')
    summaries = [summarize(path,expected_interval_s,gap_factor) for path in paths]
    result = dict(schema_version=1, tool_version='0.17.0', records=summaries,
                  notes=['统计比较不对齐时间，不进行信号相减。', '输入文件不含来源标记；不能仅凭数值判断模拟或实测。'])
    if len(summaries) == 2:
        result['mean_difference_second_minus_first'] = {
            field: dict(unit=UNITS[field], value=summaries[1]['channels'][field]['mean']-
                        summaries[0]['channels'][field]['mean']) for field in FIELDS[1:]}
    return result

def write_report(path, data, inputs):
    target = Path(path)
    for source in inputs:
        source = Path(source)
        if target.resolve() == source.resolve() or (target.exists() and target.samefile(source)):
            raise ValueError('报告路径不能与输入文件相同')
    # Exclusive creation also protects existing reports and symlinks from overwrite.
    encoded = json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    with target.open('x', encoding='utf-8') as stream:
        stream.write(encoded)

def main(argv=None):
    parser = argparse.ArgumentParser(description='地面实验 CSV 离线统计与比较 v0.17.0')
    parser.add_argument('inputs', nargs='+', help='一份或两份记录器格式 CSV')
    parser.add_argument('--output', help='新建 JSON 报告路径；不覆盖已有文件')
    parser.add_argument('--expected-interval',type=float,help='预期采样周期（秒），指定后才判断缺口')
    parser.add_argument('--gap-factor',type=float,default=1.5,help='间隔严格超过该倍数时标记，默认 1.5')
    args = parser.parse_args(argv)
    try:
        data = report(args.inputs,args.expected_interval,args.gap_factor)
        if args.output:
            write_report(args.output, data, args.inputs)
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, ArithmeticError, csv.Error, UnicodeError) as e:
        print(f'分析失败：{e}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
