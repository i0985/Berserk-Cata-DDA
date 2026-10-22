#!/usr/bin/env python3
"""Approved Flora manuscript, with owner's superseding siege/pact decisions."""
import copy
import hashlib
import json
import re
import subprocess
from recover_apostol_33 import ROOT, MOD, read, write, index, eoc, walk
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq, gt
from recovery_33_translations import source as po_source

SOURCE = json.loads((ROOT/'docs/dialogue_sources/flora-2026-10-22.json').read_text())['paragraphs']
P = 'TALK_BERSERK_FLORA_'
E = 'EOC_BERSERK_FLORA33_'
TOPICS = {}; HELPERS = {}; STRINGS = {}; EOCS = []
G = test('FORGE_GUTS'); BRAND = {'u_has_bionics':'bio_berserk_brand_of_sacrifice'}
PEACE = both(math('berserk_flora_stage <= 1'), math('berserk_flora_siege_state <= 1'))
ATTACK = both(math('berserk_flora_siege_state >= 2'), math('berserk_flora_siege_state <= 4'))
DEMON = test('APOSTOL_HUMAN_EQUIPMENT_ALLOWED')
FULL = test('FLORA_FULL_SET')
LATE = test(E+'LATE')

def tr(s): STRINGS[s]=s; return s
def s(i):
    text = SOURCE[str(i)].strip().strip('*').strip()
    text = re.sub(r'^(?:Флора|Игрок|Гатс):\s*', '', text).strip()
    return text.strip('«»')
def prose(*ids): return tr('\n\n'.join(s(i) for i in ids))
def tid(x): return x if x.startswith('TALK_') else P+x
def run(x): return {'run_eocs':x if x.startswith('EOC_') else E+x}
def v(x,n=1): return eq('u_berserk_flora33_'+x,n)
def setv(x,n=1): return math('u_berserk_flora33_'+x+' = '+str(n))
def add(obj, xs):
    old=obj.setdefault('effect',[])
    if not isinstance(old,list):old=obj['effect']=[old]
    for x in xs:
        if x not in old:old.append(x)
def choose(c,a,b):
    if isinstance(c,str) or any(k in c for k in ['and','or','not']):
        name=E+'P_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[name]=eoc(name,[],c);c=test(name)
    return {**c,'yes':a,'no':b}
def response(text,target='',condition=None,effect=None):
    obj={'text':tr(text),'topic':tid(target) if target else 'TALK_BERSERK_FLORA'}
    if condition is not None:obj['condition']=condition
    if effect is not None:obj['effect']=effect
    return obj
def back(target=''):return response('Я хотел спросить о другом.',target)
def done():return response('Мне нужно идти.','TALK_DONE')
def topic(name,text,responses=None,heard=None,effect=None):
    obj={'type':'talk_topic','id':tid(name),'dynamic_line':text,'responses':responses or [back()]}
    actions=([setv('heard_'+heard)] if heard else [])+(effect or [])
    if actions:obj['speaker_effect']={'effect':actions}
    TOPICS[obj['id']]=obj;return obj
def leaf(name,ids,parent='',heard=None):return topic(name,prose(*ids),[back(parent)],heard)

def introductions():
    greeting=choose(v('greeted_brand'),prose(88),choose(BRAND,prose(86),choose(eq('u_berserk_flora_armor_resolved'),prose(87),prose(88))))
    greeting=choose(test(E+'HURT'),prose(85),greeting)
    topic('ENTER',choose(eq('u_berserk_flora_met'),{'concatenate':[prose(83),'\n',greeting]},prose(27)),[
        response('Меня зовут Гатс. Мне сказали, что ты можешь помочь.','INTRO_GUTS',both(neg(eq('u_berserk_flora_met')),G)),
        response('Я не ожидал найти здесь жилой дом.','INTRO_STRANGER',both(neg(eq('u_berserk_flora_met')),neg(G))),
        response('Мне сказали, что здесь живёт ведьма по имени Флора.','INTRO_SOURCE',both(neg(eq('u_berserk_flora_met')),neg(G),eq('u_berserk_journal_knows_flora'))),
        response('Я хотел поговорить.','TALK_BERSERK_FLORA',eq('u_berserk_flora_met')),
        done()],effect=[run('MIGRATE'),run('EOC_BERSERK_FLORA_REGISTER_HERE')])
    met=[run('EOC_BERSERK_FLORA_DIALOGUE_BEGIN'),{'if':BRAND,'then':setv('greeted_brand')},run('EOC_BERSERK_REF_SYNC')]
    topic('INTRO_STRANGER',prose(32),[
        response('Искал укрытие.','INTRO_SHELTER'),response('Увидел дерево и решил подойти.','INTRO_TREE'),
        response('Мне нужна помощь.','INTRO_HELP'),response('Ты живёшь здесь одна?','INTRO_ALONE')],effect=met)
    for n,i in [('SHELTER',40),('TREE',42),('HELP',44),('ALONE',46)]:leaf('INTRO_'+n,[i])
    topic('INTRO_GUTS',prose(69),[response('Привычка.','INTRO_HABIT')],effect=met)
    leaf('INTRO_HABIT',[71])
    topic('INTRO_SOURCE',prose(53),[
        response('Я нашёл запись с твоим именем.','INTRO_RECORD',either(eq('u_berserk_flora_late_clue_given'),eq('u_berserk_ref_flora_named_source'))),
        # The current Knight deliberately gives no early Flora route.
        response('Мне рассказали о тебе в дороге.','INTRO_RUMOR'),done()],effect=met)
    leaf('INTRO_RECORD',[62])['speaker_effect']={'effect':[setv('source',1)]}
    leaf('INTRO_RUMOR',[64])['speaker_effect']={'effect':[setv('source',2)]}

