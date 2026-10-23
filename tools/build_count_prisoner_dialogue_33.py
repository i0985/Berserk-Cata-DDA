#!/usr/bin/env python3
"""Approved captive script, with native mi-go-prisoner NPC behavior."""
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path
from recover_apostol_33 import ROOT, MOD, read, write, index, eoc
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq
from recovery_33_translations import source as po_source

SOURCE=json.loads((ROOT/'docs/dialogue_sources/count-prisoner-2026-10-23.json').read_text())['paragraphs']
P='TALK_BERSERK_COUNT_';E='EOC_BERSERK_COUNT33_'
TOPICS={};EOCS=[];HELPERS={};STRINGS={}
CLASS='NC_BERSERK_COUNT_PRISONER';NPC='berserk_count_prisoner';UID='BERSERK_COUNT_PRISONER'
HOME='berserk_count_prisoner_home';GATE='berserk_count_prisoner_gate';GRATE='berserk_count_prisoner_grate'
GATE_C='t_berserk_count_cell_gate_c';GATE_O='t_berserk_count_cell_gate_o';GATE_U='t_berserk_count_cell_gate_shut'


def tr(s):STRINGS[s]=s;return s
def text(*ids):
    parts=[]
    for i in ids:
        s=SOURCE[str(i)].strip().strip('*').strip()
        s=re.sub(r'^(?:Пленник|Игрок):\s*','',s)
        s=re.sub(r'^\([^)]*\)\s*','',s)
        parts.append(s)
    return tr('\n\n'.join(parts))
def nv(s,v=1):return eq('n_berserk_count33_'+s,v)
def ns(s,v=1):return math('n_berserk_count33_'+s+' = '+str(v))
def uv(s,v=1):return eq('u_berserk_count33_'+s,v)
def us(s,v=1):return math('u_berserk_count33_'+s+' = '+str(v))
def run(s):return {'run_eocs':s if s.startswith('EOC_') else E+s}
def tid(s):return s if s.startswith('TALK_') else P+s
def choose(c,a,b):
    if isinstance(c,str) or any(k in c for k in ['and','or','not']):
        key=E+'LINE_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[key]=eoc(key,[],c);c=test(key)
    return {**c,'yes':a,'no':b}
def response(s,to='WITNESS',condition=None,effect=None):
    r={'text':tr(s),'topic':tid(to)}
    if condition is not None:r['condition']=condition
    if effect is not None:r['effect']=effect
    return r
def back(to='WITNESS'):return response('Я хотел спросить о другом.',to)
def topic(s,line,rs=None,effect=None):
    o={'type':'talk_topic','id':tid(s),'dynamic_line':line,'responses':rs or [back()]}
    if effect:o['speaker_effect']={'effect':effect}
    TOPICS[o['id']]=o;return o
def leaf(s,ids,to='WITNESS'):return topic(s,text(*ids),[back(to)])


VALID=both('has_beta','npc_is_npc',{'npc_has_class':CLASS})
DEAD=math('berserk_hunt_count_state >= 3')
OPEN=test(E+'CELL_OPEN')
VISIBLE=test(E+'VISIBLE_BODY')
MET=nv('met')
UNANSWERED=both(VISIBLE,nv('human_first'),neg(nv('change_seen')))
NORMAL=both(MET,neg(UNANSWERED))


