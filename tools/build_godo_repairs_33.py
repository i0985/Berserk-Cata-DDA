#!/usr/bin/env python3
"""Patch only Godo's repair service, its journal card and new translations.

Uses the 0.I item-talker APIs, not NPC trading: Godo is a monster talker.
The actual selected item moves to the forge and back; no replacement is spawned.
"""
import json
import subprocess

from recover_apostol_33 import MOD, both, eoc, index, math, read, test, upsert, write
from recovery_33_translations import source

STRINGS = {}


def tr(en, ru, zh):
    STRINGS[en] = (ru, zh)
    return en


P = 'EOC_BERSERK_GODO_REPAIR_'
BLADES = ['true_guts_sword', 'true_guts_early_sword', 'forged_guts_sword',
          'forged_guts_early_sword']
IDLE = math('u_berserk_godo_repair_state != 1')
ACTIVE = math('u_berserk_godo_repair_state == 1')
READY = both(ACTIVE, math("time('now') >= u_berserk_godo_repair_ready_at"))
AT_SMITH = test('EOC_BERSERK_GODO_AT_SMITH')
JOB = both(math('u_berserk_godo_repair_job > 0'),
           math('n_berserk_godo_repair_job == u_berserk_godo_repair_job'))
MATERIALS = both({'u_has_items': {'item': 'steel_lump', 'count': 1}},
                 {'u_has_items': {'item': 'charcoal', 'count': 50}})


def scan(callback):
    return {'u_map_run_item_eocs': 'all',
            'loc': {'u_val': 'berserk_godo_repair_storage'},
            'min_radius': 0, 'max_radius': 2,
            'search_data': [{'id': BLADES, 'condition': JOB}],
            'true_eocs': [P + callback]}