def root():
    ready=both(LATE,PEACE,neg(v('queued')),either(FULL,eq('u_berserk_flora_armor_resolved'),v('declined'),neg(DEMON)))
    responses=[
        response('Я хочу спросить о Клейме.','BRAND',both(PEACE,BRAND)),
        response('Что за существа приходят из другого мира?','WORLD',PEACE),
        response('Поговорим о доспехе.','ARMOR',both(PEACE,test(E+'ARMOR_KNOWN'))),
        response('Мне нужна помощь.','AID',PEACE),response('Расскажи об этом доме и дереве.','HOME',PEACE),
        response('Я узнал об одной опасности…','DANGERS',both(PEACE,test(E+'KNOWN_DANGER'))),
        response('Можно спросить о тебе?','PERSONAL',PEACE),
        response('Со мной произошло нечто странное.','REFUSED',both(PEACE,eq('u_berserk_apostol_outcome',2),eq('u_berserk_apostol_return_state',2))),
        response('Я закончил приготовления. Давай продолжим.','TALK_DONE',ready,[run('QUEUE')]),
        response('Что происходит?','SIEGE_WHAT',ATTACK),response('Куда идти?','SIEGE_WAY',ATTACK),
        response('Я останусь и буду сражаться.','SIEGE_FIGHT',ATTACK),response('А ты?','SIEGE_FLORA',ATTACK),
        response('Я могу что-нибудь спасти?','SIEGE_SAVE',both(ATTACK,test(E+'MANUSCRIPT_REACHABLE'))),done()]
    text=choose(ATTACK,prose(1013),choose(both(neg(DEMON),neg(v('demon_noticed'))),prose(483),
        choose(neg(LATE),prose(79),tr('О чём ты хотел поговорить?'))))
    notice=both(PEACE,neg(DEMON),neg(v('demon_noticed')))
    for r in responses:
        if r['topic']!='TALK_DONE':r['condition']=both(r.get('condition','u_is_avatar'),neg(notice))
    responses=[response('Да.','APOSTOL_YES',notice),response('Я сделал это, чтобы выжить.','APOSTOL_SURVIVE',notice),response('Это моё дело.','APOSTOL_PRIVATE',notice)]+responses
    topic('TALK_BERSERK_FLORA',text,responses)
    # Acknowledgement of the accepted power does not unlock armor through lying.
    topic('APOSTOL_NOTICE',prose(483),[
        response('Да.','APOSTOL_YES'),response('Я сделал это, чтобы выжить.','APOSTOL_SURVIVE'),response('Это моё дело.','APOSTOL_PRIVATE')],effect=[setv('demon_noticed')])
    for n,i in [('YES',495),('SURVIVE',500),('PRIVATE',505)]:
        leaf('APOSTOL_'+n,[i],heard='demon')['speaker_effect']['effect'] += [setv('demon_noticed'),math('u_berserk_ref_flora_demon_counsel = 1')]
    TOPICS['TALK_BERSERK_FLORA']['responses'].insert(0,response('Ты чувствуешь то, что со мной произошло?','APOSTOL_NOTICE',both(PEACE,neg(DEMON),v('demon_noticed'))))

