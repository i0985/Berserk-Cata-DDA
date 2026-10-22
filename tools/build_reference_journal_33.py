#!/usr/bin/env python3
"""Build the complete optional reference book after the five current builders.

The book can only observe/store knowledge and acknowledge read entries. Native
missions, physical sources, order transactions and restoration are separate.
Russian manuscript prose is the translatable source for this literary package.
"""
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from recover_apostol_33 import ROOT, MOD, read as load, write, index, walk, upsert, eoc
from recovery_33_translations import source as po_source
from reference_journal_content_33 import (
    build, MANUSCRIPT, LETTER_ITEMS, RELIC_ITEMS, math, allof, anyof, no, eq, gt,
    test, fact, visited, trait, item, bionic, known, read, NORMAL, ALTER, REFUSED,
    GUTS, BRAND, ARM, DEMON, SEALED, p,
)

PREFIX = 'EOC_BERSERK_REF_'
TOPIC = 'TALK_BERSERK_REF_'
STRINGS = {}
HELPERS = {}
GENERATED = []


def tr(ru, en=None):
    # The owner's exact Russian prose is a valid gettext source. Do not replace
    # it with fabricated English IDs that would be visible on a missing .mo.
    key = en or ru
    STRINGS[key] = ru
    return key


def run(s): return {'run_eocs': s if s.startswith('EOC_') else PREFIX + s}
def setf(s, value=1): return math('u_berserk_ref_' + s + ' = ' + str(value))
def effects(v): return v if isinstance(v, list) else [v]
def append(obj, addition):
    obj['effect'] = effects(obj.get('effect', []))
    for x in effects(addition):
        # Moving an item invalidates its old talker. Keep that transfer last,
        # including when upgrading data produced by an earlier WIP build.
        transfer = next((i for i, part in enumerate(obj['effect'])
                         if 'npc_teleport' in part or 'u_teleport' in part), len(obj['effect']))
        if x in obj['effect']:
            old = obj['effect'].index(x)
            if old <= transfer: continue
            obj['effect'].pop(old)
        obj['effect'].insert(transfer, x)


def predicate(c):
    if isinstance(c, str) or any(k in c for k in ['and', 'or', 'not']):
        name = PREFIX + 'P_' + hashlib.sha1(json.dumps(c, sort_keys=True).encode()).hexdigest()[:14].upper()
        HELPERS[name] = eoc(name, [], c)
        return test(name)
    return c


def choose(c, yes, no_=''):
    return {**predicate(c), 'yes': yes, 'no': no_}


def button(text, target, condition=None, effect=None, en=None):
    out = {'text': tr(text, en), 'topic': target}
    if condition is not None: out['condition'] = condition
    if effect is not None: out['effect'] = effect
    return out


def topic(id_, line, responses, speaker=None):
    out = {'type': 'talk_topic', 'id': id_, 'dynamic_line': line, 'responses': responses}
    if speaker: out['speaker_effect'] = {'effect': speaker}
    return out


def stamp_topics(data, ids, facts):
    for id_ in ids:
        if id_ not in data: raise ValueError('Unknown knowledge topic: ' + id_)
        obj = data[id_]
        addition = [setf(x) for x in facts] + [run('SYNC')]
        sp = obj.setdefault('speaker_effect', {'effect': []})
        if isinstance(sp, list):
            tag = {'effect': addition}
            if tag not in sp: sp.append(tag)
        else:
            old = effects(sp.get('effect', []))
            for x in addition:
                if x not in old: old.append(x)
            sp['effect'] = old


def stamp_eocs(data, ids, facts, condition=None):
    for id_ in ids:
        if id_ not in data: raise ValueError('Unknown knowledge event: ' + id_)
        action = [setf(x) for x in facts]
        if condition is not None: action = [{'if': condition, 'then': action}]
        append(data[id_], action + [run('SYNC')])


def make_reference(records, old_knight):
    topics = []
    sync = []
    sections = {'places': ('Известные места', 'Места, о которых удалось узнать'),
                'people': ('Люди и ремесло', 'Люди и их дело'),
                'past': ('Пережитое', 'То, что осталось после дороги')}
    for r in records:
        key = r['key']
        rank = f'u_berserk_ref_rank_{key}'
        revision = f'u_berserk_ref_revision_{key}'
        counter = 'u_berserk_ref_count_' + r['section']
        membership = anyof(*(part['condition'] for part in r['parts']))
        sync.append({'if': allof(eq(rank, 0), membership), 'then': [math(counter + ' = ' + counter + ' + 1'), math(rank + ' = ' + counter)]})
        for i, part in enumerate(r['parts']):
            active = f'u_berserk_ref_active_{key}_{i}'
            # Keep source conditions separate from display flags: hidden
            # branches are not archived merely because the paper exists.
            sync.append({'if': part['condition'], 'then': {'if': no(eq(active)),
                'then': [math(active + ' = 1'), math(revision + ' = ' + revision + ' + 1')]},
                'else': {'if': eq(active), 'then': [math(active + ' = 0'), math(revision + ' = ' + revision + ' + 1')]}})
        title_line = tr(r['title'])
        for cond, title in reversed(r['title_variants']): title_line = choose(cond, tr(title), title_line)
        line = {'concatenate': ['&', title_line, '\n\n'] + [
            choose(eq(f'u_berserk_ref_active_{key}_{i}'), tr(part['text']) + '\n\n')
            for i, part in enumerate(r['parts'])]}
        if key == 'l03' and old_knight:
            # Preserve every previously heard answer, with its original gate.
            # The old response tree is not retained.
            line['concatenate'] += ['\n', old_knight]
        topics.append(topic(TOPIC + key.upper(), line, [
            button('К списку', TOPIC + r['section'].upper()), button('Закрыть журнал', 'TALK_DONE')],
            math(f'u_berserk_ref_seen_{key} = {revision}')))
    GENERATED.append(eoc(PREFIX + 'SYNC', [run('OBSERVE')] + sync, 'u_is_avatar'))
    rootline = choose(anyof(*(gt('u_berserk_ref_count_' + s) for s in sections)),
        tr('&Дорожный журнал\n\nДороги, лица и события. То, что удалось узнать и сохранить в памяти.'),
        tr('&Дорожный журнал\n\nНа этих страницах пока нет записей.'))
    topics.append(topic(TOPIC + 'ROOT', rootline, [
        button(title, TOPIC + s.upper(), gt('u_berserk_ref_count_' + s))
        for s, (title, _) in sections.items()] + [button('Закрыть журнал', 'TALK_DONE')]))
    for section, (title, subtitle) in sections.items():
        entries = [x for x in records if x['section'] == section]
        responses = []
        # 0.I only repeats inventory responses and has no arbitrary sorted
        # response collection. Compile bounded rank slots instead. Only one
        # candidate in each occupied slot can pass its native math predicate.
        for slot in range(1, len(entries) + 1):
            for r in entries:
                key = r['key']
                variants = r['title_variants'] + [(None, r['title'])]
                excluded = []
                for cond, text in variants:
                    gate = allof(eq(f'u_berserk_ref_rank_{key}', slot), *(no(x) for x in excluded), *([cond] if cond is not None else []))
                    responses.append({'condition': gate,
                        'truefalsetext': {'condition': math(f'u_berserk_ref_revision_{key} > u_berserk_ref_seen_{key}'),
                            'true': tr(text + ' — Новое'), 'false': tr(text)},
                        'topic': TOPIC + key.upper()})
                    if cond is not None: excluded.append(cond)
        responses += [button('К разделам', TOPIC + 'ROOT'), button('Закрыть журнал', 'TALK_DONE')]
        topics.append(topic(TOPIC + section.upper(), tr('&' + title + '\n\n' + subtitle + '.'), responses))
    return topics


def original_catalog():
    path = ROOT / 'docs/dialogue_sources/road-journal-legacy-33.json'
    if path.exists(): return json.loads(path.read_text())
    old = load('dialogue/road_journal.json')
    readers = {}
    for name in ['items/road_story_records.json', 'items/location_records.json', 'items/flora_treehouse.json',
                 'items/first_hunt_clue.json', 'items/grunbeld_stronghold_records.json']:
        for obj in load(name):
            if obj.get('id', '').startswith('berserk_'):
                for node in walk(obj.get('use_action')):
                    ids = node.get('effect_on_conditions', [])
                    if isinstance(ids, list): readers[obj['id']] = ids
    legacy = {'topic_ids': [x['id'] for x in old], 'readers': readers,
              'knight_advice': index(old).get('TALK_BERSERK_JOURNAL_KNIGHT_ADVICE', {}).get('dynamic_line')}
    path.write_text(json.dumps(legacy, ensure_ascii=False, indent=2) + '\n')
    return legacy


