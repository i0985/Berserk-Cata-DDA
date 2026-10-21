#!/usr/bin/env python3
"""Build Rickert's approved script without replacing the forge or paid orders.

Trust uses the real NPC opinion. Anatomy and rare loot are built separately by
build_apostol_body_rules_33.py. Source indices refer to the full owner file.
"""
import hashlib
import json
import re
import subprocess

from recover_apostol_33 import ROOT, MOD, read, write, index, upsert, walk, eoc, math, test, both
from recovery_33_translations import source

SOURCE=json.loads((ROOT/'docs/dialogue_sources/rickert-2026-10-21.json').read_text())['paragraphs']
STRINGS={}; TOPICS={}; HELPERS={}
G=test('EOC_BERSERK_FORGE_GUTS')
BEFORE=test('EOC_BERSERK_FORGE_BEFORE_ECLIPSE')
AFTER=test('EOC_BERSERK_FORGE_AFTER_ECLIPSE')
MET=test('EOC_BERSERK_GODO_RICKERT_ACQUAINTED')
RICKERT=test('EOC_BERSERK_GODO_AT_RICKERT')
FORGE=test('EOC_BERSERK_GODO_AT_RICKERT_FORGE')
HAND=test('EOC_BERSERK_DIALOGUE_MISSING_LEFT_HAND')
HAS_ARM=test('EOC_BERSERK_GODO_HAS_ARM')
INSTALLED={'u_has_bionics':'bio_berserk_arm_cannon'}
LOOSE={'u_has_items':{'item':'bio_berserk_arm_cannon','count':1}}
FOLLOW='npc_following'
HUMAN=test('EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED')
KNOWS=test('EOC_BERSERK_APOSTOL_RICKERT_KNOWS_GIFT')
WAKE=test('EOC_BERSERK_RICKERT_DIALOGUE_WAKE')
WITNESS=test('EOC_BERSERK_GODO_WITNESSED_ECLIPSE')
NORMAL_WITNESS=both(math('u_berserk_eclipse_rescue_state == 2'),math('u_berserk_eclipse_route != 2'))


def neg(c):return {'not':c}
def either(*cs):return {'or':list(cs)}
def val(s,op='==',n=1):return math(f'u_berserk_rickert_{s} {op} {n}')
def nval(s,op='==',n=1):return math(f'n_berserk_rickert_{s} {op} {n}')
def setv(s,n=1):return math(f'u_berserk_rickert_{s} = {n}')
def run(s):return {'run_eocs':s if s.startswith('EOC_') else 'EOC_BERSERK_RICKERT_'+s}
def tid(s):return s if s.startswith('TALK_') else 'TALK_BERSERK_RICKERT'+('_'+s if s else '')
def tr(en,ru):
    assert en and ru
    STRINGS[en]=ru
    return en


def russian(i):
    text=SOURCE[i].strip()
    text=re.sub(r'^(?:Игрок(?:\s*\(Гатс\))?|Гатс|Рикерт)[^:\n]*:\s*','',text)
    # Standalone stage directions and all bracketed author instructions stay out.
    text=re.sub(r'^\([^\n]+\)\s*\n','',text)
    text=re.sub(r'\n\[.*','',text,flags=re.S)
    return text.strip()


def line(i,en):return tr(en,russian(i))
def choose(c,yes,no):
    if isinstance(c,str) or any(k in c for k in ['and','or','not']):
        key='EOC_BERSERK_RICKERT_LINE_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[key]=eoc(key,[],c);c=test(key)
    return {**c,'yes':yes,'no':no}


def response(ru,en,target='',condition=None,effect=None,once=None):
    if isinstance(ru,int):
        text=SOURCE[ru];match=re.search('«([^»]+)»',text)
        ru=match[1] if match else russian(ru)
    obj={'text':tr(en,ru),'topic':tid(target)}
    if once:
        condition=both(condition,val('read_'+once,'!=',1)) if condition else val('read_'+once,'!=',1)
        body=[] if effect is None else effect if isinstance(effect,list) else [effect]
        effect=body+[setv('read_'+once)]
    if condition is not None:obj['condition']=condition
    if effect is not None:obj['effect']=effect
    return obj


def back(target=''):return response('Я хотел спросить о другом.','I wanted to ask about something else.',target)
def topic(s,text,responses=None,effect=None):
    obj={'type':'talk_topic','id':tid(s),'dynamic_line':text,'responses':responses if responses is not None else [back()]}
    if effect:obj['speaker_effect']={'effect':effect}
    TOPICS[obj['id']]=obj
    return obj
def leaf(s,i,en,parent=''):return topic(s,line(i,en),[back(parent)])


def intros():
    fresh=both(neg(MET),neg(G));meet=run('EOC_BERSERK_GODO_MEET_RICKERT')
    ordinary=choose(MET,line(170,'Hey. Can you hear me? It is Rickert. Take it slowly. You are back at the forge.'),
        choose(math('u_berserk_forge_wake_context == 3'),line(247,'You are at the woodland forge. Godot lives here; he is a smith, and I help him. I am Rickert.'),line(209,'You are awake. Good. I am Rickert. We tended your wounds when you were brought here.')))
    # Details of tending wounds require a rescue-time presence record, not
    # Rickert's current proximity to a player who returned much later.
    awake=choose(FOLLOW,line(341,'You frightened me. Really. Next time, try opening your eyes a little sooner. I had time to imagine the worst.'),choose(G,line(285,'Guts?.. Guts, you are awake!'),ordinary))
    repeated=choose(val('bolts_pending'),tr('I have not forgotten your bolts. Have you come about the batch?','Про твои болты я не забыл. Насчёт заказа пришёл?'),
        choose(math('u_berserk_godo_arm_state == 1'),tr('I am still waiting for the metal for your hand.','Всё ещё жду металл для твоей руки.'),
        choose(math('u_berserk_godo_arm_state == 2'),tr('The first delivery is here. I still need the small fittings.','Первая поставка на месте. Ещё нужны мелкие детали.'),
        choose(math('u_berserk_godo_arm_state == 3'),tr('Your mechanism is being looked after. Shall we discuss the work?','Твоим механизмом занимаюсь. Поговорим о работе?'),
        choose(G,line(124,'Guts! I heard steps and thought Godot was sending me for charcoal again. Have you been here long?'),line(81,'Oh, you are alive! How was the road? Legs intact, equipment holding up?'))))))
    hello=choose(WAKE,awake,choose(FOLLOW,line(1800,'Shall we stop for a moment, or talk as we walk?'),
        choose(both(fresh,BEFORE),line(8,'Careful, do not step there. A pin the size of a fingernail. I have lost it in the grass twice already... Ah. Sorry. Are you here for Godot?'),
        choose(fresh,tr('Hello. I am Rickert; I help at the forge. What brings you here?','Привет. Я Рикерт, помогаю в кузнице. С чем пришёл?'),
        choose(both(G,AFTER),tr('Guts. Good to see you on your feet. What did you want to talk about?','Гатс. Хорошо, что ты на ногах. О чём хотел поговорить?'),repeated)))))
    hello=choose(both(KNOWS,neg(WAKE),neg(FOLLOW)),tr('I will listen. Just give me a little room while we talk.','Я выслушаю. Только дай мне немного места, пока говорим.'),hello)
    intro=both(neg(WAKE),fresh,neg(FOLLOW))
    rs=[
        response(11,'Yes. I need a smith.','INTRO_SMITH',intro,meet),
        response(12,'First I wanted to see what you are making.','INTRO_LOCK',intro,meet),
        response(13,'I am looking for somewhere to sleep.','INTRO_REST',intro,meet),
        response(296,'Wait. Who brought me here?','WAKE_RIDER',WAKE,meet),
        response('Рикерт… Спасибо, что помог.','Rickert... Thank you for helping.','WAKE_THANKS',WAKE,meet),
        response(298,'Give me some time.','WAKE_TIME',WAKE,meet),
        response(212,'I have been here before.','WAKE_BUILDING',both(WAKE,neg(MET),neg(G),math('u_berserk_forge_wake_context != 3')),meet),
        response(213,'I remember Godot, but we have not spoken.','WAKE_GODO',both(WAKE,neg(MET),neg(G),math('u_berserk_forge_wake_knew_godo == 1')),meet),
        response(251,'Is it safe here?','WAKE_SAFE',both(WAKE,neg(G)),meet),
        response(252,'Why did you take me in?','WAKE_WHY',both(WAKE,neg(G)),meet),
    ]
    menu=both(neg(WAKE),either(MET,G,FOLLOW))
    rs.extend(menu_responses(menu,meet))
    rs.append(response('Мне нужно идти.','I need to go.','GOODBYE',effect=meet))
    topic('',hello,rs,run('SYNC'))['//']='Approved Rickert dialogue 2026-10-21'
    # Old saved NPCs still use the same chat id. ENTER is only a compatible alias.
    topic('ENTER',tr('What would you like to ask?','О чём хотел спросить?'),[back()])
    topic('INTRO_SMITH',line(20,'He is at the forge. Wait until he puts down the hammer; otherwise he will not hear a thing. I am Rickert. I help him here.'),[
        response(23,'Does he always greet people like that?','INTRO_GODO'),back()])
    leaf('INTRO_GODO',27,'You have not even spoken to him yet! Sometimes he barks so loudly you want to turn around. Then he takes work every other smith would refuse.')
    topic('INTRO_LOCK',line(36,'Checking the trigger. Sometimes it releases a moment late. On a table you barely notice; with the string drawn, that little fault can cost a life.'),[
        response(39,'Did you notice the fault yourself?','INTRO_FAULT'),response(40,'Trying to make it stronger?','INTRO_STRONG'),back()])
    TOPICS[tid('INTRO_LOCK')]['responses'].insert(-1,response('Кстати, мы ведь ещё не представились.','We have not introduced ourselves yet.','INTRO_NAME',val('name_exchanged','!=',1)))
    topic('INTRO_NAME',line(49,'Rickert, by the way. And your name?'),[response('Представиться.','Introduce yourself.','INTRO_NAMED',effect=setv('name_exchanged')),back()])
    topic('INTRO_NAMED',tr('Good to meet you. Mind the parts on the cloth.','Рад знакомству. Только детали на тряпке не задень.'),[back()])
    leaf('INTRO_FAULT',43,'Yes. At first I thought I had assembled it badly. Took it apart, put it back together: same problem. Now I am looking for the part wearing faster than the others.','MECHANISMS')
    leaf('INTRO_STRONG',46,'For now, I would settle for it firing when I pull the trigger instead of when it feels like it. The rest can wait.','MECHANISMS')
    topic('INTRO_REST',line(60,'There is room upstairs. Tell Godot before staying, though, or he may mistake you for something worse than a traveler. Leave the tools where they are; if you need something, ask.'),[
        response(63,'Do you live here too?','HOME_LIFE'),back()],run('EOC_BERSERK_FORGE_SCENE_ALLOW_REST'))
    leaf('HOME_LIFE',66,'Yes. I work. Learn. Occasionally even sleep, when Godot cannot find another urgent job.','ORDERS')
    # Knight stays outside until the player's confirmed farewell.
    topic('WAKE_RIDER',choose(math('u_berserk_knight_farewell_confirmed == 1'),
        tr('A knight in a skull-shaped helm. He brought you here, then went on his way.','Рыцарь в шлеме, похожем на череп. Он принёс тебя сюда, а потом отправился дальше.'),
        tr('A knight in a skull-shaped helm. He brought you to the door. We were too busy tending your wounds to ask him much.','Рыцарь в шлеме, похожем на череп. Он принёс тебя к порогу. Мы больше занимались твоими ранами, чем расспросами.')),[back()])
    leaf('WAKE_THANKS',198,'I am glad you woke up. Really glad.')
    topic('WAKE_TIME',line(323,'All right. I am nearby if you need me.'),[response('Спасибо.','Thank you.','TALK_DONE')])
    leaf('WAKE_BUILDING',222,'Then you know the place. We only get to meet now. Not the best circumstances, but here we are.')
    leaf('WAKE_GODO',229,'He said he had seen you before. I mostly help with the work here. I will try to help you, too.')
    leaf('WAKE_SAFE',266,'For now, yes. It is quiet outside. We are nearby. We can talk about the rest when you feel better.')
    leaf('WAKE_WHY',274,'You needed help. We could give it. Do we need a better reason?')
    leaf('REUNION_LATER',351,'You came back... What happened to you? I was not there; I did not see. Tell me when you can. It does not have to be now.')


