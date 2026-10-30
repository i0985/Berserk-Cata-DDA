#!/usr/bin/env python3
"""Owner's 31 October playtest: binding bodies, readable canine silhouettes.

Run last before English finalization. Existing body IDs update in place;
no rerolled paths, removed organs, doses, new contracts or replacement actors.
"""
import json

from recover_apostol_33 import ROOT, read, write, index, walk
from build_playtest_fixes_20261024 import tr, localize


def pawn_bodies():
    costs = json.loads((ROOT/'docs/pawn-costs-2026-10-31.json').read_text())
    abilities = json.loads((ROOT/'docs/apostol-native-utilities-33.json').read_text())['bodies']
    for kind, spec in costs['bodies'].items():
        path = 'mutations/apostol_' + kind.lower() + '_pawn.json'
        rows = read(path)
        by = index(rows)
        stem = 'BERSERK_' + kind + '_PAWN_'
        seed = by[stem+'SEED']
        seed['enchantments'] = [spec['seed_enchantment']]
        seed['description'] = tr(spec['seed_en'], spec['seed_ru'])
        form = by[stem+'FORM']
        # Keep permanent, native anatomical traits, armor locations and story
        # flags. Put each permanent penalty in exactly one mutation.
        enchantment = form['enchantments'][0]
        enchantment['values'] = spec['body_values']
        enchantment.pop('incoming_damage_mod', None)
        if spec.get('incoming_damage_mod'):
            enchantment['incoming_damage_mod'] = spec['incoming_damage_mod']
        for armor in form['armor']:
            armor.update(dict(zip(['bash','cut','stab'], spec['armor'])))
        if spec.get('restricts_gear'):
            form['restricts_gear'] = spec['restricts_gear']
        utility = abilities[kind+'_PAWN']
        tr(spec['body_en'], spec['body_ru'])
        form['description'] = tr(
            spec['body_en']+'\n\nBody abilities: '+utility['en'],
            spec['body_ru']+'\n\nВозможности тела: '+utility['ru'])
        write(path, rows)

    # Replace only the existing, successful acceptance message; there is no
    # extra popup, and no narrator announcing the trap before the decision.
    rows = read('effects/apostol_pawn_eocs.json')
    by = index(rows)
    for kind, spec in costs['bodies'].items():
        found = 0
        for node in walk(by['EOC_BERSERK_APOSTOL_'+kind+'_PAWN_ACCEPT']['effect']):
            if node.get('u_message') == 'An alien power reshapes your flesh.' or \
                    node.get('u_message') == spec['accept_en']:
                node['u_message'] = tr(spec['accept_en'], spec['accept_ru'])
                found += 1
        assert found == 1, (kind, found)
    write('effects/apostol_pawn_eocs.json', rows)


def flora_surroundings():
    rows = read('overmap/flora_manor.json')
    special = index(rows)['berserk_flora_manor_special']
    # Native fixed-special required_locations checks every listed cell,
    # including generated-submap protection. The original 2x2 house stays
    # unchanged; ordinary forest entries require a real forest surround.
    # This works even with cities disabled and uses no unsupported city test.
    house = [part for part in special['overmaps']
             if part['overmap'].startswith('berserk_flora_')]
    assert len(house) == 4
    for part in house:
        part['locations'] = ['forest']
    occupied = {tuple(part['point']) for part in house}
    border = [{'point':[x,y,0], 'overmap':'forest', 'locations':['forest']}
              for y in range(-4,6) for x in range(-4,6)
              if (x,y,0) not in occupied]
    special['overmaps'] = house + border
    special['//'] = ('Story-only unique 2x2 house, surrounded by four OMT of existing '
                     'unvisited forest. No urban-edge placement; existing registered '
                     'coordinates, rooms and NPCs are never rebuilt or moved.')
    write('overmap/flora_manor.json', rows)


def main():
    pawn_bodies()
    flora_surroundings()
    localize()
    print('31 October: weaker binding bodies, actual stamina penalty, forest surround.')


if __name__ == '__main__':
    main()
