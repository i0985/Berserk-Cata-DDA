#!/usr/bin/env python3
"""Permanent native body utilities, roof gliding and one early roadside source.

Run after the English October 28 pass; finish with apply_english_source_33.py.
The saved projects and cropped native sprite sheet are inputs, never redrawn.
"""
import gettext
import hashlib
import json

from recover_apostol_33 import ROOT, MOD, read, write, index, eoc
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, eq
from build_playtest_fixes_20261024 import tr, localize

P = 'EOC_BERSERK_UTILITY29_'
E = []


def run(name): return {'run_eocs': name}
def message(en, ru, popup=False): return {'u_message': tr(en, ru), 'type': 'info', 'popup': popup}


def body_utilities():
    spec = json.loads((ROOT/'docs/apostol-native-utilities-33.json').read_text())
    with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:
        russian = gettext.GNUTranslations(stream)
    for stem, details in spec['bodies'].items():
        path = 'mutations/apostol_' + stem.lower() + '.json'
        rows = read(path)
        form = index(rows)['BERSERK_' + stem + '_FORM']
        # Native derived traits live in cached_mutations. Purifiers cannot turn
        # a permanent FORM into a human; no repeat doses or extra growth line.
        form['enchantments'][0]['mutations'] = details['traits']
        for flag in details.get('flags', []):
            if flag not in form.setdefault('flags', []): form['flags'].append(flag)
        base = form['description'].split('\n\nBody abilities: ', 1)[0]
        ru = russian.gettext(base)
        if ru == base: raise ValueError('Missing RU body description: ' + stem)
        form['description'] = tr(base + '\n\nBody abilities: ' + details['en'],
                                 ru + '\n\nВозможности тела: ' + details['ru'])
        write(path, rows)
    manifest = json.loads((ROOT/'docs/apostol-native-sprite-sources-33.json').read_text())
    sheet = MOD/manifest['sheet']
    assert hashlib.sha256(sheet.read_bytes()).hexdigest() == manifest['sha256']
    write('apostol_native_overlays_tileset.json', [{
        'type': 'mod_tileset', 'compatibility': ['UltimateCataclysm'],
        'tiles-new': [{'file': manifest['sheet'], 'sprite_width': 32, 'sprite_height': 36,
                       'sprite_offset_x': 0, 'sprite_offset_y': -8, 'tiles': manifest['tiles']}]
    }])


