#!/usr/bin/env python3
"""Approved God Hand manuscript, shared choice and exceptional combat exits.

Run after named apostles and before the optional reference-book builder.
Existing scars, growth, entry, safe landing and original actor IDs are retained.
"""
import copy
import hashlib
import json
from recover_apostol_33 import ROOT, MOD, read, write, index, eoc, walk
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq
from build_named_apostle_dialogues_33 import localization as _localization, STRINGS

SOURCE = json.loads((ROOT/'docs/dialogue_sources/godhand-2026-10-23.json').read_text())['paragraphs']
P = 'EOC_BERSERK_HAND33_'
OLD = 'EOC_BERSERK_APOSTOL_'
T = 'TALK_BERSERK_APOSTOL_'
KINDS = ['VOID', 'SLAN', 'UBIK', 'CONRAD', 'FEMTO']
NAMES = dict(zip(KINDS, ['Войд', 'Слан', 'Убик', 'Конрад', 'Фемто']))
TOPICS = {}; EOCS = []; HELPERS = {}; USED = set()
OPEN = test(OLD+'CEREMONY_OPEN')
ATTACKED = eq('u_berserk_apostol_godhand_attacked')
WON = eq('berserk_godhand_defeated')

def tr(s): STRINGS[s] = s; return s
def prose(*ids):
    USED.update(ids)
    return tr('\n\n'.join(SOURCE[str(i)].strip().strip('*').strip() for i in ids))
def run(s): return {'run_eocs':s if s.startswith('EOC_') else P+s}
def state(s, value=1): return eq('u_berserk_hand33_'+s, value)
def put(s, value=1): return math('u_berserk_hand33_'+s+' = '+str(value))
def tid(k,s): return T+k if s=='ROOT' else T+k+'_'+s
def choose(c,a,b):
    if isinstance(c,str) or any(x in c for x in ['and','or','not']):
        key=P+'LINE_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[key]=eoc(key,[],c);c=test(key)
    return {**c,'yes':a,'no':b}
def response(k,s,to='ROOT',condition=None,effect=None):
    r={'text':tr(s),'topic':to if to.startswith('TALK_') else tid(k,to)}
    if condition is not None:r['condition']=condition
    if effect is not None:r['effect']=effect
    return r
def back(k,to='ROOT'):return response(k,'Я хотел спросить о другом.',to,OPEN)
def topic(k,s,line,rs=None,effect=None):
    # Old saved topics and direct monster chat cannot restart a closed ceremony.
    line=choose(OPEN,line,tr('В ответ — только тяжёлое молчание.'))
    rows=(rs or [back(k)])+[response(k,'Отойти.','TALK_DONE',neg(OPEN))]
    obj={'type':'talk_topic','id':tid(k,s),'dynamic_line':line,'responses':rows}
    if effect:obj['speaker_effect']={'effect':[{'if':OPEN,'then':effect}]}
    TOPICS[obj['id']]=obj
    return obj
def leaf(k,s,ids,parent='ROOT',extra=None):
    return topic(k,s,prose(*ids),(extra or [])+[back(k,parent)])
def say(s,kind='info',popup=False):return {'u_message':tr(s),'type':kind,'popup':popup}
def flags_dead():return both(*[eq('u_berserk_hand33_'+k.lower()+'_dead') for k in KINDS])

