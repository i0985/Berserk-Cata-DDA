#!/usr/bin/env python3
"""Owner playtest: late sites, death scope, rescue anatomy and clear next steps."""
import copy
import json

from recover_apostol_33 import ROOT, MOD, read, write, index, eoc, walk
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq
from recovery_33_translations import source

P = 'EOC_BERSERK_FIX24_'
STRINGS = {}; EOCS = []


def tr(en, ru):
    STRINGS[en] = ru
    return en


def run(id_, **kwargs):
    return {'run_eocs': id_, **kwargs}


def append_once(obj, value):
    old = obj.setdefault('effect', [])
    if not isinstance(old, list): old = obj['effect'] = [old]
    if value not in old: old.append(value)


def worldgen():
    # These sites have real story placement. Natural generation bypassed it.
    for name in ['apostle_count', 'wyald_rosine_hunts', 'grunbeld_hunt', 'first_hunt', 'local_breach']:
        rows = read('overmap/' + name + '.json')
        for row in rows:
            if row.get('type') == 'overmap_special':
                row['occurrences'] = [0, 0]
                row['//'] = 'Story placement after the Eclipse only. Existing sites and coordinates are retained.'
                row['locations'] = ['forest']
                for part in row.get('overmaps', []):
                    if part.get('point', [0, 0, 0])[2] == 0 and 'locations' in part:
                        part['locations'] = ['forest']
        write('overmap/' + name + '.json', rows)
    for filename, ids in [
        ('apostle_hunt_eocs',['COUNT_FIND']),
        ('wyald_rosine_hunt_eocs',['WYALD_FIND','ROSINE_FIND']),
        ('local_breach_eocs',['BREACH_FIND'])]:
        rows=read('effects/'+filename+'.json')
        for obj in rows:
            if obj['id'] in ['EOC_BERSERK_'+id_ for id_ in ids]:
                era=eq('berserk_eclipse_era')
                if obj.get('condition')!=era:
                    obj['condition']=both(era,obj['condition']) if 'condition' in obj else era
        write('effects/'+filename+'.json',rows)
    rows = read('overmap/behelit_sites.json')
    for row in rows:
        if row.get('type') == 'overmap_special':
            row['occurrences'] = [1, 100]
            row['//'] = ('OVERMAP_UNIQUE occurrence chance is adaptive in native 0.I. '
                         'Base ratio reduced from 10/100 to 1/100. Existing sites are not removed.')
    write('overmap/behelit_sites.json', rows)


def death_scope():
    rows = read('effects/apostol_flesh_eocs.json'); by = index(rows)
    position = {'context_val': 'berserk_apostol_remain_position'}
    names = [('COUNT', 'COUNT_DIES'), ('WYALD', 'WYALD_DIES'), ('ROSINE', 'ROSINE_DIES'),
             ('GRUNBELD', 'GRUNBELD_DIES'), ('GRUNBELD', 'FLORA_GRUNBELD_DIES')]
    for kind, handler in names:
        obj = by['EOC_BERSERK_APOSTOL_' + kind + '_FLESH_DEATH_' + handler]
        private = P + handler + '_AVATAR'
        alive = math('berserk_hunt_count_state < 3') if kind=='COUNT' else neg(eq('berserk_apostle_'+kind.lower()+'_dead'))
        if handler=='FLORA_GRUNBELD_DIES':alive=both(alive,neg(eq('berserk_grunbeld_grove_withdrawn')))
        body = [{'if':alive,'then':[
            run('EOC_BERSERK_APOSTOL_'+kind+'_FLESH_DROP'),
            math('berserk_apostol_'+kind.lower()+'_flesh_death_confirmed = 1')]},
            run('EOC_BERSERK_'+handler),run('EOC_BERSERK_APOSTOL_'+kind+'_PAWN_MASTER_SYNC'),
            run('EOC_BERSERK_REF_SYNC')]
        # Capture beta while valid, then run all player progression without it.
        obj['effect'] = [
            {'npc_location_variable': position},
            run(private, alpha_talker='avatar', beta_talker='')]
        EOCS.append(eoc(private, body, both('u_is_avatar', math('has_var(_berserk_apostol_remain_position)'))))
    write('effects/apostol_flesh_eocs.json', rows)
    # Public legacy handlers also remain safe when called without beta.
    for file in ['apostle_hunt_eocs', 'wyald_rosine_hunt_eocs', 'grunbeld_hunt_eocs', 'flora_siege_eocs']:
        rows = read('effects/' + file + '.json')
        for obj in rows:
            if obj['id'] not in ['EOC_BERSERK_' + h for _, h in names]: continue
            scope=either(math('has_var(_berserk_apostol_remain_position)'),both('has_beta','npc_is_monster'))
            old=obj.get('condition')
            if old!=scope and not (isinstance(old,dict) and scope in old.get('and',[])):
                obj['condition']=both(old,scope) if old else scope
            def safe_positions(node):
                if isinstance(node,list):return [safe_positions(x) for x in node]
                if not isinstance(node,dict):return node
                if node.get('if')==math('has_var(_berserk_apostol_remain_position)'):return node
                if 'npc_location_variable' in node:
                    target = node['npc_location_variable']
                    return {'if': math('has_var(_berserk_apostol_remain_position)'),
                        'then': {'copy_var': position, 'target_var': target},
                        'else': {'if': 'has_beta', 'then': {'npc_location_variable': target}}}
                return {k:safe_positions(v) for k,v in node.items()}
            if obj['id']=='EOC_BERSERK_COUNT_DIES':
                # Old Count capture normalized beta coordinates inline. Keep
                # that normalization using the copied position, never n_val.
                obj['effect']=[{'npc_location_variable':{'global_val':'berserk_hunt_count_location'}},
                    math('berserk_hunt_count_location.x = floor(berserk_hunt_count_location.x / 24) * 24'),
                    math('berserk_hunt_count_location.y = floor(berserk_hunt_count_location.y / 24) * 24'),
                    math('berserk_hunt_count_location.z = 0'),
                    run('EOC_BERSERK_COUNT_DEFEATED',alpha_talker='avatar',beta_talker='')]
            obj['effect']=safe_positions(obj['effect'])
        write('effects/' + file + '.json', rows)