def menu_responses(c=None,effect=None):
    def withc(x):return both(c,x) if c and x else c or x
    return [
        response(365,'Show me what you are working on.','MECHANISMS',c,effect),
        response(366,'I need help with equipment.','ORDERS',c,effect),
        response(367,'About my order.','ORDER_STATUS',withc(test('EOC_BERSERK_RICKERT_HAS_ORDER')),effect),
        response(368,'Tell me about the Band of the Hawk.','BAND',c,effect),
        response(369,'About what happened...','ECLIPSE',withc(NORMAL_WITNESS),effect),
        response('О том месте, из которого я вернулся.','About the place I came back from.','CEREMONY_WITNESS',withc(both(WITNESS,neg(NORMAL_WITNESS))),effect),
        response(370,'I would like to know more about you.','PERSONAL',c,effect),
        response(371,'Could we travel together?','ROAD',withc(both(neg(FOLLOW),nval('recruit_refused','!=',1))),effect),
        response(372,'About our road.','COMPANION',withc(FOLLOW),effect),
        response('О твоём решении не идти со мной.','About your decision not to travel with me.','REFUSE_MENU',withc(nval('recruit_refused')),effect),
        response('Со мной происходит перемена.','Something is happening to me.','TALK_BERSERK_APOSTOL_RICKERT',withc(neg(HUMAN)),effect),
        response('Когда я вернулся, тебя рядом не было.','You were not there when I came back.','REUNION_LATER',withc(both(WITNESS,MET,val('care_present','!=',1),val('read_reunion','!=',1))),[effect,setv('read_reunion')] if effect else setv('read_reunion')),
        response('Насчёт доверия после моего обмана.','About trusting me after my lie.','TRUST_RECOVERY',withc(nval('lie_trust_pending')),effect),
    ]


def craft():
    topic('MECHANISMS',line(389,'With a crossbow I can help before the enemy reaches us. I am no swordsman. I choose a position early and try not to waste a shot; there may not be another.'),[
        response(392,'What if you miss?','TACTICS'),response(393,'Could it reload faster?','RELOAD'),
        response(394,'Would you rather learn the sword?','SWORDSMAN'),
        response(426,'Where do you get your ideas?','IDEAS'),
        response('В этом мире попадаются незнакомые тебе вещи.','This world has things you have never seen.','MODERN_OFFER'),
        response('Ты снова возишься со спуском?','Still working on that trigger?','INTRO_LOCK'),
        response('Мне нужны болты.','I need bolts.','BOLTS'),back()])
    TOPICS[tid('MECHANISMS')]['responses'].insert(-1,response('Всё возишься со своим арбалетом?','Still busy with your crossbow?','GUTS_CROSSBOW',both(G,BEFORE)))
    topic('GUTS_CROSSBOW',line(136,'You would not believe how much time one lousy part the size of a fingernail can eat.'),[
        response(139,'Take up a sword. Fewer parts: iron and an edge.','GUTS_SWORD'),back('MECHANISMS')])
    leaf('GUTS_SWORD',143,'I can barely lift your sword off the table. I will keep my little parts. Safer that way.','MECHANISMS')
    for s,i,en in [
        ('TACTICS',401,'Then I will be glad I chose cover before firing. Looking for it with a blade at your throat is a little late.'),
        ('RELOAD',409,'The mechanism can change. Convenience costs weight, complexity or reliability. Make it lighter, and rain may trouble it; faster, and it may jam. I have more testing to do.'),
        ('SWORDSMAN',417,'I would like to. But I will not become stronger than everyone who attacks me. Better to do what I know well than do badly what others live for.')]:leaf(s,i,en,'MECHANISMS')
    topic('IDEAS',line(429,'Usually something starts annoying me. A strap rubs, a fastening takes too long to open, a part cannot be replaced on the road. Then I cannot stop thinking until I find a way to fix it.'),[
        response(432,'Does it always work?','IDEAS_FAIL'),response(433,'Does Godot help?','APPRENTICE'),back('MECHANISMS')])
    leaf('IDEAS_FAIL',441,'Of course not. Sometimes fixing one problem creates a worse one. That is why I test things here, again and again. Better I break it safely than someone breaks it in battle.','IDEAS')
    leaf('APPRENTICE',448,'In his own way. I know more about mechanisms; he sees through the metal. I spend half a day on a clever drawing, he looks once and says, "It will break here." He is almost always right.','IDEAS')
    topic('MODERN_OFFER',tr('Have you brought something? Show me before I try to guess how it works.','Что-нибудь принёс? Покажи, прежде чем я начну гадать, как оно устроено.'),[
        response('Вот, посмотри.','Here, take a look.','MODERN',test('EOC_BERSERK_RICKERT_HAS_MODERN_ITEM'),setv('seen_modern')),
        response('Ты уже видел такие вещи. Что думаешь о них?','You have seen those things before. What do you think?','MODERN',val('seen_modern')),back('MECHANISMS')])
    topic('MODERN',line(461,'Sometimes I can tell what a thing does from its shape. But how they made it so small and even... I would spend a week fitting one part by hand.'),[
        response(464,'Could you reproduce it?','MODERN_COPY'),response(465,'Are you interested?','MODERN_INTEREST'),back('MECHANISMS')])
    leaf('MODERN_COPY',473,'Some parts, perhaps. The rest I would have to learn from nothing, and I am not sure our forge has the tools. I will not promise to build an unfamiliar thing after looking once.','MODERN')
    leaf('MODERN_INTEREST',481,'Very. Just bring things that are unloaded and cannot go off by themselves. I have to examine them with my hands.','MODERN')
    topic('ORDERS',tr('Godot handles blades. I can make bolts; ask me about what you need.','Клинки — к Годо. Я могу сделать болты; спрашивай, что нужно.'),[
        response(493,'Can you do something about my hand?','TALK_BERSERK_GODO_ARM',HAND),
        response('Насчёт болтов.','About bolts.','BOLTS'),
        response('Где можно отдохнуть?','Where can I rest?','INTRO_REST',either(FORGE,{'u_at_om_location':'berserk_godo_loft'})),
        response('Каково работать с Годо?','What is working with Godot like?','GODO'),
        response('Мне нужен новый дорожный журнал.','I need a new road journal.','ORDERS',neg({'u_has_item':'berserk_campaign_journal'}),run('EOC_BERSERK_JOURNAL_REPLACE_MISSING')),back()])
    topic('ORDER_STATUS',tr('Which work did you want to discuss?','О какой работе хотел спросить?'),[
        response('О протезе.','About the prosthesis.','TALK_BERSERK_GODO_ARM',HAND),
        response('Рука восстановилась. Что с моим заказом?','My hand has grown back. What about my order?','ARM_REGROWN_ORDER',both(math('u_berserk_apostol_left_hand_regrown == 1'),math('u_berserk_godo_arm_state > 0'),math('u_berserk_godo_arm_state < 4'))),
        response('О болтах.','About the bolts.','BOLTS',val('bolts_pending')),
        response(1769,'Will you still finish my order?','ORDER_AFTER_REFUSAL',both(nval('recruit_refused'),test('EOC_BERSERK_RICKERT_HAS_ORDER'))),back()])
    leaf('ORDER_AFTER_REFUSAL',1773,'I promised to finish the work, and I keep my word. That does not change my decision about traveling with you. Work is one thing; the road is another.','ORDER_STATUS')
    topic('ARM_REGROWN_ORDER',choose(math('u_berserk_godo_arm_state >= 2'),tr('You no longer need a replacement hand. I still have the materials you brought; you can take them back.','Тебе больше не нужна замена кисти. Материалы, которые ты принёс, у меня. Можешь забрать их.'),tr('You no longer need a replacement hand. Let us close that order.','Тебе больше не нужна замена кисти. Закроем этот заказ.')),[
        response('Закрыть заказ и забрать переданные материалы.','Close the order and collect any materials delivered.','ARM_REFUNDED',test('EOC_BERSERK_GODO_ARM_REFUND'),run('EOC_BERSERK_GODO_ARM_REFUND')),back('ORDER_STATUS')])
    leaf('GODO',150,'Godot grumbles, but he lets me try. When I ruin something, he makes me explain what I did wrong. Sometimes that is harder than doing it over.','PERSONAL')


