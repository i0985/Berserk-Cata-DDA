#!/usr/bin/env python3
"""Idempotent, narrow recovery of post-archive 3.3 fixes; no 3.2 generators.

Only explicitly listed objects/fields are edited. --package chooses a checkpoint.
New literary dialogue scripts are intentionally not part of this recovery.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/Berserk'
TRANSLATIONS = {}


def read(name):
    return json.loads((MOD / name).read_text())


def write(name, data):
    (MOD / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def index(data):
    return {x['id']: x for x in data if 'id' in x}


def walk(data):
    if isinstance(data, dict):
        yield data
        for value in list(data.values()):
            yield from walk(value)
    elif isinstance(data, list):
        for value in data:
            yield from walk(value)


def text(en, ru):
    TRANSLATIONS[en] = ru
    return en


def eoc(name, effect, condition=None, **kwargs):
    out = dict(type='effect_on_condition', id=name, effect=effect, **kwargs)
    if condition is not None:
        out['condition'] = condition
    return out


def math(expr):
    return {'math': [expr]}


def test(name):
    return {'test_eoc': name}


def both(*args):
    return {'and': list(args)}


def upsert(data, obj):
    for i, old in enumerate(data):
        if old.get('id') == obj['id']:
            data[i] = obj
            return
    data.append(obj)


def abilities():
    gifts = read('spells/apostol_gifts.json')
    g = index(gifts)
    for id_, distance in [('void_step', 8), ('ubik_image', 7),
                          ('ubik_confuse', 7), ('conrad_strike', 2),
                          ('conrad_cloud', 6), ('femto_dash', 6),
                          ('femto_suppression', 7)]:
        g['berserk_apostol_' + id_].update(min_range=distance, max_range=distance)
    g['berserk_apostol_ubik_image'].update(min_duration=2000, max_duration=2000)
    g['berserk_apostol_ubik_confuse'].update(min_aoe=1, max_aoe=1)
    # Native attack damages monsters AND NPCs immediately. Old EOC excluded NPCs
    # and undead, and its damage-over-time modifier was not a monster attack.
    strike = g['berserk_apostol_conrad_strike']
    strike.update(effect='attack', damage_type='acid', min_damage=40, max_damage=40)
    strike.pop('effect_str', None)
    strike['description'] = text('A corrosive touch eats into a nearby enemy.',
                                 'Едкое прикосновение разъедает тело ближайшего врага.')
    cloud = g['berserk_apostol_conrad_cloud']
    cloud.update(damage_type='acid', min_damage=24, max_damage=24, min_aoe=2,
                 max_aoe=2, min_field_intensity=2, max_field_intensity=2)
    cloud['description'] = text('A caustic breath strikes the area and leaves toxic fumes.',
                                'Едкое дыхание поражает область и оставляет ядовитую взвесь.')
    # Damage first, then push the surviving target from the same epicenter.
    pulse = g['berserk_apostol_femto_pulse']
    pulse.update(effect='attack', damage_type='bash', min_damage=35, max_damage=35,
                 min_range=7, max_range=7)
    pulse['extra_effects'] = [{'id': 'berserk_apostol_femto_push'},
                             {'id': 'berserk_apostol_cast_confirmed', 'hit_self': True}]
    push = dict(pulse, id='berserk_apostol_femto_push', effect='directed_push',
                min_damage=5, max_damage=5, extra_effects=[])
    upsert(gifts, push)
    g['berserk_apostol_femto_suppression'].update(min_damage=20, max_damage=20,
        damage_type='bash', min_aoe=2, max_aoe=2, min_duration=600, max_duration=600)
    write('spells/apostol_gifts.json', gifts)
    slan = read('spells/apostol_slan.json')
    slan[0].update(min_damage=48, max_damage=48, min_range=5, max_range=5)
    write('spells/apostol_slan.json', slan)
    flesh = read('spells/apostol_flesh.json'); f = index(flesh)
    for id_, values in {
        'count_flesh_strike': dict(min_damage=40, max_damage=40, min_range=3, max_range=3),
        'wyald_flesh_dash': dict(min_range=6, max_range=6),
        'wyald_flesh_grip': dict(min_damage=28, max_damage=28, min_duration=600, max_duration=600),
        'rosine_flesh_dash': dict(min_range=7, max_range=7),
        'rosine_flesh_impact': dict(min_damage=36, max_damage=36),
        'grunbeld_flesh_breath': dict(min_damage=52, max_damage=52, min_range=7, max_range=7,
            min_aoe=45, max_aoe=45, min_field_intensity=2, max_field_intensity=2),
    }.items():
        f['berserk_apostol_' + id_].update(values)
    write('spells/apostol_flesh.json', flesh)
    pawns = read('spells/apostol_pawns.json'); p = index(pawns)
    p['berserk_apostol_count_pawn_lash'].update(min_damage=28, max_damage=28,
                                              min_range=3, max_range=3)
    p['berserk_apostol_count_pawn_lash']['description'] = text('A heavy tendril lashes the enemy.', 'Тяжёлый отросток хлещет врага.')
    p['berserk_apostol_wyald_pawn_dash'].update(min_range=4, max_range=4)
    p['berserk_apostol_wyald_pawn_dash']['description'] = text('Rush forward and strike nearby enemies.', 'Бросок вперёд с ударом по ближайшим врагам.')
    impact = dict(f['berserk_apostol_rosine_flesh_impact'],
                  id='berserk_apostol_wyald_pawn_impact', damage_type='bash',
                  min_damage=22, max_damage=22)
    impact['name'] = text('Rending rush', 'Сокрушительный бросок')
    impact['description'] = text('A violent rush ends in a sweeping blow.',
                                  'Яростный бросок завершается размашистым ударом.')
    upsert(pawns, impact)
    write('spells/apostol_pawns.json', pawns)
    for name in ['effects/apostol_gifts_eocs.json', 'effects/apostol_slan_growth_eocs.json',
                 'effects/apostol_flesh_eocs.json', 'effects/apostol_pawn_eocs.json']:
        data = read(name)
        for obj in data:
            for node in walk(obj.get('effect')):
                id_ = node.get('u_add_effect')
                durations = {'berserk_apostol_void_ward': '4 seconds',
                    'berserk_apostol_ubik_veil': '8 seconds',
                    'berserk_apostol_flesh_flutter': '5 seconds',
                    'berserk_apostol_flesh_braced': '8 seconds',
                    'berserk_apostol_pawn_flutter': '5 seconds',
                    'berserk_apostol_pawn_brace': '6 seconds'}
                if id_ in durations:
                    node['duration'] = durations[id_]
                if 'math' in node:
                    ex = node['math'][0]
                    if 'u_hp(' in ex and ' = min(' in ex:
                        if obj['id'] == 'EOC_BERSERK_APOSTOL_SLAN_MEND_USE':
                            node['math'][0] = ex.replace(' + 6)', ' + 12)')
                        elif obj['id'] == 'EOC_BERSERK_APOSTOL_COUNT_FLESH_MEND_RESULT':
                            node['math'][0] = ex.replace(' + 3)', ' + 7)')
            if obj['id'] == 'EOC_BERSERK_APOSTOL_UBIK_CONFUSE_TARGET':
                if 'and' in obj['condition']:
                    obj['condition'] = obj['condition']['and'][1]
                obj['effect']['duration'] = '4 seconds'
            if obj['id'] == 'EOC_BERSERK_APOSTOL_WYALD_PAWN_POWER_PAY':
                effect = obj['effect']
                if not any(x.get('u_cast_spell', {}).get('id') == impact['id'] for x in effect):
                    effect.insert(0, {'u_cast_spell': {'id': impact['id'], 'hit_self': True},
                                      'targeted': False})
        write(name, data)
    for name, mods in {
        'effects/apostol_gift_effect_types.json': {
            'berserk_apostol_void_ward': ('ARMOR_ALL', 'multiply', -0.7),
            'berserk_apostol_suppressed': ('speed_mod', None, -40)},
        'effects/apostol_flesh_effect_types.json': {
            'berserk_apostol_flesh_grip': ('speed_mod', None, -40),
            'berserk_apostol_flesh_flutter': ('DODGE_CHANCE', 'add', 4),
            'berserk_apostol_flesh_braced': ('ARMOR_ALL', 'add', -7)},
        'effects/apostol_pawn_power_types.json': {
            'berserk_apostol_pawn_flutter': ('DODGE_CHANCE', 'add', 3),
            'berserk_apostol_pawn_brace': ('ARMOR_ALL', 'add', -5)},
    }.items():
        data = read(name)
        for id_, (value, operation, amount) in mods.items():
            obj = index(data)[id_]
            if operation is None:
                obj['base_mods'][value] = [amount]
            else:
                for ench in obj['enchantments']:
                    for val in ench.get('values', []):
                        if val['value'] == value:
                            val[operation] = amount
        write(name, data)


def instant_pawns():
    data = read('effects/apostol_pawn_eocs.json'); ids = index(data)
    for line in ['COUNT', 'WYALD', 'ROSINE', 'GRUNBELD']:
        prefix = 'EOC_BERSERK_APOSTOL_' + line + '_PAWN_'
        complete = []
        for suffix in ['SEED', 'SENSES', 'FORM', 'POWER', 'PAWN']:
            trait = f'BERSERK_{line}_PAWN_{suffix}'
            complete.append({'if': {'not': {'u_has_trait': trait}},
                             'then': {'u_add_trait': trait}})
        complete += [math('u_berserk_apostol_growth_step = 3'),
                     math('u_berserk_apostol_stage = 3'),
                     math('u_berserk_apostol_growth_running = 0')]
        complete_id = prefix + 'COMPLETE_NOW'
        upsert(data, eoc(complete_id, complete, both(test(prefix + 'LINE'),
            {'not': test('EOC_BERSERK_APOSTOL_PAWN_COMPLETE')})))
        begin = ids[prefix + 'BEGIN']
        begin['effect'] = [
            {'u_add_trait': f'BERSERK_{line}_PAWN_LOYALTY'},
            math("u_berserk_apostol_started_at = time('now')"),
            {'run_eocs': complete_id}]
        # Old partially grown servants finish once without renewing an oath,
        # favor duration, master health, rewards or the initiation timestamp.
        ids[prefix + 'GROW']['effect'] = {'run_eocs': complete_id}
        ids[prefix + 'GROW']['condition'] = both(test(prefix + 'LINE'),
            {'not': test('EOC_BERSERK_APOSTOL_PAWN_COMPLETE')})
        query = ids[prefix + 'ACCEPT']['effect']['if']
        query['u_query'] = text(
            'Accept the pact? Your body will change at once and forever. You will owe service to the one who changes you.',
            'Принять договор? Ваше тело изменится сразу и навсегда. Вы обязуетесь служить тому, кто вас изменит.')
    write('effects/apostol_pawn_eocs.json', data)


def night():
    # Native 0.I time_until supports sunrise/sunset. One shared solar boundary
    # prevents the refuge report and the Brand from disagreeing about dawn.
    day = 'EOC_BERSERK_SOLAR_DAY'
    controller = [eoc(day, [], math("time_until('sunset') < time_until('sunrise')")),
        eoc('EOC_BERSERK_BRAND_NEW_NIGHT', [
            math('u_berserk_brand_night_night_spawned = 0'),
            math('u_berserk_brand_night_window_active = 1')],
            math('u_berserk_brand_night_window_active != 1')),
        eoc('EOC_BERSERK_BRAND_DAY_RESET', [
            math('u_berserk_brand_night_window_active = 0')],
            both('u_is_avatar', test(day), math('u_berserk_brand_night_window_active == 1')),
            eoc_type='RECURRING', recurrence='1 minute', **{'global': True})]
    write('effects/brand_night_budget_33.json', controller)
    for name in ['effects/eclipse_brand_eocs.json', 'effects/refuge_eocs.json']:
        data = read(name)
        def replace(value):
            if value == 'is_day':
                return test(day)
            if isinstance(value, list):
                return [replace(x) for x in value]
            if isinstance(value, dict):
                return {k: replace(v) for k, v in value.items()}
            return value
        data = replace(data)
        if 'brand' in name:
            ids = index(data)
            hunt = ids['EOC_BERSERK_BRAND_NIGHT_HUNT']
            hunt['effect'] = [x for x in hunt['effect'] if x.get('run_eocs') != 'EOC_BERSERK_BRAND_NEW_NIGHT']
            hunt['effect'].insert(0, {'run_eocs': 'EOC_BERSERK_BRAND_NEW_NIGHT'})
            for node in walk(hunt['effect']):
                if node.get('math') == ["u_berserk_brand_night_next_attempt = time('now') + 3600"]:
                    node['math'] = ["u_berserk_brand_night_next_attempt = time('now') + 7200"]
            spawn = ids['EOC_BERSERK_BRAND_NIGHT_HUNT_SPAWN']
            for node in walk(spawn):
                if 'math' in node and node['math'][0].startswith('u_berserk_brand_night_requested ='):
                    node['math'] = ['u_berserk_brand_night_requested = min(2, max(0, 6 - berserk_era_nearby_count), max(0, 6 - u_berserk_brand_night_night_spawned))']
                if isinstance(node.get('then'), list):
                    calls = [x for x in node['then'] if x.get('run_eocs') == 'EOC_BERSERK_BRAND_NIGHT_SPAWN_ONE']
                    if len(calls) == 3:
                        node['then'].remove(calls[-1])
            spawn['//'] = 'At most two attempts per two hours, six successful new spawns per night, six nearby demons. Count successful spawns only; leave existing creatures alive.'
            one = ids['EOC_BERSERK_BRAND_NIGHT_SPAWN_ONE']
            one['condition']['and'][1] = math('berserk_era_nearby_count < 6')
            for node in walk(one['effect']):
                if node.get('id') == 'EOC_BERSERK_BRAND_NIGHT_ONE_ARRIVED':
                    if math('u_berserk_brand_night_night_spawned += 1') not in node['effect']:
                        node['effect'].append(math('u_berserk_brand_night_night_spawned += 1'))
        else:
            for node in walk(data):
                if str(node.get('u_message', '')).startswith('Dawn reaches the refuge.'):
                    node['u_message'] = text('Dawn reaches the refuge. You have survived the night.',
                                             'Рассвет добрался до пристанища. Вы пережили ночь.')
        write(name, data)


def descriptions():
    # Player-facing ability descriptions retain useful numbers, not internal
    # stages, old toggles, development labels or narrator-spoiled pawn rankings.
    desc = {
        'BERSERK_VOID_STEP': ('Step to a visible free place within 8 tiles. Costs 1000 stamina; recovers in 20 seconds.', 'Шаг в видимое свободное место в пределах 8 клеток. Расход: 1000 выносливости; восстановление — 20 секунд.'),
        'BERSERK_VOID_WARD': ('Bend space around the next blow, reducing damage by 70% for up to 4 seconds. Costs 1400 stamina; recovers in 45 seconds.', 'Искривление пространства ослабляет следующий удар на 70% в течение 4 секунд. Расход: 1400 выносливости; восстановление — 45 секунд.'),
        'BERSERK_SLAN_WHIP': ('Strike with a tendril for 48 cutting damage within 5 tiles. Costs 800 stamina; recovers in 15 seconds.', 'Удар отростком: 48 режущего урона в пределах 5 клеток. Расход: 800 выносливости; восстановление — 15 секунд.'),
        'BERSERK_SLAN_MEND': ('Mend up to 12 HP on each major body part. Costs 1200 stamina, 60 kcal and 6 seconds; recovers in 10 minutes. Lost organs do not regrow.', 'Восстанавливает до 12 ОЗ каждой основной части тела. Расход: 1200 выносливости, 60 ккал и 6 секунд; восстановление — 10 минут. Утраченные органы не отрастают.'),
        'BERSERK_UBIK_IMAGE': ('Create a likeness within 7 tiles for 20 seconds. Costs 800 stamina; recovers in 20 seconds.', 'Создаёт подобие в пределах 7 клеток на 20 секунд. Расход: 800 выносливости; восстановление — 20 секунд.'),
        'BERSERK_UBIK_CONFUSE': ('Stun living minds around a point within 7 tiles for 4 seconds. Machines, undead, slimes and insects are unaffected. Costs 1100 stamina; recovers in 25 seconds.', 'Оглушает живой разум вокруг точки в пределах 7 клеток на 4 секунды. Не действует на машины, нежить, слизней и насекомых. Расход: 1100 выносливости; восстановление — 25 секунд.'),
        'BERSERK_UBIK_VEIL': ('Vanish from ordinary sight for 8 seconds. Scent and sound remain. Costs 1500 stamina; recovers in 45 seconds.', 'Скрывает от обычного зрения на 8 секунд. Запах и звуки остаются. Расход: 1500 выносливости; восстановление — 45 секунд.'),
        'BERSERK_CONRAD_STRIKE': ('Deal 40 acid damage to an enemy within 2 tiles. Costs 700 stamina; recovers in 12 seconds.', 'Наносит врагу в пределах 2 клеток 40 едкого урона. Расход: 700 выносливости; восстановление — 12 секунд.'),
        'BERSERK_CONRAD_CLOUD': ('Deal 24 acid damage in an area within 6 tiles and leave toxic fumes. Allies can be harmed. Costs 1500 stamina and 2 seconds; recovers in 40 seconds.', 'Наносит 24 едкого урона в области в пределах 6 клеток и оставляет ядовитую взвесь. Опасно для союзников. Расход: 1500 выносливости и 2 секунды; восстановление — 40 секунд.'),
        'BERSERK_FEMTO_PULSE': ('Strike for 35 bash damage within 7 tiles, then push the enemy back up to 5 tiles. Costs 1600 stamina; recovers in 25 seconds.', 'Наносит 35 дробящего урона в пределах 7 клеток и отбрасывает врага до 5 клеток. Расход: 1600 выносливости; восстановление — 25 секунд.'),
        'BERSERK_FEMTO_DASH': ('Rush to a visible free place within 6 tiles. Costs 1200 stamina; recovers in 15 seconds. Your dodge briefly worsens afterward.', 'Бросок в видимое свободное место в пределах 6 клеток. Расход: 1200 выносливости; восстановление — 15 секунд. После броска уклонение ненадолго ухудшается.'),
        'BERSERK_FEMTO_SUPPRESS': ('Crush an area within 7 tiles for 20 bash damage and slow enemies by 40 for 6 seconds. Costs 1800 stamina and 2 seconds; recovers in 35 seconds.', 'Наносит в области в пределах 7 клеток 20 дробящего урона и снижает скорость врагов на 40 на 6 секунд. Расход: 1800 выносливости и 2 секунды; восстановление — 35 секунд.'),
        'BERSERK_COUNT_FLESH_STRIKE': ('A tendril strikes within 3 tiles for 40 bash damage. Costs 900 stamina and 2 seconds; recovers in 16 seconds. Briefly leaves you exposed.', 'Отросток наносит 40 дробящего урона в пределах 3 клеток. Расход: 900 выносливости и 2 секунды; восстановление — 16 секунд. После удара вы ненадолго уязвимее.'),
        'BERSERK_COUNT_FLESH_MEND': ('Mend up to 7 HP on each major body part. Costs 1000 stamina, 80 kcal and 3 seconds; recovers in 2 minutes. Lost organs do not regrow.', 'Восстанавливает до 7 ОЗ каждой основной части тела. Расход: 1000 выносливости, 80 ккал и 3 секунды; восстановление — 2 минуты. Утраченные органы не отрастают.'),
        'BERSERK_WYALD_FLESH_DASH': ('Rush up to 6 tiles along an open path. Costs 1200 stamina; recovers in 18 seconds.', 'Рывок до 6 клеток по свободному пути. Расход: 1200 выносливости; восстановление — 18 секунд.'),
        'BERSERK_WYALD_FLESH_GRIP': ('Crush an adjacent enemy for 28 bash damage and slow it by 40 for 6 seconds. Costs 900 stamina; recovers in 18 seconds.', 'Наносит соседнему врагу 28 дробящего урона и снижает его скорость на 40 на 6 секунд. Расход: 900 выносливости; восстановление — 18 секунд.'),
        'BERSERK_ROSINE_FLESH_DIVE': ('Dive up to 7 tiles and cut enemies around the landing for 36 damage. Costs 1500 stamina; recovers in 20 seconds. Heavy torso gear hinders the dive.', 'Пикирование до 7 клеток наносит врагам у места приземления 36 режущего урона. Расход: 1500 выносливости; восстановление — 20 секунд. Тяжёлое снаряжение на торсе мешает движению.'),
        'BERSERK_ROSINE_FLESH_FLUTTER': ('Gain +4 dodge for 5 seconds. Costs 700 stamina; recovers in 20 seconds. Heavy torso gear hinders wingbeats.', 'Даёт +4 к уклонению на 5 секунд. Расход: 700 выносливости; восстановление — 20 секунд. Тяжёлое снаряжение на торсе мешает взмахам.'),
        'BERSERK_GRUNBELD_FLESH_BREATH': ('Breathe fire up to 7 tiles for 52 heat damage. Flames can harm allies and belongings. Costs 1800 stamina, 60 kcal and 2 seconds; recovers in 45 seconds. Briefly overheats your body.', 'Огненное дыхание до 7 клеток наносит 52 теплового урона. Пламя опасно для союзников и вещей. Расход: 1800 выносливости, 60 ккал и 2 секунды; восстановление — 45 секунд. Ненадолго перегревает тело.'),
        'BERSERK_GRUNBELD_FLESH_BRACE': ('Brace your shell for 7 extra protection for 8 seconds, losing 20 speed. Costs 1100 stamina; recovers in 30 seconds.', 'Укрепляет панцирь: +7 защиты на 8 секунд, скорость снижена на 20. Расход: 1100 выносливости; восстановление — 30 секунд.'),
    }
    for p in sorted((MOD / 'mutations').glob('apostol_*.json')):
        data = json.loads(p.read_text())
        if not isinstance(data, list):
            continue
        for obj in data:
            id_ = obj.get('id', '')
            if id_ in desc:
                obj['description'] = text(*desc[id_])
            elif id_.endswith('_APOSTLE'):
                obj['description'] = text('Your body has reached its final shape. The power you accepted is part of you.', 'Тело обрело окончательный облик. Принятая сила стала частью вас.')
            elif id_.endswith('_PAWN_POWER'):
                obj['description'] = text('Your master strengthens this ability in return for service. Your changed body remains even without their support.', 'Хозяин укрепляет эту способность в обмен на службу. Изменённое тело остаётся с вами и без его поддержки.')
            elif id_.endswith('_PAWN_PAWN'):
                obj['description'] = text('Your body bears the lasting mark of the pact.', 'Тело несёт неизгладимый след договора.')
            elif id_.endswith(('_PAWN_SEED', '_PAWN_SENSES')):
                if 'COUNT' in id_:
                    obj['description'] = text('Heavy, pliant flesh weighs down your movements.', 'Тяжёлая податливая плоть замедляет движения.')
                elif 'WYALD' in id_:
                    obj['description'] = text('Your limbs ache with restless strength. Fine work becomes harder.', 'Конечности полны беспокойной силы. Точная работа даётся труднее.')
                elif 'ROSINE' in id_:
                    obj['description'] = text('Speech breaks into awkward clicks. Your delicate body makes patient work difficult.', 'Речь срывается в неловкие щелчки. Хрупкое тело затрудняет кропотливую работу.')
                else:
                    obj['description'] = text('The shell weighs upon your body. Every movement takes effort.', 'Оболочка отягощает тело. Каждое движение требует усилия.')
        write(str(p.relative_to(MOD)), data)
    messages = {
        'Your senses sharpen, while the gift’s weakness settles into your body.': ('Your senses shift. Familiar things feel different.', 'Чувства меняются. Привычные вещи ощущаются иначе.'),
        'Your body has changed permanently. Its new strengths and weaknesses cannot be switched off.': ('Your flesh settles into an unfamiliar shape.', 'Плоть обретает непривычный облик.'),
        'The gift answers a new impulse. Its first fighting abilities are now yours.': ('A new strength answers your will.', 'Новая сила откликается вашей воле.'),
        'The transformation settles. It will grow no further; its strength and its price remain yours.': ('The changes subside. This is your body now.', 'Изменения затихают. Теперь это ваше тело.'),
        'Your body must finish changing. You need strength and time before calling on this gift again.': ('You cannot call on this strength yet.', 'Вы пока не можете призвать эту силу.'),
        'This ability needs your fighting shape, enough strength and time to recover. Winged movements also need room for your equipment.': ('Your body is not ready for this movement.', 'Тело пока не готово к этому движению.'),
        'The impulse does not answer. Let your body finish changing, recover your stamina and honor the service owed to a living master.': ('The strength you call upon remains silent.', 'Призываемая сила молчит.'),
        'The pact takes root beneath your skin. Its price and your first service are recorded in the road journal.': ('The pact reshapes your flesh.', 'Договор преображает вашу плоть.'),
        'The bond falls silent. Your master is dead; your body remains a limited servant’s shape. No greater power takes its place.': ('The bond falls silent. Your changed flesh remains.', 'Связь умолкает. Изменённая плоть остаётся с вами.'),
        'The borrowed flesh has settled. This transformation is complete; its strength and its weakness remain.': ('The changes subside. This is your body now.', 'Изменения затихают. Теперь это ваше тело.'),
        'Your flesh has changed into a stronger, unfamiliar body. It will never return to human shape.': ('Your flesh settles into an unfamiliar shape.', 'Плоть обретает непривычный облик.'),
        'Absorb the Count’s flesh? You will slowly become a heavy, pliant apostle. Your movement will remain slower, throughout the transformation. This is permanent: no other main line can take root afterward. You cannot undo the choice by closing a breach.': ('Absorb the Count’s flesh? It will begin changing your body forever.', 'Поглотить плоть Графа? Она начнёт навсегда менять ваше тело.'),
        'Absorb Wyald’s flesh? You will slowly become a beastlike apostle. Your stamina will recover more slowly; your altered hands will hinder precise work. This is permanent: no other main line can take root afterward.': ('Absorb Wyald’s flesh? It will begin changing your body forever.', 'Поглотить плоть Уайлда? Она начнёт навсегда менять ваше тело.'),
        'Absorb Rosine’s flesh? You will slowly become a winged insectlike apostle. Your flesh will take more physical damage, throughout the transformation. Heavy equipment restricts your winged movements. This is permanent: no other main line can take root afterward.': ('Absorb Rosine’s flesh? It will begin changing your body forever.', 'Поглотить плоть Розины? Она начнёт навсегда менять ваше тело.'),
        'Absorb Grunbeld’s flesh? You will slowly grow an armored, fiery shape. Hunger and slow stamina recovery remain throughout the transformation; breathing fire overheats your body. This is permanent: no other main line can take root afterward.': ('Absorb Grunbeld’s flesh? It will begin changing your body forever.', 'Поглотить плоть Грюнбельда? Она начнёт навсегда менять ваше тело.'),
    }
    for p in sorted((MOD / 'effects').glob('apostol_*.json')):
        data = json.loads(p.read_text())
        for node in walk(data):
            for key in ['u_message', 'u_query']:
                if node.get(key) in messages:
                    node[key] = text(*messages[node[key]])
        write(str(p.relative_to(MOD)), data)
    early = read('items/true_guts_early_sword.json')
    early[0]['looks_like'] = 'mc_zweihander'
    write('items/true_guts_early_sword.json', early)
    for name in ['effects/apostol_pawn_power_types.json']:
        data = read(name)
        for obj in data:
            obj['desc'] = [text('Your altered flesh braces against danger.', 'Изменённая плоть напрягается перед опасностью.')]
        write(name, data)


def save_translations():
    # Parse only msgid entries; GNU msgfmt checks and compiles the complete PO.
    import ast
    def known_ids(path):
        result = set(); current = None
        for row in path.read_text().splitlines():
            if row.startswith('msgid '):
                if current is not None: result.add(current)
                current = ast.literal_eval(row[6:])
            elif row.startswith('"') and current is not None:
                current += ast.literal_eval(row)
            elif row.startswith('msgstr') or row.startswith('msgid_plural'):
                if current is not None: result.add(current)
                current = None
        if current is not None: result.add(current)
        return result
    for file in ['ru.po', 'Berserk.pot']:
        path = MOD / 'lang/po' / file
        known = known_ids(path)
        with path.open('a') as stream:
            for en, ru in TRANSLATIONS.items():
                if en not in known:
                    stream.write('\n#. Restored 3.3 gameplay fixes\nmsgid ' + json.dumps(en, ensure_ascii=False) + '\nmsgstr ' + json.dumps(ru if file == 'ru.po' else '', ensure_ascii=False) + '\n')
    subprocess.run(['msgfmt', '--check', '-o', str(MOD / 'lang/mo/ru/LC_MESSAGES/Berserk.mo'), str(MOD / 'lang/po/ru.po')], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', choices=['gameplay'], default='gameplay')
    parser.parse_args()
    abilities(); instant_pawns(); night(); descriptions(); save_translations()
    print('Recovered 3.3 abilities, instant servants, night budget and concise messages.')


if __name__ == '__main__':
    main()