def brand_world():
    topic('BRAND',choose(v('heard_brand'),tr('Что тебя беспокоит в Клейме?'),prose(128)),[
        response('Поэтому они находят меня?','BRAND_FIND'),response('Ты можешь его снять?','BRAND_REMOVE'),
        response('Почему рядом с одними существами боль сильнее?','BRAND_PAIN'),response('Почему здесь спокойнее?','WARD'),
        response('У меня уже есть защитный знак.','WARD_OWNED',eq('u_berserk_refuge_ready')),
        response('Закрытый прорыв ничего не изменил? Клеймо осталось.','BRAND_BREACH',eq('u_berserk_breach_sealed')),back()],heard='brand')
    leaf('BRAND_FIND',[134],'BRAND')
    topic('BRAND_REMOVE',prose(141),[response('Значит, это навсегда?','BRAND_FOREVER'),response('Хотя бы боль можно уменьшить?','BRAND_EASE'),back('BRAND')])
    leaf('BRAND_FOREVER',[153],'BRAND');leaf('BRAND_EASE',[158],'BRAND')
    topic('BRAND_PAIN',prose(165),[response('Значит, по боли можно понять, насколько враг силён?','BRAND_MEASURE'),back('BRAND')],heard='brand_pain')
    leaf('BRAND_MEASURE',[171],'BRAND')
    topic('WARD',prose(178),[response('Здесь мне ничего не угрожает?','WARD_SAFE'),response('Как подготовить защиту в другом месте?','WARD_BUILD'),back('BRAND')])
    leaf('WARD_SAFE',[184],'BRAND')
    topic('WARD_BUILD',tr('Знак из камня и костей затрудняет путь существам, которых зовёт Клеймо. Держи его рядом с местом отдыха. Он не прогонит тех, кто уже пришёл, и не заменит пути отхода.'),[back('BRAND')],effect=[math('u_berserk_ref_ward_recipe_explained = 1')])
    topic('WARD_OWNED',prose(191),[response('Этого достаточно?','WARD_LIMITS'),back('BRAND')]);leaf('WARD_LIMITS',[197],'BRAND')
    topic('BRAND_BREACH',prose(204),[response('А для меня?','BRAND_BREACH_SELF'),back('BRAND')]);leaf('BRAND_BREACH_SELF',[210],'BRAND')
    topic('WORLD',prose(221),[response('Другой мир, спрятанный внутри нашего?','WORLD_INSIDE'),response('Все его обитатели опасны?','WORLD_PEOPLE'),response('Почему теперь всё смешалось?','WORLD_COLLISION'),response('Можно закрыть все разломы?','WORLD_WOUNDS'),back()],heard='world')
    leaf('WORLD_INSIDE',[227],'WORLD');leaf('WORLD_PEOPLE',[234],'WORLD')
    topic('WORLD_COLLISION',prose(241),[response('Ты тоже не знаешь, что будет дальше?','WORLD_UNKNOWN'),back('WORLD')],heard='world')
    leaf('WORLD_UNKNOWN',[247],'WORLD')
    topic('WORLD_WOUNDS',prose(254),[response('Тогда с чего начинать?','WORLD_START'),back('WORLD')]);leaf('WORLD_START',[260],'WORLD')

def armor():
    options=[response('Как он действует?','ARMOR_PROPERTIES'),response('Какую цену?','COST'),response('Почему ты его хранишь?','ARMOR_KEEP'),
        response('Ты позволишь мне взять его?','OFFER',both(test('FLORA_CAN_RECEIVE'),neg(test(E+'ANY_ARMOR')))),
        response('У меня уже есть доспех.','OWNED',FULL),
        response('Я потерял части, которые ты передала.','UNAVAILABLE',both(eq('berserk_flora_armor_claimed'),neg(FULL))),
        response('Поможешь собрать недостающие части?','PARTIAL',both(test('FLORA_CAN_RECEIVE'),test(E+'ANY_ARMOR'))),
        response('Можно получить доспех?','APOSTOL_ARMOR',neg(DEMON)),back()]
    topic('ARMOR',choose(v('heard_armor'),prose(346),prose(270)),options,heard='armor')
    topic('ARMOR_PROPERTIES',prose(289),[response('Он лечит раны?','ARMOR_HEAL'),back('ARMOR')],heard='armor_properties')
    leaf('ARMOR_HEAL',[295],'ARMOR')
    topic('COST',prose(302),[response('Иногда остановиться нельзя.','COST_GUTS',G),response('А если пользоваться им только в крайнем случае?','COST_LAST',neg(G)),response('Я перестану отличать своих от врагов?','COST_CONTROL'),back('ARMOR')],heard='cost')
    leaf('COST_GUTS',[308],'ARMOR');leaf('COST_LAST',[316],'ARMOR')
    topic('COST_CONTROL',prose(323),[response('Что поможет удержаться?','COST_ANCHOR'),back('ARMOR')]);leaf('COST_ANCHOR',[329],'ARMOR')
    leaf('ARMOR_KEEP',[338],'ARMOR')
    topic('OFFER',prose(358),[
        response('Чтобы выдержать то, с чем обычная броня не справляется.','ARMOR_REASON_ENDURE',effect=[setv('motive',1)]),
        response('Чтобы защитить тех, кто ещё жив.','ARMOR_REASON_PROTECT',effect=[setv('motive',2)]),
        response('Чтобы добраться до того, кто всё это сделал.','ARMOR_REASON_REVENGE',eq('u_berserk_eclipse_rescue_state',2),[setv('motive',3)]),
        response('Я ещё не решил.','ARMOR_LATER'),response('Я пойду дальше без доспеха.','ARMOR_DECLINE')])
    for n,i in [('ENDURE',371),('PROTECT',376),('REVENGE',381)]:topic('ARMOR_REASON_'+n,prose(i),[response('Я понимаю.','ARMOR_CONFIRM'),back('ARMOR')])
    leaf('ARMOR_LATER',[386],'ARMOR')
    topic('ARMOR_DECLINE',prose(918),[back()],effect=[setv('declined')])
    topic('ARMOR_CONFIRM',prose(395),[
        # The owner's final instruction overrides the manuscript's separate
        # readiness confirmation for a NEW recipient. Close the clock-paused
        # conversation and let the three-second in-world timer run.
        response('Я готов принять его.','TALK_DONE',test('FLORA_CAN_RECEIVE'),[run('EOC_BERSERK_FLORA_GIVE_ARMOR')]),
        response('Сначала ещё один вопрос.','ARMOR'),response('Я вернусь к этому позже.','TALK_BERSERK_FLORA')])
    topic('PARTIAL',prose(409,414),[response('Я готов принять недостающие части.','TALK_DONE',test('FLORA_CAN_RECEIVE'),[run('EOC_BERSERK_FLORA_GIVE_ARMOR')]),back('ARMOR')])
    topic('OWNED',choose(neg(DEMON),prose(543),prose(423)),[
        response('Что я должен замечать в себе?','COST_CONTROL'),response('Что делать после тяжёлого боя?','ARMOR_RECOVER'),
        response('Я уже испытал его.','ARMOR_USED',v('used_in_combat')),back('ARMOR')])
    owner=TOPICS[tid('OWNED')]
    reminder=choose(v('motive',1),prose(371),choose(v('motive',2),prose(376),prose(381)))
    owner['dynamic_line']={'concatenate':[owner['dynamic_line'],choose(both(DEMON,neg(v('motive_recalled')),gt('u_berserk_flora33_motive')),'\n\n',''),choose(both(DEMON,neg(v('motive_recalled')),gt('u_berserk_flora33_motive')),reminder,'')]}
    owner['speaker_effect']={'effect':[setv('motive_recalled')]}
    leaf('ARMOR_RECOVER',[295,302],'ARMOR')
    topic('ARMOR_USED',prose(436),[response('Закончить.','ARMOR_STOP'),response('Я сохранял контроль.','ARMOR_CONTROL'),response('Не хочу об этом говорить.','ARMOR_SILENCE')])
    for n,i in [('STOP',448),('CONTROL',453),('SILENCE',458)]:leaf('ARMOR_'+n,[i],'ARMOR')
    leaf('UNAVAILABLE',[465],'ARMOR')
    topic('APOSTOL_ARMOR',prose(512),[
        response('Ты считаешь меня чудовищем?','APOSTOL_MONSTER'),response('Но я всё ещё могу защищать людей.','APOSTOL_PROTECT'),response('Тогда мне здесь нечего делать?','APOSTOL_DOOR'),back('ARMOR')],heard='armor_refused')
    for n,i in [('MONSTER',524),('PROTECT',529),('DOOR',534)]:leaf('APOSTOL_'+n,[i],'ARMOR')
    TOPICS[tid('APOSTOL_ARMOR')]['speaker_effect']['effect'].append(math('u_berserk_ref_flora_armor_refused = 1'))
    topic('REFUSED',prose(555),[response('Ты можешь это исправить?','REFUSED_HELP'),back()]);leaf('REFUSED_HELP',[561])