def prosthesis(old):
    active=both(math('u_berserk_godo_arm_state > 0'),math('u_berserk_godo_arm_state < 4'))
    topic('TALK_BERSERK_GODO_ARM',choose(neg(HAND),tr('We can talk about the crossbow or another job.','Можем поговорить об арбалете или другой работе.'),
        choose(INSTALLED,line(697,'How is the mounting? Does it press or chafe?'),choose(LOOSE,line(668,'You have not fitted it yet? I can show you again.'),
        choose(math('u_berserk_godo_arm_state == 4'),tr('That order is settled. If there is a problem with the device, tell me.','Этот заказ мы закончили. Если с устройством что-то не так, скажи.'),
        choose(active,tr('Let us go over what is still needed.','Давай посмотрим, что ещё нужно.'),tr('I think so. First a mounting that holds without pressing on the wound. Then the mechanical hand and the small barrel inside.','Думаю, да. Сначала нужно крепление, которое не будет давить на рану. Потом соберу механическую кисть со скрытым стволом.')))))),[
        response(499,'You want to put a cannon in it?','ARM_GUN',HAND,once='arm_gun'),
        response(500,'First I just need to hold things again.','ARM_GRIP',HAND,once='arm_grip'),
        response(501,'Will it survive a shot?','ARM_STRENGTH',HAND,once='arm_strength'),
        response(528,'What will you need?','TALK_BERSERK_GODO_ARM_STATUS',HAND),
        response('Насчёт крепления.','About the mounting.','ARM_FITTED',both(HAND,INSTALLED)),
        response(736,'About the arm cannon.','CANNON',both(HAND,INSTALLED)),
        response(671,'Remind me how to fit it.','ARM',both(HAND,LOOSE,neg(INSTALLED))),
        response('Этот механизм я собрал сам.','I assembled this mechanism myself.','PRAISE',both(HAND,HAS_ARM,math('u_berserk_arm_cannon_self_made == 1'))),
        response(832,'I came across this device.','ARM_FOUND',both(HAND,LOOSE,math('u_berserk_arm_cannon_self_made != 1'),val('arm_delivered','!=',1))),
        response(851,'Will you still help with my hand while my body changes?','ARM_CHANGED',both(HAND,neg(HUMAN))),
        response(529,'I am not ready for this yet.','ARM_LATER',both(HAND,neg(active),neg(HAS_ARM))),back()])
    for s,i,en in [
        ('ARM_GUN',508,'Yes. One shot, then it must be loaded again by hand. There is little space. But at arm\'s length one shot may be enough to keep you alive.'),
        ('ARM_GRIP',516,'The mounting and grip come first. If it cannot be worn all day without rubbing or falling apart, a barrel will be no use.'),
        ('ARM_STRENGTH',523,'It needs good metal and careful fitting. I will test it before handing it over. But a charge is a charge; you still have to be careful.'),
        ('ARM_LATER',544,'All right. Come back to it when you decide. I will not hurry you.')]:leaf(s,i,en,'TALK_BERSERK_GODO_ARM')
    topic('ARM_MAKER',line(561,'Godot can help with the metal, but I will assemble and fit the mechanism. He thinks in blades and armor. This is smaller, finer work.'),[
        response(564,'Are you sure you can do it?','ARM_CONFIDENCE'),response(565,'I trust you.','TALK_BERSERK_GODO_ARM_STATUS'),back('TALK_BERSERK_GODO_ARM')])
    leaf('ARM_CONFIDENCE',573,'I am sure I will give it all the care I can. If it does not work, I will remake it as often as I must. You have to live with this hand.','TALK_BERSERK_GODO_ARM')
    status=choose(HAS_ARM,tr('You already have a mechanism. We should look after that one.','Механизм у тебя уже есть. Лучше займёмся им.'),
        choose(math('u_berserk_godo_arm_state == 0'),tr('First, 8 lumps of steel and 2 pipes. After that, 2 springs, 4 leather patches and 200 charcoal. I will need six hours after the last delivery.','Сначала — 8 кусков стали и 2 трубы. Потом — 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля. После последней поставки мне понадобятся шесть часов.'),
        choose(math('u_berserk_godo_arm_state == 1'),tr('Right now I need 8 lumps of steel and 2 pipes. Bring them together.','Сейчас нужны 8 кусков стали и 2 трубы. Принеси их вместе.'),
        choose(math('u_berserk_godo_arm_state == 2'),tr('The steel and pipes are here. Next I need 2 springs, 4 leather patches and 200 charcoal. Do not bring the first delivery again.','Сталь и трубы на месте. Теперь нужны 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля. Первую поставку повторять не надо.'),
        choose(math('u_berserk_godo_arm_state == 3'),choose(math("time('now') >= u_berserk_godo_arm_ready_at"),line(621,'Finished. Let me show you the mounting first.'),line(606,'Not finished yet. The materials are here; do not worry. Go about your business for now.')),
               tr('We have settled this order.','С этим заказом мы закончили.'))))))
    rs=[response('Давай сделаем.','Let us make it.','TALK_BERSERK_GODO_ARM_STATUS',test('EOC_BERSERK_GODO_START_ARM'),run('EOC_BERSERK_GODO_START_ARM')),
        response('Вот сталь и трубы.','Here are the steel and pipes.','ARM_DELIVERY',test('EOC_BERSERK_GODO_ARM_METAL'),run('EOC_BERSERK_GODO_ARM_METAL')),
        response('Вот пружины, кожа и уголь.','Here are the springs, leather and charcoal.','ARM_DELIVERY',test('EOC_BERSERK_GODO_ARM_FITTINGS'),run('EOC_BERSERK_GODO_ARM_FITTINGS')),
        response('Забрать готовое устройство.','Collect the finished device.','ARM_RECEIVED',both(test('EOC_BERSERK_GODO_ARM_CLAIM'),neg(HAS_ARM)),run('EOC_BERSERK_GODO_ARM_CLAIM')),
        response('У меня уже есть устройство. Верни материалы.','I already have a device. Return the materials.','ARM_REFUNDED',test('EOC_BERSERK_GODO_ARM_REFUND'),run('EOC_BERSERK_GODO_ARM_REFUND')),
        response(557,'Would Godot be better suited to this?','ARM_MAKER',HAND),
        response('Могу я собрать механизм сам?','Could I assemble the mechanism myself?','ARM_SELF',HAND),
        response(609,'What is the hardest part?','ARM_DIFFICULT',both(HAND,math('u_berserk_godo_arm_state == 3')),once='arm_difficult'),
        response('Над этим можно работать в дороге?','Can you do this on the road?','ARM_FORGE'),
        response(1982,'I will look for what you need.','GOODBYE_MATERIALS',both(HAND,either(math('u_berserk_godo_arm_state == 1'),math('u_berserk_godo_arm_state == 2')))),back('TALK_BERSERK_GODO_ARM')]
    topic('TALK_BERSERK_GODO_ARM_STATUS',choose(HAND,status,tr('You do not need a replacement hand.','Тебе не нужна замена кисти.')),rs)
    topic('ARM_DELIVERY',choose(math('u_berserk_godo_arm_state == 3'),tr('Now everything is here. Give me six hours to assemble and test it properly.','Теперь всё есть. Дай мне шесть часов на сборку и проверку.'),tr('Yes, this will do. I can work on the base. Bring the smaller fittings when you can.','Да, подойдёт. С основой теперь разберусь. Мелкие детали принесёшь, когда сможешь.')),[back('TALK_BERSERK_GODO_ARM_STATUS')])
    leaf('ARM_DIFFICULT',610,'Getting the parts out of one another\'s way. On a quiet table everything moves easily. Add straps, load, grit and sweat, and a generous gap is suddenly too small.','TALK_BERSERK_GODO_ARM_STATUS')
    topic('ARM_FORGE',tr('We need the forge for the heavy parts. If we travel together, we will return here to hand over the materials and collect the mechanism.','Для тяжёлых деталей нужна кузница. Если пойдём вместе, за передачей материалов и готовым механизмом вернёмся сюда.'),[back('TALK_BERSERK_GODO_ARM_STATUS')])
    topic('ARM_REFUNDED',tr('Here is what you brought. Keep the device you already have.','Вот то, что ты принёс. Пользуйся устройством, которое у тебя уже есть.'),[back('TALK_BERSERK_GODO_ARM')])
    topic('ARM_RECEIVED',line(626,'Here is where it holds to the arm. The load goes here, not on the stump. Fit it without a charge first. If it presses or moves, do not simply tighten it harder.'),[
        response(629,'How do I put it on?','ARM'),response(630,'What about the cannon?','ARM_CANNON_FIRST'),response(631,'Thank you, Rickert.','ARM_THANKS'),back()])
    leaf('ARM',638,'Take the device and start with the main mounting. You can fasten it yourself. I will show you the order of the straps so nothing twists.','TALK_BERSERK_GODO_ARM')
    leaf('ARM_CANNON_FIRST',648,'Get used to the hand first. Loading and using the barrel take separate practice. Before doing anything with it, check where that barrel is pointing.','TALK_BERSERK_GODO_ARM')
    leaf('ARM_THANKS',656,'You are welcome. It may feel strange or unpleasant at first. Give yourself time; a body does not get used to it at once.','TALK_BERSERK_GODO_ARM')
    topic('ARM_FITTED',line(697,'How is the mounting? Does it press or chafe?'),[
        response(700,'Still feels strange.','ARM_UNFAMILIAR'),response(701,'It holds well.','ARM_HOLDS'),response(702,'I want to check the device.','CARE'),back('TALK_BERSERK_GODO_ARM')])
    leaf('ARM_UNFAMILIAR',709,'Start small: pick up something light, put it down, repeat. Let yourself get used to the weight before testing it in battle.','ARM_FITTED')
    leaf('ARM_HOLDS',717,'Good. Still check the straps after a long road. Dust, water and strain will tell in time.','ARM_FITTED')
    topic('CANNON',line(739,'Of course. The mounting, or the mechanism itself?'),[
        response(742,'How should I care for it?','CANNON_CARE'),response(743,'Why only one shot?','CANNON_SHOT'),response(744,'Could you make another?','CANNON_SECOND'),back('TALK_BERSERK_GODO_ARM')])
    leaf('CANNON_CARE',751,'Keep the moving parts clean of grit and fouling. Check the mounting after every shot. If something moves differently, find out why before firing again.','CANNON')
    leaf('CANNON_SHOT',758,'There is little room and weight to spare. Another loading mechanism would take space the hand needs to grip. I chose the hand.','CANNON')
    leaf('CANNON_SECOND',766,'You already have one to use. If something is wrong with it, let us look at that rather than make a second for storage.','CANNON')
    topic('CARE',tr('Keep grit out of the joint and watch the straps. At the forge I can repair a damaged loose mechanism: one steel lump and 50 charcoal.','Не допускай песка в шарнир и следи за ремнями. В кузнице могу починить повреждённый незакреплённый механизм: один кусок стали и 50 единиц древесного угля.'),[
        response('Показать повреждённый механизм.','Show the damaged mechanism.','CARE',test('EOC_BERSERK_RICKERT_REPAIR_PICK'),run('EOC_BERSERK_RICKERT_REPAIR_PICK')),back('TALK_BERSERK_GODO_ARM')])
    topic('PRAISE',choose(math('u_berserk_arm_cannon_self_made_one_hand == 1'),line(794,'Wait... You assembled this without the hand? Fitting those small parts with one hand is no small task. I am impressed. I would have sworn at every step.'),line(821,'You understand mechanisms. Sound work. How does it behave under load?')),[
        response(797,'I had to adapt.','PRAISE_ADAPT',math('u_berserk_arm_cannon_self_made_one_hand == 1')),
        response(798,'Not on the first try.','PRAISE_TRIES',math('u_berserk_arm_cannon_self_made_one_hand == 1')),back('TALK_BERSERK_GODO_ARM')])
    leaf('PRAISE_ADAPT',805,'Would you show me how? It could help someone else in the same position.','TALK_BERSERK_GODO_ARM')
    leaf('PRAISE_TRIES',813,'I believe it. Some parts are hard enough with two hands. The result matters more than how many tries it took.','TALK_BERSERK_GODO_ARM')
    leaf('ARM_FOUND',836,'Let me see. First we should check whether the mounting fits you. A device made for another arm can rub you raw in an hour.','TALK_BERSERK_GODO_ARM')
    topic('ARM_CHANGED',line(855,'I can try. I need to see how your body is changing. If the mounting stops fitting, do not force it; it could hurt you more than help.'),[
        response(858,'Are you afraid of me?','ARM_CHANGED_FEAR'),response(859,'I still need help.','TALK_BERSERK_GODO_ARM_STATUS'),back('TALK_BERSERK_GODO_ARM')],run('EOC_BERSERK_APOSTOL_TELL_RICKERT'))
    leaf('ARM_CHANGED_FEAR',867,'I am worried. I do not know how this ends, for you or the people around you. But you are standing here asking for help. For now that is enough for me to listen.','TALK_BERSERK_GODO_ARM')
    # Retained public prosthesis IDs used by old conversations/journals.
    for s,target in [('TALK_BERSERK_GODO_FITTING','ARM'),('TALK_BERSERK_GODO_SELF','ARM_SELF'),('TALK_BERSERK_GODO_PRAISE','PRAISE')]:
        topic(s,tr('What did you want to know about the mechanism?','Что хотел узнать о механизме?'),[back(target)])
    topic('ARM_SELF',tr('It is precise metalwork. You need a forge, suitable tools and a good understanding of mechanisms. If you would rather bring materials, I can assemble it here.','Это точная работа по металлу. Нужны кузница, подходящие инструменты и хорошее понимание механизмов. Если решишь принести материалы, я соберу устройство здесь.'),[back('TALK_BERSERK_GODO_ARM')])


