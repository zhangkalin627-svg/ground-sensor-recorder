"""Per-channel statistics and sampling-gap report for a samples.csv (v0.18.0).

Standard library only. Read-only on the input; the optional JSON report is
created with exclusive mode and never overwrites an existing file.

Command line (no display needed):
    python channel_report.py samples.csv --json report.json
"""
import argparse
import json
import math
import statistics
import sys

CHANNELS = ('ax_m_s2', 'ay_m_s2', 'az_m_s2', 'gx_deg_s', 'gy_deg_s', 'gz_deg_s', 'pressure_pa')
GAP_FACTOR = 5.0
MAX_GAPS_LISTED = 50


def interval_stats(times, gap_factor=GAP_FACTOR):
    """Sampling interval statistics. A gap is an interval longer than
    gap_factor times the median interval. Times must be strictly increasing."""
    if len(times) < 2:
        return {'count': 0, 'median_s': None, 'mean_s': None, 'min_s': None,
                'max_s': None, 'gap_threshold_s': None, 'gap_count': 0, 'gaps': []}
    dts = [b - a for a, b in zip(times, times[1:])]
    if any(d <= 0 for d in dts):
        raise ValueError('时间必须严格递增')
    median = statistics.median(dts)
    threshold = median * gap_factor
    gaps = [{'start_s': times[i], 'duration_s': d}
            for i, d in enumerate(dts) if d > threshold]
    return {'count': len(dts), 'median_s': median, 'mean_s': sum(dts) / len(dts),
            'min_s': min(dts), 'max_s': max(dts), 'gap_threshold_s': threshold,
            'gap_count': len(gaps), 'gaps': gaps[:MAX_GAPS_LISTED]}


def channel_stats(times, values):
    """Count, extremes with their times, mean, population std, peak-to-peak."""
    if len(times) != len(values):
        raise ValueError('时间与数值长度不一致')
    if not values:
        raise ValueError('没有数据')
    if not all(math.isfinite(v) for v in values):
        raise ValueError('数据含 NaN 或无穷值')
    i_min = min(range(len(values)), key=values.__getitem__)
    i_max = max(range(len(values)), key=values.__getitem__)
    return {'count': len(values),
            'min': values[i_min], 'min_t_s': times[i_min],
            'max': values[i_max], 'max_t_s': times[i_max],
            'mean': sum(values) / len(values),
            'std': statistics.pstdev(values),
            'peak_to_peak': values[i_max] - values[i_min]}


def build_report(samples, gap_factor=GAP_FACTOR):
    """samples: objects with t_s and the CHANNELS attributes."""
    if not samples:
        raise ValueError('没有数据')
    times = [s.t_s for s in samples]
    return {'version': '0.18.0',
            'sample_count': len(samples),
            'start_s': times[0], 'end_s': times[-1],
            'duration_s': times[-1] - times[0],
            'intervals': interval_stats(times, gap_factor),
            'channels': {c: channel_stats(times, [getattr(s, c) for s in samples])
                         for c in CHANNELS}}


def report_text(report):
    iv = report['intervals']
    lines = [f"样本 {report['sample_count']} 条，时长 {report['duration_s']:.3f} s"]
    if iv['median_s']:
        lines.append(f"采样间隔 中位 {iv['median_s']*1000:.2f} ms（约 {1/iv['median_s']:.2f} Hz），"
                     f"最小 {iv['min_s']*1000:.2f} ms，最大 {iv['max_s']*1000:.2f} ms")
        lines.append(f"缺口（间隔超过中位的 {GAP_FACTOR:g} 倍）{iv['gap_count']} 处")
        for g in iv['gaps'][:10]:
            lines.append(f"  t={g['start_s']:.3f} s 起中断 {g['duration_s']:.3f} s")
    for name, c in report['channels'].items():
        lines.append(f"{name}: 最小 {c['min']:.4g}（t={c['min_t_s']:.2f}）最大 {c['max']:.4g}"
                     f"（t={c['max_t_s']:.2f}）均值 {c['mean']:.4g} 标准差 {c['std']:.4g}")
    return '\n'.join(lines)


def write_json(report, path):
    with open(path, 'x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write('\n')


def main(argv=None):
    p = argparse.ArgumentParser(description='按通道统计采样间隔、缺口和极值（只读）')
    p.add_argument('samples', help='samples.csv，本程序导出的格式')
    p.add_argument('--json', help='JSON 报告路径；已存在则拒绝覆盖')
    args = p.parse_args(argv)
    try:
        from recorder import load_csv
        report = build_report(load_csv(args.samples))
        if args.json:
            write_json(report, args.json)
    except (OSError, ValueError, UnicodeError) as e:
        print(f'失败：{e}', file=sys.stderr)
        return 1
    print(report_text(report))
    if args.json:
        print(f'已写入 {args.json}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
