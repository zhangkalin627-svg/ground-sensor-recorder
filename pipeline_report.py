"""Run the offline replay -> channel -> drift workflow in one command (v0.26.0).

Standard library only; reads input logs and creates a new output directory.
Existing outputs are never overwritten. A manifest records input hashes and run options.

Example:
    python workbench.py pipeline baseline.txt candidate.txt --out run-001 \
        --expected-interval 0.05 --gap-factor 1.5 --strict
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import sys
from pathlib import Path

import channel_report
import drift_report
import replay_session
from recorder import load_csv

VERSION = '0.26.0'


def file_identity(path):
    """Return a name, size, and SHA-256 without storing the source contents."""
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return {'name': path.name, 'size_bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def write_manifest(manifest, path):
    """Create the run manifest without replacing an existing file."""
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def build_pipeline(baseline_path, candidate_path, out_dir,
                   expected_interval=None, gap_factor=None,
                   max_rel_change=0.1, max_abs_change=None, strict=False):
    """Create two session folders, channel reports, a drift report, and manifest.

    The output directory must not exist. This keeps every run separate and
    prevents accidental replacement of source data or previous reports.
    """
    channel_report._check_options(gap_factor, expected_interval)
    drift_report._check_options(max_rel_change, max_abs_change)
    inputs = {'baseline': Path(baseline_path), 'candidate': Path(candidate_path)}
    for label, path in inputs.items():
        if not path.is_file():
            raise ValueError(f'{label} 输入文件不存在或不是普通文件：{path}')
    fingerprints = {label: file_identity(path) for label, path in inputs.items()}

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
    final_fingerprints = {label: file_identity(path) for label, path in inputs.items()}
    if final_fingerprints != fingerprints:
        raise ValueError('输入文件在流程运行期间发生变化；请检查后使用新输出目录重跑')

    exit_code = 2 if strict and result['flagged_channels'] else 0
    manifest = {
        'schema_version': 1,
        'pipeline_version': VERSION,
        'created_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z'),
        'inputs': fingerprints,
        'options': {'expected_interval_s': expected_interval, 'gap_factor': gap_factor,
                    'max_rel_change': max_rel_change, 'max_abs_change': max_abs_change,
                    'strict': bool(strict)},
        'outputs': {'baseline_sessions': 'baseline_sessions',
                    'candidate_sessions': 'candidate_sessions',
                    'baseline_report': 'baseline.json', 'candidate_report': 'candidate.json',
                    'drift_report': 'drift.json'},
        'flagged_channels': result['flagged_channels'],
        'exit_code': exit_code,
    }
    manifest_path = output / 'pipeline_manifest.json'
    write_manifest(manifest, manifest_path)
    return collected, result, drift_path, manifest_path, manifest


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
        collected, result, drift_path, manifest_path, manifest = build_pipeline(
            args.baseline, args.candidate, args.out,
            expected_interval=args.expected_interval,
            gap_factor=args.gap_factor,
            max_rel_change=args.max_rel_change,
            max_abs_change=args.max_abs_change,
            strict=args.strict)
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
    print(f'运行清单：{manifest_path}')
    return manifest['exit_code']


if __name__ == '__main__':
    sys.exit(main())