def bolts():
    status=choose(val('bolts_pending'),choose(math("time('now') >= u_berserk_rickert_bolts_ready_at"),tr('Your ten bolts are finished. Come for them at the forge.','Твои десять болтов готовы. Заберёшь их в кузнице.'),tr('I am working on the batch. Half an hour from the delivery; the materials are already here.','Занимаюсь партией. Полчаса после поставки; материалы уже здесь.')),
        tr('I make wooden bodkin bolts with steel tips. For ten: 1 steel chunk, 1 stick, 20 thread, 10 feathers and 50 charcoal. Half an hour at the forge.','Делаю деревянные болты со стальными гранёными наконечниками. На десять штук нужны 1 обломок стали, 1 палка, 20 единиц ниток, 10 перьев и 50 единиц древесного угля. Полчаса работы в кузнице.'))
    topic('BOLTS',status,[
        response(909,'Make a batch.','BOLTS_ACCEPTED',neg(val('bolts_pending')),setv('bolts_requested')),
        response(913,'Here is everything you need.','BOLTS_DELIVERED',test('EOC_BERSERK_RICKERT_ORDER_BOLTS'),run('EOC_BERSERK_RICKERT_ORDER_BOLTS')),
        response('Забрать готовые болты.','Collect the finished bolts.','BOLTS_COLLECTED',test('EOC_BERSERK_RICKERT_COLLECT_BOLTS'),run('EOC_BERSERK_RICKERT_COLLECT_BOLTS')),
        response(899,'What types can you make?','BOLT_LIMITS'),back('ORDERS')],math('u_berserk_journal_order_bolts = 1'))
    leaf('BOLTS_ACCEPTED',910,'Agreed. Bring the materials and I will get to it.','BOLTS')
    leaf('BOLTS_DELIVERED',914,'Good, hand them over. I will check the dimensions and quality.','BOLTS')
    leaf('BOLTS_COLLECTED',918,'Here are your bolts. Check how they sit in the groove before setting out; better to find a bad fit now than in battle.','BOLTS')
    topic('BOLT_LIMITS',tr('Wooden shafts and pointed steel tips. The point helps, but the bow and the shot still matter.','Деревянное древко, стальной гранёный наконечник. Острие помогает, но многое зависит от арбалета и самого выстрела.'),[back('BOLTS')])