def dialogue():
    repeat=choose(nv('escaped'),text(726),choose(UNANSWERED,tr('Голос твой. Узнаю голос.\n\nНо что с тобой стало?'),
        choose(both(VISIBLE,nv('change_seen')),text(734),choose(nv('knows_death'),text(718),choose(OPEN,text(710),text(694))))))
    first=choose(VISIBLE,text(569),choose(eq('berserk_count_prisoner_legacy_map'),tr('Тихо… Я выбрался из камеры, но до ворот ещё надо добраться. Ты кто?'),
        choose(OPEN,text(84),text(25,29))))
    meet=[ns('met'),{'if':neg(VISIBLE),'then':ns('human_first')},math('u_berserk_ref_prisoner_met = 1'),run('EOC_BERSERK_REF_SYNC')]
    rs=[
        response('Я не служу Графу.','NOT_SERVANT',both(neg(MET),neg(VISIBLE)),meet),
        response('Ищу хозяина этого места.','SEEK_COUNT',both(neg(MET),neg(VISIBLE)),meet),
        response('Хочу тебя вытащить.','RESCUE_INTRO',both(neg(MET),neg(VISIBLE)),meet),
        response('Сначала ответь мне на пару вопросов.','QUESTIONS',both(neg(MET),neg(VISIBLE)),meet),
        response('Я не собираюсь тебя трогать.','DEMON_PEACE',both(neg(MET),VISIBLE),meet+[ns('change_seen')]),
        response('Мне нужны сведения о доме.','DEMON_INFO',both(neg(MET),VISIBLE),meet+[ns('change_seen')]),
        response('Я могу открыть клетку.','DEMON_CELL',both(neg(MET),VISIBLE,neg(OPEN)),meet+[ns('change_seen')]),
        response('Правильно боишься.','DEMON_THREAT',both(neg(MET),VISIBLE),meet+[ns('change_seen'),ns('intimidated')]),
        response('Долгая история.','CHANGE_STORY',both(MET,UNANSWERED),[ns('change_seen')]),
        response('Я всё ещё тот, кто открыл тебе дверь.','CHANGE_REMEMBER',both(MET,UNANSWERED,nv('door_help')),[ns('change_seen')]),
        response('Я всё ещё тот, с кем ты говорил.','CHANGE_STORY',both(MET,UNANSWERED,neg(nv('door_help'))),[ns('change_seen')]),
        response('Теперь я сильнее Графа.','CHANGE_STRONG',both(MET,UNANSWERED),[ns('change_seen')]),
        response('Кто ты?','WHO',NORMAL),response('Что ты знаешь о резиденции?','HOUSE',NORMAL),
        response('Расскажи о Графе.','ABOUT_COUNT',NORMAL),response('Все, кто здесь служит, такие же, как он?','SERVANTS',NORMAL),
        response('Поможешь найти обход?','ROUTE',both(NORMAL,neg(nv('escaped')))),
        response('Что нужно, чтобы ты выбрался?','ESCAPE',both(NORMAL,neg(nv('escaped')))),
        response('Граф мёртв.','DEATH_REPORT',both(NORMAL,DEAD,neg(nv('knows_death')))),
        response('Я сражался с ним, но не знаю, чем всё кончилось.','DEATH_UNCERTAIN',both(NORMAL,neg(DEAD),uv('fought'))),
        response('Что будешь делать теперь?','AFTER_PLANS',both(NORMAL,nv('escaped'))),
        response('Ты свободен. Почему не радуешься?','AFTER_JOY',both(NORMAL,nv('escaped'))),
        response('Ты мне что-нибудь должен?','AFTER_PAYMENT',both(NORMAL,nv('escaped'))),
        response('Обсудим дальнейший путь.','TALK_FRIEND',both(NORMAL,'npc_following')),
        response('Мне пора.','GOODBYE')]
    topic('WITNESS',choose(MET,repeat,first),rs,[run('DIALOGUE_BIND')])
    topic('NOT_SERVANT',tr('Тогда нечего торчать на проходе столбом. Заметят — мне потом объясняться, с кем это я тут шушукался.'))
    topic('SEEK_COUNT',tr('Зачем — не спрашиваю.\n\nТолько пойми: он не человек. Запомни это. Не человек.'))
    topic('RESCUE_INTRO',choose(OPEN,text(84),text(63,67)),[response('Посмотрю, как тебе помочь.','ESCAPE'),back()])
    leaf('QUESTIONS',[74])
    topic('WHO',text(90,94,98),[
        response('За что тебя заперли?','WHY_LOCKED'),response('Что ты увидел?','WHAT_SAW'),
        response('Почему не пытался бежать?','WHY_STAYED'),response('У тебя есть куда идти?','WHERE_GO'),back()])
    topic('WHY_LOCKED',text(106,110),[response('И только за это?','WHY_MORE'),back('WHO')])
    leaf('WHY_MORE',[117,121],'WHO');leaf('WHAT_SAW',[129,133,137],'WHO')
    topic('WHY_STAYED',tr('Пытался. Шатал решётку — пока шаги не услышал. Бросил.\n\nПотом снова начал. И опять бросил.\n\nВремени здесь много. На то, чтобы начинать сначала — хватает с избытком.'),[back('WHO')])
    leaf('WHERE_GO',[163],'WHO')
    topic('HOUSE',text(170,174),[
        response('Где искать Графа?','WHERE_COUNT'),response('Как пройти незаметнее?','ROUTE'),
        response('Где найти что-нибудь полезное?','SUPPLIES'),response('Есть ещё пленники?','OTHERS'),back()])
    topic('WHERE_COUNT',tr('Принимал он обычно в зале казней, на северо-востоке. Оттуда лестница ведёт вниз. А где он сейчас — отсюда не разглядишь, сам понимаешь.'),[back('HOUSE')])
    topic('SUPPLIES',tr('В юго-западной кухне есть кладовая. Там держали хлеб, сушёное мясо и воду для дома.\n\nЕсли, конечно, с тех пор не вынесли всё подчистую. Я-то давно там не был.'),[back('HOUSE')])
    leaf('OTHERS',[232],'HOUSE')
    topic('ABOUT_COUNT',tr('Что хочешь знать?'),[
        response('Ты видел, на что он способен?','COUNT_POWER'),response('Он всегда был таким?','COUNT_PAST'),
        response('У него есть слабость?','COUNT_WEAK'),
        response('Я уже побеждал подобных ему.','COUNT_VICTORIES',either(eq('u_berserk_first_hunt_done'),eq('u_berserk_flora33_projection_defeated'),math('berserk_hunt_wyald_state >= 3'),math('berserk_hunt_rosine_state >= 3'))),
        response('Его история закончится сегодня.','COUNT_BOAST',neg(DEAD)),back()])
    topic('COUNT_POWER',tr('Видел. Достаточно, чтобы не принять тебя за спасителя только из-за того, что ты пришёл сюда.\n\nБыл один — нарушил что-то, не знаю что. Граф его… легко так. Будто мешок пустой с плеча скинул.\n\nДальше я уже не смотрел.'),[back('ABOUT_COUNT')])
    leaf('COUNT_PAST',[256,260],'ABOUT_COUNT');leaf('COUNT_WEAK',[268,272],'ABOUT_COUNT')
    leaf('COUNT_VICTORIES',[280,284],'ABOUT_COUNT');leaf('COUNT_BOAST',[292],'ABOUT_COUNT')
    topic('SERVANTS',text(298,302,306),[response('С кем можно договориться?','SERVANT_TRUST'),response('Они знают, что делает Граф?','SERVANT_KNOW'),response('Как они ходят по дому?','SERVANT_ROUTE'),back()])
    leaf('SERVANT_TRUST',[314,318],'SERVANTS');leaf('SERVANT_KNOW',[326,330],'SERVANTS')
    topic('SERVANT_ROUTE',tr('Раньше ходили через канцелярскую часть западного крыла и узкий проход к залу. По шагам я уже научился узнавать, когда кто-то сюда направляется.\n\nНо это всё, что я слышу. Весь дом отсюда не разберёшь — ни кто где стоит сейчас, ни когда меняется охрана.'),[back('SERVANTS')])
    topic('ROUTE',choose(test(E+'BYPASS_KNOWN_OPEN'),text(411),tr('Из канцелярской части западного крыла есть узкий служебный ход к залу казней. Его закрывает решётка. Можно пройти и через двор, если не хочешь возиться с замком.')),[
        response('Где искать ключ?','KEY_PLACE',neg(test(E+'BYPASS_KNOWN_OPEN'))),
        response('Там безопасно?','ROUTE_SAFE'),
        response('Я уже прошёл там. Дверь открыта.','ROUTE_OPEN',uv('bypass_passed')),
        response('Мне этот обход не нужен.','ROUTE_OTHER'),back('HOUSE')],
        [math('u_berserk_ref_prisoner_help = 1'),run('EOC_BERSERK_REF_SYNC')])
    topic('KEY_PLACE',tr('Ключа у меня нет. Писарь прятал служебный ключ в своём сундуке, в северной комнате западного крыла. Им открывали эту решётку и ход к залу.\n\nЯ сам видел, куда он его клал. А вот проверял ли кто с тех пор — понятия не имею.'),[back('ROUTE')])
    leaf('ROUTE_SAFE',[198],'ROUTE');leaf('ROUTE_OTHER',[428],'ROUTE')
    topic('ROUTE_OPEN',text(411,415),[back('ROUTE')])
    topic('ESCAPE',choose(OPEN,text(441),text(433,435)),[
        response('Поищу ключ.','KEY_PLACE',neg(OPEN)),
        response('Подожди. Я проверю дорогу.','WAIT',both(neg('npc_following'),neg(nv('dismissed')))),
        response('Иди за мной.','FOLLOW_READY',both(OPEN,neg('npc_following'))),
        response('Дальше решай сам.','OWN_CHOICE',OPEN),
        response('Иди за мной.','TALK_DONE',both(OPEN,'npc_following')),back()])
    leaf('WAIT',[448],'ESCAPE')
    topic('FOLLOW_READY',text(454),[
        response('Пойдём.','TALK_DONE',effect=[ns('following_chosen'),'follow']),back('ESCAPE')])
    topic('OWN_CHOICE',text(451),[
        response('Тогда беги, если решишься.','TALK_DONE',effect=[ns('dismissed'),'flee']),back('ESCAPE')])
    topic('DEATH_REPORT',text(466),[response('Он больше не поднимется.','AFTER',DEAD),back()])
    topic('AFTER',choose(VISIBLE,text(674,678),text(478,482)),[
        response('Помогу тебе выбраться.','ESCAPE',neg(nv('escaped'))),
        response('Я не прошу тебя оставаться.','DEMON_AFTER',VISIBLE),back()],effect=[ns('knows_death')])
    leaf('DEATH_UNCERTAIN',[490])
    leaf('AFTER_PLANS',[537,541]);leaf('AFTER_JOY',[549,553]);leaf('AFTER_PAYMENT',[561])
    for n,ids in [('PEACE',[583]),('INFO',[591]),('CELL',[599,603]),('THREAT',[611])]:leaf('DEMON_'+n,ids)
    leaf('CHANGE_STORY',[638,642]);leaf('CHANGE_REMEMBER',[650,654]);leaf('CHANGE_STRONG',[662,666])
    leaf('DEMON_AFTER',[685])
    topic('GOODBYE',choose(nv('escaped'),text(760,764),choose(OPEN,text(752),text(744))),[response('До встречи.','TALK_DONE')])
    # Public old entry points survive, without the former omniscient advice.
    leaf('FAMILY',[174],'HOUSE')
    topic('LEGACY',tr('Человек поднимает голову на звук шагов.'),[
        response('Я хочу поговорить.','TALK_DONE',effect=[run('MIGRATE')])])


