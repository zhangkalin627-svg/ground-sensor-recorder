"""Offline replay of a text line log into a session folder (v0.17.0).

Standard library only. Read-only: the source file is opened for reading and
never modified; nothing is sent to any device. Lines are parsed by
adapters.LineAdapter in the recorder's CSV field order. Bad lines go to
anomalies.csv instead of stopping the import.

Command line (no display needed):
    python replay_session.py input.txt --out sessions
"""
import argparse
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from adapters import MAX_LINE, AnomalyLog, DeviceInfo, LineAdapter, drain, write_device_info
from recorder import MAX_ROWS, save_csv

MAX_FILE_BYTES = 50 * 1024 * 1024


@dataclass
class ImportResult:
    samples: list
    anomalies: AnomalyLog
    info: DeviceInfo
    directory: Path = None
    truncated: bool = False


def bounded_lines(f, max_line=MAX_LINE):
    """Yield lines from a binary file; a line longer than max_line is never
    held in memory whole. It is yielded as an over-long placeholder so the
    adapter logs it as line_too_long."""
    while True:
        chunk = f.readline(max_line + 1)
        if not chunk:
            return
        if len(chunk) > max_line and not chunk.endswith(b'\n'):
            while True:
                rest = f.readline(max_line + 1)
                if not rest or rest.endswith(b'\n'):
                    break
            yield b'x' * (max_line + 1)
        else:
            yield chunk


def import_lines(path, out_base=None, name=None):
    path = Path(path)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError(f'文件超过 {MAX_FILE_BYTES // 1024 // 1024} MB 限制')
    anomalies = AnomalyLog()
    info = DeviceInfo(name or f'文本行回放：{path.name}', source=path.name,
                      note='离线回放，非实时设备；序列号与固件未知')
    samples, truncated = [], False
    with path.open('rb') as f:
        adapter = LineAdapter(bounded_lines(f), info, anomalies)
        while not adapter.finished and not truncated:
            for sample in drain(adapter, 500):
                if len(samples) >= MAX_ROWS:
                    truncated = True
                    break
                samples.append(sample)
    if truncated:
        anomalies.add('row_limit', f'超过 {MAX_ROWS} 条，其余未读取')
    if not samples:
        raise ValueError(f'没有可用样本；异常行 {anomalies.total} 条')
    directory = None
    if out_base:
        directory = Path(out_base) / (datetime.now().strftime('%Y%m%d-%H%M%S')
                                      + '-lines-' + uuid.uuid4().hex[:8])
        directory.mkdir(parents=True)
        save_csv(directory / 'samples.csv', samples)
        anomalies.save(directory)
        write_device_info(directory, info)
    return ImportResult(samples, anomalies, info, directory, truncated)


def summary_text(result):
    s = result.samples
    lines = [f'有效样本 {len(s)} 条，时间 {s[0].t_s:g} s 到 {s[-1].t_s:g} s',
             f'异常行 {result.anomalies.total} 条']
    for kind, n in sorted(result.anomalies.by_kind.items()):
        lines.append(f'  {kind}: {n}')
    if result.truncated:
        lines.append(f'已达 {MAX_ROWS} 条上限，其余未读取')
    if result.directory:
        lines.append(f'已保存到 {result.directory}（samples.csv、anomalies.csv、device.json）')
    return '\n'.join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description='把文本行日志导入为一个采集目录（只读）')
    p.add_argument('input')
    p.add_argument('--out', help='保存目录；省略则只检查、不写文件')
    p.add_argument('--name', help='设备名称（可选）')
    args = p.parse_args(argv)
    try:
        result = import_lines(args.input, args.out, args.name)
    except (OSError, ValueError) as e:
        print(f'导入失败：{e}', file=sys.stderr)
        return 1
    print(summary_text(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