def band_and_story():
    known_dead=either(val('eclipse_story','==',1),val('eclipse_story','==',2),val('heard_losses'))
    topic('BAND',line(933,'What would you like to know? What I remember most are little things: who sat where by the fire, who always lost something and searched for it in the dark.'),[
        response(936,'What were they like away from battle?','HAWKS'),response(937,'Did you fight with them?','BAND_FIGHT'),
        response(938,'What was Griffith like?','COMMANDER'),
        response('О Джудо, Пиппине, Коркусе и Гастоне.','About Judeau, Pippin, Corkus and Gaston.','ECLIPSE_MEMORIES'),
        response(1003,'Do you miss the camp?','HAWK_HOME',both(G,BEFORE)),
        response('О случившемся с отрядом.','About what happened to the Band.','ECLIPSE',NORMAL_WITNESS),back()])
    leaf('HAWKS',945,'Different people. Hearing us argue, laugh and share the last bread by the fire, you would never guess we would fight shoulder to shoulder the next morning.','BAND')
    topic('BAND_FIGHT',choose(G,tr('Yes. I did what I could. Not everyone can cut through a battle the way you can, but there was work for all of us.','Да. Старался делать то, что умел. Не каждый может рубиться, как ты, но дело находилось для всех.'),line(952,'Yes. Not everyone could fight like Guts, but there was work for all of us, even me with a crossbow.')),[back('BAND')],setv('strength_compared'))
    topic('COMMANDER',choose(val('eclipse_story','==',1),line(976,'I thought I knew the answer. I thought I was following someone who led us toward something real.'),
        choose(known_dead,tr('I believed in him. You say the Band is gone, but I still do not know what became of him.','Я верил ему. Ты говоришь, отряда больше нет, но я всё ещё не знаю, что стало с ним.'),line(960,'Beside him it felt like we were going somewhere, not just surviving another battle. That is why people followed. Why I followed.'))),[
        response('Что ты думаешь о нём теперь?','What do you think of him now?','COMMANDER_AFTER',val('eclipse_story','==',1)),back('BAND')])
    leaf('COMMANDER_AFTER',981,'Now I do not know what to say. Perhaps the person he was with me was real too. Perhaps not. I do not want to guess which parts deserved my faith.','BAND')
    topic('HAWK_HOME',line(1007,'Some things, yes. Others, not a bit.'),[response(1010,'For example?','CAMP'),back('BAND')])
    topic('CAMP',line(1013,'I do not miss the wet blanket. Or everyone remembering broken equipment a minute before marching, as if they had planned it.'),[
        response(1016,'You still do that here.','CAMP_WORK'),response(1017,'What do you miss?','CAMP_PEOPLE'),back('BAND')])
    leaf('CAMP_WORK',1025,'Here I can at least say "wait" without chasing the marching Band with my tools.','BAND')
    leaf('CAMP_PEOPLE',1033,'The people. Even when they would not let me work in peace. It is quiet now. Too quiet.','BAND')
    first=both(NORMAL_WITNESS,either(val('eclipse_story','==',0),val('eclipse_story','==',3)))
    topic('ECLIPSE',choose(neg(NORMAL_WITNESS),tr('Tell me what you actually know.','Расскажи, что ты действительно знаешь.'),
        choose(val('eclipse_story','==',1),line(1148,'Yes. Not all at once, though. A piece at a time, or I start drowning in it again.'),
        choose(val('eclipse_story','==',2),line(1241,'Have you learned anything about the people who attacked the camp, or where they took Griffith?'),
        choose(val('eclipse_story','==',3),line(1322,'I am listening.'),choose(G,tr('Guts... Where are they? What happened to everyone?','Гатс… Где они? Что случилось с остальными?'),tr('You were there. Will you tell me what you saw?','Ты был там. Расскажешь, что видел?')))))),[
        response('Отряд погиб.','The Band was lost.','ECLIPSE_LOST',first,setv('heard_losses')),
        response('Я видел, что произошло. Гриффит отдал людей чудовищам.','I saw what happened. Griffith gave people to those creatures.','ECLIPSE_TRUTH',both(first,neg(G)),run('STORY_TRUTH')),
        response(1048,'Griffith offered them as a sacrifice. The monsters were waiting.','ECLIPSE_TRUTH',both(first,G),run('STORY_TRUTH')),
        response(1049,'People and beasts attacked them. Griffith was taken away.','ECLIPSE_LIE',first,run('STORY_LIE')),
        response(1050,'I cannot talk about it now.','ECLIPSE_SILENCE',first,run('STORY_SILENCE')),
        response(1151,'About our friends.','ECLIPSE_MEMORIES',val('eclipse_story','==',1)),
        response(1152,'About Griffith.','TRUTH_GRIFFITH',val('eclipse_story','==',1)),
        response(1153,'About what comes next.','ECLIPSE_LIVING',val('eclipse_story','==',1)),
        response(1244,'Nothing yet.','LIE_NOTHING',val('eclipse_story','==',2)),
        response(1245,'I have to correct what I told you.','CONFESSION',val('eclipse_story','==',2)),
        response('Сколько людей ты потерял?','How many people did you lose?','ECLIPSE_LOSSES',known_dead),back()])
    topic('ECLIPSE_LOST',line(1045,'Dead?.. All of them?.. Who attacked them?'),[
        response(1048,'Griffith offered them as a sacrifice. The monsters were waiting.','ECLIPSE_TRUTH',both(first,G),run('STORY_TRUTH')),
        response(1065,'I saw the ceremony. People were given to monsters. Griffith stood at its center.','ECLIPSE_TRUTH',both(first,neg(G)),run('STORY_TRUTH')),
        response(1049,'People and beasts attacked them. Griffith was taken away.','ECLIPSE_LIE',first,run('STORY_LIE')),
        response(1050,'I cannot talk about it now.','ECLIPSE_SILENCE',first,run('STORY_SILENCE')),back()])
    topic('ECLIPSE_TRUTH',line(1075,'Wait... Griffith? Are you saying he knew what they would do to them? Knew beforehand?'),[
        response(1078,'Yes.','TRUTH_CERTAIN',G),
        response(1079,'I do not know what was in his mind. I saw what happened.','TRUTH_SEEN'),back('TRUTH_AFTER')])
    leaf('TRUTH_CERTAIN',1087,'I try to picture him there, beside all that... and I cannot. He knew their names. Every one. They followed him through more than I could count.','TRUTH_AFTER')
    leaf('TRUTH_SEEN',1095,'Then tell me what you saw. No more. I do not want guesses, even if they might be easier to live with.','TRUTH_AFTER')
    topic('TRUTH_AFTER',line(1106,'I need time. I hear you. What I remember of him does not fit your words yet. That is not your fault.'),[
        response(1109,'I understand what you mean.','TRUTH_THANKS'),response(1110,'You do not believe me?','TRUTH_BELIEVE'),response(1111,'Would you like to be alone?','TRUTH_ALONE'),back()])
    leaf('TRUTH_THANKS',1118,'Thank you for telling me. I do not know what else to say.')
    leaf('TRUTH_BELIEVE',1126,'I am not saying you are lying. I am trying to understand how the person I knew, or thought I knew, could do that. It is not the same thing.')
    topic('TRUTH_ALONE',line(1133,'For a little while. We will talk again. I will not hide from it forever.'),[response('Хорошо.','All right.','TALK_DONE')])
    topic('TRUTH_GRIFFITH',line(1170,'I keep remembering his words, trying to understand when we stopped being people to him and became steps. A price. I have no answer.'),[
        response(1173,'Do you want to find him?','TRUTH_FIND'),back('ECLIPSE')])
    leaf('TRUTH_FIND',1177,'I want to hear him answer. Ask him to his face: why? What I would do after hearing it... I do not know.','ECLIPSE')
    leaf('ECLIPSE_LIVING',1187,'Today I can finish the work I started. My hands at least know what to do. Tomorrow I will try to understand the rest. One day at a time.','ECLIPSE')
    topic('ECLIPSE_LIE',line(1201,'Then he might still be alive?'),[
        response(1204,'I do not know what became of him.','LIE_UNKNOWN'),response(1205,'Looking for him now would be pointless.','LIE_SEARCH'),response(1206,'Do not ask any more.','LIE_ENOUGH'),back()])
    leaf('LIE_UNKNOWN',1213,'Then I cannot count him among the lost yet. Not until I know.')
    leaf('LIE_SEARCH',1221,'For now, perhaps. But if you find a trace, I want to know. Straight away.')
    leaf('LIE_ENOUGH',1229,'All right. Enough for today.')
    leaf('LIE_NOTHING',1252,'Tell me as soon as you learn something. I need to know.','ECLIPSE')
    topic('CONFESSION',line(1267,'Which part was a lie?'),[
        response(1268,'The attackers. And Griffith being taken. He took part in what happened.','CONFESSION_HURT',val('eclipse_story','==',2)),back('ECLIPSE')])
    topic('CONFESSION_HURT',line(1269,'You saw me asking about him. Hoping to find him. Clinging to that hope. And you left me with that story?'),[
        response(1271,'I chose what you should know. I was wrong.','CONFESSION_RESPONSIBLE'),
        response(1272,'I could not say it. You should not have had to live with a lie.','CONFESSION_PAIN'),
        response(1273,'Would it have been easier if you kept believing?','CONFESSION_EASIER'),back('ECLIPSE')])
    for s,i,en in [('CONFESSION_RESPONSIBLE',1276,'You could have said you could not talk yet. I would have waited. Now tell me. All of it.'),('CONFESSION_PAIN',1279,'You could have asked for time. I would have given it. Tell me now.'),('CONFESSION_EASIER',1282,'I need to decide what to do with the truth myself. Do not choose what is easier for me again. You have no right.')]:
        topic(s,line(i,en),[response('Рассказать всё, что я видел.','Tell him everything I witnessed.','CONFESSION_DONE',val('eclipse_story','==',2),run('STORY_CONFESS')),back('ECLIPSE')])
    topic('CONFESSION_DONE',tr('I hear you. What I remember of him does not fit your words yet. I need time.','Я слышу тебя. Просто всё, что я помню о нём, пока не складывается с твоими словами. Мне нужно время.'),[
        response(1287,'Could you trust me again?','CONFESSION_TRUST'),back('ECLIPSE')])
    leaf('CONFESSION_TRUST',1288,'Not straight away. But you came back and told me yourself. That counts for something. We will see what you do next.','ECLIPSE')
    topic('TRUST_RECOVERY',choose(test('EOC_BERSERK_RICKERT_TRUST_RESTORED'),
        tr('I remember the lie. But I have had time to listen to you since then. We can talk about the road again.','Я помню обман. Но с тех пор у меня было время тебя выслушать. Можем снова поговорить о дороге.'),
        line(1678,'After what came out, I need time. I can work beside you at the forge. Trusting you with my life on the road is another matter.')),[
        response(1682,'What can I do?','TRUST_ADVICE'),
        response('Поговорим о том, что я действительно видел и что собираюсь делать.','Let us talk honestly about what I saw and what I mean to do.','TRUST_TALK',test('EOC_BERSERK_RICKERT_CAN_REBUILD_TRUST'),run('REBUILD_TRUST')),
        response('Насчёт совместной дороги.','About traveling together.','ROAD',both(test('EOC_BERSERK_RICKERT_TRUST_RESTORED'),nval('recruit_refused','!=',1))),back()])
    leaf('TRUST_ADVICE',1689,'Do not try to mend this with another fine promise. Keep speaking honestly until I can see it is a habit.','TRUST_RECOVERY')
    topic('TRUST_TALK',tr('Thank you for sitting down and telling me plainly. I cannot forget everything at once. Let us leave it there for today.','Спасибо, что сел и рассказал прямо. Я не могу сразу всё забыть. На сегодня давай остановимся на этом.'),[back()])
    topic('ECLIPSE_SILENCE',tr('All right. I will not force the words out of you. Just do not tell me everything is all right if it is not.',russian(1301)+' '+russian(1306)),[
        response(1318,'I can talk now.','ECLIPSE'),response(1334,'I am still not ready.','SILENCE_MORE'),back()])
    leaf('SILENCE_MORE',1338,'Then let us do something else for now.')
    topic('ECLIPSE_LOSSES',tr('I cannot give an honest count. No one called the roll afterwards. They are people to me, not a tally.','Честного числа я тебе не назову. Переклички после этого не было. Для меня это люди, а не счёт.'),[back('ECLIPSE')])
    # Alternate refusal is first-person experience but not Griffith's sacrifice.
    topic('CEREMONY_WITNESS',tr('Tell me what you saw. I was not there; I will not pretend to know.','Расскажи, что видел. Меня там не было; я не стану делать вид, что знаю.'),[
        response('Мне предложили силу. Я отказался и ушёл человеком.','They offered me strength. I refused and left as a human.','CEREMONY_REFUSED',both(WITNESS,math('u_berserk_apostol_outcome == 2'))),back()])
    topic('CEREMONY_REFUSED',tr('I do not know how to put that right. But I can listen. You do not have to explain everything today.','Я не знаю, как это исправить. Но могу выслушать. Не обязательно рассказывать всё сегодня.'),[back()])


