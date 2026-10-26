"""Read-only sensor adapters for the ground sensor recorder.

Standard library only. An adapter can only read samples: it has no write path,
no control outputs, and no hardware-specific protocol. Opening a real serial
port or device is left to the caller, which passes in an iterator of lines.
"""
import csv
import json
import time
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from recorder import FIELDS, Sample, simulated

MAX_LINE = 512
MAX_ANOMALIES = 1000
MAX_HEADER_SKIPS_PER_READ = 1000
HEADER_LINE = ','.join(FIELDS)


@dataclass(frozen=True)
class DeviceInfo:
    """Identity of the data source. Unknown values stay '未知', never guessed."""
    name: str
    serial: str = '未知'
    firmware: str = '未知'
    source: str = ''
    note: str = ''


def write_device_info(directory, info):
    path = Path(directory) / 'device.json'
    with path.open('w', encoding='utf-8') as f:
        json.dump(asdict(info), f, ensure_ascii=False, indent=2)
    return path


def read_device_info(directory):
    with (Path(directory) / 'device.json').open(encoding='utf-8') as f:
        return DeviceInfo(**json.load(f))


class AnomalyLog:
    """Bounded anomaly record; total and by_kind keep counting past the cap."""

    def __init__(self, limit=MAX_ANOMALIES):
        self.entries = deque(maxlen=limit)
        self.total = 0
        self.by_kind = {}

    def add(self, kind, detail=''):
        self.total += 1
        self.by_kind[kind] = self.by_kind.get(kind, 0) + 1
        stamp = datetime.now().isoformat(timespec='milliseconds')
        self.entries.append((stamp, kind, str(detail)[:200]))

    def save(self, directory):
        path = Path(directory) / 'anomalies.csv'
        with path.open('w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['local_time', 'kind', 'detail'])
            writer.writerows(self.entries)
            if self.total > len(self.entries):
                stamp = datetime.now().isoformat(timespec='milliseconds')
                writer.writerow([stamp, 'truncated',
                                 f'仅保留最近 {len(self.entries)} 条，共 {self.total} 条'])
        return path


class SensorAdapter:
    """Read-only source. read() returns a Sample, or None when nothing usable
    was read (bad line, or end of stream; check finished)."""
    info = DeviceInfo('未命名')
    finished = False

    def read(self):
        raise NotImplementedError

    def close(self):
        pass


class SimulatedAdapter(SensorAdapter):
    def __init__(self, clock=time.monotonic):
        self.info = DeviceInfo('模拟数据', source='recorder.simulated')
        self._clock = clock
        self._t0 = clock()

    def read(self):
        return simulated(self._clock() - self._t0)


class LineAdapter(SensorAdapter):
    """Parse one CSV text line per sample, in the recorder's FIELDS order.

    lines: any iterator of str or bytes (an open file, or a reader the caller
    wraps around a port). Bad lines are logged to anomalies and skipped; they
    never raise. Blank lines and the header line are skipped silently. To keep
    one read bounded, it skips at most MAX_HEADER_SKIPS_PER_READ repeated headers.
    """

    def __init__(self, lines, info, anomalies=None):
        self.info = info
        self.anomalies = anomalies if anomalies is not None else AnomalyLog()
        self._lines = iter(lines)
        self._last_t = None
        self.finished = False

    def read(self):
        if self.finished:
            return None
        for _ in range(MAX_HEADER_SKIPS_PER_READ):
            try:
                raw = next(self._lines)
            except StopIteration:
                self.finished = True
                return None
            if isinstance(raw, bytes):
                raw = raw.decode('utf-8', errors='replace')
            text = raw.strip()
            if not text:
                return None
            if text.lstrip('\ufeff') == HEADER_LINE:
                continue
            if len(text) > MAX_LINE:
                self.anomalies.add('line_too_long', f'{len(text)} 字符')
                return None
            parts = [p.strip() for p in text.split(',')]
            if len(parts) != len(FIELDS):
                self.anomalies.add('field_count', f'期望 {len(FIELDS)} 项，收到 {len(parts)} 项：{text}')
                return None
            try:
                sample = Sample.parse(dict(zip(FIELDS, parts)))
            except (ValueError, TypeError) as e:
                self.anomalies.add('invalid', f'{e}：{text}')
                return None
            if self._last_t is not None and sample.t_s <= self._last_t:
                self.anomalies.add('time_order', f't={sample.t_s} 不大于上一条 {self._last_t}')
                return None
            self._last_t = sample.t_s
            return sample
        return None


def drain(adapter, max_reads=500):
    """Read at most max_reads times (bounded work per UI tick); return good samples."""
    out = []
    for _ in range(max_reads):
        if adapter.finished:
            break
        sample = adapter.read()
        if sample is not None:
            out.append(sample)
    return out