def roots():
    data={
      'VOID':([103],[106,110],[231], [('Почему камень привёл меня сюда?','STONE'),('Что это за место?','PLACE'),('Могу ли я отказаться?','REFUSE_PRICE'),('Что останется от прежнего меня?','SELF')]),
      'SLAN':([249],[253,257],[407], [('Почему человеческого тела недостаточно?','BODY'),('Что будет с болью?','PAIN'),('Почему вы предлагаете это мне?','WHY'),('Что ты во мне видишь?','SEE')]),
      'UBIK':([422],[426,430],[595], [('То, что я вижу, настоящее?','REAL'),('Почему вы показываете мне это?','SHOW'),('Вы знаете, чего я хочу?','WANT'),('Ты пытаешься меня обмануть?','LIE')]),
      'CONRAD':([612],[616],[740], [('Что случится, если уйти человеком?','LEAVE'),('Можно ли пережить это без изменений?','UNCHANGED'),('Что вы называете даром?','GIFT'),('Я всё ещё смогу умереть?','DIE'),('Вы меняете и разум?','MIND')]),
      'FEMTO':([750],[754],[855], [('Что даёт отказ от прежней жизни?','PAST'),('Смогу ли я распоряжаться этой силой?','CONTROL'),('Почему вам нужен мой выбор?','CHOICE'),('Я стану одним из вас?','EQUAL')])}
    for k,(scene,first,repeat,qs) in data.items():
        seen=state(k.lower()+'_greeted')
        firstline=tr('&'+prose(*scene)+'\n\n«'+prose(*first)+'»')
        if k=='UBIK':
            # His first interlocutor need not have asked the others anything yet.
            firstline=tr('&'+prose(*scene)+'\n\n«Ну вот и ты. Давай посмотрим, какие вопросы ты принёс с собой».')
        line=choose(seen,prose(*repeat),firstline)
        if k=='VOID':line=choose(seen,choose(state('price_heard'),tr('Ты знаешь, что решение останется с тобой. О чём ещё хочешь спросить?'),prose(*repeat)),firstline)
        if k=='UBIK':line=choose(seen,choose(eq('u_berserk_apostol_refusal_seen'),prose(599),prose(*repeat)),firstline)
        rs=[response(k,label,s,OPEN) for label,s in qs]
        if k=='FEMTO':
            rs.append(response(k,'Я видел твой образ раньше.','PROJECTION',both(OPEN,test('EOC_BERSERK_HAND33_FEMTO_PROJECTION_SEEN'))))
        rs += [response(k,'Я хочу спросить о даре.','QUESTION',OPEN),
               response(k,'Я решил принять дар.','CONFIRM',OPEN),
               response(k,'Я хочу уйти человеком.','REFUSE',OPEN),
               response(k,'Я хочу поговорить с остальными.','OTHERS',OPEN),
               response(k,'Мне нужно подумать.','PAUSE',OPEN)]
        if k=='VOID':rs.insert(0,response(k,'Кто вы?','WHO',OPEN))
        if k=='CONRAD':rs.insert(0,response(k,'И хочу унести его обратно.','TAKE_BODY_BACK',OPEN))
        topic(k,'ROOT',line,rs,[put(k.lower()+'_greeted'),math('u_berserk_ref_circle_reached = 1'),run('EOC_BERSERK_REF_SYNC')])
        topic(k,'OTHERS',{'VOID':prose(246),'SLAN':tr('Иди. Я никуда не тороплюсь.'),'UBIK':tr('Выслушай их. Любопытно, какие слова тебе понравятся.'),'CONRAD':tr('Слушай.'),'FEMTO':tr('Выбор остаётся за тобой.')}[k],[response(k,'Отойти к другим.','TALK_DONE',OPEN)])
        pauses={'VOID':tr('Твой ответ ещё не дан.'),'SLAN':prose(417,421),'UBIK':prose(609),'CONRAD':prose(749),'FEMTO':prose(866)}
        topic(k,'PAUSE',pauses[k],[response(k,'Отойти.','TALK_DONE',OPEN)])