MEMORIES=[('JUDEAU','Джудо',1349,1352,'He noticed when someone was struggling, and helped without making them feel foolish. You could ask him things you were ashamed not to know.',1363,'Tell me what you found. No comforting inventions. I want to remember the truth.', 'berserk_judeau_knife_hilt'),
 ('PIPPIN','Пиппин',1372,1375,'He said little. I would still be explaining what needed moving or holding, then see he had already done it. I felt less afraid beside him.',1383,'I kept thinking he might have escaped. I was so used to him bearing more than anyone else. It seemed nothing could break him.','berserk_pippin_broken_clasp'),
 ('CORKUS','Коркус',1390,1393,'Not always easy to get along with. One bitter remark could ruin a day. Then he would say something so absurd you could not stay angry.',1401,'I never expected to miss his grumbling. Now I try to remember his voice and cannot get it quite right.','berserk_corkus_scabbard_fragment'),
 ('GASTON','Гастон',1408,1411,'He had plans for life after the marches. He spoke of them so often I knew them by heart. Listening, I could believe we would live like people one day.',1419,'He spoke of the future as if it were already within reach. It is hard to accept it stayed only a conversation by a campfire.','berserk_gaston_sewing_roll')]


def memories():
    choices=[]
    for name,ru,question,base_i,base_en,dead_i,dead_en,item in MEMORIES:
        stem=name.lower();knows=val('knows_death_'+stem)
        proof=math('u_berserk_godo_witness_'+stem+' == 1')
        choices.append(response(question,'Tell me about '+name.title()+'.','REMEMBER_'+name))
        topic('REMEMBER_'+name,line(base_i,base_en),[
            response('Я нашёл его останки.','I found his remains.','DEATH_'+name,both(proof,neg(knows)),run('DEATH_'+name)),
            response('О том, что с ним случилось.','About what happened to him.','DEATH_'+name,knows),
            response('Показать найденную рядом вещь.','Show the object found beside him.','ITEM_'+name,{'u_has_items':{'item':item,'count':1}},setv('shown_'+stem)),back('ECLIPSE_MEMORIES')])
        topic('DEATH_'+name,line(dead_i,dead_en),[
            response('Я хотел, чтобы ты это знал.','I wanted you to know.','MEMORY_END'),back('ECLIPSE_MEMORIES')])
        # Names on items are not evidence of the avatar having examined a body.
        topic('ITEM_'+name,choose(either(proof,knows),line(1431,'I remember it.'),line(1435,'I do not know if it really belonged to him. Thank you for bringing it to show me.')),[
            response(1438,'Would you like to keep it?','KEEP_'+name),response(1439,'I just wanted you to see it.','ITEM_THANKS'),back('ECLIPSE_MEMORIES')])
        topic('KEEP_'+name,line(1442,'Yes. If you are ready to part with it.'),[
            response('Отдать памятную вещь.','Give him the keepsake.','ITEM_GIVEN',both(RICKERT,{'u_has_items':{'item':item,'count':1}}),
                     {'u_sell_item':item,'count':1,'cost':0,'true_eocs':['EOC_BERSERK_RICKERT_KEEPSAKE_'+name]}),
            response('Пока оставлю у себя.','I will keep it for now.','ECLIPSE_MEMORIES')])
    topic('ECLIPSE_MEMORIES',tr('Whom did you want to talk about?','О ком хотел поговорить?'),choices+[back('BAND')])
    leaf('MEMORY_END',2013,'I will remember that.','ECLIPSE_MEMORIES')
    leaf('ITEM_THANKS',1446,'Thank you.','ECLIPSE_MEMORIES')
    topic('ITEM_GIVEN',tr('Thank you. I will keep it safe.','Спасибо. Я сберегу её.'),[back('ECLIPSE_MEMORIES')])


def personal():
    topic('PERSONAL',tr('Go ahead. Just mind the cloth with the parts on it.','Спрашивай. Только тряпку с деталями не зацепи.'),[
        response(1458,'Do you ever get frightened?','FEAR',once='fear'),
        response(1487,'If you could choose what to work on?','WISH',once='wish'),
        response(1510,'Does it bother you that others are stronger?','WEAK',either(G,val('strength_compared')),once='weak'),
        response('Каково работать с Годо?','What is working with Godot like?','GODO'),
        response('Рад был поговорить.','Good talking with you.','GOODBYE_WARM'),back()])
    topic('FEAR',line(1462,'Of course. Especially when there is nothing left to check or tighten, my hands have no work, and my head keeps imagining the worst.'),[
        response(1465,'What do you do then?','FEAR_HELP'),response(1466,'It does not always show.','FEAR_WORK'),back('PERSONAL')])
    leaf('FEAR_HELP',1473,'I try not to be entirely alone with it. We do not even have to talk. Sometimes someone sitting nearby is enough.','PERSONAL')
    leaf('FEAR_WORK',1481,'I work with my hands. From outside, being busy may look like being calm. They are not always the same.','PERSONAL')
    topic('WISH',line(1488,'I would still make things. Things that make living easier, not only surviving.'),[
        response(1490,'For example?','WISH_EXAMPLE'),response(1491,'Weapons help people survive too.','WISH_WEAPON'),back('PERSONAL')])
    leaf('WISH_EXAMPLE',1494,'A mounting you can work with after an injury. A cart you do not have to drag out of every rut. Even a lock that does not jam in the cold.','PERSONAL')
    leaf('WISH_WEAPON',1497,'Yes. That is why I make them. Sometimes I want to make something for after the battle, too.','PERSONAL')
    topic('WEAK',line(1511,'Sometimes. Especially when someone is trapped and I cannot move what fell on them. You stand there, hands shaking, unable to help.'),[
        response(1512,'How do you deal with it?','WEAK_HELP'),back('PERSONAL')])
    leaf('WEAK_HELP',1513,'I learn what I can. Try to find a way to help before things become that bad, while there is still time to prevent it.','PERSONAL')


