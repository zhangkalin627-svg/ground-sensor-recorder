"""Run the offline replay -> channel -> drift workflow in one command (v0.25.0).

Standard library only; reads input logs and creates a new output directory.
Existing outputs are never overwritten.

Example:
    python workbench.py pipeline baseline.txt candidate.txt --out run-001 \
        --expected-interval 0.05 --gap-factor 1.5 --strict
"""
import argparse
import sys
from pathlib import Path

import channel_report
import drift_report
import replay_session
from recorder import load_csv

VERSION = '0.25.0'


def build_pipeline(baseline_path, candidate_path, out_dir,
                   expected_interval=None, gap_factor=None,
                   max_rel_change=0.1, max_abs_change=None):
    """Create two session folders, channel reports, and one drift report.

    The output directory must not exist. This keeps every run separate and
    prevents accidental replacement of source data or previous reports.
    """
    channel_report._check_options(gap_factor, expected_interval)
    drift_report._check_options(max_rel_change, max_abs_change)
    inputs = {'baseline': Path(baseline_path), 'candidate': Path(candidate_path)}
    for label, path in inputs.items():
        if not path.is_file():
            raise ValueError(f'{label} 输入文件不存在或不是普通文件：{path}')

    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=False)
    collected = {}
    for label, source in inputs.items():
        imported = replay_session.import_lines(source, output / f'{label}_sessions')
        samples = load_csv(imported.directory / 'samples.csv')
        report = channel_report.build_report(samples, gap_factor, expected_interval)
        report_path = output / f'{label}.json'
        channel_report.write_json(report, report_path)
        collected[label] = (imported, report, report_path)

    result = drift_report.compare(
        collected['baseline'][1], collected['candidate'][1],
        max_rel_change=max_rel_change, max_abs_change=max_abs_change)
    drift_path = output / 'drift.json'
    drift_report.write_json(result, drift_path)
    return collected, result, drift_path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='一条命令完成两份文本日志的 replay、channel、drift 离线流程')
    parser.add_argument('baseline', help='基准文本行日志')
    parser.add_argument('candidate', help='候选文本行日志')
    parser.add_argument('--out', required=True, help='新建输出目录；已存在时拒绝运行')
    parser.add_argument('--expected-interval', type=float, default=None,
                        help='预期采样周期（秒）')
    parser.add_argument('--gap-factor', type=float, default=None,
                        help='缺口倍数；预期周期模式默认 1.5，中位数模式默认 5')
    parser.add_argument('--max-rel-change', type=float, default=0.1,
                        help='漂移相对阈值，默认 0.1（10%%）')
    parser.add_argument('--max-abs-change', type=float, default=None,
                        help='可选的漂移绝对阈值')
    parser.add_argument('--strict', action='store_true',
                        help='发现漂移通道时返回退出码 2')
    args = parser.parse_args(argv)
    try:
        collected, result, drift_path = build_pipeline(
            args.baseline, args.candidate, args.out,
            expected_interval=args.expected_interval,
            gap_factor=args.gap_factor,
            max_rel_change=args.max_rel_change,
            max_abs_change=args.max_abs_change)
    except (OSError, ValueError, UnicodeError) as error:
        print(f'流水线失败：{error}', file=sys.stderr)
        return 1

    for label in ('baseline', 'candidate'):
        imported, _, report_path = collected[label]
        print(f'[{label}]')
        print(replay_session.summary_text(imported))
        print(f'通道报告：{report_path}')
    print(drift_report.drift_text(result))
    print(f'漂移报告：{drift_path}')
    if args.strict and result['flagged_channels']:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())