def main():
    helper = []
    helper.append(eoc(P + 'PLACE_ITEM', [
        # Global serial prevents another avatar's similarly named blade matching.
        math('berserk_godo_repair_serial = berserk_godo_repair_serial + 1'),
        math('u_berserk_godo_repair_job = berserk_godo_repair_serial'),
        math('n_berserk_godo_repair_job = u_berserk_godo_repair_job'),
        math('u_berserk_godo_repair_handoff_pending = 1'),
        # LAST: npc_teleport removes the old item_location.
        {'npc_teleport': {'u_val': 'berserk_godo_repair_storage'}},
    ], both(IDLE, MATERIALS)))
    helper.append(eoc(P + 'START_STORED', [
        {'u_consume_item': 'steel_lump', 'charges': 1},
        {'u_consume_item': 'charcoal', 'charges': 50},
        math("u_berserk_godo_repair_ready_at = time('now') + 7200"),
        math('u_berserk_godo_repair_state = 1'),
        math('u_berserk_godo_repair_handoff_pending = 0'),
        {'u_message': tr('Godot sets your blade beside his tools. "Come back in two hours. I will see to the edge and the worn metal."',
                         'Годо кладёт ваш клинок рядом с инструментами. «Вернись через два часа. Поправлю кромку и восстановлю изношенный металл».',
                         '高多把你的剑放在工具旁。“两个小时后回来。我会修好剑刃和磨损的金属。”')},
    ], both(JOB, IDLE, MATERIALS, math('u_berserk_godo_repair_handoff_pending == 1'))))

    healthy = {'u_message': tr('Godot checks the blade. "Still in good condition. No repair needed yet. Keep your materials."',
                              'Годо осматривает клинок. «Ещё в хорошем состоянии. Пока ремонт не нужен. Побереги материалы».',
                              '高多检查了剑刃。“状况还不错，暂时不用修。材料留着吧。”')}
    missing = {'u_message': tr('"The blade needs work. Bring one steel lump and 50 charcoal, and leave it with me for two hours."',
                              '«Клинку нужен ремонт. Принеси один кусок стали и 50 единиц древесного угля, а клинок оставь мне на два часа».',
                              '“这把剑需要修理。带来一块钢和50份木炭，再把剑留给我两个小时。”')}
    # Inspection results must be visible while the dialogue screen is open.
    healthy['popup'] = True
    missing['popup'] = True
    consent = {'u_query': tr('Leave this blade, one steel lump and 50 charcoal with Godot? The repair takes two hours.',
                            'Оставить этот клинок, один кусок стали и 50 единиц древесного угля Годо? Ремонт займёт два часа.',
                            '把这把剑、一块钢和50份木炭交给高多吗？修理需要两个小时。'), 'default': False}
    old = read('effects/godo_eocs.json')
    upsert(old, eoc(P + 'ITEM', {
        'if': math("n_hp('ALL') * 100 >= n_hp_max('torso') * 70"), 'then': healthy,
        'else': {'if': MATERIALS, 'then': {'if': consent, 'then': {'run_eocs': P + 'PLACE_ITEM'}},
                 'else': missing}}, IDLE))
    upsert(old, eoc(P + 'PICK', [
        {'npc_location_variable': {'u_val': 'berserk_godo_repair_storage'}},
        math('u_berserk_godo_repair_handoff_pending = 0'),
        {'u_run_inv_eocs': 'manual',
         'title': tr('Show Godot a blade', 'Показать Годо клинок', '给高多看一把剑'),
         # The approved October dialogue refuses NEW work on Dragonslayer once
         # a demonic path is accepted. A previously handed-in repair is honored.
         'search_data': [{'id': [x for x in BLADES if x != 'true_guts_sword']},
                         {'id': ['true_guts_sword'], 'condition': test('EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED')}],
         'true_eocs': [P + 'ITEM']},
        # No false_eocs: manual item callbacks also call false_eocs after a move.
        {'if': math('u_berserk_godo_repair_handoff_pending == 1'), 'then': scan('START_STORED')},
    ], both(AT_SMITH, IDLE)))
    write('effects/godo_eocs.json', old)

    helper.append(eoc(P + 'RETURN_ITEM', [
        math('u_berserk_godo_repair_found = 1'),
        # set_damage is clamped by degradation, so reset degradation FIRST.
        math('n_degradation() = 0'), math("n_hp('ALL') = n_hp_max('torso')"),
        math('u_berserk_godo_repair_state = 2'),
        {'u_message': tr('Godot lays your repaired blade at your feet. "Good as new. Take it."',
                         'Годо кладёт отремонтированный клинок у ваших ног. «Как новый. Забирай».',
                         '高多把修好的剑放在你脚边。“跟新的一样。拿去吧。”')},
        {'npc_teleport': {'u_val': 'berserk_godo_repair_return_point'}},
    ], both(JOB, READY)))
    helper.append(eoc(P + 'CLAIM', [
        {'if': READY, 'then': [
            {'u_location_variable': {'u_val': 'berserk_godo_repair_return_point'}},
            math('u_berserk_godo_repair_found = 0'), scan('RETURN_ITEM'),
            {'if': math('u_berserk_godo_repair_found == 0'),
             'then': {'u_message': tr('"Your blade is not beside my tools. If you took it, bring the same blade back so I can finish."',
                                     '«Твоего клинка нет возле инструментов. Если забрал его, принеси обратно — закончу работу».',
                                     '“工具旁没有你的剑。如果你拿走了，就把原来那把带回来，我才能完成修理。”')}},
        ], 'else': {'u_message': tr('"Not yet. Give me two hours from when you left the blade."',
                                    '«Ещё не закончил. Мне нужно два часа с того момента, как ты оставил клинок».',
                                    '“还没好。从你把剑留下算起，我需要两个小时。”')}},
    ], both(AT_SMITH, ACTIVE)))

    helper.append(eoc(P + 'REDEPOSIT_ITEM', [
        math('u_berserk_godo_repair_handoff_pending = 1'),
        {'npc_teleport': {'u_val': 'berserk_godo_repair_storage'}},
    ], both(ACTIVE, JOB)))
    helper.append(eoc(P + 'RESUME_STORED', [
        math("u_berserk_godo_repair_ready_at = time('now') + 7200"),
        math('u_berserk_godo_repair_handoff_pending = 0'),
        {'u_message': tr('"Leave it here this time. Another two hours; you have already paid for the materials."',
                         '«На этот раз оставь его здесь. Ещё два часа; за материалы ты уже заплатил».',
                         '“这次把剑留在这里。再等两个小时；材料你已经付过了。”')},
    ], both(ACTIVE, JOB, math('u_berserk_godo_repair_handoff_pending == 1'))))
    helper.append(eoc(P + 'REDEPOSIT', [
        math('u_berserk_godo_repair_handoff_pending = 0'),
        {'u_run_inv_eocs': 'manual',
         'title': tr('Return your blade to Godot', 'Вернуть свой клинок Годо', '把原来的剑交还高多'),
         'search_data': [{'id': BLADES, 'condition': JOB}],
         'true_eocs': [P + 'REDEPOSIT_ITEM']},
        {'if': math('u_berserk_godo_repair_handoff_pending == 1'), 'then': scan('RESUME_STORED')},
    ], both(AT_SMITH, ACTIVE)))
    helper.append(eoc(P + 'ABANDON', {
        'if': {'u_query': tr('Close this repair order? The materials have been used and will not be returned. No blade will be replaced.',
                            'Закрыть этот заказ ремонта? Материалы уже израсходованы и не возвращаются. Замена клинка не выдаётся.',
                            '结束这次修理委托吗？材料已经用掉，不会退还，也不会补发剑。'), 'default': False},
        'then': [math('u_berserk_godo_repair_state = 0'), math('u_berserk_godo_repair_job = 0')],
    }, both(AT_SMITH, ACTIVE)))
    write('effects/godo_repair_eocs.json', helper)

    topics = read('dialogue/godo.json'); topic = index(topics)['TALK_BERSERK_GODO_REPAIR']
    if index(topics)['TALK_BERSERK_GODO'].get('//') == 'Approved Godo dialogue 2026-10-21':
        # New authored dialogue is canonical; this helper only maintains repair
        # mechanics now. Run build_godo_dialogue_33.py for literary changes.
        return
    topic['dynamic_line'] = {
        'math': ['u_berserk_godo_repair_state == 1'],
        'yes': tr('You left a blade with me. I need two hours at the forge. If you took it away, bring the same blade back.',
                  'Ты оставил мне клинок. На работу у горна нужно два часа. Если забрал его, принеси обратно тот же клинок.',
                  '你有一把剑交给我修理，需要在炉边干两个小时。如果拿走了，就把原来那把带回来。'),
        'no': tr('Show me the blade first. No sense working sound metal. If it needs repair, leave it with one steel lump and 50 charcoal. Come back in two hours.',
                 'Сперва покажи клинок. Хороший металл зря мучить незачем. Если нужен ремонт, оставишь его, один кусок стали и 50 единиц древесного угля. Через два часа вернёшься.',
                 '先把剑给我看看。好好的金属没必要折腾。如果需要修理，就留下剑、一块钢和50份木炭，两个小时后回来。')}
    back = [r for r in topic['responses'] if r['topic'] in
            ['TALK_BERSERK_GODO_OWNER', 'TALK_BERSERK_GODO_WORK']]
    topic['responses'] = [
        {'text': tr('Have a look at my blade.', 'Осмотри мой клинок.', '看看我的剑。'),
         'topic': topic['id'], 'condition': IDLE, 'effect': {'run_eocs': P + 'PICK'}},
        {'text': tr('Is my blade ready?', 'Мой клинок готов?', '我的剑修好了吗？'),
         'topic': topic['id'], 'condition': ACTIVE, 'effect': {'run_eocs': P + 'CLAIM'}},
        {'text': tr('I took the blade. Here it is again.', 'Я забрал клинок. Вот, возвращаю.', '我把剑拿走了，现在交回来。'),
         'topic': topic['id'], 'condition': ACTIVE, 'effect': {'run_eocs': P + 'REDEPOSIT'}},
        {'text': tr('Close the repair order.', 'Закроем заказ ремонта.', '结束这次修理委托。'),
         'topic': topic['id'], 'condition': ACTIVE, 'effect': {'run_eocs': P + 'ABANDON'}},
    ] + back
    orders = index(topics)['TALK_BERSERK_GODO_ORDERS']
    entry = {'text': tr('About my blade repair.', 'Насчёт ремонта моего клинка.', '关于我的剑的修理。'),
             'topic': topic['id'], 'condition': ACTIVE}
    if not any(r['text'] == entry['text'] for r in orders['responses']): orders['responses'].insert(0, entry)
    write('dialogue/godo.json', topics)

    journal = read('dialogue/road_journal.json'); menu = index(journal)['TALK_BERSERK_JOURNAL_ORDERS']
    entry = {'text': tr('Godot: blade repair.', 'Годо: ремонт клинка.', '高多：修理剑刃。'),
             'topic': 'TALK_BERSERK_JOURNAL_REPAIR', 'condition': ACTIVE}
    if not any(r['topic'] == entry['topic'] for r in menu['responses']): menu['responses'].insert(0, entry)
    upsert(journal, {'type': 'talk_topic', 'id': entry['topic'], 'dynamic_line': {
        'math': ["time('now') >= u_berserk_godo_repair_ready_at"],
        'yes': tr('*Blade repair. The agreed time has passed. Return to Godot at the forge to collect your blade.',
                  '*Ремонт клинка. Условленное время прошло. Вернуться к Годо в кузницу за своим клинком.',
                  '*修理剑刃。约定的时间已到。回铁匠铺找高多取回自己的剑。'),
        'no': tr('*Blade repair. Godot has the blade and the materials. Allow two hours, then return to the forge.',
                 '*Ремонт клинка. Клинок и материалы оставлены Годо. Подождать два часа, затем вернуться в кузницу.',
                 '*修理剑刃。剑和材料已经交给高多。等两个小时后回铁匠铺。')},
        'responses': [{'text': 'Back.', 'topic': 'TALK_BERSERK_JOURNAL_ORDERS'}]})
    write('dialogue/road_journal.json', journal)

    for file, col in [('ru.po', 0), ('zh_CN.po', 1), ('Berserk.pot', None)]:
        path = MOD / 'lang/po' / file
        known = {source(b) for b in path.read_text().split('\n\n')}
        with path.open('a') as stream:
            for en, values in STRINGS.items():
                if en not in known:
                    stream.write('\n#. Godo blade repair\nmsgid ' + json.dumps(en, ensure_ascii=False) +
                                 '\nmsgstr ' + json.dumps('' if col is None else values[col], ensure_ascii=False) + '\n')
    for locale in ['ru', 'zh_CN']:
        subprocess.run(['msgfmt', '--check', '-o', str(MOD / f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo'),
                        str(MOD / f'lang/po/{locale}.po')], check=True)


if __name__ == '__main__':
    main()
