"""Run the offline replay -> channel -> drift workflow in one command (v0.33.0).

Standard library only; reads input logs and creates a new output directory.
Existing outputs are never overwritten. A manifest records input hashes, run
options, and either the completed result or the stage and outputs present at failure.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
from pathlib import Path

import channel_report
import drift_report
import replay_session
from recorder import load_csv

VERSION = '0.33.0'
MAX_INPUT_BYTES = replay_session.MAX_FILE_BYTES
EXPECTED_OUTPUTS = (
    'baseline_sessions', 'candidate_sessions', 'baseline.json',
    'candidate.json', 'drift.json', 'pipeline_manifest.json',
)


class PipelineFailure(Exception):
    """A workflow error annotated with its stage and failure-manifest status."""
    def __init__(self, stage, cause, output_dir, output_created, manifest_written):
        self.stage = stage
        self.cause = cause
        self.output_dir = Path(output_dir)
        self.output_created = output_created
        self.manifest_written = manifest_written
        super().__init__(str(cause))


def file_identity(path):
    """Return a name, size, and SHA-256 without storing the source contents."""
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return {'name': path.name, 'size_bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def _write_json_exclusive(value, path):
    """Write JSON exclusively and remove this call's partial file on failure."""
    path = Path(path)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    created_stat = os.fstat(fd)
    try:
        handle = os.fdopen(fd, 'w', encoding='utf-8')
        fd = None
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    except BaseException:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            current_stat = path.lstat()
            if (current_stat.st_dev, current_stat.st_ino) == (
                    created_stat.st_dev, created_stat.st_ino):
                path.unlink()
        except OSError:
            pass
        raise


def write_manifest(manifest, path):
    """Write a manifest exclusively, cleaning this call's partial file on error."""
    _write_json_exclusive(manifest, path)


def _utc_now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _present_outputs(output):
    """List paths relative to the new output directory, never absolute paths."""
    if not output.is_dir():
        return []
    return sorted(path.relative_to(output).as_posix() for path in output.rglob('*'))


def build_pipeline(baseline_path, candidate_path, out_dir,
                   expected_interval=None, gap_factor=None,
                   max_rel_change=0.1, max_abs_change=None, strict=False):
    """Create two session folders, channel reports, a drift report, and manifest.

    The output directory must not exist. Both input files must be regular files
    within replay_session's size limit. Failures after creation get a best-effort
    manifest with the failing stage and paths already present in that directory.
    """
    output = Path(out_dir)
    fingerprints = {}
    options = {'expected_interval_s': expected_interval, 'gap_factor': gap_factor,
               'max_rel_change': max_rel_change, 'max_abs_change': max_abs_change,
               'strict': bool(strict)}
    stage = 'preflight'
    output_created = False
    try:
        channel_report._check_options(gap_factor, expected_interval)
        drift_report._check_options(max_rel_change, max_abs_change)
        inputs = {'baseline': Path(baseline_path), 'candidate': Path(candidate_path)}
        for label, path in inputs.items():
            if not path.is_file():
                raise ValueError(f'{label} 输入文件不存在或不是普通文件：{path}')
            size_bytes = path.stat().st_size
            if size_bytes > MAX_INPUT_BYTES:
                limit_mb = MAX_INPUT_BYTES // 1024 // 1024
                raise ValueError(
                    f'{label} 输入文件超过 {limit_mb} MB 限制：{size_bytes} bytes')
        fingerprints = {label: file_identity(path) for label, path in inputs.items()}

        stage = 'create_output_directory'
        output.mkdir(parents=True, exist_ok=False)
        output_created = True
        collected = {}

        stage = 'baseline_replay'
        imported = replay_session.import_lines(inputs['baseline'], output / 'baseline_sessions')
        stage = 'baseline_channel_report'
        samples = load_csv(imported.directory / 'samples.csv')
        report = channel_report.build_report(samples, gap_factor, expected_interval)
        report_path = output / 'baseline.json'
        _write_json_exclusive(report, report_path)
        collected['baseline'] = (imported, report, report_path)

        stage = 'candidate_replay'
        imported = replay_session.import_lines(inputs['candidate'], output / 'candidate_sessions')
        stage = 'candidate_channel_report'
        samples = load_csv(imported.directory / 'samples.csv')
        report = channel_report.build_report(samples, gap_factor, expected_interval)
        report_path = output / 'candidate.json'
        _write_json_exclusive(report, report_path)
        collected['candidate'] = (imported, report, report_path)

        stage = 'drift_comparison'
        result = drift_report.compare(
            collected['baseline'][1], collected['candidate'][1],
            max_rel_change=max_rel_change, max_abs_change=max_abs_change)
        stage = 'drift_report'
        drift_path = output / 'drift.json'
        _write_json_exclusive(result, drift_path)

        stage = 'verify_inputs'
        final_fingerprints = {label: file_identity(path) for label, path in inputs.items()}
        if final_fingerprints != fingerprints:
            raise ValueError('输入文件在流程运行期间发生变化；请检查后使用新输出目录重跑')

        exit_code = 2 if strict and result['flagged_channels'] else 0
        manifest = {
            'schema_version': 1,
            'pipeline_version': VERSION,
            'status': 'completed',
            'failure_stage': None,
            'created_at_utc': _utc_now(),
            'inputs': fingerprints,
            'options': options,
            'outputs': {'baseline_sessions': 'baseline_sessions',
                        'candidate_sessions': 'candidate_sessions',
                        'baseline_report': 'baseline.json',
                        'candidate_report': 'candidate.json',
                        'drift_report': 'drift.json'},
            'flagged_channels': result['flagged_channels'],
            'exit_code': exit_code,
        }
        stage = 'write_success_manifest'
        manifest_path = output / 'pipeline_manifest.json'
        write_manifest(manifest, manifest_path)
    except Exception as error:
        manifest_written = False
        if output_created:
            try:
                partial_outputs = _present_outputs(output)
            except Exception:
                partial_outputs = []
            failure_manifest = {
                'schema_version': 1,
                'pipeline_version': VERSION,
                'status': 'failed',
                'failure_stage': stage,
                'created_at_utc': _utc_now(),
                'inputs': fingerprints,
                'options': options,
                'expected_outputs': list(EXPECTED_OUTPUTS),
                'partial_outputs': partial_outputs,
                'error_type': type(error).__name__,
                'exit_code': 1,
            }
            try:
                write_manifest(failure_manifest, output / 'pipeline_manifest.json')
            except Exception:
                pass
            else:
                manifest_written = True
        raise PipelineFailure(stage, error, output, output_created, manifest_written) from error

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
    except PipelineFailure as error:
        print(f'流水线失败（阶段 {error.stage}）：{error.cause}', file=sys.stderr)
        if error.manifest_written:
            print(f'部分输出清单：{error.output_dir / "pipeline_manifest.json"}', file=sys.stderr)
        elif error.output_created:
            print(f'失败清单未能写入；请检查输出目录：{error.output_dir}', file=sys.stderr)
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
