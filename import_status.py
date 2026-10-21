"""One-line status text for the result of a text line import (v0.21.0).

Standard library only, no display needed. The recorder window shows this line
after an import so the number of bad lines stays visible after the dialog is
closed.
"""

MAX_KINDS_SHOWN = 3


def anomaly_status_text(total, by_kind=None, truncated=False):
    """Return one status line. total is the bad line count, by_kind maps a
    kind name to its count."""
    if total <= 0:
        text = '最近一次导入：无异常行'
    else:
        text = f'最近一次导入：异常行 {total} 条'
        kinds = sorted((by_kind or {}).items(), key=lambda kv: (-kv[1], kv[0]))
        if kinds:
            shown = [f'{k} {n}' for k, n in kinds[:MAX_KINDS_SHOWN]]
            if len(kinds) > MAX_KINDS_SHOWN:
                shown.append(f'另有 {len(kinds) - MAX_KINDS_SHOWN} 类')
            text += '（' + '，'.join(shown) + '）'
    if truncated:
        text += '；已达行数上限，其余未读取'
    return text


def status_from_result(result):
    """Build the line from a replay_session.ImportResult-like object."""
    return anomaly_status_text(result.anomalies.total,
                               result.anomalies.by_kind,
                               result.truncated)