def bind_effects(actor):
    """Same binding in an actual NPC turn (u) and a conversation (n)."""
    own='u_location_variable' if actor=='u' else 'npc_location_variable'
    at='u_at_om_location' if actor=='u' else 'npc_at_om_location'
    body=[math('berserk_count_prisoner_spawned = 1')]
    body.append({'if':both(neg(math('has_var('+HOME+')')),{at:'berserk_count_prison'}),
        'then':[{own:{'global_val':HOME}},math(f'{HOME}.x = floor({HOME}.x / 24) * 24'),math(f'{HOME}.y = floor({HOME}.y / 24) * 24')]})
    body.append({'if':math('has_var('+HOME+')'),'then':[
        {'copy_var':{'global_val':HOME},'target_var':{'global_val':GATE}},
        {'location_variable_adjust':{'global_val':GATE},'x_adjust':8,'y_adjust':11},
        {'copy_var':{'global_val':HOME},'target_var':{'global_val':GRATE}},
        {'location_variable_adjust':{'global_val':GRATE},'x_adjust':27,'y_adjust':16}]})
    body.append({own:{'context_val':'count33_actor_pos'}})
    outside=both(math('has_var('+HOME+')'),math(f'_count33_actor_pos.z == {HOME}.z'),either(
        math(f'_count33_actor_pos.x < {HOME}.x + 2'),math(f'_count33_actor_pos.x > {HOME}.x + 45'),
        math(f'_count33_actor_pos.y < {HOME}.y + 2'),math(f'_count33_actor_pos.y > {HOME}.y + 45')))
    body.append({'if':outside,'then':[math(actor+'_berserk_count33_escaped = 1'),math('berserk_count_prisoner_escaped = 1')]})
    return body