def home_personal():
    topic('AID',tr('Расскажи, какая помощь тебе нужна.'),[
        response('Есть ли у тебя что-то, что поможет против апостолов?','ARMOR',both(LATE,neg(test(E+'ARMOR_KNOWN')))),
        response('Можно взять припасы в дорогу?','HELP',neg(eq('berserk_flora_aid_authorized'))),
        response('О приготовленных припасах.','HELP_TAKEN',eq('berserk_flora_aid_authorized')),
        response('Что мне делать дальше?','NEXT'),back()])
    topic('HELP',tr('Для тебя приготовлены свёртки в кухне, мастерской и южной галерее. Возьми их, если они помогут в дороге. Остальные вещи оставь на своих местах.'),[
        response('Спасибо. Возьму только приготовленное.','TALK_BERSERK_FLORA',effect=[run('EOC_BERSERK_FLORA_ALLOW_AID')]),back('AID')])
    leaf('HELP_TAKEN',[465],'AID')
    TOPICS[tid('HELP_TAKEN')]['dynamic_line']=tr('Ты можешь взять те свёртки, что я приготовила. Новых припасов на их месте не появится — распоряжайся ими бережно.')
    topic('HOME',prose(573),[response('Оно защищает тебя?','TREE'),response('Это обычное дерево?','TREE_OTHER'),response('Здесь всё выглядит слишком обычным.','HOME_ORDINARY'),response('Зачем тебе столько книг?','BOOKS'),response('Ты давно здесь живёшь?','HOME_AGE'),back()])
    leaf('TREE',[579],'HOME');topic('TREE_OTHER',prose(586),[response('С ним можно говорить?','TREE_SPEAK'),back('HOME')]);leaf('TREE_SPEAK',[592],'HOME')
    topic('HOME_ORDINARY',prose(600),[response('Наверное.','HOME_POTS'),response('Просто снаружи всё иначе.','HOME_OUTSIDE'),response('Мне здесь нравится.','HOME_LIKE')])
    for n,i in [('POTS',612),('OUTSIDE',617),('LIKE',622)]:leaf('HOME_'+n,[i],'HOME')
    leaf('BOOKS',[629],'HOME');topic('HOME_AGE',prose(636),[response('Ты уходишь от ответа.','HOME_AGE_MORE'),back('HOME')]);leaf('HOME_AGE_MORE',[643],'HOME')
    topic('PERSONAL',tr('Спрашивай.'),[response('Ты меня не боишься?','PERSONAL_FEAR'),response('Почему ты помогаешь незнакомым людям?','PERSONAL_HELP'),response('Ты знаешь Рыцаря-Черепа?','PERSONAL_KNIGHT',eq('u_berserk_eclipse_rescue_state',2)),response('Мне некогда сидеть у очага.','PERSONAL_GUTS',G),response('Я не понимаю, за что мне всё это.','PERSONAL_STRANGER',both(neg(G),either(BRAND,eq('u_berserk_apostol_return_state',2)))),response('Если я уйду, я смогу вернуться?','PERSONAL_RETURN'),back()])
    topic('PERSONAL_FEAR',choose(neg(DEMON),prose(765,768,771),prose(756,759)),[back('PERSONAL')])
    leaf('PERSONAL_HELP',[779,782],'PERSONAL')
    topic('PERSONAL_KNIGHT',prose(791),[response('Ему можно доверять?','KNIGHT_TRUST'),response('Он всегда так разговаривает?','KNIGHT_SPEECH'),response('Кем он был?','KNIGHT_PAST'),back('PERSONAL')])
    leaf('KNIGHT_TRUST',[797,800],'PERSONAL');leaf('KNIGHT_SPEECH',[806],'PERSONAL')
    topic('KNIGHT_PAST',choose(eq('u_berserk_knight_farewell_confirmed'),tr('Это его история. Не моя. Когда-нибудь он сам решит, кому её рассказать. Я пересказывать не буду.'),prose(812)),[back('PERSONAL')])
    topic('PERSONAL_GUTS',prose(823,826),[response('Недолго.','PERSONAL_GUTS_MORE'),back('PERSONAL')]);leaf('PERSONAL_GUTS_MORE',[834],'PERSONAL')
    leaf('PERSONAL_STRANGER',[845,848],'PERSONAL');leaf('PERSONAL_RETURN',[856],'PERSONAL')

