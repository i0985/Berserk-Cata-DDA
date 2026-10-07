#!/usr/bin/env python3
"""Build three rare, finite roadside stories, with state on each map object."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/Berserk'
RU = {}
def t(en, ru):
    RU[en] = ru
    return en
def save(path, rows):
    (MOD / path).write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
def run(id): return {'run_eocs': id}
def m(expr): return {'math': [expr]}
def response(en, ru, target='TALK_DONE', effect=None, condition=None):
    out = {'text': t(en, ru), 'topic': target}
    if effect: out['effect'] = run(effect)
    if condition: out['condition'] = condition
    return out

effects = []
furniture = []
topics = []
groups = []
items = []
om = []
maps = []
stories = [
    ('caravan', 'plundered wagon stop', 'разграбленный обоз', 15,
     'A broken wagon has been pulled off an old track. Straps hold one dry bundle beneath the iron-bound box.',
     'Сломанную телегу стащили со старой тропы. Под окованным коробом ремни удерживают один сухой свёрток.',
     '*Most of the wagon has been stripped. One dry bundle remains wedged under the box. Lifting it gently preserves the provisions; taking the iron fittings requires breaking the box and its contents.',
     '*Почти всё с телеги унесли. Один сухой свёрток зажат под коробом. Если осторожно поднять короб, припасы удастся сохранить; чтобы снять железные крепления, придётся разбить его вместе с содержимым.'),
    ('scout', 'scout trail', 'след разведчика', 12,
     'A leather pack hangs from a root above a shallow gully. A small cloth bundle can be reached from the path.',
     'Над неглубоким оврагом на корне висит кожаный ранец. До маленького свёртка можно дотянуться с тропы.',
     '*Boot prints end beside a slippery slope. The scout tied his pack to a root before descending, but never returned. A rope would let you recover the whole pack; without it, you can reach only the outer bundle.',
     '*Следы сапог заканчиваются у скользкого склона. Перед спуском разведчик привязал ранец к корню, но не вернулся. С верёвкой можно достать весь ранец; без неё — только внешний свёрток.'),
    ('camp', 'abandoned waycamp', 'оставленный дорожный лагерь', 10,
     'A folded fur blanket and a small water skin lie beneath a low windbreak beside cold ashes.',
     'Под низкой защитой от ветра рядом с остывшим кострищем лежат сложенное меховое одеяло и небольшой бурдюк.',
     '*The travelers left a dry windbreak and their last blanket. You can make a usable bed here or carry the blanket onward. A water skin and a scrap of their last message remain beside it. Neither branches nor bedding can silence the Brand.',
     '*Путники оставили сухую защиту от ветра и последнее одеяло. Можно устроить здесь постель или забрать одеяло в дорогу. Рядом остались бурдюк и клочок последней записки. Ни ветви, ни подстилка не заставят Клеймо замолчать.')
]

records = {
 'caravan': (
    'wagon tally', 'запись с обоза',
    'A list of grain, straps and iron fittings. The last line was written after the load had been counted.',
    'Список зерна, ремней и железных креплений. Последнюю строку дописали после пересчёта груза.',
    'We lost the wheel before sunset. The others carried the grain north, leaving the iron here. I heard something following the wheels, but the track behind us was empty. If we return, we will look beneath the bound box first.',
    'До заката потеряли колесо. Остальные понесли зерно на север, железо оставили здесь. Я слышал, как что-то идёт вслед за колёсами, но позади никого не было. Если вернёмся, сначала посмотрим под окованный короб.'),
 'scout': (
    "scout's field scrap", 'клочок записей разведчика',
    'A folded scrap with charcoal marks recording a forest crossing.',
    'Сложенный клочок с угольными пометками о переходе через лес.',
    'The open clearing is watched. I saw the trees move while the air was still. I tied the pack above the washout and took the lower path to see whether the other bank was clear. If I fail to return, keep to stone and leave room to turn back.',
    'За открытой поляной следят. Я видел, как деревья двигались в безветрие. Привязал ранец над промоиной и пошёл нижней тропой — проверить другой берег. Если не вернусь, держитесь камня и оставляйте место, чтобы повернуть назад.'),
 'camp': (
    'message from the waycamp', 'записка дорожного лагеря',
    'The corner of a letter left beneath a folded blanket.',
    'Уголок письма, оставленный под сложенным одеялом.',
    'We leave before the next dusk. The children slept beneath the branches, and the water is still clean. Whoever follows us may need the blanket more than we do. There were cries beyond the track last night. We did not go to look.',
    'Уходим до следующего заката. Дети спали под ветвями, вода ещё чистая. Тем, кто пойдёт следом, одеяло может понадобиться больше, чем нам. Ночью за тропой кричали. Мы не пошли смотреть.')
}
for key, (en, ru, desc, rudesc, note, runote) in records.items():
    id = 'berserk_road_' + key + '_note'
    read = 'EOC_BERSERK_ROAD_READ_' + key.upper()
    items.append({'type': 'ITEM', 'subtypes': ['TOOL'], 'id': id,
        'name': {'str': t(en, ru)}, 'description': t(desc, rudesc),
        'material': ['paper'], 'category': 'tools', 'weight': '5 g', 'volume': '10 ml',
        'symbol': '?', 'color': 'brown', 'charges_per_use': 0,
        'flags': ['ALLOWS_REMOTE_USE'],
        'use_action': {'type': 'effect_on_conditions', 'need_wielding': False,
                       'effect_on_conditions': [read]}})
    effects.append({'type': 'effect_on_condition', 'id': read,
                    'effect': {'u_message': t(note, runote), 'popup': True, 'type': 'info'}})

def item(id, count=1, **extra): return {'item': id, 'prob': 100, 'count': count, **extra}
def group(id): return {'group': id, 'prob': 100}
def note(key): return item('berserk_road_' + key + '_note')
rewards = {
 'caravan_provisions': [group('berserk_location_medieval_food'), group('berserk_location_cloth_dressings'), note('caravan')],
 'caravan_iron': [{'item': 'steel_lump', 'prob': 100, 'charges': 2}, item('leather', 2), note('caravan')],
 'scout_pack': [item('backpack_leather', damage=2), item('flint_steel'), item('bandages_makeshift', 2), note('scout')],
 'scout_bundle': [item('needle_bone'), item('scrap_cotton', 2), note('scout')],
 'camp_bed': [group('berserk_location_medieval_water'), note('camp')],
 'camp_blanket': [item('fur_blanket', damage=1), group('berserk_location_medieval_water'), note('camp')]
}
for id, entries in rewards.items():
    groups.append({'type': 'item_group', 'id': 'berserk_road_' + id, 'subtype': 'collection', 'entries': entries})

effects.append({'type': 'effect_on_condition', 'id': 'EOC_BERSERK_ROAD_USED',
    'effect': {'u_message': t('Only the traces of your earlier visit remain.', 'Остались только следы вашего прежнего посещения.'), 'type': 'info'}})

for key, en, ru, rarity, desc, rudesc, text, rutext in stories:
    full = 'f_berserk_road_' + key
    enter = 'EOC_BERSERK_ROAD_ENTER_' + key.upper()
    topic = 'TALK_BERSERK_ROAD_' + key.upper()
    condition = {'and': [m("distance('u', u_berserk_road_story_pos) <= 1"),
        {'map_furniture_id': full, 'loc': {'u_val': 'berserk_road_story_pos'}}]}
    furniture.append({'type': 'furniture', 'id': full, 'name': t(en, ru),
        'description': t(desc, rudesc), 'symbol': '?', 'color': 'brown',
        'move_cost_mod': 0, 'required_str': -1, 'flags': ['TRANSPARENT'],
        'looks_like': 'f_crate_o' if key == 'caravan' else 'f_rubble',
        'examine_action': {'type': 'effect_on_condition', 'effect_on_conditions': [enter]}})
    effects.append({'type': 'effect_on_condition', 'id': enter,
        'condition': {'and': [m("distance('u', _pos) <= 1"), {'map_furniture_id': full, 'loc': {'context_val': 'pos'}}]},
        'effect': [
            {'copy_var': {'context_val': 'pos'}, 'target_var': {'u_val': 'berserk_road_story_pos'}},
            {'open_dialogue': {'topic': topic}}]})
    options = {
        'caravan': [
            ('provisions', 'Recover the dry provisions.', 'Достать сухие припасы.', '1 minute', None),
            ('iron', 'Break the box and salvage its iron fittings.', 'Разбить короб и снять железные крепления.', '3 minutes', None)],
        'scout': [
            ('pack', 'Use a rope to recover the pack. Keep the rope.', 'Достать ранец с помощью верёвки. Верёвка останется у вас.', '2 minutes',
             {'u_has_items': {'item': 'rope_6', 'count': 1}}),
            ('bundle', 'Take only the reachable bundle.', 'Взять только доступный свёрток.', '15 seconds', None)],
        'camp': [
            ('bed', 'Spread the blanket and prepare a bed here.', 'Разложить одеяло и устроить здесь постель.', '1 minute', None),
            ('blanket', 'Take the blanket for the road.', 'Взять одеяло в дорогу.', '15 seconds', None)]
    }[key]
    responses = []
    for outcome, label, rulabel, duration, requirement in options:
        result = full + '_' + outcome
        claim = 'EOC_BERSERK_ROAD_' + key.upper() + '_' + outcome.upper()
        transform = 'berserk_road_' + key + '_' + outcome
        result_names = {
            'provisions': ('opened wagon box', 'вскрытый короб обоза'),
            'iron': ('stripped wagon box', 'разобранный короб обоза'),
            'pack': ('bare root above the gully', 'голый корень над оврагом'),
            'bundle': ('pack with its outer bundle removed', 'ранец без внешнего свёртка'),
            'bed': ('prepared waycamp bed', 'устроенная дорожная постель'),
            'blanket': ('empty waycamp windbreak', 'пустая защита от ветра')}
        n, rn = result_names[outcome]
        result_row = {'type': 'furniture', 'id': result, 'copy-from': full,
            'name': t(n, rn), 'description': t('The belongings have been recovered or put to use. There is no fresh supply waiting here.',
                                              'Вещи уже разобраны или устроены для использования. Новых запасов здесь не осталось.'),
            'examine_action': {'type': 'effect_on_condition', 'effect_on_conditions': ['EOC_BERSERK_ROAD_USED']}}
        if outcome == 'bed':
            # A blanket on dry branches must not create a wooden bed's boards,
            # nails and sheets when dismantled. Recover only the same blanket.
            result_row.update({'looks_like':'f_straw_bed', 'comfort':2,
                'floor_bedding_warmth':300, 'move_cost_mod':1,
                'flags':['TRANSPARENT','FLAMMABLE_ASH','ORGANIC','CAN_SIT'],
                'deconstruct':{'items':[item('fur_blanket',damage=1)], 'furn_set':full+'_blanket'}})
        furniture.append(result_row)
        effects.append({'type': 'ter_furn_transform', 'id': transform,
            'furniture': [{'valid_furniture': [full], 'result': result}]})
        conditions = [condition]
        if requirement: conditions.append(requirement)
        effects.append({'type': 'effect_on_condition', 'id': claim, 'condition': {'and': conditions},
            'effect': [
                {'u_transform_radius': 0, 'ter_furn_transform': transform, 'target_var': {'u_val': 'berserk_road_story_pos'}},
                {'if': {'map_furniture_id': result, 'loc': {'u_val': 'berserk_road_story_pos'}}, 'then': [
                    {'map_spawn_item': 'berserk_road_' + key + '_' + outcome, 'use_item_group': True, 'loc': {'u_val': 'berserk_road_story_pos'}},
                    {'turn_cost': duration},
                    {'u_message': t('You finish sorting the belongings. The recovered pieces are beside you.',
                                    'Вы закончили разбирать вещи. Найденное лежит рядом.'), 'type': 'info', 'popup': False}]}]})
        responses.append(response(label, rulabel, effect=claim,
                                  condition={'and': conditions}))
    responses.append(response('Leave it for now.', 'Пока оставить всё как есть.'))
    topics.append({'type': 'talk_topic', 'id': topic, 'dynamic_line': t(text, rutext), 'responses': responses})

    omt = 'berserk_road_' + key
    om.append({'type': 'overmap_terrain', 'id': omt, 'name': t(en, ru), 'sym': '?', 'color': 'brown',
               'see_cost': 'high', 'travel_cost_type': 'forest', 'flags': ['NO_ROTATE']})
    om.append({'type': 'overmap_special', 'id': omt + '_special',
        'overmaps': [{'point': [0, 0, 0], 'overmap': omt}], 'locations': ['forest_edge'],
        'rotate': False, 'occurrences': [rarity, 100], 'flags': ['OVERMAP_UNIQUE']})
    # Local tracks cross the forest fringe; these do not rewrite existing roads.
    grid = [['.'] * 24 for _ in range(24)]
    for y in range(24):
        x = 9 if y < 7 else 10 if y < 15 else 11
        for dx in (0, 1, 2): grid[y][x + dx] = 'p'
    for x, y in [(1,2),(4,3),(20,2),(21,6),(2,10),(19,11),(1,18),(22,18),(3,22),(20,22)]: grid[y][x]='T'
    for x,y in [(3,6),(19,4),(2,14),(21,14),(6,20),(17,21)]:grid[y][x]='u'
    terrain={'.':'t_grass','p':'t_dirt','T':'t_tree','u':'t_underbrush','#':'t_rock','s':'t_dirt'}
    obj={'fill_ter':'t_grass','terrain':terrain,'rows':[], 'place_furniture':[]}
    if key=='caravan':
        # One wreck by the verge, a cold meal on the opposite side, and a clear bypass.
        for x,y in [(15,9),(16,9),(15,10)]: obj['place_furniture'].append({'furn':'f_rubble','x':x,'y':y})
        obj['place_furniture'] += [{'furn':full,'x':16,'y':10},{'furn':'f_crate_o','x':18,'y':9},{'furn':'f_firering','x':6,'y':12}]
        obj['place_item']=[{'item':'splinter','x':15,'y':11,'amount':3}]
    elif key=='scout':
        # A shallow stony washout, not a lethal pit or a full-size combat arena.
        for y in range(6,19):
            for x in range(17,21):grid[y][x]='s'
        for x,y in [(17,7),(19,9),(17,12),(20,15),(18,17)]:grid[y][x]='#'
        obj['place_furniture']=[{'furn':full,'x':16,'y':13}]
        obj['place_item']=[{'item':'scrap_cotton','x':14,'y':7,'amount':1}]
    else:
        # Low shelter under the trees, bedding choice and finite provisions.
        for x,y in [(16,8),(17,8),(18,8),(18,9)]:grid[y][x]='T'
        obj['place_furniture']=[{'furn':full,'x':17,'y':10},{'furn':'f_firering','x':15,'y':13},
            {'furn':'f_bench_wooden','x':16,'y':14}]
        obj['place_item']=[{'item':'stick','x':15,'y':12,'amount':2}]
    obj['rows']=[''.join(row) for row in grid]
    maps.append({'type':'mapgen','om_terrain':omt,'method':'json','object':obj})

save('effects/road_stories_eocs.json', effects)
save('furniture/road_stories.json', furniture)
save('dialogue/road_stories.json', topics)
save('itemgroups/road_stories.json', groups)
save('items/road_story_records.json', items)
save('overmap/road_stories.json', om)
save('mapgen/road_stories.json', maps)
(ROOT/'tools/road_stories_32_ru.json').write_text(json.dumps(RU,ensure_ascii=False,indent=2)+'\n')
print('Built three rare roadside stories with six finite outcomes and local map state.')
