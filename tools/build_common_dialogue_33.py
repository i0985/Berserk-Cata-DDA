#!/usr/bin/env python3
"""Final owner manuscript: contextual reactions, native lying and scene prose.

Run after God Hand and before the read-only reference builder. The global
human/demon classification is never changed by a successful social trial.
"""
import copy
import hashlib
import json
import re
import subprocess
from recover_apostol_33 import ROOT, MOD, read, write, index, eoc, walk
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq, gt
from build_named_apostle_dialogues_33 import STRINGS, localization
from recovery_33_translations import source as po_source

SOURCE=json.loads((ROOT/'docs/dialogue_sources/common-reactions-2026-10-23.json').read_text())['paragraphs']
P='EOC_BERSERK_COMMON33_';T='TALK_BERSERK_COMMON33_'
H=test('APOSTOL_HUMAN_EQUIPMENT_ALLOWED');D=neg(H)
NAMES={'GODO':'Годо','RICKERT':'Рикерт','FLORA':'Флора','KNIGHT':'Рыцарь'}
ROOTS={'GODO':'TALK_BERSERK_GODO','RICKERT':'TALK_BERSERK_RICKERT','FLORA':'TALK_BERSERK_FLORA','KNIGHT':'TALK_BERSERK_SKULL_KNIGHT_AFTER'}
FILES={'GODO':'godo.json','RICKERT':'godo.json','FLORA':'flora.json','KNIGHT':'skull_knight.json'}
TOPICS={};EOCS=[];HELPERS={};USED=set()
CHINESE={}

def tr(s):STRINGS[s]=s;return s
def prose(*ids):
    USED.update(ids)
    return tr('\n\n'.join(re.sub(r'^(?:Годо|Рикерт|Флора|Рыцарь(?:-Череп)?):\s*[—–-]?\s*','',SOURCE[str(i)].strip().strip('*').strip()).removeprefix('— ').strip() for i in ids))
def run(s):return {'run_eocs':s if s.startswith('EOC_') else P+s}
def f(k,s):return 'u_berserk_common33_'+k.lower()+'_'+s
def flag(k,s,n=1):return eq(f(k,s),n)
def put(k,s,n=1):return math(f(k,s)+' = '+str(n))
def pred(k,s):return test(P+k+'_'+s)
def tid(k,s):return T+k+'_'+s
def choose(c,a,b):
    if isinstance(c,str) or any(x in c for x in ['and','or','not']):
        key=P+'LINE_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[key]=eoc(key,[],c);c=test(key)
    return {**c,'yes':a,'no':b}
def response(k,s,to='MENU',condition=None,effect=None):
    o={'text':tr(s),'topic':to if to.startswith('TALK_') else tid(k,to)}
    if condition is not None:o['condition']=condition
    if effect is not None:o['effect']=effect
    return o
def back(k):return response(k,'Я хотел спросить о другом.',ROOTS[k])
def topic(k,s,line,rs=None,effects=None):
    o={'type':'talk_topic','id':tid(k,s),'dynamic_line':line,'responses':rs or [back(k)]}
    if effects:o['speaker_effect']={'effect':effects}
    TOPICS[o['id']]=o;return o
def leaf(k,s,ids,extra=None):
    repeat={'GODO':'Я помню наш разговор. Что ещё?','RICKERT':'Я помню. Что-нибудь изменилось?',
            'FLORA':'Мы уже говорили об этом. Есть что-нибудь ещё?','KNIGHT':'Я помню сказанное. Продолжай.'}[k]
    return topic(k,s,choose(flag(k,'read_'+s.lower()),tr(repeat),prose(*ids)),(extra or [])+[back(k)],[put(k,'read_'+s.lower())])
def say(text,kind='info',popup=False):return {'u_message':tr(text),'type':kind,'popup':popup}
def add_effect(o,value):
    if not isinstance(o.get('effect'),list):o['effect']=[] if 'effect' not in o else [o['effect']]
    if value not in o['effect']:o['effect'].append(value)
def replace(node,old,new):
    if node==old:return copy.deepcopy(new)
    if isinstance(node,dict):return {k:replace(v,old,new) for k,v in node.items()}
    if isinstance(node,list):return [replace(v,old,new) for v in node]
    return node
def at(k):
    return test({'GODO':'GODO_AT_SMITH','RICKERT':'GODO_AT_RICKERT','FLORA':'COMMON33_AT_FLORA','KNIGHT':'COMMON33_AT_KNIGHT'}[k])