def mechanics():
    visible=sorted(o['id'] for p in (MOD/'mutations').glob('apostol_*.json') for o in json.loads(p.read_text()) if o.get('type')=='mutation' and o['id'].endswith('_FORM'))
    EOCS.append(eoc(E+'VISIBLE_BODY',[],either(*({'u_has_trait':x} for x in visible))))
    site=both(math('has_var('+HOME+')'),math("u_val('pos_z') == 0"),math(f"distance('u', {HOME}) < 72"))
    EOCS.append(eoc(E+'AT_SITE',[],site))
    gate_open=both(math('has_var('+GATE+')'),test(E+'AT_SITE'),either(*({'map_terrain_id':x,'loc':{'global_val':GATE}} for x in [GATE_O,GATE_U,'t_door_bar_o','t_door_bar_c','t_floor','t_mdoor_frame','t_dirt','t_rubble'])))
    EOCS.append(eoc(E+'CELL_OPEN',[],either(nv('escaped'),eq('berserk_count_prisoner_legacy_map'),gate_open)))
    EOCS.append(eoc(E+'BYPASS_KNOWN_OPEN',[],uv('bypass_seen')))
    scan=bind_effects('u')+[{'if':both(uv('escaped'),neg(uv('escape_announced'))),'then':[
        {'u_location_variable':{'context_val':'count33_escape_pos'}},
        {'run_eocs':E+'ESCAPE_OBSERVED','alpha_talker':'avatar'}]}]
    EOCS.append(eoc(E+'NPC_SCAN',scan,both('u_is_npc',{'u_has_class':CLASS})))
    EOCS.append(eoc(E+'DIALOGUE_BIND',bind_effects('n')+[
        {'if':uv('opened_cell'),'then':ns('door_help')},
        {'if':nv('escaped'),'then':math('u_berserk_ref_prisoner_freed = 1')},
        run('BYPASS_OBSERVE'),run('EOC_BERSERK_REF_SYNC')],VALID))
    EOCS.append(eoc(E+'ESCAPE_OBSERVED',[math('u_berserk_ref_prisoner_freed = 1'),
        {'u_run_npc_eocs':[E+'MARK_ESCAPE_OBSERVED'],'unique_ids':[UID],'local':False},run('EOC_BERSERK_REF_SYNC')],
        both('u_is_avatar',eq('u_berserk_ref_prisoner_met'),{'u_can_see_location':{'context_val':'count33_escape_pos'}})))
    EOCS.append(eoc(E+'MARK_ESCAPE_OBSERVED',us('escape_announced'),both('u_is_npc',{'u_has_class':CLASS})))
    EOCS.append(eoc(E+'BYPASS_OBSERVE',[
        us('bypass_seen'),{'if':math(f"distance('u', {GRATE}) == 0"),'then':us('bypass_passed')}],
        both('u_is_avatar',test(E+'AT_SITE'),math(f"distance('u', {GRATE}) <= 2"),
             {'map_furniture_id':'f_berserk_count_service_grate_open','loc':{'global_val':GRATE}})))
    EOCS.append(eoc(E+'TICK',[{'u_run_npc_eocs':[E+'NPC_SCAN'],'unique_ids':[UID],'local':True},run('BYPASS_OBSERVE'),run('MIGRATE')],
        'u_is_avatar',**{'global':True,'recurrence':'2 seconds'}))
    EOCS.append(eoc(E+'NPC_DEATH',[math('berserk_count_prisoner_dead = 1'),
        {'u_location_variable':{'context_val':'ref_death_pos'}},
        {'run_eocs':'EOC_BERSERK_REF_PRISONER_DEATH_OBSERVED','alpha_talker':'avatar'}],'u_is_npc'))
    EOCS.append(eoc(E+'LEGACY_DEATH',[math('berserk_count_prisoner_dead = 1'),run('EOC_BERSERK_REF_PRISONER_DEATH')]))
    EOCS.append(eoc(E+'MARK_PRESENT',math('berserk_count_prisoner_present = 1'),both('u_is_npc',{'u_has_class':CLASS})))
    EOCS.append(eoc(E+'REMOVE_LEGACY',{'u_run_monster_eocs':[E+'RETIRE_LEGACY'],'mtype_ids':['mon_berserk_count_witness'],'monster_range':32}))
    EOCS.append(eoc(E+'RETIRE_LEGACY',{'u_die':{'remove_from_creature_tracker':True}}))
    EOCS.append(eoc(E+'CAPTURE_LEGACY',[{'u_location_variable':{'global_val':'berserk_count_prisoner_legacy_pos'}}]))
    EOCS.append(eoc(E+'MIGRATE',[
        math('berserk_count_prisoner_present = 0'),
        {'u_run_npc_eocs':[E+'MARK_PRESENT'],'unique_ids':[UID],'local':False},
        {'if':eq('berserk_count_prisoner_present'),'then':run('REMOVE_LEGACY'),'else':{
            'if':both(eq('berserk_count_prisoner_spawned',0),eq('berserk_count_prisoner_dead',0)),
            'then':[{'u_run_monster_eocs':[E+'CAPTURE_LEGACY'],'mtype_ids':['mon_berserk_count_witness'],'monster_range':32},
                {'u_spawn_npc':NPC,'unique_id':UID,'real_count':1,
                 'target_var':{'global_val':'berserk_count_prisoner_legacy_pos'},'min_radius':1,'max_radius':2,
                 'true_eocs':[E+'MIGRATION_COMMIT']}]} }],
        both('u_is_avatar',eq('berserk_count_prisoner_dead',0),math("u_monsters_nearby('mon_berserk_count_witness', 'radius': 32, 'attitude': 'both') > 0"))))
    EOCS.append(eoc(E+'MIGRATION_COMMIT',[math('berserk_count_prisoner_spawned = 1'),math('berserk_count_prisoner_legacy_map = 1'),run('REMOVE_LEGACY')]))
    EOCS.append(eoc(E+'FOUGHT',[us('fought')],both('u_is_avatar',{'compare_string':[{'context_val':'victim_type'},'mon_berserk_apostle_count']}),eoc_type='EVENT',required_event='character_melee_attacks_monster'))
    EOCS.append(eoc(E+'OPEN_CELL',{
        'if':{'u_has_item':'berserk_count_service_key'},'then':{
            'if':{'u_query':tr('Открыть решётку служебным ключом?'),'default':False},'then':[
                {'u_transform_radius':0,'ter_furn_transform':'berserk_count_cell_unlocked','target_var':{'context_val':'pos'}},
                {'if':{'map_terrain_id':GATE_O,'loc':{'context_val':'pos'}},'then':us('opened_cell')},
                {'turn_cost':'2 seconds'},
                {'u_message':tr('Ключ поворачивается в замке. Решётка открыта.'),'type':'info','popup':False}]},
        'else':{'u_message':tr('Решётка заперта. Замок можно попробовать вскрыть отмычкой; железо поддастся только подходящему инструменту или сильным ударам.'),'type':'info','popup':False}},
        both('u_is_avatar',math("distance('u', _pos) <= 1"),{'map_terrain_id':GATE_C,'loc':{'context_val':'pos'}})))
    EOCS.append({'type':'ter_furn_transform','id':'berserk_count_cell_unlocked','terrain':[{'valid_terrain':[GATE_C],'result':GATE_O}]})


