#!/usr/bin/env python3
"""Approved four-apostle manuscript and owner's final pact decisions."""
import hashlib
import json
import re
import subprocess
from recover_apostol_33 import ROOT, MOD, read, write, index, eoc, walk
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq
from recovery_33_translations import source as po_source

SOURCE=json.loads((ROOT/'docs/dialogue_sources/named-apostles-2026-10-23.json').read_text())['paragraphs']
E='EOC_BERSERK_CONTRACT33_';OLD='EOC_BERSERK_APOSTOL_'
TOPICS={};EOCS=[];HELPERS={};STRINGS={}
STEMS=['COUNT','WYALD','ROSINE','GRUNBELD']
BODIES={'COUNT':['mon_berserk_apostle_count'],'WYALD':['mon_berserk_apostle_wyald'],
        'ROSINE':['mon_berserk_apostle_rosine'],'GRUNBELD':['mon_berserk_grunbeld_knight']}
SUPPLY={'COUNT':('leather',2,'два куска кожи'),'WYALD':('scrap',12,'двенадцать кусков металлолома'),
        'ROSINE':('meat',4,'четыре куска мяса'),'GRUNBELD':('steel_lump',4,'четыре куска стали')}
NAMES={'COUNT':'Граф','WYALD':'Уайлд','ROSINE':'Розина','GRUNBELD':'Грюнбельд'}
GUTS=test('FORGE_GUTS')

def tr(s):STRINGS[s]=s;return s
def prose(*ids):return tr('\n\n'.join(SOURCE[str(i)].strip().strip('*').strip() for i in ids))
def run(s):return {'run_eocs':s if s.startswith('EOC_') else E+s}
def old(k,s):return test(OLD+k+'_PAWN_'+s)
def flag(k,s,n=1):return eq('u_berserk_contract33_'+k.lower()+'_'+s,n)
def setf(k,s,n=1):return math('u_berserk_contract33_'+k.lower()+'_'+s+' = '+str(n))
def enc(k,n):return eq('berserk_apostol_'+k.lower()+'_pawn_encounter',n)
def tid(k,s):return 'TALK_BERSERK_APOSTOL_'+k+'_PAWN_'+s
def choose(c,a,b):
    if isinstance(c,str) or any(x in c for x in ['and','or','not']):
        key=E+'LINE_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[key]=eoc(key,[],c);c=test(key)
    return {**c,'yes':a,'no':b}
def response(k,s,to='ROOT',condition=None,effect=None):
    r={'text':tr(s),'topic':to if to.startswith('TALK_') else tid(k,to)}
    if condition is not None:r['condition']=condition
    if effect is not None:r['effect']=effect
    return r
def back(k,to='OFFER'):return response(k,'Я хотел спросить о другом.',to)
def topic(k,s,line,rs=None,effect=None):
    obj={'type':'talk_topic','id':tid(k,s),'dynamic_line':line,'responses':rs or [back(k)]}
    if effect:obj['speaker_effect']={'effect':effect}
    TOPICS[obj['id']]=obj;return obj
def leaf(k,s,ids,parent='OFFER',extra=None):return topic(k,s,prose(*ids),(extra or [])+[back(k,parent)])
def pending(k):return test(E+k+'_PENDING')
def dead(k):
    return math('berserk_hunt_count_state >= 3') if k=='COUNT' else eq('berserk_apostle_'+k.lower()+'_dead')