def rules():
    visible=[];visible_flags=set()
    for path in sorted((MOD/'mutations').glob('apostol_*.json')):
        for obj in json.loads(path.read_text()):
            if obj.get('type')=='mutation' and (obj.get('visibility',0)>0 or obj['id'].endswith(('_APOSTLE','_PAWN'))):visible.append({'u_has_trait':obj['id']})
            visible_flags.update(x for x in obj.get('flags',[]) if x.startswith('BERSERK_') and x.endswith('_FORM_ACTIVE'))
    EOCS.append(eoc(P+'VISIBLE',[],both(D,either(*visible,*[{'u_has_flag':s} for s in sorted(visible_flags)]))))
    EOCS.append(eoc(P+'HIDDEN',[],both(D,neg(test(P+'VISIBLE')))))
    for k in ['FLORA','KNIGHT']:
        mon='mon_berserk_flora' if k=='FLORA' else 'mon_skull_knight_rescuer'
        EOCS.append(eoc(P+'AT_'+k,[],both('has_beta','npc_is_monster',math("n_monsters_nearby('"+mon+"', 'radius': 0, 'attitude': 'both') > 0"))))
    for k in NAMES:
        previous={
            'GODO':either(eq('u_berserk_apostol_godo_told'),eq('u_berserk_godo_demon_refused')),
            'RICKERT':either(eq('u_berserk_apostol_rickert_told'),eq('u_berserk_apostol_rickert_counsel')),
            'FLORA':either(eq('u_berserk_flora33_demon_noticed'),eq('u_berserk_ref_flora_demon_counsel')),
            'KNIGHT':flag(k,'disclosed')}[k]
        known=either(previous,flag(k,'disclosed'),test(P+'VISIBLE'))
        EOCS.append(eoc(P+k+'_KNOWS',[],both(D,known)))
        EOCS.append(eoc(P+k+'_CONCEALED',[],both(test(P+'HIDDEN'),neg(known),flag(k,'lie_passed'))))
        EOCS.append(eoc(P+k+'_ALLOWED',[],either(H,pred(k,'CONCEALED'))))
        EOCS.append(eoc(P+k+'_WORK_OPEN',[],either(H,both(test(P+'HIDDEN'),neg(known)))))
        EOCS.append(eoc(P+k+'_PENDING',[],both(test(P+'HIDDEN'),neg(known),neg(flag(k,'lie_passed')))))
        told=[put(k,'disclosed')]
        if k in ['GODO','RICKERT']:told.append(math('u_berserk_apostol_'+k.lower()+'_told = 1'))
        if k=='FLORA':told.append(math('u_berserk_flora33_demon_noticed = 1'))
        EOCS.append(eoc(P+k+'_TELL',told,both(at(k),D)))
        EOCS.append(eoc(P+k+'_LIE_SUCCESS',[put(k,'lie_passed')],both(at(k),pred(k,'PENDING'))))
        EOCS.append(eoc(P+k+'_LIE_FAILURE',[put(k,'lie_failed'),run(k+'_TELL')],both(at(k),pred(k,'PENDING'))))
        EOCS.append(eoc(P+k+'_NOTICE',run(k+'_TELL'),both(at(k),test(P+'VISIBLE'))))
        if k in ['GODO','RICKERT']:
            data=read('effects/apostol_continuation_eocs.json');by=index(data)
            by['EOC_BERSERK_APOSTOL_'+k+'_KNOWS_GIFT']['condition']=pred(k,'KNOWS')
            write('effects/apostol_continuation_eocs.json',data)

def concealment():
    for k in ['GODO','RICKERT','FLORA']:
        prompt={'GODO':'С тобой что-то не так? Смотришь мимо, будто слышишь кого-то за моей спиной. Прежде чем продолжим — скажи, что происходит.',
                'RICKERT':'С тобой что-то не так? Ты всё время прислушиваешься. Это после того места, откуда ты вернулся?',
                'FLORA':'С тобой что-то не так? Я чувствую беспокойство, но не хочу решать за тебя, что оно означает. Ты ничего не хочешь рассказать?'}[k]
        lie={'text':tr('Всё нормально. С чего ты взял?' if k!='FLORA' else 'Всё нормально. С чего ты взяла?'),
             'condition':pred(k,'PENDING'),'trial':{'type':'LIE','difficulty':{'GODO':40,'RICKERT':50,'FLORA':25}[k]},
             'success':{'topic':tid(k,'LIE_PASSED'),'effect':[run(k+'_LIE_SUCCESS')]},
             'failure':{'topic':tid(k,'LIE_FAILED'),'effect':[run(k+'_LIE_FAILURE')]}}
        topic(k,'SUSPICION',choose(pred(k,'PENDING'),tr(prompt),tr('Мы уже поговорили об этом.')), [
            response(k,'Я принял чужую силу. Она меняет меня.','CONFESS',pred(k,'PENDING'),[run(k+'_TELL')]),lie,
            response(k,'Не сейчас. Мне нужно идти.','TALK_DONE')])
        follow={'GODO':'Ладно. Тогда вернёмся к работе.','RICKERT':'Хорошо. Если понадобится помощь — скажи.','FLORA':'Пусть так. О чём ты хотел поговорить?'}[k]
        topic(k,'LIE_PASSED',tr(follow),[back(k)])
        failed={'GODO':'Не держи меня за дурака. Я не знаю, что ты впустил в себя, но вижу, что ты пытаешься это скрыть. Новый клинок я тебе не отдам. За внесёнными материалами можешь обратиться — они твои.',
                'RICKERT':'Не надо. Лучше скажи прямо, чем мне потом гадать, насколько рядом с тобой безопасно. О работе мы ещё поговорим. Но прежде я хочу услышать правду.',
                'FLORA':'Нет. За этими словами есть то, что ты прячешь. Я не стану передавать тебе доспех, пока ты идёшь этим путём. Но дверь перед тобой не закрыта.'}[k]
        topic(k,'LIE_FAILED',tr(failed),[response(k,'Я расскажу.','MENU',D),back(k)])
        topic(k,'CONFESS',{'GODO':prose(303),'RICKERT':prose(312),'FLORA':tr('Спасибо, что сказал. Начало перемены ещё можно скрыть от взгляда. От себя — вряд ли.')}[k],[response(k,'Поговорим об этом.','MENU',D),back(k)])