def recruitment(old):
    open_=both(RICKERT,neg(FOLLOW),nval('recruit_refused','!=',1))
    topic('ROAD',choose(nval('recruit_refused'),line(1757,'No. I have decided. We can talk about work, but not traveling together.'),line(1526,'Where are you going? And what do you expect of me if I agree?')),[
        response(1529,'We would help each other. I do not want to go alone.','ROAD_MUTUAL',open_),
        response(1530,'I could use your knowledge. The choice is yours.','ROAD_CHOICE',open_),
        response(1531,'I do not know yet. Let us talk later.','ROAD_LATER',open_),
        response(1532,'You will do as I say. I do not need an assistant who argues.','REFUSE',open_,run('REFUSE_RECRUITMENT')),
        response(1722,'Come with me, or you will regret it.','REFUSE_THREAT',open_,run('REFUSE_RECRUITMENT')),
        response(1738,'Your friends were weak. Be useful to me and perhaps you will outlive them.','REFUSE_DEAD',both(open_,val('heard_losses')),run('REFUSE_RECRUITMENT')),
        response('Насчёт твоего решения.','About your decision.','REFUSE_MENU',nval('recruit_refused')),back()])
    topic('ROAD_MUTUAL',line(1539,'I can shoot, watch the equipment, help on the road. But if we are walking toward pointless death, I will say so.'),[
        response(1542,'I will listen.','ROAD_PLAN',open_,math('n_berserk_rickert_respect = 1')),
        response(1543,'We can argue. We will decide together.','ROAD_PLAN',open_,math('n_berserk_rickert_respect = 1')),
        response(1544,'I said you will obey.','REFUSE',open_,run('REFUSE_RECRUITMENT')),back()])
    topic('ROAD_CHOICE',line(1571,'I am glad you say that. But I do not want to come only to mend equipment while you decide everything else. My word has to mean something.'),[
        response(1574,'I am asking you to be a companion.','ROAD_PLAN',open_,math('n_berserk_rickert_respect = 1')),
        response(1575,'I understand. Think about it.','ROAD_LATER'),
        response(1576,'I feed you for your help. You will obey.','REFUSE_PROPERTY',open_,run('REFUSE_RECRUITMENT')),back()])
    topic('ROAD_PLAN',line(1583,'Then tell me where you want to go first.'),[
        response('Сначала припасы и безопасная дорога.','First, supplies and a safe road.','ROAD_READY',open_),
        response('Пойдём по известному нам следу. Сначала разведаем подходы.','We will follow the lead we know and scout the approaches first.','ROAD_READY',both(open_,test('EOC_BERSERK_RICKERT_HAS_KNOWN_GOAL'))),
        response('Перед дорогой поговорим о моей перемене.','Before setting out, let us discuss what is happening to me.','TALK_BERSERK_APOSTOL_RICKERT',both(open_,neg(HUMAN))),back()])
    topic('ROAD_READY',choose(neg(test('EOC_BERSERK_RICKERT_TRUST_RESTORED')),choose(nval('lie_trust_pending'),line(1678,'After what came out, I need time. I can work beside you at the forge. Trusting you with my life on the road is another matter.'),line(1659,'I do not know you well enough to leave everything and go with you. Come back and talk; we will see how things go.')),
        choose(both(neg(HUMAN),math('u_berserk_apostol_rickert_counsel != 1')),tr('Before we set out, tell me what is happening to you. I need to know what to expect beside you.','Прежде чем отправимся, расскажи, что с тобой происходит. Мне нужно знать, чего ждать рядом с тобой.'),line(1626,'All right. I will come. Let me gather my things and tell Godot; I do not want him wondering where I went.'))),[
        response(1629,'I will wait.','JOINED',test('EOC_BERSERK_RICKERT_JOIN'),run('JOIN')),
        response('Расскажу о перемене.','I will tell you about the change.','TALK_BERSERK_APOSTOL_RICKERT',both(neg(HUMAN),math('u_berserk_apostol_rickert_counsel != 1'))),
        response('Как вернуть твоё доверие?','How can I rebuild your trust?','TRUST_RECOVERY',nval('lie_trust_pending')),
        response(1630,'I changed my mind. We will stay for now.','ROAD_LATER'),back()])
    leaf('ROAD_LATER',1600,'All right. Better to agree now than sort it out on the road when it is too late to turn back.')
    topic('JOINED',line(1637,'I will be ready soon. I will not keep you long.'),[back('COMPANION'),response('Обсудим снаряжение и порядок в пути.','Let us discuss equipment and travel arrangements.','TALK_FRIEND',FOLLOW)])
    leaf('REFUSE',1704,'Then you need someone else. I will not go with you.')
    leaf('REFUSE_PROPERTY',1715,'You can order work from me. You cannot buy me. That ends the talk about traveling together.')
    leaf('REFUSE_THREAT',1726,'No. After those words, I am not going anywhere with you.')
    leaf('REFUSE_DEAD',1744,'Do not speak of them that way. Do not imagine I would walk beside someone who can say that.')
    topic('REFUSE_MENU',line(1757,'No. I have decided. We can talk about work, but not traveling together.'),[
        response(1783,'I was wrong to speak to you that way.','APOLOGY',nval('recruit_refused'),once='apology'),
        response(1769,'Will you at least finish my order?','ORDER_AFTER_REFUSAL',test('EOC_BERSERK_RICKERT_HAS_ORDER')),back()])
    leaf('APOLOGY',1787,'Thank you for saying so. But I have not changed my decision.')
    topic('COMPANION',line(1800,'Shall we stop for a moment, or talk as we walk?'),[
        response(1803,'How are you holding up?','COMPANION_STATE'),
        response(1804,'What do you think of our road?','COMPANION_ROUTE'),
        response(1805,'About our equipment.','ORDERS'),
        response(1806,'I just wanted to know how you are.','COMPANION_SELF'),
        response('Обсудим снаряжение и порядок в пути.','Let us discuss equipment and travel arrangements.','TALK_FRIEND',FOLLOW),back()])
    topic('COMPANION_STATE',choose(test('EOC_BERSERK_RICKERT_HURT'),tr('I am hurt. Let us find somewhere quiet and look at the wounds before going farther.','Я ранен. Давай найдём тихое место и займёмся ранами, прежде чем идти дальше.'),tr('When we can, I want to check the crossbow without rushing. On the road I keep worrying about something I missed.','Как будет возможность — хочу спокойно, без спешки проверить арбалет. В дороге всё время кажется, что делаю это кое-как, на бегу, а потом в самый неподходящий момент вылезет то, что я не заметил.')),[back('COMPANION')])
    topic('COMPANION_ROUTE',choose(test('EOC_BERSERK_RICKERT_HAS_KNOWN_GOAL'),line(1825,'Before we get closer, let us look for a way to retreat if things go wrong. I am happier seeing a way back before I need it.'),line(1830,'I would like to know where we are going. If it is just looking for supplies, say so. That is worthwhile too.')),[
        response('Сначала припасы.','Supplies first.','COMPANION_PLAN'),
        response('Прежде чем идти дальше, осмотримся.','We will look around before going farther.','COMPANION_PLAN',test('EOC_BERSERK_RICKERT_HAS_KNOWN_GOAL')),back('COMPANION')])
    leaf('COMPANION_PLAN',1825,'Before we get closer, let us look for a way to retreat if things go wrong. I am happier seeing a way back before I need it.','COMPANION')
    topic('COMPANION_SELF',line(1841,'Ah... I see. Not always well, honestly. Thank you for asking. Not everyone notices the difference.'),[
        response(1844,'Want to talk?','COMPANION_TALK'),response(1845,'We could just sit a while.','COMPANION_SIT'),back('COMPANION')])
    leaf('COMPANION_TALK',1852,'Yes. Something ordinary first, though, not the hardest things at once.','PERSONAL')
    leaf('COMPANION_SIT',1859,'Let us.','COMPANION')


def changed():
    topic('TALK_BERSERK_APOSTOL_RICKERT',choose(both(FOLLOW,neg(KNOWS)),line(1872,'Were you going to tell me what is happening to you? Or was I meant to guess?'),tr('Tell me what you know about this change.','Расскажи, что сам знаешь об этой перемене.')),[
        response(1875,'Yes. I accepted the power.','TALK_BERSERK_APOSTOL_RICKERT_ANSWER',neg(HUMAN),run('EOC_BERSERK_APOSTOL_TELL_RICKERT')),
        response(1876,'I did not know how to start.','CHANGED_BEGIN',neg(HUMAN),run('EOC_BERSERK_APOSTOL_TELL_RICKERT')),
        response(1877,'It is none of your business.','CHANGED_BOUNDARY',neg(HUMAN)),
        response(1909,'I do not know what I will become.','CHANGED_FEAR',neg(HUMAN),run('EOC_BERSERK_APOSTOL_TELL_RICKERT')),
        response(1920,'You do not need to understand. Just obey.','CHANGED_BREAK',both(FOLLOW,neg(HUMAN)),run('BREAK_COMPANIONSHIP')),back()])
    topic('TALK_BERSERK_APOSTOL_RICKERT_ANSWER',line(1884,'Then tell me what you were promised. And what you understand yourself, beyond somebody else\'s words.'),[
        response('Я принял силу, но не стану распоряжаться людьми как вещами.','I accepted strength. I will not treat people as possessions.','CHANGED_COUNSEL',neg(HUMAN),run('EOC_BERSERK_APOSTOL_RICKERT_GIFT_COUNSEL')),
        response('Мне всё ещё нужна помощь с рукой.','I still need help with my hand.','ARM_CHANGED',HAND),back()])
    leaf('CHANGED_BEGIN',1892,'Start with what you know for certain. We can work through the rest as we go.','TALK_BERSERK_APOSTOL_RICKERT_ANSWER')
    topic('CHANGED_BOUNDARY',choose(FOLLOW,line(1900,'When we walk side by side, it concerns me too. I need to know what to expect, so I can survive beside you.'),tr('You can keep your own counsel. But before I travel with you, I need to know what to expect.','Можешь оставить это при себе. Но прежде чем идти с тобой, мне нужно знать, чего ждать.')),[back()])
    leaf('CHANGED_FEAR',1913,'Then do not hide changes from me. Tell me before it is too late. I cannot promise to stop it, but I want to understand you while I still can.','TALK_BERSERK_APOSTOL_RICKERT_ANSWER')
    topic('CHANGED_COUNSEL',tr('We can keep talking. My choice about the road is still mine.','Можем разговаривать дальше. Решение о дороге всё ещё остаётся за мной.'),[
        response('Обсудим путь как товарищи.','Let us discuss the road as companions.','ROAD',both(neg(FOLLOW),nval('recruit_refused','!=',1))),back()])
    topic('CHANGED_BREAK',line(1924,'No. That was not our agreement when I chose to come with you.'),[back()])
    # One-off observations only for actual visible body traits, never a seed.
    topic('VISIBLE_HANDS',line(1938,'Can you still hold a tool comfortably with that hand?'),[back()],setv('seen_hands'))
    topic('VISIBLE_SHELL',line(1946,'Does that plate get in the way when you bend? You seem to move differently.'),[back()],setv('seen_shell'))
    topic('VISIBLE_WINGS',line(1953,'I will walk behind you in narrow passages. I do not want to get in the way if you have to turn or spread those wings.'),[back()],setv('seen_wings'))
    for key,label,en in [('hands','Ты заметил мои руки?','Have you noticed my hands?'),('shell','Панцирь изменил мои движения.','The shell has changed how I move.'),('wings','С крыльями стало тесно.','The wings make things cramped.')]:
        TOPICS[tid('')]['responses'].insert(-1,response(label,en,'VISIBLE_'+key.upper(),both(either(MET,G,FOLLOW),test('EOC_BERSERK_RICKERT_VISIBLE_'+key.upper()),val('seen_'+key,'!=',1))))


def goodbyes():
    topic('GOODBYE',choose(FOLLOW,line(1972,'All right. I am nearby if you need me.'),line(1967,'All right. I will be here.')),[response('До встречи.','Until next time.','TALK_DONE')])
    leaf('GOODBYE_MATERIALS',1985,'Good luck. Bring them and we will carry on.','GOODBYE')
    topic('GOODBYE_HEAVY',line(1999,'Yes. Thank you for staying with me.'),[response('До встречи.','Until next time.','TALK_DONE')])
    topic('GOODBYE_WARM',choose(FOLLOW,tr('So was I. We can talk without something being broken first.','Я тоже. Можно ведь поговорить и без очередной поломки.'),line(2027,'So was I. Visit without broken equipment sometimes. Give me a rest from other people\'s repairs.')),[response('До встречи.','Until next time.','TALK_DONE')])
    for s in ['ECLIPSE','TRUTH_AFTER','CONFESSION_DONE','CEREMONY_REFUSED','TALK_BERSERK_APOSTOL_RICKERT_ANSWER']:
        TOPICS[tid(s)]['responses'].append(response(1995,'Enough for today.','GOODBYE_HEAVY'))