DATA={
 'COUNT':dict(intro='&Граф приподнимает тяжёлое тело над полом подземелья и преграждает путь.\n\n«Довольно. Стоишь передо мной, а не валяешься на полу. Значит, либо ты чего-то стоишь, либо просто ещё не понял, где находишься».',
   offer=[89,93],followup=[100,104],defy=[197,201],accepted=[214,218,226],refuse=[237],challenge=[250],
   decision='Я приму твою искру. Буду служить. Меняй меня.',no='Я не стану твоим подчинённым.',
   challenge_button='Я заберу твой дар. Посмотрим, кто распорядится им лучше.',loyal=[260],late=[296],
   missing=[303],body=[311,315],paid=[282,286],betray=[323,327],combat=[1173],
   requirements='Мне нужны два куска кожи для домашних запасов. Принесёшь сюда. Тогда сможешь вновь призвать силу отростка.',
   gut=choose({'u_has_bionics':'bio_berserk_brand_of_sacrifice'},prose(1201),tr('С пустыми руками или с железом — ты всё равно пришёл в мои владения.'))),
 'WYALD':dict(intro='&Уайлд оскаливается, упираясь огромными лапами в землю.\n\n«Эй! Не спеши раскисать. Спросить хочу. Тебе ещё не надоело дрожать от каждой тени на дороге?»',
   offer=[364,368],followup=[375],defy=[353,357],accepted=[474,480,484],refuse=[497],challenge=[510],
   decision='Я в твоей стае. Давай силу. Назад просить не буду.',no='Оставь свою стаю себе.',
   challenge_button='Мне не нужна твоя подачка. Я заберу свою долю силы прямо из твоих рук.',loyal=[520],late=[552],
   missing=[560,564],body=[572,576],paid=[542],betray=[584,588],combat=[1179],
   requirements='Притащи двенадцать кусков металлолома для снаряжения Псов. Хочу глянуть, умеешь ли ты возвращаться с добычей, а не только языком трепать. С моей помощью сможешь рвануть вперёд и смести тех, кто окажется рядом.',
   gut=tr('Ну давай, мечник. Покажи, зачем ты пришёл.')),
 'ROSINE':dict(intro='&Между деревьями мелькают крылья. Розина зависает над тропой, разглядывая вас.\n\n«Ты оттуда? Из мест, где дома полны мёртвых?»',
   offer=[608,612],followup=[629],accepted=[751,758],refuse=[771,778],challenge=[792,796],
   decision='Я останусь. Понимаю, что человеком уже не вернусь. Меняй меня.',no='Нет. Я не позволю тебе меня менять.',
   challenge_button='Я заберу твою силу сам. Из твоей плоти.',loyal=[806],late=[842],
   missing=[],body=[861],paid=[829,833],betray=[883,887],combat=[1185],
   requirements='Принеси четыре куска мяса для гнезда. Тогда я помогу тебе двигаться легче: на короткое время уходить от чужих ударов.',
   gut=prose(1217)),
 'GRUNBELD':dict(intro='&Грюнбельд поворачивается всем корпусом. Молот остаётся опущенным.\n\n«Остановись. Ещё шаг — и это будет значить, что ты пришёл драться».',
   offer=[909,913],followup=[919,923],accepted=[1055,1061,1065],refuse=[1076,1080],challenge=[1093],
   decision='Я принимаю службу и клянусь исполнить её условия. Дай мне новую природу.',no='Я не принесу тебе клятву.',
   challenge_button='Я заберу твою силу после боя. Без клятвы.',loyal=[1102],late=[1134,1138],
   missing=[1145],body=[1152,1156],paid=[1123,1127],betray=[1164],combat=[1191],
   requirements='Доставь четыре куска стали. Они нужны для ремонта доспехов. Взамен я помогу тебе на короткое время укрепить панцирь; двигаться под ударами станет тяжелее.',
   gut=prose(1223))}