def branches():
    k='VOID'
    leaf(k,'WHO',[75])
    leaf(k,'STONE',[125,129],extra=[response(k,'Значит, всё было предрешено?','DESTINY',OPEN)])
    leaf(k,'DESTINY',[136,140],extra=[response(k,'Я сам выбрал прийти.','OWN_CHOICE',OPEN),response(k,'Я не знал, чем это закончится.','DID_NOT_KNOW',OPEN)])
    leaf(k,'OWN_CHOICE',[152]);leaf(k,'DID_NOT_KNOW',[159])
    leaf(k,'PLACE',[166,170],extra=[response(k,'Я смогу вернуться?','BACK',OPEN)])
    leaf(k,'BACK',[176,180]);leaf(k,'REFUSE_PRICE',[187,191],extra=[response(k,'Это наказание за отказ?','PUNISHMENT',OPEN)])
    leaf(k,'PUNISHMENT',[197,201]);leaf(k,'SELF',[210,214],extra=[response(k,'А если я передумаю потом?','UNDO',OPEN)])
    leaf(k,'UNDO',[220,224])
    k='SLAN'
    leaf(k,'BODY',[272,276],extra=[response(k,'Слабость тела ещё не причина от него отказываться.','WEAKNESS',OPEN)])
    leaf(k,'WEAKNESS',[283],extra=[response(k,'Ты обещаешь неуязвимость?','INVINCIBLE',OPEN),response(k,'Я хочу силу, а не чужую волю.','WILL',OPEN)])
    leaf(k,'INVINCIBLE',[294]);leaf(k,'WILL',[302,306])
    leaf(k,'PAIN',[313,317],extra=[response(k,'Звучит почти приятно.','PLEASANT',OPEN)])
    leaf(k,'PLEASANT',[324,328]);leaf(k,'WHY',[335,339],extra=[response(k,'Я хочу выжить.','SURVIVE',OPEN),response(k,'Я хочу перестать бояться.','FEAR',OPEN),response(k,'Ты ничего обо мне не знаешь.','KNOW_NOTHING',OPEN)])
    topic(k,'SURVIVE',prose(351).replace('сама понимаешь','понимаешь'))
    leaf(k,'FEAR',[358,362]);leaf(k,'KNOW_NOTHING',[370])
    leaf(k,'SEE',[377,381],extra=[response(k,'Тебе это нравится?','ENJOY',OPEN)])
    leaf(k,'ENJOY',[387]);leaf(k,'HER_FORM',[395,399])
    k='UBIK'
    leaf(k,'REAL',[445,449],extra=[response(k,'А то, что вокруг?','SURROUNDINGS',OPEN)])
    leaf(k,'SURROUNDINGS',[455,459],extra=[response(k,'Почему я должен тебе верить?','TRUST',OPEN),response(k,'А воспоминания?','MEMORIES',OPEN)])
    leaf(k,'TRUST',[471]);leaf(k,'MEMORIES',[478,482])
    topic(k,'SHOW',choose(eq('u_berserk_apostol_refusal_seen'),prose(502),prose(493,497)),[response(k,'Почему только плохое?','BAD_ONLY',both(OPEN,eq('u_berserk_apostol_refusal_seen'))),back(k)])
    leaf(k,'BAD_ONLY',[509]);leaf(k,'WANT',[516,520],extra=[response(k,'Я хочу защитить тех, кто рядом.','PROTECT',OPEN),response(k,'Я хочу отомстить.','REVENGE',OPEN),response(k,'Я сам не знаю.','UNSURE',OPEN),response(k,'Я не обязан тебе это объяснять.','PRIVATE',OPEN)])
    leaf(k,'PROTECT',[533,537]);leaf(k,'REVENGE',[544]);leaf(k,'UNSURE',[552]);leaf(k,'PRIVATE',[559,563])
    leaf(k,'LIE',[570,573],extra=[response(k,'Изменение действительно необратимо?','FOREVER',OPEN)])
    leaf(k,'FOREVER',[577])
    k='CONRAD'
    leaf(k,'TAKE_BODY_BACK',[623])
    leaf(k,'LEAVE',[639,643],extra=[response(k,'Что именно изменится?','HUMAN_PRICE',OPEN)])
    leaf(k,'HUMAN_PRICE',[649,653],extra=[response(k,'Зрение или слух станут хуже?','SENSES',OPEN),response(k,'Значит, уйти невредимым нельзя?','UNHARMED',OPEN)])
    topic(k,'SENSES',tr('Возможно. Слух может ослабнуть, зрение — потерять остроту. Дрожь, тревога, память, не дающая покоя. Заранее ты не узнаешь, что останется с тобой.'),effect=[put('price_heard')])
    leaf(k,'UNHARMED',[665]);leaf(k,'UNCHANGED',[674,677],extra=[response(k,'Я хочу понять, на что соглашаюсь.','UNDERSTAND',OPEN)])
    leaf(k,'UNDERSTAND',[681]);leaf(k,'GIFT',[688,692],extra=[response(k,'Это произойдёт сразу?','IMMEDIATE',OPEN)])
    leaf(k,'IMMEDIATE',[698,702]);leaf(k,'DIE',[709],extra=[response(k,'Тогда зачем принимать?','WHY_ACCEPT',OPEN)])
    leaf(k,'WHY_ACCEPT',[716,720]);leaf(k,'MIND',[727,731])
    k='FEMTO'
    leaf(k,'PAST',[770],extra=[response(k,'Этого достаточно?','ENOUGH',OPEN)]);leaf(k,'ENOUGH',[777])
    leaf(k,'CONTROL',[784],extra=[response(k,'Я сам решу, против кого её обратить?','TARGET',OPEN)])
    leaf(k,'TARGET',[790]);leaf(k,'CHOICE',[799,803],extra=[response(k,'Ты называешь это свободой?','FREEDOM',OPEN)])
    leaf(k,'FREEDOM',[809]);topic(k,'EQUAL',tr('Ты получишь дар. Но не место среди нас.'),[response(k,'Тогда сколько силы мне достанется?','STRENGTH',OPEN),back(k)])
    leaf(k,'STRENGTH',[826,830]);leaf(k,'PROJECTION',[839],extra=[response(k,'Я уничтожил его.','PROJECTION_KILLED',both(OPEN,test('EOC_BERSERK_HAND33_FEMTO_PROJECTION_KILLED')))])
    leaf(k,'PROJECTION_KILLED',[846])