def rescue():
    rows = read('effects/eclipse_aftermath_eocs.json'); by = index(rows)
    obj = by['EOC_BERSERK_ECLIPSE_RETURN_RECOVER']
    body = [x for x in obj['effect'] if not ('math' in x and x['math'][0].startswith('u_hp('))]
    parts = ['head', 'eyes', 'mouth', 'torso', 'arm_l', 'arm_r', 'hand_l', 'hand_r', 'leg_l', 'leg_r', 'foot_l', 'foot_r']
    obj['effect'] = [math("u_hp('" + part + "') = u_hp_max('" + part + "')") for part in parts] + body
    append_once(obj, math('u_berserk_rescue_anatomy_v24 = 1'))
    obj['//'] = 'One-time rescue heals main and minor HP. Story hand/eye bionics, Brand and armor consequences remain.'
    EOCS.append(eoc(P + 'OLD_RESCUE_ANATOMY', [
        *[math("u_hp('" + part + "') = u_hp_max('" + part + "')") for part in parts],
        math('u_berserk_rescue_anatomy_v24 = 1'), {'u_lose_effect': 'blind', 'target_part': 'ALL'}],
        both('u_is_avatar', eq('u_berserk_eclipse_rescue_state', 2), eq('u_berserk_eclipse_return_recovered'),
             neg(eq('u_berserk_rescue_anatomy_v24')), neg(eq('u_berserk_first_hunt_done')),
             either({'u_at_om_location': 'berserk_godo_workshop'}, {'u_at_om_location': 'berserk_godo_loft'}),
             math("u_hp('eyes') <= 0"), test('APOSTOL_HUMAN_ROUTE'))))
    append_once(by['EOC_BERSERK_ECLIPSE_AFTERMATH'], run(P + 'HAND_GOAL'))
    write('effects/eclipse_aftermath_eocs.json', rows)