def common(k):
    d=DATA[k];p=pending(k);loyal=old(k,'LOYAL');favor=old(k,'FAVOR')
    first=choose(flag(k,'intro_seen'),prose(*d['offer']),tr(d['intro']))
    rootline=choose(loyal,prose(*d['loyal']),choose(p,first,
        choose(both(old(k,'LINE'),eq('u_berserk_apostol_pawn_oath_broken')),prose(*d['betray']),
               choose(GUTS,d['gut'],prose(*d['combat'])))))
    rs=[]
    for label,to in {'COUNT':[('Я слушаю.','OFFER'),('Мне не нужно твоё разрешение.','DEFY'),('Я пришёл положить конец твоему правлению.','REFUSAL')],
                     'WYALD':[('Смотря что ты предлагаешь.','OFFER'),('Я тебя не боюсь.','DEFY'),('Отойди с дороги.','REFUSAL')],
                     'ROSINE':[('Да.','OFFER'),('Я ищу того, кто живёт в этой долине.','OFFER'),('Что здесь происходит?','OFFER')],
                     'GRUNBELD':[('Я выслушаю тебя.','OFFER'),('Ты знаешь, зачем я пришёл.','REFUSAL'),('Говори.','OFFER')]}[k]:
        rs.append(response(k,label,to,p))
    rs += [response(k,{'COUNT':'Что ты требуешь?','WYALD':'Какое дело?','ROSINE':'Что тебе нужно?','GRUNBELD':'Каково поручение?'}[k],'SERVICE',loyal),
           response(k,'Я принёс требуемое.','PAID',both(loyal,neg(favor),{'u_has_items':{'item':SUPPLY[k][0],'count':SUPPLY[k][1]}}),[run(OLD+k+'_PAWN_PAY')]),
           response(k,{'COUNT':'Я ещё не закончил.','WYALD':'Пока ничего.','ROSINE':'Я ещё не нашёл.','GRUNBELD':'Я не справился.'}[k],'LATE',both(loyal,neg(favor))),
           response(k,'Твоя помощь перестала действовать.','SUPPORT_GONE',both(loyal,neg(favor))),
           response(k,'Твоя помощь ещё со мной.','SUPPORT_ACTIVE',both(loyal,favor)),
           response(k,'А новая природа останется со мной?','BODY',loyal),
           response(k,'Закончить разговор.','TALK_DONE',neg(p))]
    if k=='ROSINE':rs.insert(-1,response(k,'Мне нужно побыть одному.','ALONE',loyal))
    topic(k,'ROOT',rootline,rs,effect=[{'if':p,'then':setf(k,'intro_seen')}])
    topic(k,'OFFER',choose(p,prose(*d['offer']),prose(*d['combat'])),[
        response(k,{'COUNT':'Ты предлагаешь мне службу?','WYALD':'И что тебе с этого?','ROSINE':'И что нужно, чтобы остаться?','GRUNBELD':'И подчинение тебе.'}[k],'DETAILS',p),
        response(k,'Я уже решил.','DECISION',p),response(k,'Закончить разговор.','TALK_DONE',neg(p))])
    topic(k,'DETAILS',prose(*d['followup']),offer_questions(k))
    if 'defy' in d:leaf(k,'DEFY',d['defy'])
    topic(k,'DECISION',tr('Решай.') if k!='ROSINE' else tr('Так ты останешься?'),[
        response(k,d['decision'],'ACCEPTED',p,[run(OLD+k+'_PAWN_ACCEPT')]),
        response(k,'Я хочу ещё кое-что спросить.','DETAILS',p),
        response(k,d['no'],'REFUSAL',p),response(k,d['challenge_button'],'CHALLENGE',p),
        response(k,'Закончить разговор.','TALK_DONE',neg(p))])
    topic(k,'ACCEPTED',choose(loyal,prose(*d['accepted']),tr('Ты ещё не дал согласия. Решение остаётся за тобой.')),[
        response(k,'Поговорим о моих обязанностях.','ROOT',loyal),response(k,'Мне нужно идти.','TALK_DONE',loyal),
        response(k,'Вернёмся к моим вопросам.','DETAILS',p)])
    refusal=[run(OLD+k+'_PAWN_REFUSE'),setf(k,'combat_spoken')]
    topic(k,'REFUSAL',prose(*d['refuse']),[response(k,'Защищайся.','TALK_DONE',effect=refusal)])
    topic(k,'CHALLENGE',prose(*d['challenge']),[response(k,'Посмотрим, кто останется стоять.','TALK_DONE',effect=refusal)])
    # Public SERVICE/PRICE IDs are retained for old dialogue entry points.
    topic(k,'SERVICE',tr(d['requirements']),[back(k,'ROOT')])
    topic(k,'PRICE',tr(d['requirements']),[back(k,'DETAILS')])
    for s,ids in [('LATE',d['late']),('BODY',d['body']),('PAID',d['paid'])]:leaf(k,s,ids,'ROOT')
    topic(k,'SUPPORT_GONE',tr('Без мяса для гнезда я не смогу продолжать. Принеси — и я помогу снова.') if k=='ROSINE' else prose(*d['missing']),[back(k,'ROOT')])
    topic(k,'SUPPORT_ACTIVE',tr('Я помню свою часть уговора. Пока помощь действует, новой поставки не требуется.'),[back(k,'ROOT')])
    if k=='ROSINE':leaf(k,'ALONE',[869,873],'ROOT')