def dangers():
    rs=[]
    for key,ru in [('count','Графе'),('wyald','Уайлде'),('rosine','Розине'),('grunbeld','Грюнбельде')]:
        target='KNOWN_'+key.upper()
        rs.append(response('Я кое-что знаю о '+ru+'.',target,eq('u_berserk_journal_knows_'+key)))
        # Remove the draft's accidental English word, without inventing facts.
        topic(target,tr(s(663).replace('что land... что земля','что земля')+'\n\n'+s(675)),[back('DANGERS')])
    rs += [response('Я закрыл прорыв.','DANGER_BREACH',eq('u_berserk_breach_sealed')),
           response('Я убил его отражение — или что это было.','DANGER_PROJECTION',v('projection_defeated')),
           response('Куда мне идти дальше?','NEXT'),back()]
    topic('DANGERS',tr('Расскажи, что тебе известно.'),rs)
    leaf('DANGER_BREACH',[688,691,694],'DANGERS')
    topic('DANGER_PROJECTION',tr('Больно от него было настоящее, да?'),[response('Да.','PROJECTION_ANSWER'),back('DANGERS')])
    topic('PROJECTION_ANSWER',tr('То, что ты изрубил, — отражение. Оно ранит по-настоящему. Но его гибель ещё ничего не говорит о судьбе оригинала.'),[back('DANGERS')],heard='projections')
    text=prose(740,743)
    for key,name in reversed([('first','лесная низина'),('breach','пепельный разрыв'),('count','резиденция Графа'),('wyald','лагерь Чёрных Псов'),('rosine','туманная долина'),('grunbeld','крепость Грюнбельда')]):
        text=choose(both(eq('u_berserk_journal_knows_'+key),neg(test('JOURNAL_DONE_'+key.upper()))),tr('У тебя есть известная дорога: '+name+'.\n\n'+s(734)),text)
    topic('NEXT',text,[back('AID')])

def siege():
    leaf('SIEGE_WHAT',[939])
    topic('SIEGE_WAY',tr('Через сад на запад или через южный выход. Смотри, куда ещё можно пройти: огонь не будет ждать.'),[back()])
    topic('SIEGE_FIGHT',tr('Сдержи врагов, если можешь. Но не стой тут из гордости. Уйти — не значит проиграть.'),[back()])
    leaf('SIEGE_FLORA',[978,981])
    topic('SIEGE_SAVE',tr('На столе в библиотеке — рукопись. Если дорога туда ещё цела, забери. Нет — бросай и беги.\n\n'+s(996)),[response('Попробую.','TALK_BERSERK_FLORA'),response('Туда уже не пройти.','SIEGE_SAVE_NO')])
    leaf('SIEGE_SAVE_NO',[1005])