def replacement_search():
    # The native om_terrain_replace branch honors min_distance for the forest
    # candidate AND actually sets the OMT before its normal mapgen loads.
    rows = read('effects/first_hunt_eocs.json'); by = index(rows)
    locate = by['EOC_BERSERK_FIRST_HUNT_LOCATE']
    locate['effect'] = [math('u_berserk_first_hunt_search_attempts = u_berserk_first_hunt_search_attempts + 1'),
        {'u_location_variable': {'u_val': 'berserk_first_hunt_search_origin'}}, run(P+'FIRST_CREATE')]
    # REQUEST already reuses persisted coordinates. A single native search
    # reuses an existing site in the ring, or replaces unseen dense forest.
    # A separate unsuccessful search-only call would emit a debug error and
    # return the origin (not false_eocs!) in native get_om_terrain_pos.
    EOCS.append(eoc(P + 'FIRST_CREATE', {
        'u_location_variable': {'context_val': 'berserk_first_hunt_candidate'},
        'target_params': {'om_terrain': 'berserk_first_hunt_lair', 'om_terrain_replace': 'forest_thick',
                         'random': True, 'cant_see': True, 'min_distance': 24, 'search_range': 48, 'z': 0},
        'true_eocs': ['EOC_BERSERK_FIRST_HUNT_VALIDATE'], 'false_eocs': ['EOC_BERSERK_FIRST_HUNT_SEARCH_FAILED']},
        both('u_is_avatar',eq('berserk_eclipse_era'),eq('u_berserk_eclipse_rescue_state',2),test('APOSTOL_HUMAN_ROUTE'))))
    write('effects/first_hunt_eocs.json', rows)
    rows = read('effects/local_breach_eocs.json'); by = index(rows)
    for node in walk(by['EOC_BERSERK_BREACH_FIND']['effect']):
        if 'target_params' not in node: continue
        node['target_params']={'om_terrain':'berserk_local_breach','om_terrain_replace':'forest_thick',
            'random':True,'cant_see':True,'min_distance':24,'search_range':48,'z':0}
    write('effects/local_breach_eocs.json', rows)


def rickert():
    rows = read('dialogue/godo.json'); by = index(rows)
    first_old = either(eq('u_berserk_rickert_eclipse_story', 0), eq('u_berserk_rickert_eclipse_story', 3))
    first_new = neg(either(eq('u_berserk_rickert_eclipse_story', 1), eq('u_berserk_rickert_eclipse_story', 2)))
    def replace(v):
        if v == first_old: return copy.deepcopy(first_new)
        if isinstance(v, dict): return {k: replace(x) for k, x in v.items()}
        if isinstance(v, list): return [replace(x) for x in v]
        return v
    for obj in rows:
        if obj['id'].startswith('TALK_BERSERK_RICKERT'): obj.update(replace(obj))
    root = by['TALK_BERSERK_RICKERT_ECLIPSE']
    label = tr('What do you remember of the Band?', 'Что ты сам помнишь об отряде?')
    if not any(r.get('text') == label for r in root['responses']):
        root['responses'].insert(-1, {'text': label, 'topic': 'TALK_BERSERK_RICKERT_BAND'})
    write('dialogue/godo.json', rows)
    rows = read('effects/rickert_dialogue_33_eocs.json')
    for obj in rows:
        if obj['id'].startswith('EOC_BERSERK_RICKERT_STORY_') and obj['id'] != 'EOC_BERSERK_RICKERT_STORY_CONFESS':
            obj.update(replace(obj))
    write('effects/rickert_dialogue_33_eocs.json', rows)


