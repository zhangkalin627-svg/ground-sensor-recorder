"""Compare two channel_report.py JSON reports and flag drifted channels (v0.22.0).

Standard library only. Read-only on both inputs; the optional JSON output is
created with exclusive mode and never overwrites an existing file.

Command line (no display needed):
    python drift_report.py baseline.json candidate.json
    python drift_report.py a.json b.json --max-rel-change 0.05 --json drift.json
    python drift_report.py a.json b.json --max-abs-change 0.5 --strict

A channel is flagged as drift when any of its metrics (count, mean, std, min,
max, peak_to_peak) changes by more than the relative threshold (default 10%)
or by more than the absolute threshold when one is given. When the baseline
value is zero the relative change is undefined, so any nonzero change counts
as drift.
"""
import argparse
import json
import math
import sys

VERSION = '0.22.0'
METRICS = ('count', 'mean', 'std', 'min', 'max', 'peak_to_peak')
INTERVAL_KEYS = ('sample_count', 'duration_s', 'median_s', 'gap_count')


def _number(name, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name} 不是数值')
    if not math.isfinite(value):
        raise ValueError(f'{name} 不是有限数值')
    return float(value)


def _check_options(max_rel_change, max_abs_change):
    if not isinstance(max_rel_change, (int, float)) or isinstance(max_rel_change, bool):
        raise ValueError('相对阈值必须是数值')
    value = float(max_rel_change)
    if not math.isfinite(value) or value < 0:
        raise ValueError('相对阈值必须是不小于 0 的有限数')
    if max_abs_change is not None:
        if not isinstance(max_abs_change, (int, float)) or isinstance(max_abs_change, bool):
            raise ValueError('绝对阈值必须是数值')
        absolute = float(max_abs_change)
        if not math.isfinite(absolute) or absolute <= 0:
            raise ValueError('绝对阈值必须是大于 0 的有限数')


def rel_change(base, candidate):
    """Relative change against the baseline; None when the baseline is zero."""
    if base == 0:
        return None
    return (candidate - base) / abs(base)


def validate_report(data):
    """Check that data looks like a channel_report.py JSON report."""
    if not isinstance(data, dict):
        raise ValueError('报告不是 JSON 对象')
    if not isinstance(data.get('channels'), dict) or not isinstance(data.get('intervals'), dict):
        raise ValueError('报告缺少 channels 或 intervals')
    if 'sample_count' not in data:
        raise ValueError('报告缺少 sample_count')
    return data


def load_report(path):
    with open(path, encoding='utf-8') as handle:
        return validate_report(json.load(handle))


def _metric_drift(baseline, candidate, rel, max_rel_change, max_abs_change):
    delta = candidate - baseline
    if max_abs_change is not None and abs(delta) > max_abs_change:
        return True
    if rel is None:
        return delta != 0
    return abs(rel) > max_rel_change


def compare_channels(base_channels, cand_channels, max_rel_change, max_abs_change):
    missing_in_baseline = sorted(set(cand_channels) - set(base_channels))
    missing_in_candidate = sorted(set(base_channels) - set(cand_channels))
    if missing_in_baseline or missing_in_candidate:
        parts = []
        if missing_in_baseline:
            parts.append('基准缺 ' + '、'.join(missing_in_baseline))
        if missing_in_candidate:
            parts.append('候选缺 ' + '、'.join(missing_in_candidate))
        raise ValueError('两份报告的通道不一致：' + '；'.join(parts))
    channels = {}
    flagged = []
    for name in sorted(base_channels):
        base = base_channels[name]
        cand = cand_channels[name]
        if not isinstance(base, dict) or not isinstance(cand, dict):
            raise ValueError(f'通道 {name} 的统计不是对象')
        changes = {}
        drift = False
        for metric in METRICS:
            if metric not in base or metric not in cand:
                raise ValueError(f'通道 {name} 缺少 {metric}')
            baseline = _number(f'{name}.{metric}', base[metric])
            candidate = _number(f'{name}.{metric}', cand[metric])
            rel = rel_change(baseline, candidate)
            metric_drift = _metric_drift(baseline, candidate, rel, max_rel_change, max_abs_change)
            changes[metric] = {'baseline': baseline, 'candidate': candidate,
                               'delta': candidate - baseline,
                               'rel_change': rel, 'drift': metric_drift}
            drift = drift or metric_drift
        channels[name] = {'status': 'drift' if drift else 'ok', 'changes': changes}
        if drift:
            flagged.append(name)
    return channels, flagged


