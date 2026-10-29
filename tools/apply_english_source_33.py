#!/usr/bin/env python3
"""Publish English JSON sources with the approved Russian text in gettext.

Manuscript builders may assemble Russian drafts; the canonical build always
finishes here. Missing English is a build error, never a silent fallback.
"""
import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/Berserk'
DATA = ROOT / 'tools/translations/english_33.json'
CYRILLIC = re.compile(r'[А-Яа-яЁё]')
TAGS = re.compile(r'<[^<>]+>')


def translations():
    rows = json.loads(DATA.read_text())
    result = {}
    reverse = {}
    for row in rows:
        ru, en = row['ru'], row['en']
        if not en or CYRILLIC.search(en):
            raise ValueError(f"Missing English translation {row['id']}")
        if TAGS.findall(ru) != TAGS.findall(en):
            raise ValueError(f"Changed runtime tags in translation {row['id']}")
        if ru[:1] in ('&', '*') and en[:1] != ru[:1]:
            raise ValueError(f"Changed narrator marker in translation {row['id']}")
        if en in reverse and reverse[en] != ru:
            raise ValueError(f"Ambiguous Russian lookup: {row['id']}")
        result[ru] = en
        reverse[en] = ru
    return result


def convert(value, mapping, path=''):
    if isinstance(value, str):
        if CYRILLIC.search(value):
            if value not in mapping:
                raise ValueError(f'Missing English at {path}: {value!r}')
            return mapping[value]
        return value
    if isinstance(value, list):
        return [convert(x, mapping, f'{path}/{i}') for i, x in enumerate(value)]
    if isinstance(value, dict):
        return {k: convert(v, mapping, f'{path}/{k}') for k, v in value.items()}
    return value


def fields(block):
    out = {}; active = None
    for line in block.splitlines():
        m = re.match(r'(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?) (".*")$', line)
        if m:
            active = m[1]; out[active] = ast.literal_eval(m[2])
        elif line.startswith('"') and active:
            out[active] += ast.literal_eval(line)
        else:
            active = None
    return out


def block(en, ru, template=False):
    return ('#. English base source; approved Russian manuscript 2026-10-24\n'
            'msgid ' + json.dumps(en, ensure_ascii=False) + '\nmsgstr ' +
            json.dumps('' if template else ru, ensure_ascii=False))


def catalogs(mapping):
    pairs = {en: ru for ru, en in mapping.items()}
    for filename in ('Berserk.pot', 'ru.po', 'zh_CN.po'):
        path = MOD / 'lang/po' / filename
        remaining = dict(pairs); output = []; chinese = {}
        for old in path.read_text().split('\n\n'):
            if not old.strip():
                continue
            f = fields(old); key = f.get('msgid', '')
            if CYRILLIC.search(key):
                # A genuine existing Chinese translation follows its new key.
                if filename == 'zh_CN.po' and key in mapping and f.get('msgstr') and not CYRILLIC.search(f['msgstr']):
                    chinese[mapping[key]] = f['msgstr']
                continue
            if not f.get('msgctxt') and key in remaining:
                ru = remaining.pop(key)
                if filename != 'zh_CN.po':
                    old = block(key, ru, filename == 'Berserk.pot')
            output.append(old.strip())
        if filename == 'zh_CN.po':
            seen = {fields(x).get('msgid') for x in output}
            for en, zh in chinese.items():
                if en not in seen:
                    output.append(block(en, zh))
        else:
            output += [block(en, ru, filename == 'Berserk.pot') for en, ru in remaining.items()]
        path.write_text('\n\n'.join(output).rstrip() + '\n')
    for locale in ('ru', 'zh_CN'):
        subprocess.run(['msgfmt', '--check', '-o',
            str(MOD / f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo'),
            str(MOD / f'lang/po/{locale}.po')], check=True)


def main():
    mapping = translations(); updates = []
    # Check every file before writing any; an unknown string aborts the build.
    for path in sorted(MOD.rglob('*.json')):
        if any(part.startswith('.') for part in path.relative_to(MOD).parts):
            continue  # Editor/synchronization internals are not mod sources.
        old = json.loads(path.read_text())
        new = convert(old, mapping, str(path.relative_to(ROOT)))
        if new != old:
            updates.append((path, new))
    for path, value in updates:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    catalogs(mapping)
    print(f'English base: {len(mapping)} strings; {len(updates)} JSON files updated; RU retained.')


if __name__ == '__main__':
    main()