def reactions():
    for k in NAMES:
        known=pred(k,'KNOWS');hidden=test(P+'HIDDEN');path=lambda n:eq('u_berserk_apostol_path',n)
        offered=either({'u_has_item':'berserk_behelit'},{'u_has_item':'berserk_behelit_distorted'})
        choices=[response(k,'Посмотри на этот камень.','STONE',offered),
            response(k,'Я принял силу. Но внешне почти ничего не изменилось.','EARLY',hidden,[run(k+'_TELL')]),
            response(k,'Тело уже начало меняться.','BODY',both(known,eq('u_berserk_apostol_stage',2))),
            response(k,'Я научился ещё кое-чему.','POWER',both(known,gt('u_berserk_apostol_growth_step',1))),
            response(k,'Кажется, тело больше не меняется.','COMPLETE',both(known,eq('u_berserk_apostol_stage',3))),
            response(k,'Я поглотил плоть побеждённого апостола.','FLESH',both(D,path(2)),[run(k+'_TELL')]),
            response(k,'О договоре с тем, кто меня изменил.','PACT',both(D,path(3)),[run(k+'_TELL')]),
            response(k,'Я нарушил договор.','BROKEN',both(known,path(3),eq('u_berserk_apostol_pawn_oath_broken'))),
            response(k,'Того, кому я служил, больше нет.','DEAD',both(known,path(3),eq('u_berserk_apostol_pawn_master_dead'))),
            response(k,'Я отказался от дара, но последствия остались.','REFUSED',both(eq('u_berserk_apostol_outcome',2),eq('u_berserk_apostol_return_state',2))),back(k)]
        topic(k,'MENU',tr('Что ты хочешь обсудить?'),choices)
        early={'GODO':303,'RICKERT':312,'FLORA':323,'KNIGHT':327}
        extra=[]
        if k=='GODO':extra=[response(k,'Я хотел выжить.','SURVIVE'),response(k,'Стать сильнее любого врага.','STRONG'),response(k,'Я не хочу об этом говорить.','QUIET')]
        if k=='RICKERT':extra=[response(k,'Да. И я скажу, если что-нибудь станет опасным.','PROMISE'),response(k,'Я сам справлюсь.','ALONE')]
        leaf(k,'EARLY',[early[k]],extra)
        if k=='GODO':
            for s,ids in [('SURVIVE',[306]),('STRONG',[308]),('QUIET',[310])]:leaf(k,s,ids)
        if k=='RICKERT':
            topic(k,'PROMISE',prose(314),[back(k)],[put(k,'promised_warning')]);leaf(k,'ALONE',[318])
        bodies={'GODO':334,'RICKERT':336,'FLORA':343,'KNIGHT':347}
        leaf(k,'BODY',[bodies[k]],([response(k,'Болит.','PAINFUL'),response(k,'Нет. Просто непривычно.','UNFAMILIAR')] if k=='RICKERT' else []))
        if k=='RICKERT':leaf(k,'PAINFUL',[339]);leaf(k,'UNFAMILIAR',[341])
        powers={'GODO':355,'RICKERT':358,'FLORA':363,'KNIGHT':367}
        leaf(k,'POWER',[powers[k]],([response(k,'Ты предлагаешь не пользоваться силой?','POWER_CHOICE')] if k=='FLORA' else []))
        if k=='FLORA':leaf(k,'POWER_CHOICE',[365])
        complete={'GODO':373,'RICKERT':377,'FLORA':380,'KNIGHT':384}
        text=prose(complete[k])
        if k=='RICKERT':text=tr('Ты уверен? Хорошо, что теперь хоть знаешь, чего ждать от собственного тела. Мне всё ещё нужно немного времени.')
        if k=='KNIGHT':text=choose(path(1),text,tr('Тело перестало меняться. Это не освобождает тебя от ответственности за то, как ты распорядишься им.'))
        topic(k,'COMPLETE',choose(flag(k,'read_complete'),tr('Я помню. Как ты справляешься теперь?'),text),[back(k)],[put(k,'read_complete')])
        flesh={'GODO':392,'RICKERT':399,'FLORA':405,'KNIGHT':409}
        extra=[response(k,'Мне нужна была его сила.','FLESH_POWER'),response(k,'Я хотел стать лучше него.','FLESH_BETTER')] if k=='GODO' else []
        leaf(k,'FLESH',[flesh[k]],extra)
        if k=='GODO':leaf(k,'FLESH_POWER',[395]);leaf(k,'FLESH_BETTER',[397])
        if k=='RICKERT':TOPICS[tid(k,'FLESH')]['responses'].insert(0,response(k,'Я знал не всё.','FLESH_PRICE'))
        if k=='RICKERT':topic(k,'FLESH_PRICE',choose('npc_following',prose(401),prose(403)),[back(k)])
        pact={'GODO':416,'RICKERT':420,'FLORA':428,'KNIGHT':432}
        extra=[response(k,'Нет. Ты сам решаешь.','PACT_RESPECT'),response(k,'Если идёшь со мной, придётся слушаться.','PACT_COMMAND')] if k=='RICKERT' else []
        leaf(k,'PACT',[pact[k]],extra)
        if k=='RICKERT':
            leaf(k,'PACT_RESPECT',[423]);topic(k,'PACT_COMMAND',prose(425),[back(k)],
                [{'if':'npc_following','then':run('EOC_BERSERK_RICKERT_BREAK_COMPANIONSHIP'),'else':run('EOC_BERSERK_RICKERT_REFUSE_RECRUITMENT')}])
        broken={'GODO':439,'RICKERT':443,'FLORA':444,'KNIGHT':445}
        leaf(k,'BROKEN',[broken[k]])
        dead={'GODO':449,'RICKERT':450,'FLORA':451,'KNIGHT':452};leaf(k,'DEAD',[dead[k]])
        refused={'GODO':458,'RICKERT':460,'FLORA':465,'KNIGHT':467};leaf(k,'REFUSED',[refused[k]])
        if k=='RICKERT':
            TOPICS[tid(k,'REFUSED')]['dynamic_line']=choose({'u_has_trait':'BERSERK_ECLIPSE_SCAR_HEARING'},prose(462),prose(460))
        stones={'GODO':272,'RICKERT':279,'FLORA':287,'KNIGHT':295}
        leaf(k,'STONE',[stones[k]], [response(k,'Знаешь, что это?','STONE_MORE')])
        answers={'GODO':274,'RICKERT':284,'FLORA':289,'KNIGHT':297};leaf(k,'STONE_MORE',[answers[k]])
        if k=='GODO':TOPICS[tid(k,'STONE_MORE')]['dynamic_line']=choose({'u_has_item':'berserk_behelit_distorted'},tr(prose(274)+'\n\n'+prose(276)),prose(274))
        if k=='FLORA':TOPICS[tid(k,'STONE_MORE')]['dynamic_line']=choose({'u_has_item':'berserk_behelit_distorted'},prose(293),prose(289))
    details=[('GODO','WINGS','BERSERK_ROSINE_FLESH_FORM',476),('RICKERT','WINGS','BERSERK_ROSINE_FLESH_FORM',478),
             ('GODO','SHELL','BERSERK_GRUNBELD_FLESH_FORM',480),('FLORA','SHELL','BERSERK_GRUNBELD_FLESH_FORM',482),
             ('RICKERT','SPEECH','BERSERK_ROSINE_PAWN_SEED',484),('FLORA','SPEECH','BERSERK_ROSINE_PAWN_SEED',486),
             ('GODO','HEAVY','BERSERK_COUNT_FLESH_FORM',488)]
    for k,s,trait,paragraph in details:
        condition={'u_has_trait':trait}
        if s=='WINGS':condition=either(*[{'u_has_trait':x} for x in ['BERSERK_ROSINE_FLESH_FORM','BERSERK_ROSINE_PAWN_FORM','BERSERK_FEMTO_FORM']])
        if s=='SHELL':condition=either(*[{'u_has_trait':x} for x in ['BERSERK_GRUNBELD_FLESH_FORM','BERSERK_GRUNBELD_PAWN_FORM']])
        TOPICS[tid(k,'MENU')]['responses'].insert(-1,response(k,{'WINGS':'Из-за крыльев стало тесно.','SHELL':'О панцире.','SPEECH':'Мне трудно говорить.','HEAVY':'Моё тело стало тяжелее.'}[s],s,condition))
        leaf(k,s,[paragraph])