def mechanics():
    EOCS.extend([
        eoc(E+'HURT',[],either(*(math(f"u_hp('{bp}') < u_hp_max('{bp}') * 0.8") for bp in ['head','torso','arm_l','arm_r','leg_l','leg_r']))),
        eoc(E+'ANY_ARMOR',[],either(*({'u_has_item':x} for x in ['berserk_helmet','berserk_chestplate','berserk_gloves','berserk_armguards','berserk_legguards','berserk_boots']))),
        eoc(E+'ARMOR_KNOWN',[],either(FULL,test(E+'ANY_ARMOR'),eq('u_berserk_ref_armor_properties'),eq('u_berserk_ref_flora_armor'),v('heard_armor'))),
        eoc(E+'KNOWN_DANGER',[],either(v('projection_defeated'),eq('u_berserk_breach_sealed'),*(eq('u_berserk_journal_knows_'+s) for s in ['count','wyald','rosine','grunbeld']))),
    ])
    # A historical pact is a separate successful personal outcome. It does not
    # change the world boss, wound, relic, flesh reward, or loyalty conditions.
    for stem in ['count','wyald','rosine','grunbeld']:
        flag=eq('u_berserk_pact_resolved_'+stem)
        EOCS.append(eoc(E+'RESOLVED_'+stem.upper(),[],either(math('berserk_hunt_'+stem+'_state >= 4'),flag)))
        data=read('effects/apostol_pawn_eocs.json');by=index(data)
        old=by['EOC_BERSERK_APOSTOL_'+stem.upper()+'_PAWN_SUSPEND_HUNT']
        old['condition']=test('APOSTOL_'+stem.upper()+'_PAWN_LINE')
        old['effect']=[math('u_berserk_pact_resolved_'+stem+' = 1'),
            {'if':{'u_has_mission':'MISSION_BERSERK_'+stem.upper()},'then':{'finish_mission':'MISSION_BERSERK_'+stem.upper(),'success':True}},
            run('EOC_BERSERK_LATE_FLORA_RECOVER')]
        write('effects/apostol_pawn_eocs.json',data)
        data=read('effects/hunt_mission_eocs.json');obj=index(data)['EOC_BERSERK_MISSION_'+stem.upper()]
        original=copy.deepcopy(obj['effect'])
        if 'if' in original and original['if']==flag:original=original['else']
        obj['condition']=either(flag,both(math('has_var(berserk_hunt_'+stem+'_location)'),math('berserk_hunt_'+stem+'_state >= 1'),neg(test('APOSTOL_'+stem.upper()+'_PAWN_LOYAL'))))
        obj['effect']={'if':flag,'then':{'if':{'u_has_mission':'MISSION_BERSERK_'+stem.upper()},'then':{'finish_mission':'MISSION_BERSERK_'+stem.upper(),'success':True}},'else':original}
        # Do NOT set the old victory-finished flag: the reference observer
        # previously used it as evidence of a slain and sealed keeper.
        write('effects/hunt_mission_eocs.json',data)
        data=read('missions/named_hunts.json');obj=index(data)['MISSION_BERSERK_'+stem.upper()]
        obj['goal_condition']=either(math('berserk_hunt_'+stem+'_state >= 5'),flag)
        write('missions/named_hunts.json',data)
        data=read('effects/road_journal_eocs.json');obj=index(data)['EOC_BERSERK_JOURNAL_DONE_'+stem.upper()]
        c=obj['condition']
        if not (isinstance(c,dict) and c.get('or',[None])[0]==flag):obj['condition']=either(flag,c)
        write('effects/road_journal_eocs.json',data)
    resolved=both(*(test(E+'RESOLVED_'+s) for s in ['COUNT','WYALD','ROSINE']))
    data=read('effects/new_horizon_progression_eocs.json');by=index(data)
    by['EOC_BERSERK_EARLY_HUNTS_CLOSED']['condition']=resolved
    # A manually discovered home must not suppress the later real clue, and
    # an alternative survivor is not required to have been rescued by Knight.
    survived=both(eq('berserk_eclipse_era'),either(eq('u_berserk_eclipse_rescue_state',2),eq('u_berserk_apostol_return_state',2)))
    by['EOC_BERSERK_LATE_FLORA_CHECK']['condition']=both(survived,resolved,math("u_val('pos_z') == 0"),eq('u_berserk_flora_late_clue_given',0),math('berserk_flora_stage < 2'))
    write('effects/new_horizon_progression_eocs.json',data)
    EOCS.append(eoc(E+'LATE',[],both(survived,either(resolved,v('legacy_ready')))))
    data=read('effects/flora_eocs.json');by=index(data)
    c=by['EOC_BERSERK_FLORA_CAN_RECEIVE']['condition']
    if c.get('and') and c['and'][-1]==LATE:c=c['and'][0]
    by['EOC_BERSERK_FLORA_CAN_RECEIVE']['condition']=both(c,test('FLORA_AT_REGISTERED_MANOR'),LATE)
    add(by['EOC_BERSERK_FLORA_GIVE_ARMOR'],[run('QUEUE')])
    write('effects/flora_eocs.json',data)
    data=read('effects/flora_siege_eocs.json');by=index(data)
    by['EOC_BERSERK_FLORA_CAN_PREPARE_SIEGE']['condition']=both(LATE,PEACE,test('FLORA_AT_REGISTERED_MANOR'),neg(v('queued')))
    # Retain anchors/layout compatibility, but stop handing out a second
    # campaign switch. Existing charms survive as inert keepsakes.
    by['EOC_BERSERK_FLORA_PREPARE_SIEGE']['effect']=[x for x in by['EOC_BERSERK_FLORA_PREPARE_SIEGE']['effect'] if not ('if' in x and 'berserk_flora_escape_charm' in json.dumps(x))]
    by['EOC_BERSERK_FLORA_CAN_START_SIEGE']['condition']=both('u_is_avatar',survived,eq('berserk_flora_siege_state'),eq('berserk_flora_stage'),test('FLORA_AT_REGISTERED_MANOR'))
    # The old public START handler remains available to the scheduled event,
    # but records an attack only if its native commit really succeeded.
    start=by['EOC_BERSERK_FLORA_START_SIEGE']
    start['effect']=[x for x in start['effect'] if x != math('u_berserk_ref_flora_attack = 1')]
    for node in walk(start):
        if node.get('u_message','').startswith('The charm tightens'):
            node['u_message']=prose(929)
    add(start,[{'if':ATTACK,'then':[math('u_berserk_ref_flora_attack = 1'),run('EOC_BERSERK_REF_SYNC')]}])
    write('effects/flora_siege_eocs.json',data)
    EOCS.extend([
        eoc(E+'QUEUE',[run('EOC_BERSERK_FLORA_PREPARE_SIEGE'),{'if':eq('berserk_flora_siege_state'),'then':[setv('queued'),math("u_berserk_flora33_due = time('now') + 3")]}],both('u_is_avatar',neg(v('queued')),LATE,PEACE)),
        eoc(E+'DUE',[run('EOC_BERSERK_FLORA_START_SIEGE'),{'if':ATTACK,'then':[setv('queued',2),run('EOC_BERSERK_FLORA_APOSTLES_ARRIVE')]}],both('u_is_avatar',v('queued'),math("time('now') >= u_berserk_flora33_due"),test('FLORA_AT_REGISTERED_MANOR')),**{'global':True,'recurrence':'1 second'}),
        eoc(E+'CHARM',{'u_message':tr('Бумажный оберег хранит слабый запах трав.'),'type':'info'},'u_is_avatar'),
    ])
    data=read('items/flora_escape_charm.json')
    for obj in data:
        obj['description']=tr('Бумажный оберег Флоры. Среди волокон ещё держится запах сушёных трав.')
        obj['use_action']['menu_text']=tr('Осмотреть оберег')
        obj['use_action']['effect_on_conditions']=[E+'CHARM']
    write('items/flora_escape_charm.json',data)
    # Migrate only proven existing pacts, including broken ones. No reward or
    # body change is replayed and no monster absence is used as evidence.
    EOCS.append(eoc(E+'MIGRATE',[
        {'if':either(eq('berserk_flora_siege_state'),both(eq('berserk_flora_armor_claimed'),eq('u_berserk_flora_armor_resolved'))), 'then':setv('legacy_ready')},
        setv('schema')],both('u_is_avatar',neg(v('schema')))))
    EOCS.append(eoc(E+'NEW_GAME',[setv('schema')],'u_is_avatar',eoc_type='EVENT',required_event='game_start'))
    migration=[run('MIGRATE'),{'if':eq('u_berserk_griffith_projection_defeated'),'then':setv('projection_defeated')}]
    for stem in ['count','wyald','rosine','grunbeld']:
        migration.append({'if':test('APOSTOL_'+stem.upper()+'_PAWN_LINE'),'then':math('u_berserk_pact_resolved_'+stem+' = 1')})
    EOCS.append(eoc(E+'RECOVER',migration,'u_is_avatar',**{'global':True,'recurrence':'1 minute'}))
    # Only actual player kills count. This event exists in native 0.I and is
    # also the source used by the engine's projection death rewards.
    EOCS.append(eoc(E+'PROJECTION_KILL',[setv('projection_defeated'),run('EOC_BERSERK_REF_SYNC')],both('u_is_avatar',{'compare_string':[{'context_val':'victim_type'},'unused']}),eoc_type='EVENT',required_event='character_kills_monster'))
    EOCS[-1]['condition']=both('u_is_avatar',either(*({'compare_string':[{'context_val':'victim_type'},m['id']]} for m in read('monsters/apostle_projections.json'))))
    # Confirmed combat while berserking, not possession or merely equipping.
    for event in ['character_melee_attacks_monster','character_melee_attacks_character']:
        EOCS.append(eoc(E+'ARMOR_COMBAT_'+event.upper(),[setv('used_in_combat')],both('u_is_avatar',eq('u_berserk_mode_state')),
            eoc_type='EVENT',required_event=event))
    # The manuscript's optional save action already exists. Require the real
    # desk to remain within the loaded manor, not a flag claiming it exists.
    # There is no native route guarantee here. Keep this optional question
    # hidden until a real desk inspection has established the remaining task.
    EOCS.append(eoc(E+'MANUSCRIPT_REACHABLE',[],both(v('manuscript_seen'),eq('berserk_flora_manuscript_rescued',0),test('FLORA_AT_REGISTERED_MANOR'))))
    data=read('effects/flora_treehouse_eocs.json');by=index(data)
    add(by['EOC_BERSERK_FLORA_MANUSCRIPT'],[{'if':{'map_furniture_id':'f_berserk_flora_manuscript','loc':{'context_val':'pos'}},'then':setv('manuscript_seen')}])
    write('effects/flora_treehouse_eocs.json',data)