def offer_questions(k):
    queries={
      'COUNT':[('Что значит служить тебе?','DUTY'),('Что ты сделаешь со мной?','CHANGE'),('Кого ты здесь защищаешь?','PROTECT'),('Почему именно я?','WHY'),('Что стало с твоими слугами?','SERVANTS')],
      'WYALD':[('Что ты считаешь силой?','STRENGTH'),('Какое место ты мне отдашь?','PLACE'),('Что станет с моим обликом?','CHANGE'),('А слабые?','WEAK'),('Чего ты потребуешь?','DUTY'),('Почему предлагаешь мне, а не просто избавишься от меня?','WHY')],
      'ROSINE':[('Кто живёт в долине?','VALLEY'),('Что значит стать одним из вас?','CHANGE'),('Я смогу уйти?','LEAVE'),('Почему ты хочешь оставить меня?','WHY'),('А если мне здесь не понравится?','DISLIKE')],
      'GRUNBELD':[('Что ты требуешь от вассала?','DUTY'),('Какова цена этой брони?','CHANGE'),('Что означает клятва?','OATH'),('Ты запрещаешь отступать?','RETREAT'),('Почему выбрал меня?','WHY')]}
    rs=[response(k,label,to,pending(k)) for label,to in queries[k]]
    if k=='ROSINE':rs.append(response(k,'Что находится в коконах?','COCOONS',both(pending(k),eq('u_berserk_ref_cocoon_examined'))))
    if k=='GRUNBELD':rs.append(response(k,'Я видел тебя у обители Флоры.','FLORA',both(pending(k),either(eq('u_berserk_contract33_siege_witness'),eq('u_berserk_ref_grunbeld_siege_alive'),eq('u_berserk_ref_grunbeld_siege_dead')))))
    rs.append(response(k,'Я решил.','DECISION',pending(k)))
    rs.append(response(k,'Закончить разговор.','TALK_DONE',neg(pending(k))))
    return rs

