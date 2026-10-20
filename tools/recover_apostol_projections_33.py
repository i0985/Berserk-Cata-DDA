#!/usr/bin/env python3
"""Restore seven independent rare Nether projections, without original flags."""
from recover_apostol_33 import read, write, index, walk, upsert, text, save_translations

LINES = ['count', 'wyald', 'rosine', 'grunbeld', 'slan', 'ubik', 'conrad']
IDS = ['mon_berserk_projection_' + x for x in LINES]


def spell(name, title, description, damage, damage_type, range_, **extra):
    return dict(type='SPELL', id='berserk_projection_' + name,
        name=title, description=description, effect='attack', shape='blast',
        valid_targets=['hostile'], min_range=range_, max_range=range_,
        min_aoe=0, max_aoe=0, min_damage=damage, max_damage=damage,
        damage_type=damage_type, max_level=0, base_energy_cost=0,
        energy_source='NONE', base_casting_time=100,
        message=text('The apparition gathers its strength.', 'Призрачный образ собирает силы.'),
        flags=['SILENT', 'NO_EXPLOSION_SFX'], **extra)


def main():
    attacks = [
        spell('count_tendril', text('Spectral tendril', 'Призрачный отросток'),
              text('A heavy tendril lashes outward.', 'Тяжёлый отросток хлещет вперёд.'), 16, 'bash', 2),
        spell('grunbeld_heat', text('Cinder gust', 'Пепельный жар'),
              text('A short cone of heat spills from the apparition.', 'Из призрачного образа вырывается короткий поток жара.'),
              18, 'heat', 3),
        spell('slan_cord', text('Crimson cord', 'Багровый жгут'),
              text('A cord of flesh lashes a distant target.', 'Жгут плоти хлещет далёкую цель.'), 16, 'cut', 3),
        spell('ubik_haze', text('Uncertain footing', 'Обманчивый шаг'),
              text('Conflicting sensations disturb movement.', 'Противоречивые ощущения мешают движению.'),
              0, 'bash', 4, effect_str='berserk_projection_ubik_haze',
              min_duration=300, max_duration=300),
        spell('conrad_cloud', text('Bitter exhalation', 'Едкий выдох'),
              text('A bitter cloud eats into nearby flesh.', 'Едкое облако разъедает плоть.'),
              12, 'acid', 3, field_id='fd_toxic_gas', min_field_intensity=1,
              max_field_intensity=1, field_chance=1),
    ]
    index(attacks)['berserk_projection_grunbeld_heat'].update(shape='cone', min_aoe=30, max_aoe=30)
    index(attacks)['berserk_projection_conrad_cloud'].update(min_aoe=1, max_aoe=1)
    write('spells/apostle_projections.json', attacks)
    write('effects/apostle_projection_effects.json', [dict(type='effect_type',
        id='berserk_projection_ubik_haze', name=[text('Uncertain footing', 'Обманчивый шаг')],
        desc=[text('Your senses disagree about the ground beneath you.', 'Чувства обманывают вас: земля под ногами кажется неустойчивой.')],
        max_intensity=1, dur_add_perc=0, base_mods={'speed_mod': [-12]})])
    records = [
        ('count', 'the Count', 'Графа', 210, 80, 10, 'bash', 3, 5, 'C',
         'A swollen likeness fills the passage. Its heavy flesh wavers at the edges.',
         'Раздувшееся подобие заполняет проход. Края тяжёлой плоти зыбко колышутся.'),
        ('wyald', 'Wyald', 'Уайлда', 190, 100, 12, 'cut', 2, 4, 'W',
         'A grinning, beastlike likeness moves in sudden bounds.',
         'Ухмыляющееся звероподобное подобие движется резкими прыжками.'),
        ('rosine', 'Rosine', 'Розины', 140, 115, 8, 'cut', 1, 3, 'R',
         'A delicate winged apparition darts above the ground.',
         'Хрупкий крылатый образ стремительно скользит над землёй.'),
        ('grunbeld', 'Grunbeld', 'Грюнбельда', 240, 80, 12, 'bash', 6, 10, 'G',
         'A heavy armored likeness radiates a brief, wavering heat.',
         'Тяжёлое закованное подобие излучает колеблющийся жар.'),
        ('slan', 'Slan', 'Слан', 170, 100, 8, 'cut', 2, 4, 'S',
         'A crimson likeness of living flesh reaches through a thin place in the world.',
         'Багровое подобие живой плоти тянется сквозь истончившуюся грань мира.'),
        ('ubik', 'Ubik', 'Убика', 130, 105, 6, 'bash', 1, 3, 'U',
         'A small hovering image blurs whenever your gaze shifts.',
         'Небольшой парящий образ расплывается, стоит перевести взгляд.'),
        ('conrad', 'Conrad', 'Конрада', 200, 75, 10, 'bash', 4, 4, 'K',
         'A squat likeness gathers amid a bitter, drifting haze.',
         'Приземистое подобие проступает среди едкой плывущей взвеси.'),
    ]
    data = read('monsters/apostle_projections.json')
    spells = {'count':'count_tendril', 'grunbeld':'grunbeld_heat', 'slan':'slan_cord',
              'ubik':'ubik_haze', 'conrad':'conrad_cloud'}
    messages = {
        'count': ('The apparition lashes out with a heavy tendril!', 'Призрачный образ хлещет тяжёлым отростком!'),
        'grunbeld': ('Heat spills from the apparition!', 'Из призрачного образа вырывается жар!'),
        'slan': ('A crimson cord lashes outward!', 'Багровый жгут хлещет вперёд!'),
        'ubik': ('The hovering image confuses your senses!', 'Парящий образ обманывает ваши чувства!'),
        'conrad': ('The apparition exhales a bitter cloud!', 'Призрачный образ выдыхает едкое облако!')}
    for line, title, ru, hp, speed, damage, dtype, bash, cut, symbol, en_desc, ru_desc in records:
        monster = dict(type='MONSTER', id='mon_berserk_projection_' + line,
            name={'str': text('Projection of ' + title, 'Проекция ' + ru),
                  'str_pl': text('Projections of ' + title, 'Проекции ' + ru)},
            description=text(en_desc, ru_desc), looks_like='',
            default_faction='berserk_eclipse_demons', bodytype='humanoid',
            species=['NETHER'], volume='90000 ml', weight='110000 g',
            material=['flesh'], hp=hp, speed=speed, regenerates=0,
            symbol=symbol, color='magenta', aggression=100, morale=100,
            melee_skill=4, melee_dice=1, melee_dice_sides=4,
            melee_damage=[{'damage_type': dtype, 'amount': damage}], dodge=1,
            armor={'bash':bash, 'cut':cut}, vision_day=18, vision_night=20,
            harvest='exempt', flags=['SEES', 'HEARS'],
            death_drops='berserk_projection_behelit_drops',
            death_function={'corpse_type':'NO_CORPSE', 'message':'The %s unravels.',
                            'eoc':'EOC_BERSERK_BEHELIT_BOSS_DIES'})
        if line in spells:
            monster['special_attacks'] = [dict(type='monster_attack', attack_type='spell',
                id='berserk_projection_' + line + '_attack', cooldown=18,
                spell_data={'id':'berserk_projection_' + spells[line], 'min_level':0},
                monster_message=text(*messages[line]))]
        else:
            monster['special_attacks'] = [dict(type='leap', id='berserk_projection_' + line + '_bound',
                cooldown=14, max_range=3 if line == 'rosine' else 2,
                min_range=1, move_cost=150, allow_no_target=False)]
        if line in ['rosine', 'ubik']:
            monster['flags'].append('FLIES')
        upsert(data, monster)
    write('monsters/apostle_projections.json', data)
    groups = read('monstergroups/monster_groups.json')
    group = index(groups)['GROUP_NETHER']
    group['monsters'] = [x for x in group['monsters'] if not x['monster'].startswith('mon_berserk_projection_')]
    for line, weight in [('zodd',2),('griffith',1),('void',1),('count',3),('wyald',2),
                         ('rosine',2),('grunbeld',2),('slan',1),('ubik',1),('conrad',1)]:
        group['monsters'].append(dict(monster='mon_berserk_projection_' + line,
                                      weight=weight, cost_multiplier=1))
    write('monstergroups/monster_groups.json', groups)
    for name in ['effects/eclipse_brand_eocs.json', 'effects/eclipse_era_eocs.json',
                 'effects/apostle_relic_eocs.json']:
        data = read(name)
        for node in walk(data):
            if 'mtype_ids' in node and 'mon_berserk_projection_void' in node['mtype_ids']:
                node['mtype_ids'] += [x for x in IDS if x not in node['mtype_ids']]
            if 'math' in node and isinstance(node['math'][0], str):
                expression = node['math'][0]
                if 'u_monsters_nearby(' in expression and 'mon_berserk_projection_void' in expression:
                    missing = [x for x in IDS if "'" + x + "'" not in expression]
                    if missing:
                        node['math'][0] = expression.replace("'radius':", ', '.join(repr(x) for x in missing) + ", 'radius':")
        write(name, data)
    save_translations()
    print('Restored 10 projections with unchanged combined Nether weight 16.')


if __name__ == '__main__': main()