def godo_memories():
    rows = read('dialogue/godo.json'); by = index(rows)
    guts = test('FORGE_GUTS'); voice = by['TALK_BERSERK_GODO_TRAUMA_VOICES']
    choices = []
    memories = [
        ('JUDEAU', 'Judeau always noticed when someone needed help. He taught me things without making me feel a fool.',
         'Джудо всегда замечал, когда кому-то нужна помощь. Он учил меня, не заставляя чувствовать себя дураком.',
         'Then remember him doing that. You said he made things easier for others. His last moments do not take that away.',
         'Вот таким его и помни. Ты говоришь, он помогал другим. Последние минуты этого не отменяют.'),
        ('PIPPIN', 'Pippin hardly spoke. But if he stood behind you, you knew your back was covered.',
         'Пиппин почти не говорил. Но если он стоял за спиной, ты знал, что тебя прикроют.',
         'Some men spend their whole lives promising that. He did it. You have something worth remembering.',
         'Иные всю жизнь только обещают такое. А он делал. Тебе есть что о нём помнить.'),
        ('CORKUS', 'Corkus and I argued all the time. Now I catch myself wishing I could hear him grumble again.',
         'Мы с Коркусом вечно спорили. А теперь я ловлю себя на том, что хочу снова услышать его ворчание.',
         'You need not turn him into a saint to miss him. Remember the arguments too. That was a living man, not a statue.',
         'Не надо делать из него святого, чтобы по нему скучать. Помни и споры. Он был живым человеком, а не памятником.'),
        ('GASTON', 'Gaston wanted to leave the war and open a shop. I keep remembering how certain he sounded.',
         'Гастон хотел оставить войну и открыть своё дело. Я всё вспоминаю, как уверенно он об этом говорил.',
         'A shop, a roof, work of his own. I understand that wish. Do not let the way he died swallow the life he wanted.',
         'Своя лавка, крыша, работа. Такое желание я понимаю. Не позволяй его смерти заслонить жизнь, которой он хотел.')]
    for name, en, ru, reply, reply_ru in memories:
        topic = 'TALK_BERSERK_GODO_MEMORY_' + name
        choices += [{'text': tr(en, ru), 'topic': topic, 'condition': guts},
                    {'text': tr('I found a trace of ' + name.title() + '. I did not know him.',
                                'Я нашёл свидетельство о человеке по имени ' + {'JUDEAU':'Джудо','PIPPIN':'Пиппин','CORKUS':'Коркус','GASTON':'Гастон'}[name] + '. Я его не знал.'),
                     'topic': topic, 'condition': both(neg(guts), eq('u_berserk_godo_witness_' + name.lower()))}]
        by[topic]['dynamic_line'] = {**guts, 'yes': tr(reply, reply_ru),
            'no': tr('Then speak of what you found. Neither of us knew his life. We can at least leave room for it, instead of inventing one.',
                     'Тогда расскажи о том, что нашёл. Ни ты, ни я не знали его жизни. Можно хотя бы оставить ей место, а не выдумывать её за него.')}
        by[topic]['responses'] = [
            {'text': tr('I am afraid I will forget their voices.', 'Боюсь, что забуду их голоса.'), 'topic': 'TALK_BERSERK_GODO_MEMORY_KEEP', 'condition':guts},
            {'text':tr('Should I tell Rickert what I found?','Стоит рассказать Рикерту о том, что я нашёл?'),'topic':'TALK_BERSERK_GODO_MEMORY_KEEP','condition':neg(guts)},
            {'text': tr('And I am here, alive.', 'А я здесь, живой.'), 'topic': 'TALK_BERSERK_GODO_MEMORY_SURVIVED'},
            {'text': tr('There is someone else I want to remember.', 'Я хочу вспомнить ещё кое-кого.'), 'topic': voice['id'], 'condition':guts},
            {'text':tr('I found other traces too.','Я нашёл и другие следы.'),'topic':voice['id'],'condition':neg(guts)},
            {'text': tr('Enough for today. Thank you for listening.', 'На сегодня хватит. Спасибо, что выслушал.'), 'topic': 'TALK_BERSERK_GODO', 'effect': run('EOC_BERSERK_GODO_END_TRAUMA')}]
    voice['responses'] = choices + voice['responses'][-1:]
    for suffix, en, ru in [
        ('KEEP', 'Tell the boy, if you can. He knew them. Say one thing you remember, then another. You do not have to carry every voice alone.',
         'Расскажи мальчишке, если сможешь. Он знал их. Вспомни одно, потом другое. Не обязательно одному удерживать все голоса.'),
        ('SURVIVED', 'Yes. That is what we have to work with. Eat, mend what can be mended, and decide how to live tomorrow. You owe the dead more than another body.',
         'Да. С этим и придётся работать. Поешь, почини то, что ещё можно, и реши, как жить завтра. Ещё одно мёртвое тело — не всё, что ты можешь им оставить.')]:
        id_ = 'TALK_BERSERK_GODO_MEMORY_' + suffix
        obj = {'type':'talk_topic', 'id':id_, 'dynamic_line':tr(en,ru), 'responses':[
            {'text':tr('I want to remember someone else.','Я хочу вспомнить другого.'),'topic':voice['id']},
            {'text':tr('Thank you. I need some time.','Спасибо. Мне нужно немного времени.'),'topic':'TALK_BERSERK_GODO','effect':run('EOC_BERSERK_GODO_END_TRAUMA')}]}
        if suffix=='KEEP':
            obj['dynamic_line']={**eq('berserk_rickert_dead'),
                'yes':tr('Then tell me. I did not know their voices, but I can listen. Say one thing you remember, then another.',
                         'Тогда расскажи мне. Я не знал их голосов, но могу выслушать. Вспомни одно, потом другое.'),
                'no':obj['dynamic_line']}
        if id_ in by:by[id_].update(obj)
        else:rows.append(obj)
    write('dialogue/godo.json', rows)