def branches():
    k='COUNT'
    for s,ids,q,to,answer in [
      ('DUTY',[119,123],'А если я не соглашусь с твоей волей?','DISOBEY',[130]),
      ('CHANGE',[137],'А прежний облик?','OLD_BODY',[144]),
      ('SERVANTS',[179],'Не все выглядят довольными.','HAPPY',[186])]:
        leaf(k,s,ids,'DETAILS',[response(k,q,to,pending(k))]);leaf(k,to,answer,'DETAILS')
    leaf(k,'PROTECT',[151],'DETAILS',[response(k,'Пленников ты тоже так называешь?','PRISONERS',both(pending(k),either(eq('u_berserk_ref_prisoner_met'),eq('u_berserk_journal_read_berserk_count_prison_list'))))])
    leaf(k,'PRISONERS',[160],'DETAILS');leaf(k,'WHY',[168,172],'DETAILS')
    k='WYALD'
    for s,ids,q,to,answer in [
      ('STRENGTH',[391],'Даже если придётся забрать чужое?','TAKE',[398]),
      ('PLACE',[405],'А ты?','LEADER',[412]),
      ('CHANGE',[419],'Назад дороги не будет?','OLD_BODY',[426]),
      ('WEAK',[433],'И своих так же бросаешь?','ABANDON',[440])]:
        leaf(k,s,ids,'DETAILS',[response(k,q,to,pending(k))]);leaf(k,to,answer,'DETAILS')
    leaf(k,'DUTY',[447,451],'DETAILS');leaf(k,'WHY',[459,463],'DETAILS')
    k='ROSINE'
    for s,ids,q,to,answer in [
      ('VALLEY',[645,649],'Они сами захотели?','WANTED',[656]),
      ('CHANGE',[685],'А я останусь собой?','SELF',[693]),
      ('SELF',[693],'Я не это спросил.','SELF_MORE',[700]),
      ('LEAVE',[709],'Если захочу.','LEAVE_MORE',[716])]:
        leaf(k,s,ids,'DETAILS',[response(k,q,to,pending(k))]);leaf(k,to,answer,'DETAILS')
    # No invented scream: inspecting the actual cocoon is the proof.
    leaf(k,'COCOONS',[665],'DETAILS',[response(k,'Им страшно?','FEAR',pending(k))])
    leaf(k,'FEAR',[674,678],'DETAILS');leaf(k,'WHY',[726,730],'DETAILS');leaf(k,'DISLIKE',[738],'DETAILS')
    k='GRUNBELD'
    for s,ids,q,to,answer in [
      ('DUTY',[938,942],'А если приказ мне противен?','DISOBEY',[948,952]),
      ('CHANGE',[959],'Я смогу от неё избавиться?','OLD_BODY',[965,969]),
      ('OATH',[976],'А если я уйду?','LEAVE',[982])]:
        leaf(k,s,ids,'DETAILS',[response(k,q,to,pending(k))]);leaf(k,to,answer,'DETAILS')
    leaf(k,'RETREAT',[991,995],'DETAILS');leaf(k,'WHY',[1002,1006],'DETAILS')
    topic(k,'FLORA',prose(1019),[response(k,'Там был мирный кров. Люди могли там остаться жить.','FLORA_PRICE',pending(k)),back(k,'DETAILS')])
    topic(k,'FLORA_PRICE',prose(1026),[response(k,'Да. Защищайся.','REFUSAL',pending(k)),response(k,'Я хочу понять, чего будет стоить служба тебе.','FLORA_DUTY',pending(k)),response(k,'Я услышал достаточно.','DECISION',pending(k))])
    leaf(k,'FLORA_DUTY',[1038,1042],'DETAILS')
    for k in STEMS:
        original=TOPICS[tid(k,'CHANGE')]
        TOPICS[tid(k,'PRICE')]={**original,'id':tid(k,'PRICE')}

def append(obj,values):
    if not isinstance(obj['effect'],list):obj['effect']=[obj['effect']]
    for x in values:
        if x not in obj['effect']:obj['effect'].append(x)