def patch_services():
    data=read('effects/godo_eocs.json');by=index(data)
    for obj in data:
        if H in list(walk(obj)):
            gate=pred('GODO','ALLOWED') if obj['id'] in ['EOC_BERSERK_GODO_SWORD_CLAIM','EOC_BERSERK_GODO_EARLY_CLAIM'] else pred('GODO','WORK_OPEN')
            obj.update(replace(obj,H,gate))
    join=by['EOC_BERSERK_RICKERT_JOIN']
    for node in walk(join.get('condition')):
        if 'or' in node and eq('u_berserk_apostol_rickert_counsel') in node['or'] and pred('RICKERT','CONCEALED') not in node['or']:
            node['or'].append(pred('RICKERT','CONCEALED'))
    write('effects/godo_eocs.json',data)
    # Shared dynamic-line predicate helpers must describe the smith's knowledge,
    # not reveal the avatar's secret before the social trial.
    data=read('effects/godo_dialogue_33_eocs.json')
    for obj in data:
        if obj['id'].startswith('EOC_BERSERK_GODO_LINE_'):obj.update(replace(obj,H,pred('GODO','WORK_OPEN')))
    write('effects/godo_dialogue_33_eocs.json',data)
    data=read('effects/flora_eocs.json');by=index(data)
    can=by['EOC_BERSERK_FLORA_CAN_RECEIVE']
    raw=copy.deepcopy(can['condition'])
    # On a direct rerun it already contains our narrow service gate.
    raw=replace(replace(raw,H,'u_is_avatar'),pred('FLORA','ALLOWED'),'u_is_avatar')
    EOCS.append(eoc(P+'FLORA_READY',[],raw))
    can['condition']=replace(can['condition'],H,pred('FLORA','ALLOWED'))
    by['EOC_BERSERK_FLORA_GIVE_ARMOR']['false_effect']=say('Флора не протягивает вам свёрток. Сначала поговорите с ней о доспехе.','info')
    write('effects/flora_eocs.json',data)
    data=read('effects/flora_dialogue_33_eocs.json')
    for obj in data:
        if obj['id'].startswith('EOC_BERSERK_FLORA33_P_'):obj.update(replace(obj,H,neg(pred('FLORA','KNOWS'))))
    write('effects/flora_dialogue_33_eocs.json',data)

    # Patch only the dialogue's interpretation of secrecy, not demonic anatomy.
    data=read('dialogue/godo.json');by=index(data)
    for id_ in ['TALK_BERSERK_GODO_EARLY_SWORD','TALK_BERSERK_GODO_SWORD','TALK_BERSERK_GODO_WORK']:
        by[id_].update(replace(by[id_],H,pred('GODO','WORK_OPEN')))
    for stem,ready_id in [('EARLY','EOC_BERSERK_GODO_EARLY_CLAIM'),('SWORD','EOC_BERSERK_GODO_SWORD_CLAIM')]:
        ready=replace(by_eoc(read('effects/godo_eocs.json'),ready_id)['condition'],pred('GODO','ALLOWED'),'u_is_avatar')
        EOCS.append(eoc(P+'GODO_'+stem+'_READY',[],ready))
        obj=by['TALK_BERSERK_GODO_EARLY_SWORD' if stem=='EARLY' else 'TALK_BERSERK_GODO_SWORD']
        inject(obj,response('GODO','Я пришёл забрать готовый клинок.','SUSPICION',both(pred('GODO','PENDING'),test(P+'GODO_'+stem+'_READY'))))
    # Rickert's crafts stay available after a truthful discussion. The lie only
    # hides the accepted path; it never manufactures a missing left hand.
    for obj in data:
        if obj['id'].startswith('TALK_BERSERK_RICKERT'):
            for row in list(obj.get('responses',[])):
                if row.get('topic')=='TALK_BERSERK_RICKERT_ORDERS' and not any(
                        n.get('run_eocs')=='EOC_BERSERK_JOURNAL_REPLACE_MISSING' for n in walk(row)):
                    old=row.get('condition','u_is_avatar')
                    if not any(n==pred('RICKERT','PENDING') for n in walk(old)):
                        copyrow=copy.deepcopy(row);copyrow['topic']=tid('RICKERT','SUSPICION');copyrow['condition']=both(old,pred('RICKERT','PENDING'))
                        row['condition']=both(old,neg(pred('RICKERT','PENDING')));obj['responses'].insert(obj['responses'].index(row),copyrow)
    obj=by['TALK_BERSERK_RICKERT_ROAD_READY']
    inject(obj,response('RICKERT','Ты хочешь о чём-то спросить, прежде чем мы пойдём?','SUSPICION',pred('RICKERT','PENDING')))
    write('dialogue/godo.json',data)
    data=read('dialogue/flora.json');by=index(data)
    for obj in data:
        # Old negative-H branches made Flora omniscient from the seed alone.
        obj.update(replace(obj,H,neg(pred('FLORA','KNOWS'))))
    for id_ in ['TALK_BERSERK_FLORA_ARMOR','TALK_BERSERK_FLORA_ARMOR_CONFIRM','TALK_BERSERK_FLORA_PARTIAL']:
        inject(by[id_],response('FLORA','Прежде чем ты передашь доспех…','SUSPICION',both(pred('FLORA','PENDING'),test(P+'FLORA_READY'))))
    write('dialogue/flora.json',data)

