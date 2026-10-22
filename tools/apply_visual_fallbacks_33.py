#!/usr/bin/env python3
"""Apply the reviewed fallback policy without altering authored sprite assets."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/'docs/visual-fallbacks-2026-10-23.json'


def main():
    denied={x['id'] for x in json.loads(POLICY.read_text())['removed']}
    authored=set()
    for path in (ROOT/'mods').rglob('*.json'):
        data=json.loads(path.read_text());data=data if isinstance(data,list) else [data]
        for obj in data:
            if obj.get('type')!='mod_tileset':continue
            for sheet in obj.get('tiles-new',[]):
                for tile in sheet.get('tiles',[]):
                    ids=tile.get('id',[]);authored.update([ids] if isinstance(ids,str) else ids)
    assert not denied.intersection(authored), denied.intersection(authored)
    changed=0
    for path in (ROOT/'mods/Berserk').rglob('*.json'):
        data=json.loads(path.read_text());objects=data if isinstance(data,list) else [data]
        dirty=False
        for obj in objects:
            if obj.get('id') not in denied:continue
            if 'copy-from' in obj:
                if obj.get('looks_like')!='':obj['looks_like']='';dirty=True
            elif 'looks_like' in obj:
                del obj['looks_like'];dirty=True
        if dirty:path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');changed+=1
    print(f'Visual fallbacks: {len(denied)} reviewed IDs; {changed} files updated; authored sprite sheets unchanged.')


if __name__=='__main__':main()