def early_caravan():
    # Retire the automatic shelter handout; keep its ID for queued old calls.
    rows = read('effects/playtest_fixes_20261028_eocs.json')
    old = index(rows)[ 'EOC_BERSERK_FIX28_SHELTER_NOTICE' ]
    old['effect'] = []
    old['condition'] = 'u_is_avatar'
    write('effects/playtest_fixes_20261028_eocs.json', rows)

    project = json.loads((ROOT/'docs/location_projects/early-caravan-3.3-01.json').read_text())
    write('mapgen/early_caravan.json', project['maps'])
    write('overmap/early_caravan.json', [
        {'type': 'overmap_terrain', 'id': 'berserk_early_caravan',
         'name': tr('abandoned roadside wagon', 'брошенная придорожная повозка'),
         'sym': '?', 'color': 'brown', 'see_cost': 'high', 'travel_cost_type': 'forest',
         'flags': ['NO_ROTATE']},
        {'type': 'overmap_special', 'id': 'berserk_early_caravan_special',
         'overmaps': [{'point': [0, 0, 0], 'overmap': 'berserk_early_caravan'}],
         'connections': [{'point': [0, 1, 0], 'terrain': 'road', 'connection': 'local_road',
                          'from': [0, 0, 0], 'existing': True}],
         'locations': ['forest', 'field'], 'city_distance': [3, -1],
         'rotate': True, 'occurrences': [0, 0], 'flags': ['GLOBALLY_UNIQUE'],
         '//': 'Once per world, requested at the first surface start/exit. Existing road required.'}
    ])
    loc = {'global_val': 'berserk_early_caravan_location'}
    eligible = both('u_is_avatar', math("u_val('pos_z') == 0"),
                    either(neg('u_is_outside'), *[{'u_at_om_location': t}
                           for t in ['field', 'forest', 'forest_thick', 'road']]),
                    neg(eq('u_berserk_eclipse_trial_active')), neg(eq('berserk_early_caravan_placed')),
                    math('u_berserk_early_caravan_attempts < 3'),
                    math("time('now') >= u_berserk_early_caravan_retry_at"))
    E.append(eoc(P+'EARLY_REQUEST', [
        {'if': eq('u_berserk_early_caravan_attempts', 0),
         'then': {'u_location_variable': {'u_val': 'berserk_early_caravan_origin'}}},
        math('u_berserk_early_caravan_attempts = u_berserk_early_caravan_attempts + 1'),
        math("u_berserk_early_caravan_retry_at = time('now') + time('30 minutes')"),
        run(P+'EARLY_FIND')], eligible))
    E.append(eoc(P+'EARLY_FIND', {
            'u_location_variable': {'context_val': 'early_caravan_candidate'},
            'target_params': {'om_terrain': 'berserk_early_caravan',
                              'om_special': 'berserk_early_caravan_special',
                              'random': True, 'search_range': 48, 'z': 0},
            # Native mission lookup returns the origin after placement failure;
            # f_location_variable still calls true_eocs. STORE checks the OMT.
            'true_eocs': [P+'EARLY_STORE']}, 'u_is_avatar'))
    E.append(eoc(P+'EARLY_STORE', [
        {'copy_var': {'context_val': 'early_caravan_candidate'}, 'target_var': loc},
        math('berserk_early_caravan_placed = 1')],
        {'overmap_at_point': 'berserk_early_caravan', 'point': {'context_val': 'early_caravan_candidate'}}))
    # A normal optional mission points to the wagon; it does not read the paper
    # or introduce either smith. The existing physical source awards the forge.
    E.append(eoc(P+'EARLY_NOTIFY', [
        {'assign_mission': 'MISSION_BERSERK_EARLY_CARAVAN'},
        {'reveal_map': loc, 'radius': 1},
        math('u_berserk_early_caravan_notified = 1'),
        message('An abandoned wagon stop is marked near the road. There may still be useful belongings there.',
                'У дороги отмечена брошенная повозка. Возможно, там ещё остались полезные вещи.', True)],
        both('u_is_avatar', eq('berserk_early_caravan_placed'),
             neg(eq('u_berserk_early_caravan_notified')), neg(eq('u_berserk_journal_knows_godo')))))
    E.append(eoc(P+'EARLY_ARRIVAL', [
        math('u_berserk_early_caravan_arrival = 1'),
        message('A dry sheet of paper shows beneath the wagon box lid. Examine the box to read it, or take the order with you.',
                'Из-под крышки ящика на повозке выглядывает сухой лист. Осмотрите ящик, чтобы прочитать его, или возьмите заказ с собой.')],
        both('u_is_avatar', {'u_at_om_location': 'berserk_early_caravan'},
             neg(eq('u_berserk_early_caravan_arrival')))))
    E.append(eoc(P+'EARLY_TICK', [run(P+'EARLY_REQUEST'), run(P+'EARLY_NOTIFY'), run(P+'EARLY_ARRIVAL')],
                 both('u_is_avatar', neg(eq('berserk_eclipse_era')))))
    for event in ['game_start', 'game_load', 'avatar_moves']:
        E.append(eoc(P+'EARLY_'+event.upper(), run(P+'EARLY_TICK'), 'u_is_avatar',
                     eoc_type='EVENT', required_event=event))
    write('missions/early_caravan.json', [{
        'type': 'mission_definition', 'id': 'MISSION_BERSERK_EARLY_CARAVAN',
        'name': tr('The abandoned wagon', 'Брошенная повозка'),
        'description': tr('Examine the wagon box at the marked roadside stop. A repair order has survived beneath its lid. You can read it there even if you leave the paper behind.',
                          'Осмотрите ящик на повозке у отмеченной дороги. Под крышкой уцелел заказ на ремонт. Прочитать его можно на месте, даже если оставить бумагу.'),
        'goal': 'MGOAL_CONDITION',
        'goal_condition': either(eq('u_berserk_journal_read_berserk_road_caravan_note'),
                                 eq('u_berserk_journal_knows_godo')),
        'difficulty': 1, 'value': 0, 'origins': ['ORIGIN_SECONDARY'],
        'start': {'assign_mission_target': {'om_terrain': 'berserk_early_caravan', 'var': loc, 'reveal_radius': 1}}
    }])


def main():
    body_utilities()
    early_caravan()
    write('effects/apostol_utilities_33_eocs.json', E)
    localize()
    print('Native body utilities, multi-level roof gliding and a unique early roadside source.')


if __name__ == '__main__': main()