def common_choices():
    for k in KINDS:
        rs=[response(k,'Я смогу выбрать свой облик?','FORM_CHOICE',OPEN),response(k,'Изменения продолжатся сами?','GROWTH',OPEN),
            response(k,'Когда они закончатся?','END_GROWTH',OPEN),response(k,'Вы потребуете чью-то жизнь?','SACRIFICE',OPEN),
            response(k,'Какова цена возвращения человеком?','PRICE',OPEN),response(k,'Я решил принять дар.','CONFIRM',OPEN),
            response(k,'Я хочу уйти человеком.','REFUSE',OPEN),back(k)]
        topic(k,'QUESTION',tr({'VOID':'Спрашивай, прежде чем дать ответ.','SLAN':'Что ещё тебя удерживает?','UBIK':'Хорошо, давай разберёмся, на что ты собираешься согласиться.','CONRAD':'Спрашивай.','FEMTO':'Говори.'}[k]),rs)
        p=dict(zip(KINDS,[873,877,881,885,888]))[k]
        formline=prose(p) if k!='FEMTO' else tr('Ты можешь принять силу. Но её природу не тебе назначать.')
        topic(k,'FORM_CHOICE',formline,[back(k,'QUESTION')],[math('u_berserk_ref_gift_choice_explained = 1'),run('EOC_BERSERK_REF_SYNC')])
        if k=='SLAN':TOPICS[tid(k,'FORM_CHOICE')]['responses'].insert(0,response(k,'Если я соглашусь с тобой, стану похожим на тебя?','HER_FORM',OPEN))
        leaf(k,'GROWTH',[898,902],'QUESTION');leaf(k,'END_GROWTH',[912,916],'QUESTION')
        # Do not put Void's long answer in everyone else's mouth.
        price={'VOID':prose(1076,1080),'SLAN':tr('Вернуться ты сможешь. Вернуть себе всё, что было до этого места, — уже нет. Тело и память удержат что-нибудь из пережитого.'),
               'UBIK':tr('Уйдёшь человеком. Только не жди, что память, слух, зрение и спокойствие окажутся точно такими, какими ты их помнишь.'),
               'CONRAD':tr('Слух. Зрение. Твёрдость рук. Память и покой. Что-то из этого изменится.'),'FEMTO':tr('Отказ сохранит человеческую природу. Он не отменит пережитого.')}
        topic(k,'PRICE',price[k],[response(k,'Что именно со мной случится?','EXACT_PRICE',OPEN),back(k,'QUESTION')],[put('price_heard')])
        topic(k,'EXACT_PRICE',tr('Чувства могут притупиться. Руки — дрожать. Воспоминания и тревога — лишать покоя. Какие следы ты унесёшь, заранее не узнать.'),[back(k,'PRICE')])
        sacrifice={'VOID':prose(928,932),'SLAN':tr('Здесь ты отдаёшь прежнюю плоть. О чужой жизни тебя не спрашивают.'),'UBIK':tr('Мы говорим о твоей жизни. Не стоит торопиться подставлять вместо неё чью-то другую.'),'CONRAD':tr('Твоё тело. Твоя перемена.'),'FEMTO':tr('От тебя требуется собственное решение.')}
        topic(k,'SACRIFICE',sacrifice[k],[back(k,'QUESTION')])
        topic(k,'CONFIRM',prose(dict(zip(KINDS,[950,953,957,961,964]))[k]),[
            response(k,'Я принимаю дар. Понимаю, что прежнее тело уже не вернуть.','TALK_DONE',OPEN,[put('choice_confirmed'),run(OLD+'CHOOSE_GIFT')]),
            response(k,'Прежде я хочу ещё кое-что спросить.','QUESTION',OPEN),response(k,'Я ещё не готов.','ROOT',OPEN)])
        first_refusal=tr(prose(dict(zip(KINDS,[1003,1007,1011,1014,1017]))[k])+'\n\n'+prose(1023,1025,1027,1029,1031))
        topic(k,'REFUSE',choose(eq('u_berserk_apostol_refusal_seen'),prose(1109,1113),first_refusal),[
            response(k,'Вы показываете только то, что вам удобно.','MEMORY_BIASED',OPEN),
            response(k,'Это всё ещё моя жизнь.','MEMORY_OWN',OPEN),response(k,'Я не хочу возвращаться к этому.','MEMORY_ESCAPE',OPEN),
            response(k,'Хватит. Уберите это.','MEMORY_STOP',OPEN)], [run(OLD+'REFUSAL_MEMORY')])
        for s,ids in [('MEMORY_BIASED',[1047,1051]),('MEMORY_OWN',[1058]),('MEMORY_ESCAPE',[1066]),('MEMORY_STOP',[1072])]:
            # The memory is narrated; a later response names its actual speaker.
            speaker={'MEMORY_BIASED':'Убик: ','MEMORY_OWN':'Войд: ','MEMORY_ESCAPE':'Слан: ','MEMORY_STOP':''}[s]
            topic(k,s,tr('&'+speaker+prose(*ids)),[response(k,'Я хочу знать, что ждёт меня снаружи.','LAST_CHOICE',OPEN)])
        topic(k,'LAST_CHOICE',tr('&Войд: '+prose(1076,1080)+'\n\nКонрад: '+prose(1084)),[
            response(k,'Что именно со мной случится?','LAST_PRICE',OPEN),
            response(k,'Я отказываюсь. Верните меня человеком.','TALK_DONE',both(OPEN,eq('u_berserk_apostol_refusal_seen')),[run(OLD+'CHOOSE_HUMAN')]),
            response(k,'Я изменил решение. Я хочу принять дар.','CONFIRM',OPEN),
            response(k,'Мне нужно подумать.','PAUSE',OPEN),response(k,'У меня остались вопросы.','ROOT',OPEN)])
        topic(k,'LAST_PRICE',tr('&Конрад: '+prose(1090,1094)),[response(k,'Я понял.','LAST_CHOICE',OPEN)],[put('price_heard')])
    # Old public entry points remain valid for saved items and final-circle use.
    for alias,s in [('OFFER','ROOT'),('PRICE','QUESTION'),('MEMORY','REFUSE'),('LAST_CHOICE','LAST_CHOICE')]:
        TOPICS[T+alias]={**copy.deepcopy(TOPICS[tid('VOID',s)]),'id':T+alias}
    # Reference builder subsequently supplies the legacy read-only progress page.
    topic('PROGRESS','ROOT',tr('О принятом и пережитом можно прочесть в дорожном справочнике.'),[response('PROGRESS','Закрыть.','TALK_DONE')])