def _interval_deltas(base_report, cand_report):
    pairs = (
        ('sample_count', base_report['sample_count'], cand_report['sample_count']),
        ('duration_s', base_report.get('duration_s'), cand_report.get('duration_s')),
        ('median_s', base_report['intervals'].get('median_s'),
         cand_report['intervals'].get('median_s')),
        ('gap_count', base_report['intervals'].get('gap_count'),
         cand_report['intervals'].get('gap_count')),
    )
    deltas = {}
    for name, base, cand in pairs:
        if base is None or cand is None:
            deltas[name] = {'baseline': None, 'candidate': None,
                            'delta': None, 'rel_change': None}
            continue
        baseline = _number(name, base)
        candidate = _number(name, cand)
        deltas[name] = {'baseline': baseline, 'candidate': candidate,
                        'delta': candidate - baseline,
                        'rel_change': rel_change(baseline, candidate)}
    return deltas


def compare(base_report, cand_report, max_rel_change=0.1, max_abs_change=None):
    """Compare two validated reports. Returns a plain dict result."""
    _check_options(max_rel_change, max_abs_change)
    channels, flagged = compare_channels(base_report['channels'], cand_report['channels'],
                                         float(max_rel_change), max_abs_change)
    return {'version': VERSION,
            'baseline_version': base_report.get('version'),
            'candidate_version': cand_report.get('version'),
            'thresholds': {'max_rel_change': float(max_rel_change),
                           'max_abs_change': None if max_abs_change is None
                           else float(max_abs_change)},
            'intervals': _interval_deltas(base_report, cand_report),
            'channels': channels,
            'flagged_channels': flagged}


def _fmt(value):
    return '—' if value is None else f'{value:.6g}'


def _signed(value):
    return '—' if value is None else f'{value:+.6g}'


def _pct(value):
    return '—' if value is None else f'{value * 100:+.2f}%'


def drift_text(result):
    lines = [f"阈值 相对 {_pct(result['thresholds']['max_rel_change'])}，绝对 "
             f"{_fmt(result['thresholds']['max_abs_change'])}"]
    for name in INTERVAL_KEYS:
        item = result['intervals'][name]
        line = f"{name}: {_fmt(item['baseline'])} -> {_fmt(item['candidate'])}"
        if item['delta'] is not None:
            line += f"（{_signed(item['delta'])}，{_pct(item['rel_change'])}）"
        lines.append(line)
    if result['flagged_channels']:
        lines.append('漂移通道：' + '、'.join(result['flagged_channels']))
    else:
        lines.append('没有通道超过阈值')
    for name, info in result['channels'].items():
        parts = [f"{metric} {_fmt(ch['baseline'])} -> {_fmt(ch['candidate'])}"
                 f"（{_signed(ch['delta'])}，{_pct(ch['rel_change'])}）"
                 for metric, ch in info['changes'].items() if ch['drift']]
        if parts:
            lines.append(f"{name}: " + '；'.join(parts))
    return '\n'.join(lines)


def write_json(result, path):
    with open(path, 'x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description='对比两份 channel_report.py JSON 报告并标出漂移（只读）')
    parser.add_argument('baseline', help='基准报告 JSON')
    parser.add_argument('candidate', help='候选报告 JSON')
    parser.add_argument('--max-rel-change', type=float, default=0.1,
                        help='相对变化阈值，默认 0.1（10%%）')
    parser.add_argument('--max-abs-change', type=float, default=None,
                        help='绝对变化阈值；给出后超出也算漂移')
    parser.add_argument('--json', help='结果 JSON 路径；已存在则拒绝覆盖')
    parser.add_argument('--strict', action='store_true',
                        help='有漂移通道时以退出码 2 结束')
    args = parser.parse_args(argv)
    try:
        base_report = load_report(args.baseline)
        cand_report = load_report(args.candidate)
        result = compare(base_report, cand_report, args.max_rel_change, args.max_abs_change)
        if args.json:
            write_json(result, args.json)
    except (OSError, ValueError, UnicodeError) as error:
        print(f'失败：{error}', file=sys.stderr)
        return 1
    print(drift_text(result))
    if args.json:
        print(f'已写入 {args.json}')
    if args.strict and result['flagged_channels']:
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