def sources_and_legacy(catalog, topics, records):
    by_key = {r['key']: r for r in records}
    new_by_id = index(topics)
    # Old IDs remain valid aliases, not competing objects with duplicated text.
    aliases = {'TALK_BERSERK_ROAD_JOURNAL': 'ROOT', 'TALK_BERSERK_JOURNAL_PLACES': 'PLACES',
        'TALK_BERSERK_JOURNAL_ORDERS': 'PEOPLE', 'TALK_BERSERK_JOURNAL_CURRENT': 'ROOT',
        'TALK_BERSERK_JOURNAL_REFUGE': 'PAST', 'TALK_BERSERK_JOURNAL_RECORDS': 'PAST',
        'TALK_BERSERK_JOURNAL_CHAPTER_END': 'C18', 'TALK_BERSERK_JOURNAL_KNIGHT_ADVICE': 'L03',
        'TALK_BERSERK_APOSTOL_ROAD': 'T01', 'TALK_BERSERK_APOSTOL_FLESH_PROGRESS': 'T01',
        'TALK_BERSERK_APOSTOL_PAWN_PROGRESS': 'T01', 'TALK_BERSERK_JOURNAL_REPAIR': 'L07',
        'TALK_BERSERK_JOURNAL_EARLY': 'L08', 'TALK_BERSERK_JOURNAL_ARM': 'L09',
        'TALK_BERSERK_JOURNAL_SWORD': 'L08', 'TALK_BERSERK_JOURNAL_BOLTS': 'L10'}
    places = {'FIRST': 'M06', 'BREACH': 'M07', 'COUNT': 'M08', 'WYALD': 'M09', 'ROSINE': 'M10',
              'FLORA': 'M11', 'GRUNBELD': 'M12', 'GODO': 'M01'}
    for stem, key in places.items():
        aliases['TALK_BERSERK_JOURNAL_PLACE_' + stem] = key
        aliases['TALK_BERSERK_JOURNAL_INFO_' + stem] = key
    for i, stem in enumerate(LETTER_ITEMS, 1): aliases['TALK_BERSERK_JOURNAL_RECORD_BERSERK_' + stem.upper()] = f'P{i:02}'
    aliases['TALK_BERSERK_JOURNAL_RECORD_BERSERK_COUNT_IRON_SEAL'] = 'R01'
    for old_id in catalog['topic_ids']:
        target = aliases.get(old_id, 'PAST')
        if target in ['ROOT', 'PLACES', 'PEOPLE', 'PAST']:
            # The historical topic is not a second copy of thousands of rank
            # candidates. Public item entrypoints already open the real menu.
            original = topic(old_id, tr('&Дорожный журнал'), [
                button('Прочитать записи', TOPIC + target), button('Закрыть журнал', 'TALK_DONE')])
        else: original = copy.deepcopy(new_by_id[TOPIC + target])
        original['id'] = old_id
        # Never acknowledge a record through an obsolete hidden route.
        if 'speaker_effect' in original: original.pop('speaker_effect')
        topics.append(original)
    generated_readers = []
    # Physical source reading ends at its own popup. The archived copy has
    # only navigation/read acknowledgement and cannot replay these effects.
    for i, stem in enumerate(LETTER_ITEMS, 1):
        code = f'П{i:02}'
        full = 'berserk_' + stem
        targets = catalog['readers'].get(full, [])
        if not targets:
            if stem == 'eclipse_last_stand_note': targets = ['EOC_BERSERK_ECLIPSE_LAST_STAND_READ']
            else: raise ValueError('No physical reader: ' + full)
        text = tr('\n\n'.join(MANUSCRIPT[code]['paragraphs']))
        flag = 'u_berserk_journal_read_' + full
        first = [math(flag + ' = 1')]
        if stem in ['road_caravan_note', 'road_camp_note', 'chapel_relief_roster']:
            first += [run('EOC_BERSERK_GODO_LEARN_TRACE'), run('EOC_BERSERK_GODO_ROUTE_MISSION')]
        if stem == 'apostle_burned_clue': first += [run('EOC_BERSERK_JOURNAL_LEARN_BREACH'), run('EOC_BERSERK_JOURNAL_BREACH_LOCATE')]
        if stem == 'count_next_trace': first += [run('EOC_BERSERK_JOURNAL_LEARN_COUNT'), run('EOC_BERSERK_JOURNAL_LEARN_WYALD'), run('EOC_BERSERK_JOURNAL_LEARN_ROSINE'), run('EOC_BERSERK_KNOWN_ROUTES_NOW')]
        if stem == 'wyald_command_orders': first += [run('EOC_BERSERK_JOURNAL_LEARN_WYALD'), run('EOC_BERSERK_KNOWN_ROUTES_NOW')]
        # Preserve source-only recipe discovery; these are not demonic rituals.
        old_recipe = set()
        for path in (MOD / 'effects').glob('*.json'):
            for obj in json.loads(path.read_text()):
                if obj.get('id') in targets:
                    old_recipe.update(n['u_learn_recipe'] for n in walk(obj.get('effect')) if 'u_learn_recipe' in n)
        first += [{'u_learn_recipe': x} for x in sorted(old_recipe)]
        first += [run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL')]
        new_effect = [{'u_message': text, 'type': 'info', 'popup': True},
                      {'if': no(eq(flag)), 'then': first}, run('SYNC')]
        for path in (MOD / 'effects').glob('*.json'):
            data = json.loads(path.read_text()); changed = False
            for obj in data:
                if obj.get('id') in targets:
                    obj['effect'] = copy.deepcopy(new_effect)
                    if stem == 'apostle_burned_clue':
                        # Reading evidence and locating its destination are
                        # separate. Underground reading still saves the clue;
                        # the existing surface retry can bind the target later.
                        obj['condition'] = 'u_is_avatar'
                        obj.pop('false_effect', None)
                    obj['//'] = 'Reference journal: physical source only; rereading never reapplies progression.'
                    changed = True
            if changed: write('effects/' + path.name, data)
        generated_readers.extend(targets)
    return generated_readers


def compatibility_eocs():
    data = load('effects/road_journal_eocs.json'); by = index(data)
    by['EOC_BERSERK_JOURNAL_REFRESH']['effect'] = run('SYNC')
    # Migration only repairs personal knowledge, and is also run without a
    # book. Opening the book does not search, reveal, assign, heal or reward.
    by['EOC_BERSERK_JOURNAL_MIGRATE']['effect'] = run('MIGRATE')
    by['EOC_BERSERK_JOURNAL_DISCOVER']['effect'] = run('VISIT')
    entrypoints = {'OPEN': 'ROOT', 'OPEN_CURRENT': 'ROOT', 'OPEN_HUNTS': 'PLACES',
                  'OPEN_ORDERS': 'PEOPLE', 'OPEN_REFUGE': 'PAST',
                  'LEGACY_HUNTS': 'PLACES', 'LEGACY_ORDERS': 'PEOPLE'}
    for suffix, target in entrypoints.items():
        id_ = 'EOC_BERSERK_JOURNAL_' + suffix
        by[id_]['effect'] = [run('SYNC'), {'open_dialogue': {'topic': TOPIC + target}}]
    for suffix, stem, code in [('FIRST', 'first', 'М06'), ('FLORA', 'flora', 'М11')]:
        obj = by['EOC_BERSERK_JOURNAL_LEGACY_' + suffix]
        obj['effect'] = [{'u_message': tr(p(code, 0)), 'type': 'info', 'popup': True},
            {'if': no(fact('legacy_read_' + stem)), 'then': [setf('legacy_read_' + stem),
                run('EOC_BERSERK_JOURNAL_LEARN_' + suffix),
                run('EOC_BERSERK_JOURNAL_LOCATE_' + suffix)]}, run('SYNC')]
    by['EOC_BERSERK_JOURNAL_REPLACE_MISSING']['effect'] = run('RESTORE')
    write('effects/road_journal_eocs.json', data)
    # No old book can teach all future names or rebuild a scene.
    for file, id_, target in [('campaign_journal_eocs', 'EOC_BERSERK_CAMPAIGN_REPORT', 'ROOT'),
        ('godo_eocs', 'EOC_BERSERK_GODO_BOOK', 'ROOT'),
        ('refuge_eocs', 'EOC_BERSERK_REFUGE_JOURNAL', 'PAST'),
        ('wyald_rosine_hunt_eocs', 'EOC_BERSERK_HUNT_JOURNAL_USE', 'PLACES')]:
        data = load('effects/' + file + '.json'); obj = index(data)[id_]
        obj['effect'] = [run('SYNC'), {'open_dialogue': {'topic': TOPIC + target}}]
        if id_ == 'EOC_BERSERK_GODO_BOOK': obj['effect'] = run('RESTORE')
        write('effects/' + file + '.json', data)
    data = load('effects/wyald_rosine_hunt_eocs.json')
    index(data)['EOC_BERSERK_HUNT_GIVE_JOURNAL']['effect'] = run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL')
    for suffix in ['HUNT_RETURN_BREACH', 'HUNT_STATUS']:
        index(data)['EOC_BERSERK_' + suffix]['effect'] = [run('EOC_BERSERK_MISSIONS_SYNC'), run('SYNC')]
    write('effects/wyald_rosine_hunt_eocs.json', data)
    data = load('effects/local_breach_eocs.json')
    index(data)['EOC_BERSERK_POST_ECLIPSE_CHOOSE']['effect'] = [run('EOC_BERSERK_KNOWN_ROUTES_NOW'), run('SYNC')]
    write('effects/local_breach_eocs.json', data)
    data = load('effects/refuge_eocs.json')
    index(data)['EOC_BERSERK_REFUGE_NEXT_TRAIL']['effect'] = [run('EOC_BERSERK_KNOWN_ROUTES_NOW'), run('SYNC')]
    write('effects/refuge_eocs.json', data)
    data = load('effects/apostol_pawn_eocs.json')
    for node in walk(index(data)['EOC_BERSERK_APOSTOL_PAWN_BEGIN']):
        if node.get('run_eocs') == 'EOC_BERSERK_JOURNAL_REPLACE_MISSING':
            node['run_eocs'] = 'EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL'
    write('effects/apostol_pawn_eocs.json', data)


def items_and_restoration():
    data = load('items/campaign_journal.json')
    data[0]['name'] = {'str_sp': tr('Дорожный журнал', 'road journal')}
    data[0]['description'] = tr('Тетрадь с дорожными заметками. Здесь собраны известные места, имена встреченных людей и сведения, которые стоит сохранить. Задания и отметки на карте останутся с вами, даже если книга потеряется.')
    data[0]['use_action']['menu_text'] = tr('Прочитать записи', 'Read the entries')
    write('items/campaign_journal.json', data)
    # All legacy items keep their IDs; no new copies are handed out.
    for name in ['apostle_hunt_journal', 'godo_orders', 'post_eclipse_journal', 'refuge_journal']:
        data = load('items/' + name + '.json')
        for obj in data: obj['use_action']['menu_text'] = tr('Прочитать записи', 'Read the entries')
        if name == 'post_eclipse_journal':
            data[0]['use_action']['effect_on_conditions'] = ['EOC_BERSERK_JOURNAL_OPEN_REFUGE']
        write('items/' + name + '.json', data)
    restore = eoc(PREFIX + 'RESTORE', [
        {'u_spawn_item': 'berserk_campaign_journal', 'count': 1, 'suppress_message': True},
        math('u_berserk_road_journal_issued = 1'),
        {'u_message': tr('Вы заново записываете то, что сохранили в памяти.'), 'type': 'info', 'popup': False}],
        allof('u_is_avatar', no(item('berserk_campaign_journal'))))
    GENERATED.append(restore)
    # A paper-bound notebook can be recreated without a living quest NPC.
    write('recipes/reference_journal.json', [{
        'type': 'recipe', 'result': 'berserk_campaign_journal', 'id_suffix': 'copy_road_notes',
        'category': 'CC_OTHER', 'subcategory': 'CSC_OTHER_OTHER', 'skill_used': 'fabrication',
        'difficulty': 0, 'time': '15 minutes', 'autolearn': True,
        'components': [[['paper', 20]], [['thread', 10]]],
        'result_eocs': [PREFIX + 'COPY_FINISHED']}])
    GENERATED.append(eoc(PREFIX + 'COPY_FINISHED', [math('u_berserk_road_journal_issued = 1'),
        {'u_message': tr('Вы заново записываете то, что сохранили в памяти.'), 'type': 'info', 'popup': False}], 'u_is_avatar'))
    # Relic examination replaces the old route-control activation. Wearing
    # and enchantments are untouched; no item is consumed or awarded here.
    data = load('items/apostle_relics.json')
    for i, id_ in enumerate(RELIC_ITEMS, 1):
        obj = index(data)[id_]
        reader_id = PREFIX + 'RELIC_' + str(i)
        obj['use_action'] = {'type': 'effect_on_conditions', 'menu_text': tr('Осмотреть реликвию'),
            'need_wielding': False, 'effect_on_conditions': [reader_id]}
        GENERATED.append(eoc(reader_id, [setf('relic_' + str(i)), run('SYNC'),
            {'u_message': tr('\n\n'.join(MANUSCRIPT[f'Р{i:02}']['paragraphs'])), 'type': 'info', 'popup': True}]))
    write('items/apostle_relics.json', data)


def localization():
    for name, localized in [('ru.po', True), ('Berserk.pot', False)]:
        path = MOD / 'lang/po' / name
        remaining = dict(STRINGS); out = []
        for block in [x for x in path.read_text().split('\n\n') if x.strip()]:
            key = po_source(block)
            if key in remaining:
                ru = remaining.pop(key)
                block = '#. Approved reference book 2026-10-22\nmsgid ' + json.dumps(key, ensure_ascii=False) + '\nmsgstr ' + json.dumps(ru if localized else '', ensure_ascii=False)
            out.append(block.strip('\n'))
        for key, ru in remaining.items():
            out.append('#. Approved reference book 2026-10-22\nmsgid ' + json.dumps(key, ensure_ascii=False) + '\nmsgstr ' + json.dumps(ru if localized else '', ensure_ascii=False))
        path.write_text('\n\n'.join(out) + '\n')
    subprocess.run(['msgfmt', '--check', '-o', str(MOD / 'lang/mo/ru/LC_MESSAGES/Berserk.mo'), str(MOD / 'lang/po/ru.po')], check=True)


def knowledge_events_and_hooks():
    """Persist personal observations, never infer knowledge from world state."""
    terrain = {
        'godo': ['berserk_godo_workshop', 'berserk_godo_loft'],
        'oak': ['berserk_cursed_oak'],
        'cave': ['berserk_echo_cave_entrance', 'berserk_echo_cave_depth', 'berserk_echo_cave_gallery', 'berserk_echo_cave_passage', 'berserk_echo_cave_relic_chamber'],
        'expedition': ['berserk_lost_expedition'],
        'chapel': ['berserk_desecrated_chapel_nave', 'berserk_desecrated_chapel_reliquary'],
        'first': ['berserk_first_hunt_lair'], 'breach': ['berserk_local_breach'],
        'count': ['berserk_count_prison', 'berserk_count_hall', 'berserk_count_west_yard', 'berserk_count_east_yard', 'berserk_count_dungeon'],
        'wyald': ['berserk_wyald_approach', 'berserk_wyald_camp', 'berserk_wyald_quarry', 'berserk_wyald_ring'],
        'rosine': ['berserk_rosine_trail', 'berserk_rosine_cocoons', 'berserk_rosine_gully', 'berserk_rosine_nest'],
        # Native u_at_om_location uses the directionless base ID.
        'flora': ['berserk_flora_manor', 'berserk_flora_garden'],
        'grunbeld': ['berserk_grunbeld_approach', 'berserk_grunbeld_ramparts', 'berserk_grunbeld_quarry', 'berserk_grunbeld_barracks', 'berserk_grunbeld_ruins', 'berserk_grunbeld_crucible'],
    }
    here = {k: anyof(*({'u_at_om_location': x} for x in ids)) for k, ids in terrain.items()}
    visit = [run('MIGRATE')]
    for key, cond in here.items():
        visit.append({'if': allof(no(visited(key)), cond), 'then': [setf('visit_' + key), run('SYNC')]})
    GENERATED.append(eoc(PREFIX + 'VISIT', visit, 'u_is_avatar'))
    # The existing avatar_moves entrypoint calls VISIT. A minute observer also
    # catches crafting, installed devices and growth without owning a book.
    GENERATED.append(eoc(PREFIX + 'TICK', [run('MIGRATE'), run('SYNC')], 'u_is_avatar',
                         **{'global': True, 'recurrence': '1 minute'}))
    GENERATED.append(eoc(PREFIX + 'NEW_CHARACTER', [setf('schema'), run('SYNC')], 'u_is_avatar',
                         eoc_type='EVENT', required_event='game_start'))
    legacy = []
    for stem in ['godo', 'count', 'wyald', 'rosine', 'flora', 'grunbeld']:
        legacy.append({'if': known(stem), 'then': setf('name_' + stem)})
    legacy += [setf('schema')]
    GENERATED.append(eoc(PREFIX + 'MIGRATE', legacy, allof('u_is_avatar', no(fact('schema')))))
    observe = []
    def remember(name, proof):
        observe.append({'if': allof(no(fact(name)), proof), 'then': setf(name)})
    remember('name_godo', anyof(eq('u_berserk_godo_personally_met'), eq('u_berserk_rickert_met'),
        read('road_caravan_note'), read('road_camp_note'), read('chapel_relief_roster'),
        allof(GUTS, known('godo'))))
    remember('name_count', anyof(fact('breach_directions'), read('count_prison_list'), read('count_physician_ledger'), fact('prisoner_met')))
    remember('name_wyald', anyof(fact('breach_directions'), read('count_next_trace'), read('wyald_muster_roll'), read('wyald_command_orders')))
    remember('name_rosine', anyof(fact('breach_directions'), read('count_next_trace'), read('rosine_witness_note')))
    remember('name_flora', anyof(eq('u_berserk_flora_met'), eq('u_berserk_flora_late_clue_given'), fact('flora_named_source')))
    remember('name_grunbeld', anyof(fact('grunbeld_siege_seen'), read('grunbeld_scorched_badge'), allof(known('grunbeld'), eq('u_berserk_flora_escaped'))))
    remember('grunbeld_castle_victory', allof(here['grunbeld'], eq('berserk_apostle_grunbeld_dead'), eq('berserk_hunt_grunbeld_defeated_in_lair')))
    remember('grunbeld_siege_alive', allof(fact('grunbeld_siege_seen'), eq('berserk_grunbeld_grove_withdrawn'), no(eq('berserk_apostle_grunbeld_dead'))))
    for stem in ['count', 'wyald', 'rosine', 'grunbeld']:
        # Completion of one's own mission is historical evidence. A dead
        # global boss by itself is not; observe it on the actual site.
        state = 'berserk_hunt_' + stem + '_state'
        gone = math(state + ' >= 3') if stem == 'count' else eq('berserk_apostle_' + stem + '_dead')
        remember('dead_' + stem, anyof(allof(here[stem], gone), eq('u_berserk_mission_' + stem + '_finished')))
        remember('sealed_' + stem, anyof(allof(here[stem], math(state + ' >= 4')), eq('u_berserk_mission_' + stem + '_finished')))
        remember('name_' + stem, test('APOSTOL_' + stem.upper() + '_PAWN_LINE'))
    remember('breach_directions', allof(SEALED, known('count'), known('wyald'), known('rosine')))
    remember('breach_keeper_dead', anyof(allof(here['breach'], math('berserk_hunt_first_breach_state >= 3')), SEALED))
    remember('flora_home_lost', allof(eq('u_berserk_flora_escaped'), eq('u_berserk_flora_fire_summary_seen')))
    remember('flora_attack', allof(here['flora'], math('berserk_flora_siege_state >= 2')))
    remember('godo_care', allof(NORMAL, eq('u_berserk_godo_rescue_relocated'), eq('u_berserk_godo_wake_greeted')))
    remember('repair_handoff', gt('u_berserk_godo_repair_job'))
    remember('early_blade_known', anyof(eq('u_berserk_godo_early_delivered'), allof(GUTS, item('true_guts_early_sword'))))
    remember('arm_device_owned', anyof(item('bio_berserk_arm_cannon'), ARM))
    remember('behelit_examined', anyof(item('berserk_behelit'), item('berserk_behelit_distorted'), gt('u_berserk_apostol_behelit_notice')))
    remember('behelit_call', eq('u_berserk_apostol_behelit_notice'))
    remember('behelit_distorted', item('berserk_behelit_distorted'))
    remember('body_changed', allof(DEMON, eq('u_berserk_apostol_body_checked')))
    remember('eclipse_hand_lost', allof(NORMAL, anyof(bionic('bio_berserk_hand_stump'), ARM, eq('u_berserk_apostol_left_hand_regrown'))))
    remember('eclipse_eye_lost', allof(NORMAL, bionic('bio_berserk_lost_eye')))
    for stem, id_ in [('judeau', 'berserk_judeau_knife_hilt'), ('pippin', 'berserk_pippin_broken_clasp'),
                      ('corkus', 'berserk_corkus_scabbard_fragment'), ('gaston', 'berserk_gaston_sewing_roll')]:
        remember('keepsake_' + stem, allof(eq('u_berserk_godo_witness_' + stem), item(id_)))
    remember('armor_part_known', anyof(*(item(x) for x in ['berserk_helmet', 'berserk_chestplate', 'berserk_armguards', 'berserk_gloves', 'berserk_legguards', 'berserk_boots'])))
    remember('refuge_chosen', eq('u_berserk_refuge_ready'))
    remember('chapter_closed_known', allof(eq('u_berserk_campaign_chapter_closed'),
        *(eq('u_berserk_mission_' + s + '_finished') for s in ['count', 'wyald', 'rosine', 'grunbeld']), fact('flora_home_lost')))
    GENERATED.append(eoc(PREFIX + 'OBSERVE', observe, 'u_is_avatar'))
    data = load('dialogue/godo.json'); by = index(data)
    def god(suffixes, facts): stamp_topics(by, ['TALK_BERSERK_GODO_' + s for s in suffixes], facts)
    def rick(suffixes, facts): stamp_topics(by, ['TALK_BERSERK_RICKERT_' + s for s in suffixes], facts)
    god(['INTRO_WORK', 'WORK', 'CRAFT'], ['godo_work'])
    god(['ORDERS', 'EARLY_SWORD', 'SWORD_REQUEST', 'EARLY_DELIVERY', 'SWORD_DELIVERY'], ['forge_orders'])
    god(['REPAIR', 'INTRO_REPAIR'], ['repair_explained'])
    god(['EARLY_SWORD', 'OWNER', 'COPY', 'WEAPON_REQUEST'], ['early_blade_known'])
    god(['DRAGON_STORY', 'DRAGON_EXIST', 'SWORD_REQUEST'], ['dragonslayer_story'])
    rick(['BAND', 'HAWKS', 'COMMANDER', 'CAMP'], ['rickert_band'])
    rick(['MECHANISM', 'MECHANISMS', 'RELOAD', 'TACTICS', 'GUTS_CROSSBOW'], ['crossbow_explained'])
    rick(['BOLTS', 'BOLT_LIMITS'], ['bolts_explained', 'forge_orders'])
    rick(['ARM', 'ARM_GUN', 'ARM_GRIP', 'ARM_SELF', 'PRAISE', 'CANNON'], ['prosthesis_explained'])
    rick(['PRAISE'], ['rickert_one_hand_praise'])
    # A real NPC trust check is captured only in that NPC's conversation.
    for s in ['CONFESSION_TRUST', 'TRUST_TALK']:
        obj = by['TALK_BERSERK_RICKERT_' + s]
        sp = obj.setdefault('speaker_effect', {'effect': []})
        if isinstance(sp, dict):
            append(sp, {'if': allof(eq('u_berserk_rickert_lied_before'), test('RICKERT_TRUST_RESTORED')),
                        'then': [setf('rickert_trust_restored'), run('SYNC')]})
    # Keep the optional book request explicit, with no transition from an
    # ordinary answer into a book menu.
    for obj in data:
        if obj.get('type') != 'talk_topic': continue
        for response in obj.get('responses', []):
            if any(n.get('run_eocs') == 'EOC_BERSERK_JOURNAL_REPLACE_MISSING' for n in walk(response)):
                response['text'] = tr('Я потерял дорожные записи. Можно взять новую тетрадь?',
                                      'I lost my road notes. Could I have a new notebook?')
                response['condition'] = no(item('berserk_campaign_journal'))
    restore_response = button('Я потерял дорожные записи. Можно взять новую тетрадь?',
        'TALK_BERSERK_GODO_WORK', no(item('berserk_campaign_journal')), run('RESTORE'),
        en='I lost my road notes. Could I have a new notebook?')
    if restore_response not in by['TALK_BERSERK_GODO_WORK']['responses']:
        by['TALK_BERSERK_GODO_WORK']['responses'].insert(-1, restore_response)
    # The bolt request is an explicit promise. Looking at its topic alone
    # must not create a materials task.
    for suffix in ['BOLTS_ACCEPTED', 'BOLTS_DELIVERED', 'BOLTS_COLLECTED']:
        obj = by['TALK_BERSERK_RICKERT_' + suffix]
        sp = obj.setdefault('speaker_effect', {'effect': []}); append(sp, run('ORDERS_SYNC'))
    write('dialogue/godo.json', data)
    data = load('dialogue/flora.json'); by = index(data)
    for names, facts_ in [(['BRAND'], ['flora_brand']), (['BRAND_PAIN'], ['flora_brand_pain']),
        (['ARMOR', 'ARMOR_PROPERTIES', 'OWNED', 'OFFER'], ['flora_armor', 'armor_properties']),
        (['COST', 'COST_CONTROL'], ['armor_cost']), (['WARD'], ['ward_recipe_explained']),
        (['WORLD', 'WORLD_COLLISION'], ['flora_world']),
        (['HELP', 'AID'], ['flora_aid_allowed']), (['APOSTOL_FLORA'], ['flora_demon_counsel'])]:
        ids = [('TALK_BERSERK_' + s if s.startswith('APOSTOL_') else 'TALK_BERSERK_FLORA_' + s) for s in names]
        stamp_topics(by, ids, facts_)
    stamp_topics(by, ['TALK_BERSERK_APOSTOL_FLORA_ARMOR'], ['flora_armor_refused'])
    for stem, name in [('COUNT', 'Графа'), ('WYALD', 'Уайлда'), ('ROSINE', 'Розины'), ('GRUNBELD', 'Грюнбельда')]:
        target = 'TALK_BERSERK_FLORA_KNOWN_' + stem
        key = stem.lower(); state = 'berserk_hunt_' + key + '_state'
        text = choose(math(state + ' >= 5'), tr('Этот след уже пройден. Не позволяйте законченной охоте удерживать вас там, где больше нечего искать.'),
            choose(math(state + ' >= 4'), tr('Рана уже закрыта. Осмотрите её уцелевший след, если ещё не успели это сделать.'),
                choose(math(state + ' >= 3'), tr('Хранитель пал, но сам проход ещё нужно осмотреть. Смерть чудовища не всегда закрывает дорогу за ним.'),
                    tr('Продолжите известную вам дорогу. Не входите в незнакомое место, прежде чем увидите, куда сможете отступить.'))))
        obj = topic(target, text, [
            button('Я хотел спросить о другом.', 'TALK_BERSERK_FLORA_NEXT'),
            button('Спасибо. До свидания.', 'TALK_DONE')])
        upsert(data, obj)
        for response in by['TALK_BERSERK_FLORA_NEXT']['responses']:
            if response['topic'] == 'TALK_BERSERK_JOURNAL_PLACE_' + stem: response['topic'] = target
    smith_topic = 'TALK_BERSERK_FLORA_KNOWN_SMITH'
    upsert(data, topic(smith_topic, choose(test('JOURNAL_VALID_GODO'),
        tr('Годо работает в лесной кузнице. С ним живёт Рикерт, молодой мастер механизмов. Теперь у вас есть направление; познакомиться с ними нужно самим.'),
        tr('Я знаю мастеров лесной кузницы. Годо занимается клинками, Рикерт — механизмами. По имеющимся сведениям пока трудно уточнить дорогу, но этот след стоит сохранить.')),
        [button('Я хотел спросить о другом.', 'TALK_BERSERK_FLORA_HELP'), button('Спасибо. До свидания.', 'TALK_DONE')]))
    for response in by['TALK_BERSERK_FLORA_SMITH']['responses']:
        if response['topic'] == 'TALK_BERSERK_JOURNAL_PLACE_GODO':
            response.update(text=tr('Где искать эту кузницу?', 'Where can I find that forge?'), topic=smith_topic,
                            effect=[run('EOC_BERSERK_GODO_LEARN_TRACE')])
    by['TALK_BERSERK_FLORA_AID']['responses'] = [r for r in by['TALK_BERSERK_FLORA_AID']['responses']
        if not any(n.get('run_eocs') == 'EOC_BERSERK_JOURNAL_OPEN' for n in walk(r))]
    write('dialogue/flora.json', data)
    data = load('dialogue/apostle_count.json'); by = index(data)
    stamp_topics(by, ['TALK_BERSERK_COUNT_WITNESS'], ['prisoner_met', 'name_count'])
    stamp_topics(by, ['TALK_BERSERK_COUNT_ROUTE'], ['prisoner_help'])
    # This conversation proves the individual captive survived the keeper.
    # A global boss flag alone says nothing about the captive's fate.
    stamp_topics(by, ['TALK_BERSERK_COUNT_AFTER'], ['prisoner_freed'])
    write('dialogue/apostle_count.json', data)
    data = load('dialogue/apostol_ceremony.json'); by = index(data)
    stamp_topics(by, ['TALK_BERSERK_APOSTOL_OFFER', 'TALK_BERSERK_APOSTOL_PRICE'], ['circle_reached', 'gift_choice_explained'])
    for s in ['VOID', 'SLAN', 'UBIK', 'CONRAD', 'FEMTO']:
        stamp_topics(by, ['TALK_BERSERK_APOSTOL_' + s, 'TALK_BERSERK_APOSTOL_' + s + '_QUESTION'], ['circle_reached'])
    write('dialogue/apostol_ceremony.json', data)
    hookmap = {
        'godo_eocs': [(['GODO_LEARN_TRACE', 'GODO_MEET_SMITH', 'GODO_MEET_RICKERT'], ['name_godo']),
                      (['RICKERT_JOIN'], ['rickert_joined'])],
        'local_breach_eocs': [(['BREACH_CLOSE_COMMIT'], ['breach_directions', 'name_count', 'name_wyald', 'name_rosine'])],
        'new_horizon_progression_eocs': [(['LATE_FLORA_CHECK'], ['flora_named_source'])],
        'eclipse_victory_eocs': [(['ECLIPSE_VICTORY'], ['eclipse_manifestation_defeated'])],
        'eclipse_brand_eocs': [(['ECLIPSE_INSTALL_MARKS'], ['brand_explained']), (['BRAND_NIGHT_HUNT_SPAWN'], ['night_experienced'])],
        'refuge_eocs': [(['REFUGE_INSPECT'], ['ward_examined']), (['REFUGE_REGISTER'], ['refuge_chosen'])],
        'behelit_site_eocs': [(['CAVE_DISTRACTION'], ['cave_chime'])],
        'location_interactions_eocs': [(['CAVE_OPEN_RETURN'], ['cave_prop'])],
        'location_scenery_eocs': [(['SCENERY_CHAPEL'], ['chapel_bypass'])],
        'rosine_cocoon_eocs': [(['COCOON_OPEN'], ['cocoon_examined']), (['COCOON_EMPTIED'], ['rosine_creatures'])],
        'flora_treehouse_eocs': [(['FLORA_ALLOW_AID'], ['flora_aid_allowed']),
            (['FLORA_AID_PANTRY', 'FLORA_AID_WORKSHOP', 'FLORA_AID_WARD'], ['flora_aid_taken']),
            (['FLORA_READ_COSMOLOGY_SHELF'], ['flora_world']),
            (['FLORA_READ_SANCTUARY_WARD'], ['ward_examined']),
            (['FLORA_READ_ARMOR_STAND'], ['armor_properties']),
            (['FLORA_READ_WARD_SHELF'], ['ward_recipe_explained'])],
        'flora_siege_eocs': [(['FLORA_START_SIEGE'], ['flora_attack']), (['FLORA_GRUNBELD_ARRIVED'], ['grunbeld_siege_seen'])],
        'godo_repair_eocs': [(['GODO_REPAIR_START_STORED'], ['repair_handoff'])],
    }
    for file, rules in hookmap.items():
        data = load('effects/' + file + '.json'); by = index(data)
        for suffixes, flags in rules:
            ids = ['EOC_BERSERK_' + s for s in suffixes]
            stamp_eocs(by, ids, flags)
        write('effects/' + file + '.json', data)
    data = load('effects/apostol_path_eocs.json'); by = index(data)
    stamp_eocs(by, ['EOC_BERSERK_APOSTOL_DISTORTED_BEHELIT_USE'], ['distorted_warning'],
               allof(no(GUTS), item('berserk_behelit_distorted')))
    write('effects/apostol_path_eocs.json', data)
    # Record the site of a confirmed death before it becomes merely a shared
    # world flag. Actor-only cleanup and leaving the reality bubble are not
    # evidence of death.
    GENERATED.append(eoc(PREFIX + 'GRUNBELD_GROVE_DEATH', [setf('grunbeld_siege_dead'), setf('dead_grunbeld'), run('SYNC')],
                         allof('u_is_avatar', here['flora'], eq('berserk_apostle_grunbeld_dead'),
                               {'u_can_see_location': {'context_val': 'berserk_grunbeld_siege_body'}})))
    data = load('effects/flora_siege_eocs.json'); by = index(data)
    append(by['EOC_BERSERK_FLORA_GRUNBELD_DIES'], {'run_eocs': PREFIX + 'GRUNBELD_GROVE_DEATH', 'alpha_talker': 'avatar'})
    write('effects/flora_siege_eocs.json', data)
    data = load('effects/griffith_projection_history.json')
    append(data[0], {'if': allof('u_is_avatar', eq('u_berserk_griffith_projection_defeated')),
                     'then': [setf('griffith_projection_understood'), setf('projection_studied'), run('SYNC')]})
    write('effects/griffith_projection_history.json', data)
    # Exact reward success, not an attempt to open an already empty hiding
    # place. The source instance retains its native per-instance furniture.
    data = load('effects/behelit_reward_eocs.json'); by = index(data)
    for stem, loc in [('oak', 'oak'), ('cave', 'cave'), ('chapel', 'chapel'), ('expedition', 'expedition')]:
        append(by['EOC_BERSERK_BEHELIT_SITE_REWARD'], {'if': here[loc], 'then': setf('behelit_' + stem)})
    append(by['EOC_BERSERK_BEHELIT_SITE_REWARD'], run('SYNC'))
    # A real projection's drop is not archived before the player retrieves it.
    append(by['EOC_BERSERK_BEHELIT_BOSS_REWARD'], {
        'if': math("distance('u', _berserk_behelit_drop_pos) <= 3"),
        'then': [setf('projection_drop_seen'), setf('projection_studied')]})
    write('effects/behelit_reward_eocs.json', data)
    # The dawn observation is personal. A solar clock reading alone is not a
    # claim that the player witnessed a nocturnal attack.
    observe.extend([{'if': allof(fact('night_experienced'), test('SOLAR_DAY')), 'then': setf('brand_dawn_seen')},
                    {'if': allof(fact('projection_drop_seen'), item('berserk_behelit')), 'then': setf('projection_behelit')}])
    # Only actual close inspection of the known building can record physical
    # damage. A failed placement/rescue check never calls this observer.
    damage = [{'copy_var': {'global_val': 'berserk_godo_location'}, 'target_var': {'context_val': 'ref_forge_floor'}},
              math('_ref_forge_floor.x = _ref_forge_floor.x + 9'), math('_ref_forge_floor.y = _ref_forge_floor.y + 14'),
              math('_ref_forge_floor.z = 0'),
              {'if': allof(math("distance('u', _ref_forge_floor) <= 3"),
                  anyof({'map_terrain_id': 't_dirt', 'loc': {'context_val': 'ref_forge_floor'}},
                        {'map_field_id': 'fd_fire', 'loc': {'context_val': 'ref_forge_floor'}})),
               'then': setf('forge_damage_observed')}]
    GENERATED.append(eoc(PREFIX + 'FORGE_OBSERVE_DAMAGE', damage,
        allof('u_is_avatar', visited('godo'), no(fact('forge_damage_observed')), here['godo'],
              math('has_var(berserk_godo_location)'), math("u_val('pos_z') == 0"))))
    GENERATED.append(eoc(PREFIX + 'REFUGE_OBSERVE_LOSS', setf('refuge_lost'),
        allof('u_is_avatar', fact('refuge_chosen'), no(fact('refuge_lost')),
              math('has_var(u_berserk_refuge_ward_location)'),
              math("distance('u', u_berserk_refuge_ward_location) <= 1"), 'u_is_outside',
              no({'map_furniture_id': 'f_berserk_shelter_ward', 'loc': {'u_val': 'berserk_refuge_ward_location'}}))))
    observe += [run('FORGE_OBSERVE_DAMAGE'), run('REFUGE_OBSERVE_LOSS')]
    data = load('effects/refuge_eocs.json')
    append(index(data)['EOC_BERSERK_REFUGE_REGISTER'], [setf('refuge_lost', 0), run('SYNC')])
    write('effects/refuge_eocs.json', data)
    # Monster death: beta is the dying actor. NPC_DEATH: alpha is the actor.
    # Capture its actual position before switching to the avatar, then require
    # sight of that position. Unloading and scene cleanup are not real deaths;
    # remove_from_creature_tracker bypasses monster::die entirely in 0.I.
    death_pos = {'context_val': 'ref_death_pos'}
    for person in ['godo', 'rickert', 'flora', 'prisoner']:
        GENERATED.append(eoc(PREFIX + person.upper() + '_DEATH', [
            {'npc_location_variable': death_pos},
            {'run_eocs': PREFIX + person.upper() + '_DEATH_OBSERVED', 'alpha_talker': 'avatar'}]))
        GENERATED.append(eoc(PREFIX + person.upper() + '_DEATH_OBSERVED', [setf(person + '_dead'), run('SYNC')],
            allof('u_is_avatar', {'u_can_see_location': death_pos})))
    for file, actors in [('monsters/apostle_count.json', [('mon_berserk_count_witness', 'PRISONER')]),
                         ('monsters/godo.json', [('mon_berserk_godo', 'GODO'), ('mon_berserk_rickert', 'RICKERT')]),
                         ('monsters/flora.json', [('mon_berserk_flora', 'FLORA')])]:
        data = load(file)
        for actor, person in actors:
            obj = index(data)[actor]; expected = {'eoc': PREFIX + person + '_DEATH'}
            if obj.get('death_function') not in [None, expected]:
                raise ValueError(actor + ' already has an unrelated death function')
            obj['death_function'] = expected
        write(file, data)
    data = load('effects/godo_eocs.json')
    append(index(data)['EOC_BERSERK_RICKERT_DEATH'], [
        {'u_location_variable': death_pos},
        {'run_eocs': PREFIX + 'RICKERT_DEATH_OBSERVED', 'alpha_talker': 'avatar'}])
    write('effects/godo_eocs.json', data)
    # Observe all state transitions on their actual events. This does not
    # insert anything into mutation/encounter condition-only EOCs.
    watch_files = ['apostol_path_eocs', 'apostol_slan_growth_eocs', 'apostol_gifts_eocs',
        'apostol_flesh_eocs', 'apostol_pawn_eocs', 'apostol_body_rules_eocs',
        'apostol_ceremony_eocs', 'apostol_continuation_eocs', 'rickert_dialogue_33_eocs',
        'godo_dialogue_33_eocs', 'skull_knight_dialogue_33_eocs', 'campaign_journal_eocs',
        'first_hunt_eocs', 'eclipse_aftermath_eocs']
    for file in watch_files:
        data = load('effects/' + file + '.json')
        for obj in data:
            if obj.get('type') != 'effect_on_condition' or not obj.get('effect'): continue
            if any(' = ' in n.get('math', [''])[0] and re.search(r'\b(?:u_)?berserk_', n['math'][0])
                   for n in walk(obj['effect'])):
                append(obj, run('SYNC'))
        write('effects/' + file + '.json', data)


def order_missions():
    """Complete the missing ordinary repair/bolt tasks; do not change prices."""
    defs = []
    descriptions = [
        ('MISSION_BERSERK_GODO_REPAIR_COLLECT', 'Забрать отремонтированный клинок',
         'Клинок оставлен у Годо. Вернитесь в лесную кузницу через два часа после передачи и попросите вернуть оружие. Материалы уже переданы.',
         eq('u_berserk_godo_repair_state', 2)),
        ('MISSION_BERSERK_RICKERT_BOLTS_MATERIALS', 'Материалы для болтов',
         'Для десяти арбалетных болтов Рикерту нужны: 1 кусок стали, 1 палка, 20 ниток, 10 перьев и 50 древесного угля. Передайте весь набор самому Рикерту в лесной кузнице. После передачи работа займёт полчаса.',
         anyof(eq('u_berserk_rickert_bolts_pending'), eq('u_berserk_ref_bolts_paid'))),
        ('MISSION_BERSERK_RICKERT_BOLTS_COLLECT', 'Забрать болты у Рикерта',
         'Рикерт получил материалы для десяти болтов. Вернитесь к нему в лесную кузницу через полчаса после передачи и заберите готовую работу.',
         allof(eq('u_berserk_ref_bolts_paid'), no(eq('u_berserk_rickert_bolts_pending')))),
    ]
    for id_, title, desc, goal in descriptions:
        defs.append({'type': 'mission_definition', 'id': id_, 'name': tr(title), 'description': tr(desc),
            'goal': 'MGOAL_CONDITION', 'goal_condition': goal, 'difficulty': 1, 'value': 0,
            'origins': ['ORIGIN_GAME_START'], 'has_generic_rewards': False, 'invisible_on_complete': False,
            'start': {'assign_mission_target': {'om_terrain': 'berserk_godo_workshop',
                'var': {'global_val': 'berserk_godo_location'}, 'reveal_radius': 0}}})
    write('missions/reference_orders_33.json', defs)
    repair = 'MISSION_BERSERK_GODO_REPAIR_COLLECT'
    materials = 'MISSION_BERSERK_RICKERT_BOLTS_MATERIALS'
    collect = 'MISSION_BERSERK_RICKERT_BOLTS_COLLECT'
    def active(id_): return {'u_has_mission': id_}
    def finish(id_, success=True): return {'if': active(id_), 'then': {'finish_mission': id_, 'success': success}}
    # Conditions never finish a missing blade as a success. Abandonment
    # preserves the original consumed supplies and physical item handling.
    sync = [
        {'if': eq('u_berserk_godo_repair_state', 2), 'then': finish(repair),
         'else': {'if': eq('u_berserk_godo_repair_state', 0), 'then': finish(repair, False)}},
        {'if': allof(eq('u_berserk_godo_repair_state'), no(active(repair))), 'then': {'assign_mission': repair}},
        {'if': eq('u_berserk_rickert_bolts_pending'), 'then': [setf('bolts_paid'),
            math('u_berserk_rickert_bolts_requested = 0'), finish(materials),
            {'if': no(active(collect)), 'then': {'assign_mission': collect}}],
         'else': {'if': fact('bolts_paid'), 'then': [finish(collect), setf('bolts_paid', 0)]}},
        {'if': allof(eq('u_berserk_rickert_bolts_requested'), no(eq('u_berserk_rickert_bolts_pending')), no(active(materials))),
         'then': {'assign_mission': materials}}]
    GENERATED.append(eoc(PREFIX + 'ORDERS_SYNC', sync, allof('u_is_avatar', test('GODO_KNOWN'))))
    for file, suffixes in [
        ('godo_eocs', ['RICKERT_ORDER_BOLTS', 'RICKERT_COLLECT_BOLTS', 'GODO_ORDER_SYNC']),
        ('godo_repair_eocs', ['GODO_REPAIR_START_STORED', 'GODO_REPAIR_RETURN_ITEM', 'GODO_REPAIR_ABANDON'])]:
        data = load('effects/' + file + '.json'); by = index(data)
        for s in suffixes: append(by['EOC_BERSERK_' + s], run('ORDERS_SYNC'))
        write('effects/' + file + '.json', data)
    GENERATED.append(eoc(PREFIX + 'ORDERS_REPAIR', run('ORDERS_SYNC'), 'u_is_avatar',
                         **{'global': True, 'recurrence': '1 minute'}))
    # Sources and objectives are reached through the native task list. Remove
    # stale instructions which still present this book as a campaign control.
    for file, descriptions in {
        'missions/first_hunt.json': {
            'MISSION_BERSERK_FIRST_HUNT': ('First hunt: the apostle\'s hollow', 'Первая охота: лесная низина',
                'Find the predator in the marked hollow. Inspect the approaches and the ruined stopping place, prepare a way back, then defeat the creature. After the fight, examine the traces and belongings left in its lair.',
                'Найдите хищника в отмеченной низине. Осмотрите подходы и разрушенное пристанище, подготовьте путь назад и одолейте существо. После боя изучите следы и оставленные в логове вещи.')},
        'missions/named_hunts.json': {
            'MISSION_BERSERK_BREACH': ('Close the ashen breach', 'Закрыть пепельный разрыв',
                'Defeat the keeper at the marked breach, then examine the wound at its center. Closing the passage will not destroy creatures which have already crossed. Study the surviving marks for further trails.',
                'Одолейте хранителя отмеченного разрыва, затем осмотрите рану в его центре. Закрытие прохода не уничтожит уже пришедших существ. Уцелевшие отметки могут указать дальнейшие пути.'),
            'MISSION_BERSERK_COUNT': ('The Count\'s residence', 'Резиденция Графа',
                'Explore the marked residence and the rooms below its execution hall. The trail leads to the Count and a passage held open beneath his house. Deal with the keeper, examine the wound and recover what remains after it is sealed.',
                'Исследуйте отмеченную резиденцию и помещения под залом казней. След ведёт к Графу и проходу под его домом. Одолейте хранителя, осмотрите рану и заберите находку, которая останется после её закрытия.'),
            'MISSION_BERSERK_WYALD': ('The Black Dogs\' camp', 'Лагерь Чёрных Псов',
                'Follow the trail to the Black Dogs\' camp. Inspect its stores, prisoners\' traces and paths of retreat. Wyald holds this place; after confronting him, find the wound linked to the camp and examine what remains when it closes.',
                'Продолжите след к лагерю Чёрных Псов. Осмотрите запасы, следы пленников и пути отступления. Здесь властвует Уайлд; после встречи с ним найдите связанную с лагерем рану и осмотрите то, что останется после её закрытия.'),
            'MISSION_BERSERK_ROSINE': ('The misty valley', 'Туманная долина',
                'Follow the marked trail into the valley. The evidence names Rosine. Study the flowers, cocoons and paths before confronting her. Examine the wound linked to this place and recover the surviving relic after it closes.',
                'Пройдите по отмеченному следу в долину. В свидетельствах названа Розина. Изучите цветы, коконы и проходы, прежде чем встретиться с ней. Осмотрите связанную с этим местом рану и заберите уцелевшую реликвию после её закрытия.'),
            'MISSION_BERSERK_GRUNBELD': ('Grunbeld\'s stronghold', 'Крепость Грюнбельда',
                'The surviving trail leads to the stronghold. Explore the fortifications and the passage linked to this place. Examine the traces Grunbeld left here, close the wound and recover what remains.',
                'Уцелевший след ведёт к крепости. Исследуйте укрепления и связанный с этим местом проход. Изучите оставленные Грюнбельдом следы, закройте рану и заберите то, что останется.')},
    }.items():
        data = load(file)
        for obj in data:
            if obj['id'] in descriptions:
                en, ru, desc_en, desc_ru = descriptions[obj['id']]
                obj['name'] = tr(ru, en); obj['description'] = tr(desc_ru, desc_en)
        write(file, data)
    data = load('missions/godo.json')
    for obj in data:
        if obj['id'] == 'MISSION_BERSERK_GODO_SWORD_TEMPER':
            obj['description'] = tr('Принесите Годо 8 кусков высокоуглеродистой стали, 600 древесного угля и 4 лоскутка кожи. После передачи мастеру понадобятся два дня на ковку и закалку.',
                'Bring Godot 8 lumps of high steel, 600 charcoal and 4 leather patches. After delivery, allow two days for forging and tempering.')
        elif obj['id'] == 'MISSION_BERSERK_GODO_SWORD_COLLECT':
            obj['description'] = tr('Вернитесь к Годо через два дня после последней поставки и заберите готовый клинок.',
                'Return to Godot two days after the last delivery and collect your finished blade.')
        elif obj['id'] == 'MISSION_BERSERK_GODO_EARLY_COLLECT':
            obj['description'] = tr('Вернитесь к Годо через двенадцать часов после передачи материалов и заберите боевой меч.',
                'Return to Godot twelve hours after delivering the materials and collect the battle sword.')
    write('missions/godo.json', data)


def source_loss_recovery():
    # Inspecting the permanent, victory-unlocked trail is a real source. It
    # does not require the one loose paper object to survive on the corpse.
    data = load('effects/hunt_site_detail_eocs.json'); by = index(data)
    by['EOC_BERSERK_HUNT_REVEALED_TRAIL']['effect'] = run('EOC_BERSERK_BREACH_READ_CLUE')
    by['EOC_BERSERK_HUNT_REVEALED_TRAIL']['condition'] = allof(eq('u_berserk_first_hunt_done'),
        {'u_at_om_location': 'berserk_first_hunt_lair'})
    write('effects/hunt_site_detail_eocs.json', data)
    id_ = 'MISSION_BERSERK_FIRST_TRACE'
    write('missions/reference_traces_33.json', [{
        'type': 'mission_definition', 'id': id_, 'name': tr('След в опустевшем логове', 'Traces in the empty lair'),
        'description': tr('Хищник погиб. Осмотрите следы возле его логова: среди пепла и оставленных вещей может сохраниться дорога к тому месту, откуда он пришёл. Если обгоревший клочок найден, его тоже можно изучить.',
            'The predator is dead. Examine the traces in its lair: the ash and abandoned belongings may preserve a trail to the place it came from. If you recovered the burned scrap, you can study it as well.'),
        'goal': 'MGOAL_CONDITION', 'goal_condition': read('apostle_burned_clue'), 'difficulty': 1, 'value': 0,
        'origins': ['ORIGIN_GAME_START'], 'has_generic_rewards': False, 'invisible_on_complete': False,
        'start': {'assign_mission_target': {'om_terrain': 'berserk_first_hunt_lair',
            'var': {'u_val': 'berserk_first_hunt_location'}, 'reveal_radius': 0}}}])
    GENERATED.append(eoc(PREFIX + 'TRACE_SYNC', {
        'if': read('apostle_burned_clue'),
        'then': {'if': {'u_has_mission': id_}, 'then': {'finish_mission': id_, 'success': True}},
        'else': {'if': allof(eq('u_berserk_first_hunt_done'), test('JOURNAL_VALID_FIRST'), no({'u_has_mission': id_})),
                 'then': {'assign_mission': id_}}}, 'u_is_avatar'))
    GENERATED.append(eoc(PREFIX + 'TRACE_REPAIR', run('TRACE_SYNC'), 'u_is_avatar',
                         **{'global': True, 'recurrence': '1 minute'}))
    data = load('effects/first_hunt_eocs.json')
    append(index(data)['EOC_BERSERK_FIRST_HUNT_FINISH_MISSION'], run('TRACE_SYNC'))
    write('effects/first_hunt_eocs.json', data)
    data = load('effects/local_breach_eocs.json')
    append(index(data)['EOC_BERSERK_BREACH_READ_CLUE'], run('TRACE_SYNC'))
    write('effects/local_breach_eocs.json', data)


def quiet_notifications():
    # One source popup is enough. Silent bookkeeping does not pretend the
    # physical journal is needed or reissue it after it was deliberately lost.
    replacements = {
        "Refuge recorded. Stay within this ward's reach for the Brand's protection; keep watch for creatures that are already here. The refuge journal keeps your preparations and onward directions. It grants no healing, armor or immunity.":
            'Вы выбрали пристанище у защитного знака. Он ослабит зов Клейма поблизости, но уже пришедшие существа остаются опасны.',
        'The recorded ward is gone. Its journal entry no longer marks the refuge as ready; inspect another ward when your preparations are complete.':
            'Защита прежнего знака больше не действует. Если нужно новое пристанище, осмотрите другой знак.',
        'You claim the relic from the sealed mark. The gift is issued once for this hunt; check the floor if you cannot carry it. Wear it to receive its effect. The hunt journal preserves the directions.':
            'Вы забираете реликвию из затихшей раны. Наденьте её, чтобы ощутить силу. Если в вещах не хватило места, находка осталась у ног.',
        'The charm has already served its purpose. Keep the surviving directions in your journal.':
            'Оберег уже исполнил своё назначение.',
        'The woodland forge is marked on your map. The direction is kept in your road journal.':
            'Лесная кузница отмечена на карте.',
        'The woodland forge’s road is still uncertain. The account is saved in your road journal; return to it when you have more bearings.':
            'По этим сведениям пока не удалось уточнить дорогу к кузнице. Полученный след сохранён.',
        'Grunbeld has fallen, but the wound linked to his stronghold remains to be examined. Keep that unfinished trail in your journal.':
            'Грюнбельд пал, но связанную с его крепостью рану ещё предстоит осмотреть.',
        'The unfinished trail to the misty valley remains in your journal.':
            'Осталась незавершённая дорога в туманную долину.',
        'The ashen breach is still open. Its location remains in your journal.':
            'Пепельный разрыв ещё открыт. Его место вам известно.',
        'Recover at your refuge. Consult your journal for wounds still open and trails you have not completed.':
            'Отдохните в своём пристанище, прежде чем продолжать незавершённые пути.',
        'The flesh dissolves beneath your skin. The change has begun and will finish without another portion. Find food, water and somewhere to rest; your road journal records its progress.':
            'Плоть растворяется под кожей. Перемена началась и продолжится сама. Найдите воду, еду и место для отдыха.',
        'You return to the living world. A broken road and an ashen wound linger behind your eyes. You record that trail in your road journal. Find food and somewhere to recover before following it.':
            'Вы вернулись в мир живых. Перед глазами всё ещё стоят разбитая дорога и пепельная рана. Этот след не забыт. Найдите еду и место для отдыха, прежде чем идти дальше.',
    }
    def clean(v):
        if isinstance(v, list):
            return [clean(x) for x in v if not (isinstance(x, dict) and x.get('u_message') in [
                'A new entry has been added to your road journal.', 'The directions have been copied into your road journal.'])]
        if isinstance(v, dict):
            return {k: tr(replacements[x]) if k in ['u_message', 'set_string_var'] and isinstance(x, str) and x in replacements
                    else clean(x) for k, x in v.items()}
        return v
    for path in (MOD / 'effects').glob('*.json'):
        if path.name == 'reference_journal_eocs.json': continue
        data = json.loads(path.read_text()); new = clean(data)
        if new != data: write('effects/' + path.name, new)
    # Preserve the one existing fire summary, replacing only its reliance on
    # the book as a route controller. No second summary is introduced.
    data = load('effects/campaign_journal_eocs.json')
    for obj in walk(data):
        if obj.get('set_string_var') == 'The surviving directions point toward Grunbeld’s stronghold. Consult that entry when you are ready to continue.':
            obj['set_string_var'] = tr('Уцелевший след ведёт к крепости Грюнбельда. Направление отмечено среди ваших заданий.')
        elif isinstance(obj.get('set_string_var'), str) and 'unfinished trail remains in your journal' in obj['set_string_var']:
            obj['set_string_var'] = tr('Среди известных дорог остались незавершённые следы.')
    write('effects/campaign_journal_eocs.json', data)


def main():
    catalog = original_catalog()
    records = build()
    topics = make_reference(records, catalog['knight_advice'])
    readers = sources_and_legacy(catalog, topics, records)
    compatibility_eocs()
    knowledge_events_and_hooks()
    items_and_restoration()
    order_missions()
    source_loss_recovery()
    quiet_notifications()
    write('dialogue/road_journal.json', topics)
    write('effects/reference_journal_eocs.json', GENERATED + list(HELPERS.values()))
    manifest = {'records': records, 'physical_readers': readers, 'manuscript_entries': 93,
                'sections': ['places', 'people', 'past']}
    (ROOT / 'docs/dialogue_sources/reference-journal-bindings-33.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    localization()
    print(f'Optional reference book: {len(records)} records, {len(topics)} topics; {len(readers)} source readers.')


if __name__ == '__main__': main()
