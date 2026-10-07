#!/usr/bin/env python3
"""Append new 3.2 RU strings and compile the catalog with GNU msgfmt."""
import ast
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'mods/Berserk'
def ids(path):
    found=set();current=None
    for row in path.read_text().splitlines():
        if row.startswith('msgid '):
            if current is not None:found.add(current)
            current=ast.literal_eval(row[6:])
        elif row.startswith('"') and current is not None:current+=ast.literal_eval(row)
        elif row.startswith('msgstr') or row.startswith('msgid_plural'):
            if current is not None:found.add(current);current=None
    if current is not None:found.add(current)
    return found
strings=json.loads((ROOT/'tools/godo_32_ru.json').read_text())
for name in ['ru.po','Berserk.pot']:
    path=MOD/'lang/po'/name
    existing=ids(path)
    with path.open('a') as f:
        for source,translation in strings.items():
            if source in existing:continue
            f.write('\n#. New Horizon 3.2: Godot and dialogue\n')
            f.write('msgid '+json.dumps(source,ensure_ascii=False)+'\n')
            f.write('msgstr '+json.dumps(translation if name=='ru.po' else '',ensure_ascii=False)+'\n')
out=MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'
subprocess.run(['msgfmt','--check','-o',str(out),str(MOD/'lang/po/ru.po')],check=True)
print('Added 3.2 RU sources and compiled Berserk.mo; existing ZH catalog preserved.')
