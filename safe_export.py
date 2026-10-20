"""Create-only CSV exports; never overwrite a database or an existing file."""
import csv
from pathlib import Path

def export_new(destination, source, fields, rows):
    target=Path(destination)
    if target.resolve()==Path(source).resolve():
        raise ValueError('导出路径不能与数据库相同')
    # Exclusive creation rejects existing targets, hard links and symlinks.
    with target.open('x',newline='',encoding='utf-8-sig') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(row.as_row() for row in rows)