def state_hooks():
    helpers=[]
    def add(id,body,condition=None,**extra):
        id=id if id.startswith('EOC_') else 'EOC_BERSERK_RICKERT_'+id
        helpers.append(eoc(id,body,condition,**extra))
    add('HAS_ORDER',[],either(both(math('u_berserk_godo_arm_state > 0'),math('u_berserk_godo_arm_state < 4')),val('bolts_pending')))
    add('HAS_KNOWN_GOAL',[],either(*[both(math(f'u_berserk_journal_goal == {i}'),test('EOC_BERSERK_JOURNAL_KNOWN_'+name),neg(test('EOC_BERSERK_JOURNAL_DONE_'+name))) for i,name in enumerate(['FIRST','BREACH','COUNT','WYALD','ROSINE','FLORA','GRUNBELD','GODO'],1)]))
    wake=both(math('u_berserk_eclipse_rescue_state == 2'),val('care_present'),val('wake_greeted','!=',1))
    add('DIALOGUE_WAKE',[],wake)
    # Scan only people actually loaded at the validated arrival. The avatar
    # receives the snapshot after callbacks, because their alpha is the NPC.
    add('RECORD_CARE_NPC',math('berserk_rickert_care_present = 1'),both('u_is_npc',{'u_has_class':'NC_BERSERK_RICKERT'},either({'u_at_om_location':'berserk_godo_workshop'},{'u_at_om_location':'berserk_godo_loft'})))
    add('CAPTURE_CARE',[
        math('berserk_rickert_care_present = 0'),
        {'u_run_npc_eocs':['EOC_BERSERK_RICKERT_RECORD_CARE_NPC'],'unique_ids':[],'local':True,'npc_range':60,'z_min':0,'z_max':1},
        {'if':math("u_monsters_nearby('mon_berserk_rickert', 'radius': 32, 'attitude': 'both') > 0"),'then':math('berserk_rickert_care_present = 1')},
        math('u_berserk_rickert_care_present = berserk_rickert_care_present'),setv('care_recorded')],
        both('u_is_avatar',math('u_berserk_godo_rescue_relocated == 1'),val('care_recorded','!=',1)))
    visible_hands=either(*[{'u_has_flag':s} for s in ['BERSERK_WYALD_FLESH_FORM_ACTIVE','BERSERK_WYALD_PAWN_FORM_ACTIVE','BERSERK_SLAN_FORM_ACTIVE']])
    visible_shell=either(*[{'u_has_flag':s} for s in ['BERSERK_GRUNBELD_FLESH_FORM_ACTIVE','BERSERK_GRUNBELD_PAWN_FORM_ACTIVE']])
    visible_wings=either({'u_has_flag':'WINGS_2'},{'u_has_flag':'BERSERK_FEMTO_FORM_ACTIVE'})
    for key,c in [('HANDS',visible_hands),('SHELL',visible_shell),('WINGS',visible_wings)]:add('VISIBLE_'+key,[],both(neg(HUMAN),c))
    add('SYNC',[run('EOC_BERSERK_GODO_REPAIR_REFUSAL_CLASSIFICATION'),
        {'if':KNOWS,'then':math('u_berserk_apostol_rickert_told = 1')}],RICKERT)
    for id,value in [('TRUTH',1),('LIE',2),('SILENCE',3)]:
        body=[setv('eclipse_story',value)]
        if id!='SILENCE':body.append(setv('heard_losses'))
        if id=='TRUTH':body.extend([{'if':G,'then':[setv('knows_death_'+n.lower()) for n,*_ in MEMORIES]}])
        add('STORY_'+id,body,both(RICKERT,NORMAL_WITNESS,either(val('eclipse_story','==',0),val('eclipse_story','==',3))))
    confession_effect=[
        math('n_berserk_rickert_lie_trust_target = max(0, n_npc_trust())'),
        math('n_npc_trust() = n_npc_trust() - 4'),
        math("n_berserk_rickert_confession_at = time('now')"),
        math("n_berserk_rickert_trust_next_talk = time('now') + 86400"),
        math('n_berserk_rickert_lie_trust_pending = 1'),
        setv('lied_before'),setv('eclipse_story',1),setv('heard_losses'),{'if':G,'then':[setv('knows_death_'+n.lower()) for n,*_ in MEMORIES]}]
    add('STORY_CONFESS',confession_effect,both(RICKERT,NORMAL_WITNESS,val('eclipse_story','==',2)))
    trust_ok=both(math('n_npc_trust() >= 0'),either(nval('lie_trust_pending','!=',1),both(math("time('now') >= n_berserk_rickert_confession_at + 86400"),math('n_npc_trust() >= n_berserk_rickert_lie_trust_target'))))
    add('TRUST_RESTORED',[],trust_ok)
    rebuild=both(RICKERT,nval('lie_trust_pending'),math('n_npc_trust() < n_berserk_rickert_lie_trust_target'),math("time('now') >= n_berserk_rickert_trust_next_talk"),'u_at_safe_space')
    add('CAN_REBUILD_TRUST',[],rebuild)
    add('REBUILD_TRUST',[math('n_npc_trust() = min(n_berserk_rickert_lie_trust_target, n_npc_trust() + 1)'),math("n_berserk_rickert_trust_next_talk = time('now') + 86400")],rebuild)
    for name,*_,item in MEMORIES:
        stem=name.lower()
        add('DEATH_'+name,[setv('knows_death_'+stem),setv('heard_losses')],both(RICKERT,math('u_berserk_godo_witness_'+stem+' == 1')))
        add('KEEPSAKE_'+name,setv('given_'+stem),RICKERT)
    add('BREAK_COMPANIONSHIP',[math('n_berserk_rickert_recruit_refused = 1'),math('n_berserk_rickert_respect = 0'),math('n_berserk_rickert_recruited = 0'),'leave','assign_guard',{'npc_first_topic':tid('')}],both(RICKERT,FOLLOW,neg(HUMAN)))
    # Native 0.I hp math; no invented numeric relationship or fatigue mechanic.
    add('HURT',[],either(*[math(f"n_hp('{bp}') < n_hp_max('{bp}') / 2") for bp in ['head','torso','arm_l','arm_r','leg_l','leg_r']]))
    add('HAS_MODERN_ITEM',[],either(*[{'u_has_items':{'item':s,'count':1}} for s in ['smart_phone','two_way_radio','flashlight','binoculars','soldering_iron']]))
    data=read('effects/godo_eocs.json');ids=index(data)
    # Greeting choices record acquaintance only after rendering the first line.
    ids['EOC_BERSERK_GODO_MEET_RICKERT']['effect']=[
        {'if':WAKE,'then':setv('wake_greeted')},
        setv('met'),math('u_berserk_godo_met = 1'),run('EOC_BERSERK_GODO_BEGIN'),run('EOC_BERSERK_GODO_ROUTE_MISSION')]
    claim=ids['EOC_BERSERK_GODO_ARM_CLAIM']
    body=claim['effect'][0]['else']
    marker=setv('arm_delivered')
    if marker not in body:body.insert(1,marker)
    for obj in walk(ids['EOC_BERSERK_FORGE_RESCUE_CHECK_ROOM']['effect']):
        then=obj.get('then')
        if isinstance(then,list) and math('u_berserk_godo_rescue_relocated = 1') in then:
            hook=run('CAPTURE_CARE')
            if hook not in then:then.insert(1,hook)
    # Preserve respect, demon counsel, rejoining and permanent refusal, adding
    # the actual NPC opinion rather than a second relationship score.
    join=ids['EOC_BERSERK_RICKERT_JOIN']
    if neg(FOLLOW) not in join['condition'].get('and',[]):
        join['condition']=both(neg(FOLLOW),join['condition'])
    trust_requirement=test('EOC_BERSERK_RICKERT_TRUST_RESTORED')
    if not any(x.get('test_eoc')==trust_requirement['test_eoc'] for x in walk(join['condition'])):
        join['condition']=both(trust_requirement,join['condition'])
    write('effects/godo_eocs.json',data)
    cont=read('effects/apostol_continuation_eocs.json');by=index(cont)
    by['EOC_BERSERK_APOSTOL_TELL_RICKERT']['condition']=both(neg(HUMAN),RICKERT)
    by['EOC_BERSERK_APOSTOL_RICKERT_GIFT_COUNSEL']['condition']=both(neg(HUMAN),RICKERT)
    by['EOC_BERSERK_APOSTOL_RICKERT_KNOWS_GIFT']['condition']=both(neg(HUMAN),either(math('u_berserk_apostol_rickert_told == 1'),test('EOC_BERSERK_APOSTOL_FORM_VISIBLE')))
    write('effects/apostol_continuation_eocs.json',cont)
    write('effects/rickert_dialogue_33_eocs.json',helpers+list(HELPERS.values()))


def translations():
    for filename,localized in [('ru.po',True),('Berserk.pot',False)]:
        p=MOD/'lang/po'/filename;remaining=dict(STRINGS);out=[]
        for block in [b for b in p.read_text().split('\n\n') if b.strip()]:
            key=source(block)
            if key in remaining:
                value=remaining.pop(key)
                block='#. Approved Rickert dialogue 2026-10-21\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(value if localized else '',ensure_ascii=False)
            out.append(block.strip('\n'))
        for en,ru in remaining.items():out.append('#. Approved Rickert dialogue 2026-10-21\nmsgid '+json.dumps(en,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False))
        p.write_text('\n\n'.join(out)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)


def main():
    original=read('dialogue/godo.json');old=index(original)
    intros();craft();prosthesis(old);bolts();band_and_story();memories();personal();recruitment(old);changed();goodbyes()
    aliases={'TOPICS':'','CRAFT':'MECHANISMS','MECHANISM':'INTRO_LOCK','LEARN':'IDEAS','HOME':'INTRO_REST',
             'ECLIPSE_ASK':'ECLIPSE','ECLIPSE_RETURN':'ECLIPSE'}
    for alias,target in aliases.items():
        if tid(alias) not in TOPICS:topic(alias,tr('What would you like to ask?','О чём хотел спросить?'),[back(target)])
    for obj in original:
        if obj['id'].startswith('TALK_BERSERK_RICKERT') and obj['id'] not in TOPICS:
            topic(obj['id'],tr('What would you like to ask?','О чём хотел спросить?'),[back()])
    state_hooks()
    write('dialogue/godo.json',[TOPICS.pop(x['id'],x) for x in original]+list(TOPICS.values()))
    translations()
    print('Approved Rickert dialogue built; RU source preserved. Strings:',len(STRINGS))


if __name__=='__main__':main()