def by_eoc(data,id_):return index(data)[id_]
def inject(obj,r):
    obj['responses']=[x for x in obj['responses'] if x.get('topic')!=r['topic']]
    obj['responses'].insert(max(0,len(obj['responses'])-1),r)

def patch_roots():
    for filename in sorted(set(FILES.values())):
        data=read('dialogue/'+filename);by=index(data)
        for k in NAMES:
            if FILES[k]!=filename:continue
            root=by[ROOTS[k]]
            meaningful=either(D,{'u_has_item':'berserk_behelit'},{'u_has_item':'berserk_behelit_distorted'},both(eq('u_berserk_apostol_outcome',2),eq('u_berserk_apostol_return_state',2)))
            if k in ['GODO','RICKERT']:
                # Keep the approved personal confession entry. Shared followups
                # live inside it, avoiding two parallel transformation menus.
                meaningful=both(meaningful,H)
                old=by['TALK_BERSERK_APOSTOL_'+k]
                inject(old,response(k,'Как теперь жить с этой переменой?','MENU',D))
            if k=='FLORA':meaningful=both(meaningful,math('berserk_flora_siege_state <= 1'),neg(both(pred(k,'KNOWS'),neg(eq('u_berserk_flora33_demon_noticed')))))
            inject(root,response(k,'О странном камне и переменах.','MENU',meaningful))
            if k in ['GODO','RICKERT','FLORA']:
                inject(root,response(k,'Ты как-то смотришь на меня. Что-то не так?','SUSPICION',pred(k,'PENDING')))
            hook=run(k+'_NOTICE')
            if 'speaker_effect' not in root:root['speaker_effect']={'effect':[]}
            add_effect(root['speaker_effect'],hook)
        write('dialogue/'+filename,data)

FALLEN=[('JUDEAU','Джудо','judeau','рукоять метательного ножа',590,592),
        ('PIPPIN','Пиппин','pippin','сорванная застёжка доспеха',596,598),
        ('CORKUS','Коркус','corkus','расколотый фрагмент ножен',602,604),
        ('GASTON','Гастон','gaston','раздавленный швейный набор',608,610)]