def mechanics():
    data=read('effects/apostol_pawn_eocs.json');by=index(data)
    for k in STEMS:
        stem=k.lower();p=OLD+k+'_PAWN_';sp='BERSERK_'+k+'_PAWN_'
        # Keep every original guard: species, range, site, health and path.
        original=by[p+'OPEN']['condition']['and']
        checks=[x for x in original if x!=enc(k,0)]
        checks.append(enc(k,1))
        EOCS.append(eoc(E+k+'_PENDING',[],both(*checks)))
        by[p+'OPEN']['effect']=[math('berserk_apostol_'+stem+'_pawn_encounter = 1'),run(E+k+'_CONVERSATION'),run(p+'CLOSE'),run('EOC_BERSERK_REF_SYNC')]
        # Native bounded run_eocs loop reopens after Esc without recursion,
        # acceptance, refusal or time passing. A saved pending offer resumes.
        EOCS.append(eoc(E+k+'_ROUND',[{'npc_add_effect':'berserk_apostol_parley','duration':'1 second'},'open_dialogue'],pending(k)))
        EOCS.append(eoc(E+k+'_CONVERSATION',{'run_eocs':E+k+'_ROUND','condition':pending(k),'iterations':100},pending(k)))
        by[p+'CLOSE']['effect']=[{'if':neg(enc(k,1)),'then':{'npc_lose_effect':'berserk_apostol_parley'}}]
        by[p+'REFUSE']['effect']=[x for x in by[p+'REFUSE']['effect'] if 'u_message' not in x]
        seen=by[p+'SEEN'];prior=seen['effect']
        if isinstance(prior,list) and prior and prior[0].get('if')==enc(k,1):prior=prior[0]['else']
        seen['effect']=[{'if':enc(k,1),'then':{'run_eocs':E+k+'_CONVERSATION','alpha_talker':'avatar','beta_talker':'u'},'else':prior}]
        check=by[p+'CHECK']['condition']['and']
        if enc(k,0) in check:
            by[p+'CHECK']['condition']=both(*[x for x in check if x!=enc(k,0)],either(enc(k,0),enc(k,1)))
        accept=by[p+'ACCEPT']
        for node in walk(accept):
            if 'u_query' in node:node['u_query']=tr('Принять дар? Ваше тело изменится сразу и навсегда. Хозяин и его подчинённые оставят вас и ваших спутников в покое, пока вы соблюдаете договор. Нападение с вашей стороны разорвёт его.')
            if node.get('u_message')=='The pact reshapes your flesh.':node['u_message']=tr('Чужая сила перекраивает вашу плоть.')
        append(accept,[run(E+'PARTY_SYNC')])
        pay=by[p+'PAY'];item,count,_=SUPPLY[k]
        pay['effect']=[{'u_consume_item':item,'count':count},math('u_berserk_apostol_pawn_service_done = 1'),
            math("u_berserk_apostol_pawn_favor_until = time('now') + time('6 hours')"),
            run('EOC_BERSERK_APOSTOL_PAWN_SYNC'),run('EOC_BERSERK_REF_SYNC')]
        # Existing long support intervals are capped once, never extended.
        EOCS.append(eoc(E+k+'_MIGRATE',[
            {'if':math("u_berserk_apostol_pawn_favor_until > time('now') + time('6 hours')"),'then':math("u_berserk_apostol_pawn_favor_until = time('now') + time('6 hours')")},
            setf(k,'schema')],both('u_is_avatar',old(k,'LINE'),neg(flag(k,'schema')))))
        # Spell/environment damage to servants also counts after a pact.
        by[p+'DAMAGED']['condition']=both('u_is_monster',{'u_has_species':sp+'HOUSEHOLD'})
        hurt=by[p+'HURT']['effect'][0]
        hurt['if']=both(math('berserk_apostol_'+stem+'_pawn_encounter <= 1'),either({'npc_has_species':sp+'MASTER'},enc(k,1)))
        for suffix in ['BETRAY','MASTER_DIED']:
            lost=[]
            if k=='ROSINE':lost.append({'u_lose_effect':'berserk_apostol_pawn_flutter'})
            if k=='GRUNBELD':lost.append({'u_lose_effect':'berserk_apostol_pawn_brace'})
            append(by[p+suffix],lost+[run(E+'PARTY_SYNC')])
            for node in walk(by[p+suffix]):
                if 'u_message' in node:node['u_message']=tr('Договор разорван. Изменённая плоть осталась с вами.') if suffix=='BETRAY' else tr('Связь с хозяином оборвалась. Ваше тело осталось прежним.')
        for suffix in ['ATTACK_CHARACTER_MELEE_ATTACKS_MONSTER','ATTACK_CHARACTER_RANGED_ATTACKS_MONSTER','DAMAGED']:
            for node in walk(by[p+suffix]):
                if node.get('or')==['u_is_avatar','u_following']:node['or'].append('u_friend')
                elif isinstance(node.get('or'),list) and 'npc_following' in node['or'] and 'npc_friend' not in node['or']:node['or'].append('npc_friend')
        damage=by[p+'DAMAGED']['effect']
        if isinstance(damage,dict) and 'or' in damage.get('if',{}):damage['if']=both('has_beta',damage['if'])
        # Personal proof of an actual contract, never mere possession of flesh.
        EOCS.append(eoc(E+k+'_PARTY_FLAG',math('berserk_contract33_'+stem+'_party = 1'),old(k,'LOYAL')))
        EOCS.append(eoc(E+k+'_NPC_TRUCE',{
            'if':both(either('u_friend','u_following'),eq('berserk_contract33_'+stem+'_party')),
            'then':{'if':neg({'u_has_trait':sp+'COMPANION_TRUCE'}),'then':{'u_add_trait':sp+'COMPANION_TRUCE'}},
            'else':{'if':{'u_has_trait':sp+'COMPANION_TRUCE'},'then':{'u_lose_trait':sp+'COMPANION_TRUCE'}}},'u_is_npc'))
        EOCS.append(eoc(E+k+'_COMBAT_CHECK',{'u_run_monster_eocs':[E+k+'_COMBAT_SEEN'],'mtype_ids':BODIES[k],
            'monster_range':14,'monster_must_see':True},both('u_is_avatar',neg(flag(k,'combat_spoken')),
            neg(dead(k)),eq('u_berserk_eclipse_trial_active',0),
            either(GUTS,both(enc(k,2),neg(old(k,'LOYAL'))),both(enc(k,0),neg(test('APOSTOL_PAWN_ELIGIBLE')))))))
        # Dynamic lines are resolved as talk topics, not as u_message objects.
        EOCS.append(eoc(E+k+'_COMBAT_SEEN',[{'run_eocs':E+k+'_COMBAT_SAY','alpha_talker':'avatar','beta_talker':'u'}],'u_is_monster'))
        combat_say={'if':both(old(k,'LINE'),eq('u_berserk_apostol_pawn_oath_broken')),
            'then':{'u_message':tr(NAMES[k]+': '+ '\n'.join(SOURCE[str(i)] for i in DATA[k]['betray'])),'type':'bad','popup':False},
            'else':{'if':GUTS,'then':{'u_message':tr(NAMES[k]+': '+('Клеймёный. Сам пришёл в мой дом.' if k=='COUNT' else '\n'.join(SOURCE[str(i)] for i in {'WYALD':[1211],'ROSINE':[1217],'GRUNBELD':[1223]}[k]))),'type':'warning','popup':False},
              'else':{'u_message':tr(NAMES[k]+': '+'\n'.join(SOURCE[str(i)] for i in DATA[k]['combat'])),'type':'warning','popup':False}}}
        if k=='COUNT':combat_say['else']['then']={'if':{'u_has_bionics':'bio_berserk_brand_of_sacrifice'},'then':{'u_message':tr('Граф: Клеймёный. Сам пришёл в мой дом.'),'type':'warning','popup':False},'else':{'u_message':tr('Граф: Ты пришёл в мои владения. Защищайся.'),'type':'warning','popup':False}}
        if k=='WYALD':combat_say['else']['then']['u_message']=tr('Уайлд: Ну давай, мечник. Покажи, зачем ты пришёл.')
        EOCS.append(eoc(E+k+'_COMBAT_SAY',[combat_say,setf(k,'combat_spoken')],both('u_is_avatar','has_beta','npc_is_monster',neg(flag(k,'combat_spoken')))))
    recover=by['EOC_BERSERK_APOSTOL_PAWN_RECOVER_PARLEY']
    recover['effect']=[run(E+'PARTY_SYNC')]+[{'if':enc(k,1),'then':run(OLD+k+'_PAWN_CHECK')} for k in STEMS]
    write('effects/apostol_pawn_eocs.json',data)
    party=[]
    for k in STEMS:party += [math('berserk_contract33_'+k.lower()+'_party = 0'),run(E+k+'_MIGRATE'),run(E+k+'_PARTY_FLAG')]
    party += [{'u_run_npc_eocs':[E+k+'_NPC_TRUCE' for k in STEMS],'unique_ids':[],'local':True}]
    EOCS.append(eoc(E+'PARTY_SYNC',party,'u_is_avatar'))
    EOCS.append(eoc(E+'PARTY_TICK',[run('PARTY_SYNC')]+[
        {'if':enc(k,1),'then':run(OLD+k+'_PAWN_CHECK')} for k in STEMS]+[
        run(E+k+'_COMBAT_CHECK') for k in STEMS]+[run('GROVE_LOOK')], 'u_is_avatar',**{'global':True,'recurrence':'1 second'}))
    EOCS.append(eoc(E+'PARTY_MOVE',[run('PARTY_SYNC')],'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))
    EOCS.append(eoc(E+'GROVE_LOOK',{'u_run_monster_eocs':[E+'GROVE_SEEN'],'mtype_ids':['mon_berserk_flora_grunbeld'],
        'monster_range':45,'monster_must_see':True},both('u_is_avatar',neg(eq('u_berserk_contract33_siege_witness')))))
    EOCS.append(eoc(E+'GROVE_SEEN',[{'u_location_variable':{'context_val':'contract33_grove_actor'}},
        {'run_eocs':E+'GROVE_OBSERVED','alpha_talker':'avatar'}],'u_is_monster'))
    EOCS.append(eoc(E+'GROVE_OBSERVED',math('u_berserk_contract33_siege_witness = 1'),
        both('u_is_avatar',{'u_can_see_location':{'context_val':'contract33_grove_actor'}})))
    truce=[]
    for k in STEMS:
        truce.append({'type':'mutation','id':'BERSERK_'+k+'_PAWN_COMPANION_TRUCE','name':{'str':tr('Перемирие: '+NAMES[k])},
            'description':tr('Спутника защищает действующий договор. Его тело не меняется.'),'points':0,'valid':False,
            'starting_trait':False,'purifiable':False,'player_display':False,'visibility':0,
            'ignored_by':['BERSERK_'+k+'_PAWN_HOUSEHOLD']})
        data=read('mutations/apostol_'+k.lower()+'_pawn.json')
        for obj in data:
            if obj.get('id')=='BERSERK_'+k+'_PAWN_LOYALTY':
                obj['description']=tr('Хозяин и его подчинённые не трогают вас и ваших спутников, пока действует договор. Нападение с вашей стороны разорвёт его. Это перемирие не даёт власти над демонами.')
        write('mutations/apostol_'+k.lower()+'_pawn.json',data)
    write('mutations/apostol_companion_truce.json',truce)
    # Explicit species removes cross-household inheritance from Count's servant.
    data=read('monsters/apostle_wyald.json')
    thrall=index(data)['mon_berserk_black_dog_thrall']
    parent=index(read('monsters/apostle_count.json'))['mon_berserk_count_servant']
    # The source servant ultimately inherits the common Eclipse halfbreed.
    species=[]
    current=parent
    while current:
        own=current.get('species')
        if own is not None:species=list(own) if isinstance(own,list) else [own];break
        ancestor=current.get('copy-from');current=None
        if ancestor:
            for file in (MOD/'monsters').glob('*.json'):
                objects=json.loads(file.read_text());objects=objects if isinstance(objects,list) else [objects]
                match=next((o for o in objects if o.get('id')==ancestor),None)
                if match:current=match;break
    thrall['species']=list(dict.fromkeys(species+['BERSERK_WYALD_PAWN_HOUSEHOLD']))
    thrall.get('extend',{}).pop('species',None)
    if not thrall.get('extend'):thrall.pop('extend',None)
    write('monsters/apostle_wyald.json',data)
    missions=read('missions/apostol_pawns.json')
    titles={'COUNT':'Служба Графу','WYALD':'Добыча для Чёрных Псов','ROSINE':'Припасы для гнезда','GRUNBELD':'Поручение Грюнбельда'}
    for k in STEMS:
        mission=index(missions)['MISSION_BERSERK_APOSTOL_'+k+'_PAWN_SERVICE']
        mission['name']=tr(titles[k]);mission['description']=tr(DATA[k]['requirements'])
    write('missions/apostol_pawns.json',missions)

def localization():
    for file,translated in [('ru.po',True),('Berserk.pot',False)]:
        path=MOD/'lang/po'/file;remaining=dict(STRINGS);blocks=[]
        for block in path.read_text().split('\n\n'):
            if not block.strip():continue
            key=po_source(block)
            if key in remaining:
                value=remaining.pop(key);block='#. Named apostles 2026-10-23\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if translated else '',ensure_ascii=False)
            blocks.append(block.strip())
        for key,value in remaining.items():blocks.append('#. Named apostles 2026-10-23\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if translated else '',ensure_ascii=False))
        path.write_text('\n\n'.join(blocks)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)

def main():
    for k in STEMS:common(k)
    branches();mechanics()
    write('dialogue/apostol_contracts.json',list(TOPICS.values()))
    write('effects/named_apostle_dialogue_33_eocs.json',EOCS+list(HELPERS.values()))
    localization()
    print('Named apostles:',len(TOPICS),'topics; four pacts and party truce.')

if __name__=='__main__':main()