def append_effect(obj, effect):
    if not isinstance(obj['effect'],list):obj['effect']=[obj['effect']]
    if effect not in obj['effect']:obj['effect'].append(effect)

def mechanics():
    ceremony=read('effects/apostol_ceremony_eocs.json');by=index(ceremony)
    by[OLD+'CHOOSE_GIFT']['condition']=both(OPEN,state('choice_confirmed'))
    # Legacy CHOOSE_SLAN remains an alias to the single shared five-way draw.
    by[OLD+'CHOOSE_HUMAN']['condition']=both(OPEN,eq('u_berserk_apostol_refusal_seen'))
    ret=by[OLD+'RETURN']
    ret['condition']['and'][-1]=either(*[eq('u_berserk_apostol_outcome',n) for n in [1,2,3,4]])
    by[OLD+'RETURN_COMMIT']['effect']=[
        math('u_berserk_apostol_return_state = 2'),math('u_berserk_eclipse_trial_active = 0'),math('berserk_eclipse_happened = 1'),
        {'if':eq('u_berserk_apostol_outcome',4),'then':run('VICTORY_COMMIT'),
         'else':{'if':eq('u_berserk_apostol_outcome',3),'then':run('ESCAPE_COMMIT'),
                 'else':[{'if':neg(WON),'then':math('berserk_eclipse_era = 1')},run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL'),
                         {'if':eq('u_berserk_apostol_outcome',1),'then':[run(OLD+'GIFT_BEGIN'),say('Вы снова стоите под знакомым небом. Внутри шевелится нечто чужое. Принятое не осталось за порогом.', 'warning', True)],
                          'else':[run(OLD+'APPLY_REFUSAL_SCAR'),say('Вы вернулись человеком. Но тишина не приносит покоя: что-то из пережитого осталось с вами.', 'warning', True)]},
                         run(OLD+'CONTINUATION_BEGIN')]}},run('EOC_BERSERK_REF_SYNC')]
    circle=by[OLD+'CIRCLE_USE']
    circle['effect']=[run(OLD+'HAND_ENSURE'),{'if':ATTACKED,'then':say('Впереди нет выхода. Разорванный проход остался там, где вы вошли в это поле.','warning'),
        'else':{'if':eq('u_berserk_apostol_return_state',1),'then':run(OLD+'RETURN'),
                'else':{'if':OPEN,'then':{'open_dialogue':{'topic':T+'OFFER'}},'else':say('Круг молчит.','neutral')}}}]
    # Capture actual arrival for old generated maps; no map repaint on migration.
    arrived=by[OLD+'ARRIVE']['effect'][2]['then']
    arrival_capture={'u_location_variable':{'u_val':'berserk_hand33_arrival'}}
    if arrival_capture not in arrived:arrived.insert(0,arrival_capture)
    write('effects/apostol_ceremony_eocs.json',ceremony)

    hands=read('effects/apostol_godhand_eocs.json');hb=index(hands)
    active=both('u_is_avatar',eq('u_berserk_eclipse_route',2),eq('u_berserk_eclipse_trial_active'),eq('u_berserk_apostol_return_state',0))
    hb[OLD+'HAND_RAGE']['condition']=both(active,neg(ATTACKED),{'u_at_om_location':'berserk_eclipse_apostol_ceremony'})
    hb[OLD+'HAND_RAGE']['effect']=[math('u_berserk_apostol_godhand_attacked = 1'),
        {'u_run_monster_eocs':[OLD+'HAND_ANGER'],'mtype_ids':['mon_berserk_godhand_'+k.lower() for k in KINDS],'monster_range':80},
        run('COMBAT_LINES')]
    # Personal attacks and attacks by allied NPCs both close negotiations.
    for suffix in ['ATTACK_CHARACTER_MELEE_ATTACKS_MONSTER','ATTACK_CHARACTER_RANGED_ATTACKS_MONSTER']:
        obj=hb[OLD+'HAND_'+suffix]
        obj['condition']=both(either('u_is_avatar','u_following','u_friend'),'has_beta',{'npc_has_species':'BERSERK_GODHAND'})
        obj['effect']={'run_eocs':OLD+'HAND_RAGE','alpha_talker':'avatar'}
    hb[OLD+'HAND_DAMAGE']['condition']=both('u_is_monster',{'u_has_species':'BERSERK_GODHAND'},'has_beta',either('npc_is_avatar','npc_following','npc_friend'))
    hb[OLD+'HAND_DAMAGE']['effect']={'run_eocs':OLD+'HAND_RAGE','alpha_talker':'avatar','beta_talker':'u'}
    for k in KINDS:
        # Native 0.I monster::die passes killer as alpha, dying monster as beta
        # (including a null killer). Capture the victim before switching alpha.
        hb[OLD+'HAND_'+k+'_DIED']['condition']=both('has_beta','npc_is_monster',{'npc_has_species':'BERSERK_GODHAND'})
        hb[OLD+'HAND_'+k+'_DIED']['effect']=[{'npc_location_variable':{'context_val':'hand33_dead_point'}},
            {'run_eocs':P+k+'_DEATH_RECORD','alpha_talker':'avatar'}]
        EOCS.append(eoc(P+k+'_DEATH_RECORD',[put(k.lower()+'_dead'),run('CHECK_VICTORY')],
            both(active,ATTACKED,{'overmap_at_point':'berserk_eclipse_apostol_ceremony','point':{'context_val':'hand33_dead_point'}})))
    append_effect(hb[OLD+'HAND_ENSURE'],run('INTRO'))
    write('effects/apostol_godhand_eocs.json',hands)
    intro=tr(prose(61,63)+'\n\nТяжёлый пульс отдаётся в ладони, хотя камня в ней больше нет.\n\nВойд: «'+prose(69)+'»')
    EOCS.append(eoc(P+'INTRO',[say(intro,'warning',True),put('scene_seen')],both(OPEN,neg(state('scene_seen')))))
    warning='Пять голосов умолкают. У начала тропы разрывается сомкнувшийся проход.'
    rebukes={'VOID':'Войд: '+prose(1152),'SLAN':'Слан: '+prose(1158),
             'UBIK':'Убик: '+tr('Теперь посмотрим, сумеешь ли ты добраться до дороги назад.'),
             'CONRAD':prose(1169),'FEMTO':'Фемто: '+prose(1175)}
    combat=say(warning,'bad')
    for k in reversed(KINDS):
        combat={'if':both('has_beta','npc_is_monster',math("n_monsters_nearby('mon_berserk_godhand_"+k.lower()+"', 'radius': 0, 'attitude': 'both') > 0")),
                'then':say(rebukes[k]+'\n\n'+warning,'bad'),'else':combat}
    EOCS.append(eoc(P+'COMBAT_LINES',combat,both(active,ATTACKED)))
    EOCS.append(eoc(P+'CHECK_VICTORY',[
        math('berserk_godhand_defeated = 1'),math('berserk_eclipse_era = 0'),put('victory_earned'),
        run('VICTORY_REWARD'),
        say('Пятая фигура распадается. Давление исчезает. За мёртвым полем снова чувствуется мир живых; путь назад открыт у начала тропы.','good',True)],
        both(active,ATTACKED,flags_dead(),neg(WON))))
    EOCS.append(eoc(P+'START_AVAILABLE',[],both(active,ATTACKED,{'u_at_om_location':'berserk_eclipse_apostol_arrival'})))
    EOCS.append(eoc(P+'START_USE',[
        {'if':eq('u_berserk_apostol_return_state',1),'then':run(OLD+'RETURN'),
         'else':{'if':test(P+'START_AVAILABLE'),'then':[
             {'if':WON,'then':math('u_berserk_apostol_outcome = 4'),'else':math('u_berserk_apostol_outcome = 3')},
             math('u_berserk_apostol_return_state = 1'),run(OLD+'RETURN')],
             'else':say('Живая ткань сомкнулась. Проход не отвечает.','neutral')}}],
        both('u_is_avatar',{'u_at_om_location':'berserk_eclipse_apostol_arrival'},eq('u_berserk_eclipse_route',2),ATTACKED,
             either(eq('u_berserk_apostol_return_state',0),eq('u_berserk_apostol_return_state',1)))))
    # Existing maps already contain this scar; adding an examine action needs no
    # furniture replacement and preserves all dropped items and player changes.
    furniture=read('furniture/eclipse_trial.json');scar=index(furniture)['f_berserk_eclipse_arrival_scar']
    scar['description']=tr('Рубец там, где сомкнулся проход. Живая ткань подрагивает под ногами.')
    scar['examine_action']={'type':'effect_on_condition','effect_on_conditions':[P+'START_USE']}
    write('furniture/eclipse_trial.json',furniture)
    EOCS.append(eoc(P+'ESCAPE_COMMIT',[
        math('u_berserk_eclipse_route = 1'),math('u_berserk_eclipse_rescue_state = 1'),
        {'copy_var':{'u_val':'berserk_apostol_origin'},'target_var':{'u_val':'berserk_eclipse_return_origin'}},
        say('Вы вырываетесь из прохода. Боль прожигает кожу. Прежде чем тьма успевает сомкнуться снова, между вами и ней возникает всадник в черепообразном шлеме.','warning',True),
        run('EOC_BERSERK_ECLIPSE_RESCUE_STABILIZE'),run('EOC_BERSERK_ECLIPSE_RESCUE_RETURN')],
        both('u_is_avatar',eq('u_berserk_apostol_outcome',3),eq('u_berserk_apostol_return_state',2))))
    EOCS.append(eoc(P+'VICTORY_COMMIT',[
        math('berserk_eclipse_era = 0'),math('berserk_godhand_defeated = 1'),
        run('VICTORY_REWARD'),
        say('Нить оборвалась. Вы стоите под небом прежнего мира. Из прохода за вами никто не вышел.','good',True),
        run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL')],
        both('u_is_avatar',eq('u_berserk_apostol_outcome',4),eq('u_berserk_apostol_return_state',2),state('victory_earned'),flags_dead())))
    EOCS.append(eoc(P+'VICTORY_REWARD',[
        {'if':neg({'u_has_trait':'BERSERK_THREADBREAKER'}),'then':{'u_add_trait':'BERSERK_THREADBREAKER'}},put('reward_given')],
        both('u_is_avatar',state('victory_earned'),flags_dead(),neg(state('reward_given')))))
    write('mutations/godhand_victory.json',[{
        'type':'mutation','id':'BERSERK_THREADBREAKER','name':{'str':tr('Разорвавший нить')},
        'description':tr('Вы пережили невозможную битву и сохранили человеческую природу. Сила +8, ловкость, интеллект и восприятие +4, скорость +25; запас здоровья и выносливости увеличен наполовину. Этот след победы останется с вами.'),
        'points':0,'valid':False,'starting_trait':False,'purifiable':False,
        'enchantments':[{'condition':'ALWAYS','values':[
            {'value':'STRENGTH','add':8},{'value':'DEXTERITY','add':4},{'value':'INTELLIGENCE','add':4},{'value':'PERCEPTION','add':4},
            {'value':'SPEED','add':25},{'value':'MAX_HP','multiply':0.5},{'value':'MAX_STAMINA','multiply':0.5}]}]}])
    # Confirmed personal laboratory records, not inventory or normal Griffith.
    EOCS.append(eoc(P+'FEMTO_PROJECTION_KILLED',[],eq('u_berserk_griffith_projection_defeated')))
    EOCS.append(eoc(P+'FEMTO_PROJECTION_SEEN',[],either(test(P+'FEMTO_PROJECTION_KILLED'),state('femto_projection_seen'))))
    EOCS.append(eoc(P+'OBSERVE_PROJECTION',{'u_run_monster_eocs':[P+'PROJECTION_LOCATION'],
        'mtype_ids':['mon_berserk_projection_griffith'],'monster_range':40},
        both('u_is_avatar',neg(state('femto_projection_seen'))),eoc_type='EVENT',required_event='avatar_moves'))
    EOCS.append(eoc(P+'PROJECTION_LOCATION',[{'u_location_variable':{'context_val':'hand33_projection_point'}},
        {'run_eocs':P+'PROJECTION_OBSERVED','alpha_talker':'avatar'}],'u_is_monster'))
    EOCS.append(eoc(P+'PROJECTION_OBSERVED',put('femto_projection_seen'),
        both('u_is_avatar',{'u_can_see_location':{'context_val':'hand33_projection_point'}})))
    world_rules()

def world_rules():
    """Separate a historical fact from the world invasion toggle.

    Victory ends this alternate chapter. It does not erase old map monsters,
    fabricate named-apostle deaths, or start human hunts without the rescue.
    """
    def protect_writers(node):
        if isinstance(node,list):
            for child in node:protect_writers(child)
        elif isinstance(node,dict):
            if node.get('if')==neg(WON) and node.get('then')==math('berserk_eclipse_era = 1'):
                return
            if node.get('math')==['berserk_eclipse_era = 1']:
                node.clear();node.update({'if':neg(WON),'then':math('berserk_eclipse_era = 1')})
                return
            for child in node.values():protect_writers(child)
    def has_guard(node):
        return any(x==neg(WON) for x in walk(node))
    for file in sorted((MOD/'effects').glob('*.json')):
        if file.name=='godhand_dialogue_33_eocs.json':continue
        data=json.loads(file.read_text());before=copy.deepcopy(data)
        for obj in data:
            if obj.get('id')=='EOC_BERSERK_FORGE_AFTER_ECLIPSE':
                proof=eq('berserk_eclipse_happened')
                if proof not in obj['condition'].get('or',[]):obj['condition']=either(obj['condition'],proof)
            # Keep existing era readers, but stop every stale writer/migrator
            # from re-enabling invasion after the confirmed exceptional victory.
            protect_writers(obj)
            if file.name=='eclipse_era_eocs.json' and obj.get('id') in [
                'EOC_BERSERK_ECLIPSE_ERA_ENTER_OMT','EOC_BERSERK_ECLIPSE_ERA_TARGET_ONCE']:
                guard=neg(WON);condition=obj.get('condition')
                if condition is None:obj['condition']=guard
                elif not has_guard(condition):obj['condition']=both(condition,guard)
            if file.name=='eclipse_brand_eocs.json' and obj.get('id')=='EOC_BERSERK_BRAND_NIGHT_HUNT':
                guard=neg(WON)
                if not has_guard(obj['condition']):obj['condition']=both(obj['condition'],guard)
            if file.name=='shadow_illusion_eoc.json' and obj.get('id')=='EOC_BERSERK_SPAWN_ONE_SHADOW':
                guard=neg(WON)
                if not has_guard(obj.get('condition',{})):
                    obj['condition']=both(obj['condition'],guard) if 'condition' in obj else both('u_is_avatar',guard)
        if data!=before:write('effects/'+file.name,data)

def main():
    roots();branches();common_choices();mechanics()
    write('dialogue/apostol_ceremony.json',list(TOPICS.values()))
    write('effects/godhand_dialogue_33_eocs.json',EOCS+list(HELPERS.values()))
    _localization()
    (ROOT/'docs/dialogue_sources/godhand-bindings-33.json').write_text(json.dumps({
        'source':'godhand-2026-10-23.json','used_paragraphs':sorted(USED),'topics':list(TOPICS),
        'adaptations':['Consumed Behelit is not held in the palm.','Five mild scars; no full blindness/deafness.',
                       'Shared memory once; source voices explicitly named in narrated group responses.',
                       'Combat escape at arrival scar; ordinary one-time rescue and wounds.',
                       'All-five actual deaths: human reward, world era remains off; existing world actors not erased.']},ensure_ascii=False,indent=2)+'\n')
    print('God Hand:',len(TOPICS),'topics;',len(USED),'source paragraphs; escape and exceptional victory.')

if __name__=='__main__':main()
