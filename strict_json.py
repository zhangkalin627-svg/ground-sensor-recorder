"""Shared bounded JSON reader for local text databases."""
import json

MAX_BYTES=16*1024*1024
MAX_RECORDS=10000

def unique_pairs(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError(f'JSON 重复字段：{k}')
        result[k]=v
    return result

def reject_constant(value):
    raise ValueError(f'JSON 不允许非有限数值：{value}')

def read(stream):
    # Count encoded bytes so a multibyte text document cannot bypass the bound.
    raw=stream.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES or len(raw.encode('utf-8'))>MAX_BYTES:
        raise ValueError('JSON 文件超过 16 MiB 限制')
    try:
        return json.loads(raw,object_pairs_hook=unique_pairs,parse_constant=reject_constant)
    except RecursionError as e:
        raise ValueError('JSON 嵌套过深') from e

def records(rows):
    if not isinstance(rows,list) or len(rows)>MAX_RECORDS:
        raise ValueError('记录必须为列表且不超过 10000 条')

def schema(value):
    if type(value) is not int or value!=1:
        raise ValueError('不支持的 schema_version，必须是整数 1')
