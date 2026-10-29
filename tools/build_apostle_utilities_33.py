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
        base = details.get('base_en', form['description'].split('\n\nBody abilities: ', 1)[0])
        ru = details.get('base_ru', russian.gettext(base))
        if ru == base: raise ValueError('Missing RU body description: ' + stem)
        # The earlier clothing pass looks up the unsuffixed base on rebuild.
        # Register it too so the second canonical build can translate it.
        if 'base_en' in details:
            tr(base.split('\n\nClothing: ', 1)[0], ru.split('\n\n', 1)[0])
        form['description'] = tr(base + '\n\nBody abilities: ' + details['en'],
                                 ru + '\n\nВозможности тела: ' + details['ru'])
        write(path, rows)
    # The veil changes sight; the mature body now also suppresses scent.
    rows = read('mutations/apostol_ubik.json')
    index(rows)['BERSERK_UBIK_VEIL']['description'] = tr(
        'Vanish from ordinary sight for 8 seconds. Sounds can still betray you. Costs 1500 stamina; recovers in 45 seconds.',
        'Исчезните из обычного поля зрения на 8 секунд. Звуки всё ещё могут выдать вас. Требует 1500 выносливости; восстановление — 45 секунд.')
    write('mutations/apostol_ubik.json', rows)
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
         '//': 'One hidden source per world, requested on actual surface land. Existing road required.'}
    ])
    loc = {'global_val': 'berserk_early_caravan_location'}
    land = both(math("u_val('pos_z') == 0"),
                either(*[{'u_at_om_location': t} for t in ['field', 'forest', 'forest_thick', 'road']]))
    # Carrier decks/interiors, water, roofs and underground starts do not spend
    # attempts. Old failed interior searches get one bounded migration on land.
    E.append(eoc(P+'EARLY_LAND_MIGRATION', [
        math('u_berserk_early_caravan_attempts = 0'),
        math('u_berserk_early_caravan_retry_at = 0'),
        math('u_berserk_early_caravan_land_v2 = 1')],
        both('u_is_avatar', land, neg(eq('berserk_early_caravan_placed')),
             neg(eq('u_berserk_early_caravan_land_v2')))))
    eligible = both('u_is_avatar', land,
                    neg(eq('u_berserk_eclipse_trial_active')), neg(eq('berserk_early_caravan_placed')),
                    math('u_berserk_early_caravan_attempts < 3'),
                    math("time('now') >= u_berserk_early_caravan_retry_at"))
    E.append(eoc(P+'EARLY_REQUEST', [
        {'if': eq('u_berserk_early_caravan_attempts', 0),
         'then': {'u_location_variable': {'u_val': 'berserk_early_caravan_origin'}}},
        math('u_berserk_early_caravan_attempts = u_berserk_early_caravan_attempts + 1'),
        math("u_berserk_early_caravan_retry_at = time('now') + time('30 minutes')"),
        {'if': math('u_berserk_early_caravan_attempts > 1'),
         'then': run(P+'EARLY_FIND_WIDE'), 'else': run(P+'EARLY_FIND')}], eligible))
    for name, radius in [('EARLY_FIND', 48), ('EARLY_FIND_WIDE', 96)]:
        E.append(eoc(P+name, {
            'u_location_variable': {'context_val': 'early_caravan_candidate'},
            'target_params': {'om_terrain': 'berserk_early_caravan',
                              'om_special': 'berserk_early_caravan_special',
                              'random': True, 'search_range': radius, 'z': 0},
            # Native mission lookup returns the origin after placement failure;
            # f_location_variable still calls true_eocs. STORE checks the OMT.
            'true_eocs': [P+'EARLY_STORE']}, 'u_is_avatar'))
    E.append(eoc(P+'EARLY_STORE', [
        {'copy_var': {'context_val': 'early_caravan_candidate'}, 'target_var': loc},
        math('berserk_early_caravan_placed = 1')],
        {'overmap_at_point': 'berserk_early_caravan', 'point': {'context_val': 'early_caravan_candidate'}}))
    # The source is a discovery, never a starting marker. Keep the former EOC
    # and mission IDs for saved references; retire only its active old mission.
    E.append(eoc(P+'EARLY_NOTIFY', [], 'u_is_avatar'))
    E.append(eoc(P+'EARLY_RETIRE_MISSION', {
        'remove_active_mission': 'MISSION_BERSERK_EARLY_CARAVAN'}, 'u_is_avatar'))
    E.append(eoc(P+'EARLY_ARRIVAL', [
        math('u_berserk_early_caravan_arrival = 1'),
        message('A dry sheet of paper shows beneath the wagon box lid. Examine the box to read it, or take the order with you.',
                'Из-под крышки ящика на повозке выглядывает сухой лист. Осмотрите ящик, чтобы прочитать его, или возьмите заказ с собой.')],
        both('u_is_avatar', {'u_at_om_location': 'berserk_early_caravan'},
             neg(eq('u_berserk_early_caravan_arrival')))))
    E.append(eoc(P+'EARLY_TICK', [run(P+'EARLY_LAND_MIGRATION'), run(P+'EARLY_REQUEST'), run(P+'EARLY_ARRIVAL')],
                 both('u_is_avatar', neg(eq('berserk_eclipse_era')))))
    for event in ['game_start', 'game_load', 'avatar_moves']:
        effects = [run(P+'EARLY_RETIRE_MISSION'), run(P+'EARLY_TICK')] if event != 'avatar_moves' else run(P+'EARLY_TICK')
        E.append(eoc(P+'EARLY_'+event.upper(), effects, 'u_is_avatar',
                     eoc_type='EVENT', required_event=event))
    write('missions/early_caravan.json', [{
        'type': 'mission_definition', 'id': 'MISSION_BERSERK_EARLY_CARAVAN',
        'name': tr('The abandoned wagon', 'Брошенная повозка'),
        'description': tr('Examine the wagon box at the marked roadside stop. A repair order has survived beneath its lid. You can read it there even if you leave the paper behind.',
                          'Осмотрите ящик на повозке у отмеченной дороги. Под крышкой уцелел заказ на ремонт. Прочитать его можно на месте, даже если оставить бумагу.'),
        'goal': 'MGOAL_CONDITION',
        'goal_condition': either(eq('u_berserk_journal_read_berserk_road_caravan_note'),
                                 eq('u_berserk_journal_knows_godo')),
        'difficulty': 1, 'value': 0, 'origins': ['ORIGIN_GAME_START'],
        'start': {'assign_mission_target': {'om_terrain': 'berserk_early_caravan', 'var': loc, 'reveal_radius': 1}}
    }])


def main():
    body_utilities()
    early_caravan()
    write('effects/apostol_utilities_33_eocs.json', E)
    localize()
    for stem in json.loads((ROOT/'docs/apostol-native-utilities-33.json').read_text())['bodies']:
        assert 'Body abilities: ' in index(read('mutations/apostol_'+stem.lower()+'.json'))['BERSERK_'+stem+'_FORM']['description'], stem
    print('Native body utilities, multi-level roof gliding and a unique early roadside source.')


if __name__ == '__main__': main()