def remains():
    data=read('effects/eclipse_field_scenes.json');by=index(data)
    material={
        'JUDEAU':'Среди разорванного снаряжения лежит обломанная рукоять метательного ножа. Дерево стёрто ладонью; у сломанного конца осталась тёмная нить.',
        'PIPPIN':'Тело крупного бойца осталось у тесного прохода. Рядом — тяжёлая застёжка, вырванная из разбитого доспеха. Свежие царапины пересекают старые следы молота.',
        'CORKUS':'Рядом с телом — расколотый обломок ножен. Кожа залоснилась под пальцами прежнего владельца; в разошедшемся шве застрял пепел.',
        'GASTON':'Под помятым нагрудником рассыпались иглы и обрывки ткани из раздавленного швейного набора. Мелкие, аккуратные починки уцелели среди грубых разрывов.'}
    for key,ru,stem,item,guts,ordinary in FALLEN:
        first=both(neg(flag('FALLEN',stem)),neg(eq('u_berserk_godo_witness_'+stem)))
        # The physical item and its established name remain unchanged. Only
        # Guts has personal recollections; the ordinary avatar describes a find.
        human=tr('Имя «'+ru+'» пока ничего вам не говорит. Здесь погиб человек; о его жизни вы ещё не знаете.')
        if key=='GASTON':human=tr('Швейный набор не объясняет, кем был погибший. Но кто-то берёг эти иглы и находил время для аккуратной работы.')
        personal=prose(guts)
        if key=='GASTON':personal=tr('Гастон говорил о жизни после войны. Вы узнаёте его швейный набор и вспоминаете, как всерьёз он строил эти планы.')
        obj=by['EOC_BERSERK_ECLIPSE_SCENE_'+key]
        obj['effect']=[{'if':first,'then':[
            {'if':test('FORGE_GUTS'),'then':say(material[key]+'\n\n'+personal,'info',True),'else':say(material[key]+'\n\n'+human,'info',True)},
            put('FALLEN',stem),math('u_berserk_godo_witness_'+stem+' = 1')],
            'else':say('Вы уже осмотрели это место. Найденные сведения сохранены.','info')},run('EOC_BERSERK_REF_SYNC')]
        title='У останков найдена '+item+'.'
        TOPICS.setdefault(tid('RICKERT','FINDS'),{'type':'talk_topic','id':tid('RICKERT','FINDS'),'dynamic_line':tr('Покажи, что нашёл, или опиши. Я постараюсь вспомнить.'),'responses':[back('RICKERT')]})
        inject(TOPICS[tid('RICKERT','FINDS')],response('RICKERT',title,'FIND_'+key,eq('u_berserk_godo_witness_'+stem)))
        answer={
          'JUDEAU':'Джудо. Он часто перебирал ножи в руке, даже когда разговаривал. Если рядом лежала такая рукоять… Спасибо, что рассказал.',
          'PIPPIN':'Пиппин. Я чинил его снаряжение. Он приносил сломанную вещь, молча ждал — и всегда помогал убрать после работы.',
          'CORKUS':'Коркус. Вечно ворчал на ножны, ремни, дорогу. Теперь даже его ворчания не хватает.',
          'GASTON':'Гастон. Он умел работать с тканью и говорил о деле, которым займётся после войны. Такие разговоры давали нам всем надежду.'}[key]
        topic('RICKERT','FIND_'+key,tr(answer),[response('RICKERT','Расскажи о нём.','TALK_BERSERK_RICKERT_REMEMBER_'+key),back('RICKERT')],
              [put('FALLEN','understood_'+stem),math('u_berserk_rickert_knows_death_'+stem+' = 1'),math('u_berserk_rickert_heard_losses = 1'),run('EOC_BERSERK_REF_SYNC')])
    write('effects/eclipse_field_scenes.json',data)
    data=read('dialogue/godo.json');inject(index(data)['TALK_BERSERK_RICKERT'],response('RICKERT','Я нашёл вещи среди погибших.','FINDS',either(*[eq('u_berserk_godo_witness_'+s) for _,_,s,*_ in FALLEN])))
    write('dialogue/godo.json',data)