def epilogue():
    data=read('effects/campaign_journal_eocs.json');by=index(data)
    body='\n\n'.join(s(i) for i in [1016,1018,1020,1022])
    # Avoid inventing personal behavior at the hearth or claiming healing is
    # mandatory when the escaping character is uninjured.
    body=body.replace('Снимали сапоги, грели руки, задавали вопросы, на которые получали ответы или молчание.','Разговаривали с хозяйкой и узнавали этот дом.')
    obj=by['EOC_BERSERK_CAMPAIGN_POST_FIRE']
    obj['effect']=[math('u_berserk_flora_fire_summary_seen = 1'),run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL'),
        {'set_string_var':tr('Прежде чем продолжать известные дороги, найдите место для отдыха.'),'target_var':{'context_val':'flora_next'},'i18n':True},
        {'if':eq('u_berserk_ref_grunbeld_siege_seen'),'then':{'set_string_var':prose(1050),'target_var':{'context_val':'flora_next'},'i18n':True}},
        {'if':eq('u_berserk_ref_grunbeld_siege_dead'),'then':{'set_string_var':tr('Грюнбельд мёртв. Но связанные с ним раны не исчезли вместе с ним.'),'target_var':{'context_val':'flora_next'},'i18n':True},
         'else':{'if':eq('u_berserk_ref_grunbeld_siege_alive'),'then':{'if':eq('u_berserk_journal_knows_grunbeld'),'then':{'set_string_var':tr('Грюнбельд выжил. Уцелевший след ведёт к его крепости. Прежде чем продолжать дорогу, можно восстановить силы.'),'target_var':{'context_val':'flora_next'},'i18n':True},'else':{'set_string_var':tr('Грюнбельд выжил и исчез в дыму. Куда он делся после боя, ещё предстоит выяснить.'),'target_var':{'context_val':'flora_next'},'i18n':True}}}},
        {'u_message':tr(body+'\n\n<context_val:flora_next>'),'type':'warning','popup':True},run('EOC_BERSERK_REF_SYNC')]
    # A pact can finish the cycle, but never claim all its wounds were closed.
    by['EOC_BERSERK_CAMPAIGN_CHAPTER_CHECK']['condition']=both(neg(eq('u_berserk_campaign_chapter_closed')),
        *(test(E+'RESOLVED_'+s) for s in ['COUNT','WYALD','ROSINE','GRUNBELD']),
        eq('u_berserk_flora_escaped'),eq('u_berserk_breach_sealed'))
    write('effects/campaign_journal_eocs.json',data)
    data=read('effects/flora_treehouse_eocs.json');by=index(data)
    by['EOC_BERSERK_FLORA_READ_CHARRED_ARCHIVE']['effect']={'u_message':prose(1074),'type':'info','popup':True}
    # Keep the saved manuscript and its text unchanged until the owner has
    # decided the pending note. No archive is created from an unread item.
    write('effects/flora_treehouse_eocs.json',data)

