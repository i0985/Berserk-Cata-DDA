#!/usr/bin/env python3
"""Complete restored strings in Chinese and real gettext plural entries."""
import ast
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/Berserk'


def source(block):
    value = None
    for row in block.splitlines():
        if row.startswith('msgid '): value = ast.literal_eval(row[6:])
        elif value is not None and row.startswith('"'): value += ast.literal_eval(row)
        elif value is not None and row.startswith(('msgstr', 'msgid_plural')): break
    return value


def main():
    zh = json.loads((ROOT / 'tools/recovery_33_zh.json').read_text())
    path = MOD / 'lang/po/zh_CN.po'
    blocks = [b.strip('\n') for b in path.read_text().split('\n\n') if b.strip()]
    known = {source(b) for b in blocks}
    for en, translated in zh.items():
        if en not in known:
            blocks.append('#. Restored 3.3 gameplay fixes\nmsgid ' + json.dumps(en, ensure_ascii=False) + '\nmsgstr ' + json.dumps(translated, ensure_ascii=False))
    path.write_text('\n\n'.join(blocks).rstrip() + '\n')
    names = [('the Count','Графа'),('Wyald','Уайлда'),('Rosine','Розины'),
             ('Grunbeld','Грюнбельда'),('Slan','Слан'),('Ubik','Убика'),('Conrad','Конрада')]
    for file in ['ru.po', 'zh_CN.po', 'Berserk.pot']:
        path = MOD / 'lang/po' / file
        blocks = [b.strip('\n') for b in path.read_text().split('\n\n') if b.strip()]
        singulars = {'Projection of ' + en for en, _ in names}
        blocks = [b for b in blocks if source(b) not in singulars]
        for en, ru in names:
            singular = 'Projection of ' + en; plural = 'Projections of ' + en
            block = '#. Restored 3.3 projection names\nmsgid ' + json.dumps(singular) + '\nmsgid_plural ' + json.dumps(plural)
            values = ([f'Проекция {ru}', f'Проекции {ru}', f'Проекций {ru}'] if file == 'ru.po'
                      else [zh[singular]] if file == 'zh_CN.po' else ['', ''])
            for i, value in enumerate(values):
                block += '\nmsgstr[' + str(i) + '] ' + json.dumps(value, ensure_ascii=False)
            blocks.append(block)
        path.write_text('\n\n'.join(blocks).rstrip() + '\n')
    for locale in ['ru', 'zh_CN']:
        subprocess.run(['msgfmt', '--check', '-o', str(MOD / f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo'),
                        str(MOD / f'lang/po/{locale}.po')], check=True)
    print('Restored strings translated in RU/ZH; seven names have real plural entries.')


if __name__ == '__main__': main()
