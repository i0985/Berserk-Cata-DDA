#!/usr/bin/env python3
"""Restore the immediate, persistent human-equipment gate after acceptance."""
from recover_apostol_33 import (MOD, read, write, index, walk, eoc, math, test,
                                both, upsert, text, save_translations)

ALLOWED = 'EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED'


def gate(condition):
    if test(ALLOWED) in list(walk(condition)):
        return condition
    return both(test(ALLOWED), condition)


def main():
    traits = []
    for path in sorted((MOD / 'mutations').glob('apostol_*.json')):
        data = read(str(path.relative_to(MOD)))
        if not isinstance(data, list): continue
        traits += [{'u_has_trait': x['id']} for x in data if x.get('type') == 'mutation']
    accepted = {'or': [math('u_berserk_apostol_human_equipment_locked == 1'),
                        math('u_berserk_apostol_path > 0'),
                        math('u_berserk_apostol_lineage > 0'), *traits]}
    write('effects/apostol_human_equipment_eocs.json', [
        eoc(ALLOWED, [], {'not': accepted}),
        eoc('EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_LATCH',
            math('u_berserk_apostol_human_equipment_locked = 1'),
            both('u_is_avatar', math('u_berserk_apostol_human_equipment_locked != 1'),
                 {'not': test(ALLOWED)}), eoc_type='RECURRING', recurrence='1 minute',
            **{'global': True})])
    paths = read('effects/apostol_path_eocs.json')
    accept = index(paths)['EOC_BERSERK_APOSTOL_ACCEPT_REQUEST']['effect']
    latch = math('u_berserk_apostol_human_equipment_locked = 1')
    if latch not in accept:
        accept.insert(0, latch)
    write('effects/apostol_path_eocs.json', paths)

    data = read('effects/godo_eocs.json'); ids = index(data)
    blocked = ['START_SWORD', 'SWORD_IRON', 'SWORD_TEMPER', 'SWORD_CLAIM',
               'START_EARLY_SWORD', 'EARLY_MATERIALS', 'EARLY_CLAIM']
    for suffix in blocked:
        obj = ids['EOC_BERSERK_GODO_' + suffix]
        obj['condition'] = gate(obj['condition'])
    for suffix, owned in [
        ('SWORD_REFUND', test('EOC_BERSERK_GODO_HAS_SWORD')),
        ('EARLY_REFUND', {'u_has_items': {'item': 'true_guts_early_sword', 'count': 1}})]:
        refund = ids['EOC_BERSERK_GODO_' + suffix]
        # The original bounds (state < claimed) provide one-time payment.
        for node in walk(refund['condition']):
            for key in ['and']:
                values = node.get(key, [])
                if owned in values:
                    values[values.index(owned)] = {'or': [owned, {'not': test(ALLOWED)}]}
                    break
    sync = ids['EOC_BERSERK_GODO_ORDER_SYNC']
    updated = []
    for branch in sync['effect']:
        encoded = str(branch)
        if any(x in encoded for x in ['GODO_SWORD_', 'GODO_EARLY_']) and branch.get('if') != test(ALLOWED):
            missions = sorted({n['assign_mission'] for n in walk(branch) if 'assign_mission' in n})
            updated.append({'if': test(ALLOWED), 'then': branch, 'else': [
                {'if': {'u_has_mission': name}, 'then': {'finish_mission': name, 'success': False}}
                for name in missions]})
        else:
            updated.append(branch)
    sync['effect'] = updated
    write('effects/godo_eocs.json', data)

    dialogue = read('dialogue/godo.json')
    blocked_ids = {'EOC_BERSERK_GODO_' + x for x in blocked}
    for obj in dialogue:
        for response in obj.get('responses', []):
            calls = {n.get('run_eocs') for n in walk(response.get('effect')) if isinstance(n.get('run_eocs'), str)}
            if calls & blocked_ids:
                response['condition'] = gate(response.get('condition', both()))
    orders = index(dialogue)['TALK_BERSERK_GODO_ORDERS']['responses']
    for suffix, state, terminal in [('EARLY', 'early', 3), ('SWORD', 'sword', 4)]:
        topic = 'TALK_BERSERK_GODO_CHANGED_' + suffix
        label = (text('The change has begun. What about the long sword?', 'Изменения уже начались. Что будет с заказом боевого меча?')
                 if suffix == 'EARLY' else text('The change has begun. What about the Dragonslayer?', 'Изменения уже начались. Что будет с заказом Драконоборца?'))
        if not any(x.get('topic') == topic for x in orders):
            orders.insert(-1, {'text': label,
                'topic': topic,
                'condition': both({'not': test(ALLOWED)}, math(f'u_berserk_godo_{state}_state > 0'),
                                  math(f'u_berserk_godo_{state}_state < {terminal}'))})
        else:
            next(x for x in orders if x.get('topic') == topic)['text'] = label
        upsert(dialogue, {'type': 'talk_topic', 'id': topic,
            'dynamic_line': text('Then I will not finish this blade for you. Take back the materials you brought.',
                                 'Тогда этот клинок я для тебя не закончу. Забери материалы, которые принёс.'),
            'responses': [
                {'text': text('Return my materials.', 'Верни мои материалы.'),
                 'topic': 'TALK_BERSERK_GODO_ORDERS',
                 'effect': {'run_eocs': f'EOC_BERSERK_GODO_{suffix}_REFUND'}},
                {'text': 'Back to the topics.', 'topic': 'TALK_BERSERK_GODO'}]})
    write('dialogue/godo.json', dialogue)

    flora = read('effects/flora_eocs.json'); f = index(flora)
    f['EOC_BERSERK_FLORA_CAN_RECEIVE']['condition'] = gate(f['EOC_BERSERK_FLORA_CAN_RECEIVE']['condition'])
    write('effects/flora_eocs.json', flora)
    siege = read('effects/flora_siege_eocs.json')
    ready = index(siege)['EOC_BERSERK_FLORA_CAN_PREPARE_SIEGE']['condition']['and']
    armor = next(x for x in ready if 'or' in x and test('EOC_BERSERK_FLORA_FULL_SET') in x['or'])
    if {'not': test(ALLOWED)} not in armor['or']:
        armor['or'].append({'not': test(ALLOWED)})
    write('effects/flora_siege_eocs.json', siege)
    dialogue = read('dialogue/flora.json')
    index(dialogue)['TALK_BERSERK_APOSTOL_FLORA_ARMOR']['dynamic_line'] = text(
        'The armor cannot undo your change. I will not place another dangerous power upon it. You may still rest here, and we can speak of the road ahead.',
        'Доспех не отменит твоего превращения. Я не стану добавлять к нему ещё одну опасную силу. Но ты можешь отдохнуть здесь, и мы поговорим о дальнейшей дороге.')
    write('dialogue/flora.json', dialogue)
    # This old global loot extension bypassed any NPC decision and rolled armor
    # in laboratories for everybody. Remove only the mod's extension, not base loot.
    legacy = MOD / 'item_groups.json'
    if legacy.exists():
        assert all(x.get('id') == 'lab_artifacts' for x in read('item_groups.json'))
        legacy.unlink()
    save_translations()
    print('Human-equipment gate, existing-order refunds and Flora continuation recovered.')


if __name__ == '__main__': main()