def missions():
    need = both({'u_has_bionics':'bio_berserk_hand_stump'}, neg({'u_has_bionics':'bio_berserk_arm_cannon'}))
    EOCS.append(eoc(P+'HAND_GOAL', {'if':need,'then':{'if':both(math('has_var(berserk_godo_location)'),neg({'u_has_mission':'MISSION_BERSERK_RECOVERY_HAND'}),neg(eq('u_berserk_recovery_hand_done'))),
        'then':[{'assign_mission':'MISSION_BERSERK_RECOVERY_HAND'},math('u_berserk_recovery_hand_issued = 1')]},'else':[{'if':{'u_has_mission':'MISSION_BERSERK_RECOVERY_HAND'},
        'then':{'finish_mission':'MISSION_BERSERK_RECOVERY_HAND','success':True}},
        {'if':eq('u_berserk_recovery_hand_issued'),'then':math('u_berserk_recovery_hand_done = 1')}]},
        both('u_is_avatar',eq('u_berserk_eclipse_rescue_state',2))))
    EOCS.append(eoc(P+'LOAD', [run(P+'OLD_RESCUE_ANATOMY'),run(P+'HAND_GOAL')], 'u_is_avatar',eoc_type='EVENT',required_event='game_load'))
    EOCS.append(eoc(P+'HAND_WATCH',run(P+'HAND_GOAL'),both('u_is_avatar',eq('u_berserk_eclipse_rescue_state',2)),
                     eoc_type='RECURRING',recurrence='30 minutes',global_=True))
    # eoc helper takes arbitrary JSON keys; use the actual schema spelling.
    EOCS[-1]['global']=EOCS[-1].pop('global_')
    write('missions/recovery_hand_33.json', [{'type':'mission_definition','id':'MISSION_BERSERK_RECOVERY_HAND',
        'name':tr('First, get help from Rickert','Сначала — помощь Рикерта'),
        'description':tr('Speak to Rickert at the forest forge about replacing your lost left hand. He can build a prosthetic arm cannon if you bring the materials; ask him what is needed and deliver them to him. You may pursue the hunts with your own equipment, but restoring your grip will make the road much easier. Install the finished device from your inventory.',
            'Поговорите с Рикертом в лесной кузнице о замене потерянной левой кисти. Он соберёт протез с пушкой, если принести материалы: узнайте у него требования и передайте нужное ему самому. Охоты доступны и с вашим снаряжением, но восстановленный хват заметно облегчит путь. Готовое устройство устанавливается из инвентаря.'),
        'goal':'MGOAL_CONDITION','goal_condition':neg(need),'difficulty':2,'value':0,'origins':['ORIGIN_GAME_START'],
        'has_generic_rewards':False,'invisible_on_complete':False,'start':{'assign_mission_target':{'var':{'global_val':'berserk_godo_location'},'reveal_radius':0}}}])
    rows=read('effects/eclipse_aftermath_eocs.json');notice=index(rows)['EOC_BERSERK_KNIGHT_FORGE_NOTICE']
    messages=[]
    for base,ru in [('The Skull Knight waits outside the door. He wanted to speak with you before leaving.',
                     'За дверью ждёт Рыцарь-Череп. Он хотел поговорить с вами перед уходом.'),
                    ('The Skull Knight waits nearby. He wanted to speak with you before leaving.',
                     'Неподалёку ждёт Рыцарь-Череп. Он хотел поговорить с вами перед уходом.')]:
        base=tr(base,ru)
        msg=tr(base+' If you need a replacement hand, speak to Rickert first. His help is listed in your missions.',
               ru+' Если вам нужна замена кисти, сначала поговорите с Рикертом. Его помощь отмечена в списке заданий.')
        messages.append({'if':need,'then':{'u_message':msg,'type':'info','popup':True},
                         'else':{'u_message':base,'type':'info','popup':True}})
    notice['effect']=[math('u_berserk_knight_forge_notice_shown = 1'),
        {'if':eq('u_berserk_godo_rescue_relocated'),'then':[math('u_berserk_forge_rest_allowed = 1'),messages[0]],'else':messages[1]},
        run('EOC_BERSERK_REF_SYNC')]
    write('effects/eclipse_aftermath_eocs.json',rows)
    instructions={
        'MISSION_BERSERK_FIRST_HUNT':('Before hunting, consider asking Rickert at the forge for a replacement hand if you need one. Find and defeat the predator in the marked hollow. After the fight, examine the surviving trail in the lair; it gives the next mission even without a journal or the scrap of paper.',
            'Перед охотой стоит попросить Рикерта в кузнице о замене кисти, если она вам нужна. Найдите и победите хищника в отмеченной низине. После боя осмотрите уцелевший след в логове: он даст следующее задание даже без журнала и бумажного клочка.'),
        'MISSION_BERSERK_BREACH':('Reach the marked ashen breach and defeat its guardian. Then examine the exposed wound in the earth to close it. Examine the quieted mark afterward to collect what remains. Closing this passage reveals the next known hunts in your mission list.',
            'Доберитесь до отмеченного пепельного разрыва и победите хранителя. Затем осмотрите открывшуюся рану в земле, чтобы закрыть её. После этого осмотрите затихшую печать и заберите оставшееся. Закрытие прохода откроет следующие известные охоты в списке заданий.'),
        'MISSION_BERSERK_COUNT':('Reach the Count\'s residence and confront him below the execution hall. After defeating him, examine the exposed breach in the dungeon, then examine the sealed mark to take the relic. The prisoner and written evidence are optional help; neither is required to close the breach.',
            'Доберитесь до резиденции Графа и встретьтесь с ним под залом казней. После победы осмотрите открывшийся прорыв в подземелье, затем запечатанный след, чтобы забрать реликвию. Пленник и записи могут помочь, но для закрытия прорыва не обязательны.'),
        'MISSION_BERSERK_WYALD':('Reach the Black Dogs\' camp and confront Wyald in its final clearing. After defeating him, examine the exposed breach in the northern part of that clearing to close it. Then examine the sealed mark to collect the relic.',
            'Доберитесь до лагеря Чёрных Псов и встретьтесь с Уайлдом на дальней поляне. После победы осмотрите открывшийся прорыв в северной части этой поляны, чтобы закрыть его. Затем осмотрите запечатанный след и заберите реликвию.'),
        'MISSION_BERSERK_ROSINE':('Reach the misty valley and confront Rosine among the great roots. After defeating her, examine the exposed wound at her nest to close the passage. Then examine the sealed mark to collect the relic. You can leave cocoons behind; clearing every creature is not required.',
            'Доберитесь до туманной долины и встретьтесь с Розиной среди огромных корней. После победы осмотрите открывшуюся рану у её гнезда, чтобы закрыть проход. Затем осмотрите запечатанный след и заберите реликвию. Коконы можно оставить: уничтожать всех существ не обязательно.')}
    instructions['MISSION_BERSERK_GRUNBELD']=(
        'Reach the marked stronghold and follow the passage to the crucible. Deal with its keeper if he is still alive. Once the wound is exposed, examine the breach north of the crucible to close it, then examine the sealed mark to recover the relic.',
        'Доберитесь до отмеченной крепости и найдите проход к горнилу. Разберитесь с хранителем, если он ещё жив. Когда рана откроется, осмотрите прорыв к северу от горнила, чтобы закрыть его, затем запечатанный след, чтобы забрать реликвию.')
    for path in (MOD/'missions').glob('*.json'):
        rows=json.loads(path.read_text());changed=False
        for obj in rows:
            if obj.get('id') in instructions:obj['description']=tr(*instructions[obj['id']]);changed=True
        if changed:write(str(path.relative_to(MOD)),rows)


def localize():
    for filename,template in [('ru.po',False),('Berserk.pot',True)]:
        p=MOD/'lang/po'/filename;remaining=dict(STRINGS);blocks=[]
        for old in p.read_text().split('\n\n'):
            if not old.strip():continue
            key=source(old)
            if key in remaining:
                ru=remaining.pop(key);old='#. Owner playtest fixes 2026-10-24\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps('' if template else ru,ensure_ascii=False)
            blocks.append(old.strip())
        for en,ru in remaining.items():blocks.append('#. Owner playtest fixes 2026-10-24\nmsgid '+json.dumps(en,ensure_ascii=False)+'\nmsgstr '+json.dumps('' if template else ru,ensure_ascii=False))
        p.write_text('\n\n'.join(blocks)+'\n')


def main():
    worldgen();death_scope();rescue();replacement_search();rickert();godo_memories();missions()
    write('effects/playtest_fixes_20261024_eocs.json',EOCS);localize()
    print('24 October playtest fixes: story sites, forest placement, rescue, death scopes and dialogue followups.')


if __name__=='__main__':main()