def scenes():
    # Short ordinary ceremony. The man with a second Behelit from the first
    # draft is not inserted into the existing manifestation encounter.
    data=read('effects/eclipse_grasp_eocs.json');by=index(data)
    for node in walk(by['EOC_BERSERK_ECLIPSE_GRASP_BEGIN']['effect']):
        if 'u_message' in node:node['u_message']=prose(510)
    # Existing wounds are applied by the original resolver, never by prose.
    write('effects/eclipse_grasp_eocs.json',data)
    data=read('effects/eclipse_victory_eocs.json');by=index(data)
    for node in walk(by['EOC_BERSERK_ECLIPSE_VICTORY']['effect']):
        if 'u_message' in node:node['u_message']=tr(prose(519)+' Между вами и смыкающейся тьмой появляется Рыцарь-Череп.')
    write('effects/eclipse_victory_eocs.json',data)
    actors=[('GRIFFITH','mon_berserk_eclipse_griffith_active'),('ZODD','mon_berserk_flora_zodd'),('GRUNBELD','mon_berserk_flora_grunbeld')]
    for key,mon in actors:
        EOCS.append(eoc(P+key+'_LOCATION',[{'u_location_variable':{'context_val':'common33_actor_pos'}},
            {'run_eocs':P+key+'_OBSERVED','alpha_talker':'avatar'}],'u_is_monster'))
        if key=='GRIFFITH':
            body=[{'if':test('FORGE_GUTS'),'then':say(prose(498)+'\n\n«Гриффит!»\n\n'+prose(501),'warning',True),
                   'else':say(prose(498)+'\n\n«Ты управляешь ими?»\n\n'+prose(504),'warning',True)},put('SCENE','griffith')]
            condition=both(test('APOSTOL_HUMAN_ROUTE'),eq('u_berserk_eclipse_trial_active'),eq('u_berserk_eclipse_grasp_state',0))
        elif key=='ZODD':
            body=[{'if':test('FORGE_GUTS'),'then':say(prose(525)+'\n\nЗодд: «'+prose(527)+'»','warning'),
                   'else':say(prose(525)+'\n\nЗодд: «'+prose(529)+'»','warning')},put('SCENE','zodd')]
            condition=both(math('berserk_flora_siege_state >= 2'),math('berserk_flora_siege_state <= 4'))
        else:
            body=[say('Грюнбельд останавливается у внешнего рубежа. «Отступите от дома».','warning'),put('SCENE','grunbeld')]
            condition=both(math('berserk_flora_siege_state >= 2'),math('berserk_flora_siege_state <= 4'))
        EOCS.append(eoc(P+key+'_OBSERVED',body,both('u_is_avatar',condition,neg(flag('SCENE',key.lower())),{'u_can_see_location':{'context_val':'common33_actor_pos'}})))
    observe=[{'u_run_monster_eocs':[P+key+'_LOCATION'],'mtype_ids':[mon],'monster_range':50} for key,mon in actors]
    EOCS.append(eoc(P+'OBSERVE',observe,'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))
    data=read('effects/flora_siege_eocs.json');by=index(data)
    for key in ['ZODD','GRUNBELD']:
        add_effect(by['EOC_BERSERK_FLORA_'+key+'_ARRIVED'],run('OBSERVE_NOW'))
    # No named room is reported burning merely because a timer advanced.
    for obj in data:
        for node in walk(obj):
            if isinstance(node.get('u_message'),str):
                if node['u_message'].startswith('The outer roots give way.'):
                    node['u_message']=tr('Снаружи трещит дерево. Сквозь дым между стволами движутся демоны.')
                elif node['u_message'].startswith('Smoke spills through the gallery.'):
                    node['u_message']=tr('Дым становится гуще. Над домом с треском обламываются горящие ветви.')
    write('effects/flora_siege_eocs.json',data)
    EOCS.append(eoc(P+'OBSERVE_NOW',observe,'u_is_avatar'))
    data=read('effects/eclipse_expanded_final_eocs.json');by=index(data)
    add_effect(by['EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_ALREADY_PRESENT'],run('OBSERVE_NOW'))
    for node in walk(by['EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_BLOCKED']):
        if 'u_message' in node:node['u_message']=tr('Среди тел не видно того, к кому ведёт тропа.')
    write('effects/eclipse_expanded_final_eocs.json',data)
    data=read('effects/grunbeld_hunt_eocs.json');by=index(data)
    by['EOC_BERSERK_GRUNBELD_TRANSFORM_MESSAGE']['effect']=say(prose(538),'warning',True)
    write('effects/grunbeld_hunt_eocs.json',data)
    # Real hits, not mere proximity, allow one short reply from each attacker.
    for key,mon in actors[1:]:
        EOCS.append(eoc(P+key+'_HIT',[
            {'u_location_variable':{'context_val':'common33_combat_pos'}},
            {'run_eocs':P+key+'_COMBAT','alpha_talker':'avatar'}],
            both('u_is_monster','has_beta',either('npc_is_avatar','npc_following'),
                 math("u_monsters_nearby('"+mon+"', 'radius': 0, 'attitude': 'both') > 0")),
            eoc_type='EVENT',required_event='monster_takes_damage'))
        EOCS.append(eoc(P+key+'_COMBAT',[
            say(NAMES.get(key,'Зодд' if key=='ZODD' else 'Грюнбельд')+': «'+prose(532 if key=='ZODD' else 536)+'»','warning'),put('SCENE',key.lower()+'_combat')],
            both('u_is_avatar',neg(flag('SCENE',key.lower()+'_combat')),math('berserk_flora_siege_state >= 2'),math('berserk_flora_siege_state <= 4'),
                 {'u_can_see_location':{'context_val':'common33_combat_pos'}})))

def projections():
    data=read('monsters/apostle_projections.json')
    descriptions={'count':551,'wyald':553,'rosine':555,'grunbeld':557,'zodd':559,'griffith':561,'void':563,'slan':565,'ubik':567,'conrad':569}
    spells={'count':571,'grunbeld':574,'slan':575,'ubik':576,'conrad':577}
    translations={
        'count':('A heavy figure with human features. Its edges tremble like an image in muddy water.','一个带有人类特征的沉重身影，身体边缘如浑水中的倒影般颤动。'),
        'wyald':('A beastlike figure with a broad grin. Its outline lags behind its sudden movements.','一个咧嘴狞笑的兽形身影，轮廓跟不上它突如其来的动作。'),
        'rosine':('A winged silhouette hovers above the ground. The space behind it shows through the thin edges of its wings.','一个有翼的身影悬浮在地面上方，透过薄薄的翅缘可以看见后面的空间。'),
        'grunbeld':('An image enclosed in a heavy carapace. Heat glimmers in its cracks without casting the light it should.','一个裹在厚重甲壳中的幻影，裂缝中闪烁着热光，却没有照亮周围。'),
        'zodd':('An enormous beastlike figure. Its presence feels solid, but the edges of its body keep fading in and out.','一个巨大的兽形身影，存在感仿佛实物，身体边缘却不断显现又消失。'),
        'griffith':('A motionless winged image. Its face is clearer than the rest of its body.','一个静止的有翼幻影，面容比身体其他部分更加清晰。'),
        'void':('An inhuman figure that seems to bend straight lines around it.','一个非人的身影，周围的直线似乎都发生了扭曲。'),
        'slan':('An image of living flesh held in an alien space. Its movements are too smooth for its blurred outline.','一个被维系在异质空间中的血肉幻影，动作与模糊的轮廓相比过于流畅。'),
        'ubik':('A small floating figure. Look away, and it becomes hard to remember exactly where it was.','一个小小的漂浮身影，只要移开视线，就很难记起它刚才究竟在哪里。'),
        'conrad':('A squat image amid a cloudy suspension. Its contours slowly emerge, then dissolve again.','一个笼罩在浑浊悬浮物中的矮胖幻影，轮廓缓缓浮现，又再次消散。')}
    attacktexts={571:('A tendril bursts from the image.','一道触须从幻影体内猛然伸出。'),574:('Heat erupts from the cracks in the carapace.','热浪从甲壳裂缝中喷涌而出。'),575:('A strip of flesh lashes toward its target.','一道血肉长鞭向目标抽去。'),576:('For a moment, the distance to the figure seems to change.','一瞬间，你与那个身影的距离似乎发生了变化。'),577:('A caustic suspension thickens around the image.','腐蚀性的悬浮物在幻影周围聚集。')}
    for obj in data:
        stem=obj['id'].removeprefix('mon_berserk_projection_')
        en,zh=translations[stem];STRINGS[en]=prose(descriptions[stem]).strip('«».')+'.';CHINESE[en]=zh
        obj['description']=en
        en='The %s loses its outline and dissolves.';STRINGS[en]='%s теряет очертания и распадается.';CHINESE[en]='%s的轮廓消散，随之瓦解。'
        obj['death_function']['message']=en
        for attack in obj.get('special_attacks',[]):
            if attack.get('type')=='spell' and stem in spells:
                para=spells[stem];en,zh=attacktexts[para];STRINGS[en]=prose(para).strip('«».').replace('в вашу сторону','в сторону цели')+'.';CHINESE[en]=zh
                attack['monster_message']=en
    write('monsters/apostle_projections.json',data)
    data=read('effects/behelit_reward_eocs.json');by=index(data)
    notice={'if':both(math("distance('u', _berserk_behelit_drop_pos) <= 3"),{'u_can_see_location':{'context_val':'berserk_behelit_drop_pos'}}),
            'then':say(prose(581),'info')}
    add_effect(by['EOC_BERSERK_BEHELIT_BOSS_REWARD'],notice)
    write('effects/behelit_reward_eocs.json',data)

def existing_translations():
    pairs={
      'О странном камне и переменах.':'About the strange stone and the changes.',
      'Ты как-то смотришь на меня. Что-то не так?':'You are looking at me strangely. Is something wrong?',
      'Я пришёл забрать готовый клинок.':'I came to collect the finished blade.',
      'Ты хочешь о чём-то спросить, прежде чем мы пойдём?':'Did you want to ask something before we set out?',
      'Прежде чем ты передашь доспех…':'Before you hand me the armor...',
      'Как теперь жить с этой переменой?':'How do I live with this change?',
      'Я нашёл вещи среди погибших.':'I found belongings among the dead.'}
    for file in sorted(set(FILES.values())):
        data=read('dialogue/'+file)
        for obj in data:
            for r in obj.get('responses',[]):
                ru=r.get('text')
                if isinstance(ru,str) and ru in pairs:r['text']=pairs[ru];STRINGS[pairs[ru]]=ru
        write('dialogue/'+file,data)
    p=MOD/'lang/po/zh_CN.po';remaining=dict(CHINESE);blocks=[]
    for block in p.read_text().split('\n\n'):
        if not block.strip():continue
        key=po_source(block)
        if key in remaining:block='#. Shared projection prose 2026-10-23\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(remaining.pop(key),ensure_ascii=False)
        blocks.append(block.strip())
    for key,value in remaining.items():blocks.append('#. Shared projection prose 2026-10-23\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value,ensure_ascii=False))
    p.write_text('\n\n'.join(blocks)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/zh_CN/LC_MESSAGES/Berserk.mo'),str(p)],check=True)

def main():
    rules();concealment();reactions();patch_services();patch_roots();remains();scenes();projections();existing_translations()
    write('dialogue/common_reactions_33.json',list(TOPICS.values()))
    write('effects/common_reactions_33_eocs.json',EOCS+list(HELPERS.values()))
    localization()
    (ROOT/'docs/dialogue_sources/common-reactions-bindings-33.json').write_text(json.dumps({
        'source':'common-reactions-2026-10-23.json','paragraphs_used':sorted(USED),'topics':list(TOPICS),
        'native_trial':{'type':'LIE','base_chances':{'GODO':40,'RICKERT':50,'FLORA':25}},
        'scope':['Later short Griffith scene; no human form.','Named items retained; personal memory belongs only to Guts.',
                 'Persistent per-person concealment does not change the global demonic path.',
                 'No injury, fire, sacrifice, resident evacuation or ritual invented by prose.',
                 'Known optional reference remains read-only; no route search from archived sources.']},ensure_ascii=False,indent=2)+'\n')
    print('Shared reactions:',len(TOPICS),'topics; native lies, named remains, short scenes.')

if __name__=='__main__':main()
