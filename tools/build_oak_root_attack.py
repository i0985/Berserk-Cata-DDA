#!/usr/bin/env python3
"""Build the oak's fixed-sector windup from the existing committed attack graph.

No terrain is replaced. The brief root tangle slows a struck victim, rather
than trapping the player inside an impassable ring.
"""
import json
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'


def write(path, objects):
    (MOD / path).write_text(json.dumps(objects, ensure_ascii=False, indent=2) + '\n')


def build():
    original = json.loads((MOD / 'effects/apostle_committed_attacks.json').read_text())
    graph = []
    for obj in original:
        if obj['id'].startswith('EOC_BERSERK_COUNT_COMMITTED_'):
            encoded = json.dumps(obj).replace('COUNT_COMMITTED', 'OAK_COMMITTED')
            encoded = encoded.replace('committed_count', 'committed_oak')
            encoded = encoded.replace('berserk_count_heavy_ready', 'berserk_oak_root_ready')
            encoded = encoded.replace('mon_berserk_apostle_count', 'mon_berserk_cursed_oak_guardian')
            item = json.loads(encoded)
            if item['id'].endswith('_BEGIN'):
                for effect in item['effect']:
                    if effect.get('math') == ['n_berserk_committed_oak_due = time(\'now\') + 3']:
                        effect['math'] = ["n_berserk_committed_oak_due = time('now') + 2"]
                    if 'npc_add_effect' in effect:
                        effect['duration'] = '3 seconds'
            if item['id'].endswith('_RECOVER'):
                item['effect'][-1]['math'] = ["u_berserk_committed_oak_cooldown = time('now') + 10"]
            if item['id'].endswith('_CANCEL'):
                item['effect'][-1]['math'] = ["u_berserk_committed_oak_cooldown = time('now') + 4"]
            if item['id'].endswith('_RELEASE'):
                sound = next(e for e in item['effect'] if 'u_make_sound' in e)
                sound['u_make_sound'] = 'Thick roots lash across the disturbed earth!'
                sound['volume'] = 24
            graph.append(item)
    write('effects/oak_root_eocs.json', graph)

    spells = []
    original = json.loads((MOD / 'spells/apostle_committed_attacks.json').read_text())
    for obj in original:
        if obj['id'].startswith('berserk_committed_count_'):
            item = json.loads(json.dumps(obj).replace('committed_count', 'committed_oak')
                              .replace('COUNT_COMMITTED', 'OAK_COMMITTED'))
            suffix = item['id'].rsplit('_', 1)[-1]
            if suffix == 'prepare':
                item['name'] = 'Oak guardian: lift roots'
                item['description'] = 'The guardian fixes a direction and lifts its roots for a two-second sweep.'
            elif suffix == 'warning':
                item['name'] = 'Oak guardian: disturbed ground'
                item['description'] = 'Splitting earth marks the sector where the roots will strike.'
                item['min_duration'] = item['max_duration'] = 300
            else:
                item['name'] = 'Oak guardian: root sweep'
                item['description'] = 'Roots strike the marked sector and briefly tangle anyone who stayed there.'
                item['min_damage'] = item['max_damage'] = 22
                item['effect_str'] = 'berserk_oak_root_tangle'
                item['min_duration'] = item['max_duration'] = 200
            spells.append(item)
    write('spells/oak_root_attack.json', spells)

    fields = []
    original = json.loads((MOD / 'fields/apostle_committed_attacks.json').read_text())
    for obj in original:
        if 'committed_count' in obj['id']:
            item = json.loads(json.dumps(obj).replace('committed_count', 'committed_oak'))
            if item['type'] == 'field_type':
                item['intensity_levels'][0]['name'] = 'earth lifting over a root sweep'
                item['intensity_levels'][0]['color'] = 'brown'
            fields.append(item)
    write('fields/oak_root_attack.json', fields)
    write('effects/oak_combat_effects.json', [
        {'type': 'effect_type', 'id': 'berserk_oak_root_ready',
         'name': ['Lifting a mass of roots'],
         'desc': ['The oak guardian is braced for a root sweep. Its direction is fixed; the disturbed earth will be struck in two seconds.'],
         'max_duration': '3 seconds', 'flags': ['CANNOT_MOVE', 'CANNOT_ATTACK']},
        {'type': 'effect_type', 'id': 'berserk_oak_root_tangle',
         'name': ['Roots caught around your feet'],
         'desc': ['Roots briefly hinder your movement. You can still move and fight.'],
         'rating': 'bad', 'max_duration': '2 seconds', 'max_intensity': 1,
         'base_mods': {'speed_mod': [-25]}}
    ])


if __name__ == '__main__':
    build()
    print('Built fixed oak sweep, visible warning and brief movement penalty')