def content():
    # A native NPC with the same low-skill class/AI basis as the 0.I mi-go captive.
    write('npcs/count_prisoner.json',[
        {'type':'npc_class','id':CLASS,'name':{'str':tr('пленник Графа')},'common':False,'sells_belongings':False,
         'job_description':tr('Я только хочу выбраться отсюда живым.'),
         'skills':[{'skill':'ALL','level':{'sum':[{'dice':[3,3]},{'constant':-5}]}}],
         'worn_override':'naked_prisoner','carry_override':'naked_prisoner','weapon_override':'naked_prisoner'},
        {'type':'npc','id':NPC,'temp_suffix':tr('пленник Графа'),'gender':'male','class':CLASS,
         'attitude':0,'mission':7,'chat':P+'WITNESS','talk_friend':P+'WITNESS',
         'talk_friend_guard':P+'WITNESS','faction':'no_faction','death_eocs':[E+'NPC_DEATH']}])
    gates=[
        {'type':'terrain','id':GATE_C,'copy-from':'t_door_bar_locked','name':tr('запертая железная решётка'),
         'description':tr('Тяжёлая решётка из кованого железа. Замок удерживает её в каменном проёме.'),
         'looks_like':'t_bars','lockpick_result':GATE_O,
         'examine_action':{'type':'effect_on_condition','effect_on_conditions':[E+'OPEN_CELL']}},
        {'type':'terrain','id':GATE_O,'copy-from':'t_door_bar_o','name':tr('открытая железная решётка'),
         'description':tr('Железная решётка отведена в сторону. Проём свободен.'),'looks_like':'t_door_bar_o','close':GATE_U},
        {'type':'terrain','id':GATE_U,'copy-from':'t_door_bar_c','name':tr('железная решётка'),
         'description':tr('Тяжёлая железная решётка закрывает проём. Замок не заперт.'),'looks_like':'t_bars','open':GATE_O}]
    # Keep native picking/strength, but forged bars must not yield modern pipes.
    for gate in gates:
        gate['roof']='t_floor'
        gate['hacksaw']={'result':'t_floor','duration':'15 minutes',
            'message':tr('Вы заканчиваете перепиливать железные прутья.'),
            'byproducts':[{'item':'mc_steel_chunk','count':[6,12]}]}
        gate['oxytorch']={'result':'t_floor','duration':'14 seconds',
            'byproducts':[{'item':'mc_steel_chunk','count':[3,8]}]}
        gate['bash']={'str_min':45,'str_max':210,'sound':'metal screeching!','sound_fail':'clang!',
            'ter_set':'t_floor','items':[{'item':'mc_steel_chunk','count':[3,10]}]}
    write('furniture/count_cell_gate.json',gates)
    data=read('mapgen/apostle_count.json')
    prison=next(x['object'] for x in data if x.get('om_terrain')==['berserk_count_prison'])
    prison['place_monster']=[x for x in prison.get('place_monster',[]) if x['monster']!='mon_berserk_count_witness']
    placed={'class':NPC,'x':7,'y':11,'unique_id':UID}
    prison['place_npcs']=[x for x in prison.get('place_npcs',[]) if x['class']!=NPC]+[placed]
    for prop in prison['place_furniture']:
        if prop['furn']=='f_bed' and (prop['x'],prop['y'])==(9,18):prop.update(x=6,y=9)
        if prop['furn']=='f_berserk_location_count_property' and (prop['x'],prop['y'])==(7,7):prop.update(x=7,y=18)
    write('mapgen/apostle_count.json',data)
    data=read('mapgen/apostle_count_palettes.json');data[0]['terrain']['!']=GATE_C
    write('mapgen/apostle_count_palettes.json',data)
    data=read('monsters/apostle_count.json');obj=index(data)['mon_berserk_count_witness']
    obj['chat_topics']=[P+'LEGACY'];obj['death_function']={'eoc':E+'LEGACY_DEATH'}
    write('monsters/apostle_count.json',data)
    data=read('items/location_records.json');obj=index(data)['berserk_count_service_key']
    obj['description']=tr('Простой железный ключ. Им запирали камеру западного крыла и служебный проход между канцелярией и залом казней.')
    write('items/location_records.json',data)


def localization():
    for file,translated in [('ru.po',True),('Berserk.pot',False)]:
        path=MOD/'lang/po'/file;remaining=dict(STRINGS);blocks=[]
        for block in path.read_text().split('\n\n'):
            if not block.strip():continue
            key=po_source(block)
            if key in remaining:
                value=remaining.pop(key);block='#. Count prisoner 2026-10-23\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if translated else '',ensure_ascii=False)
            blocks.append(block.strip())
        for key,value in remaining.items():blocks.append('#. Count prisoner 2026-10-23\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if translated else '',ensure_ascii=False))
        path.write_text('\n\n'.join(blocks)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)


def main():
    dialogue();mechanics();content()
    write('dialogue/apostle_count.json',list(TOPICS.values()))
    write('effects/count_prisoner_33_eocs.json',EOCS+list(HELPERS.values()))
    localization()
    print('Count captive:',len(TOPICS),'topics; native NPC, locked barred cell and follow/flee.')


if __name__=='__main__':main()