def localization():
    for name,translated in [('ru.po',True),('Berserk.pot',False)]:
        path=MOD/'lang/po'/name;remain=dict(STRINGS);out=[]
        for block in path.read_text().split('\n\n'):
            if not block.strip():continue
            key=po_source(block)
            if key in remain:
                value=remain.pop(key);block='#. Flora manuscript 2026-10-22\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if translated else '',ensure_ascii=False)
            out.append(block.strip())
        for key,value in remain.items():out.append('#. Flora manuscript 2026-10-22\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if translated else '',ensure_ascii=False))
        path.write_text('\n\n'.join(out)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)

def main():
    old=read('dialogue/flora.json')
    introductions();root();brand_world();armor();home_personal();dangers();siege();mechanics();epilogue()
    aliases={'APOSTOL_FLORA':'APOSTOL_NOTICE','APOSTOL_FLORA_CHOICE':'APOSTOL_YES','APOSTOL_FLORA_ARMOR':'APOSTOL_ARMOR',
        'APOSTLES':'WORLD','RELICS':'DANGERS','RELIC_LIMITS':'BRAND_BREACH','PREPARATION':'AID','PREPARED':'AID',
        'SIEGE_CONFIRM':'AID','SIEGE_OWNER_CONFIRM':'AID','STATUS':'NEXT','RECEIVED':'ARMOR_CONFIRM',
        'SMITH':'AID','KNOWN_SMITH':'AID'}
    for obj in old:
        id_=obj['id']
        if id_ in TOPICS:continue
        suffix=id_.removeprefix(P)
        target=aliases.get(suffix,'TALK_BERSERK_FLORA')
        if id_.startswith('TALK_BERSERK_APOSTOL_FLORA'):target=aliases[id_.removeprefix('TALK_BERSERK_')]
        alias=copy.deepcopy(TOPICS[tid(target)]);alias['id']=id_;TOPICS[id_]=alias
    write('dialogue/flora.json',list(TOPICS.values()))
    write('effects/flora_dialogue_33_eocs.json',EOCS+list(HELPERS.values()))
    localization()
    print('Flora: manuscript topics',len(TOPICS),'; armor siege delay: 3 seconds; pacts are distinct outcomes.')

if __name__=='__main__':main()

