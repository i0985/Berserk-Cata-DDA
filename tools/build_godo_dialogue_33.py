#!/usr/bin/env python3
"""Godo's approved 21 October script; source paragraphs remain in the repository.

Only Godo's topics and the state hooks needed by them are replaced. Rickert's
dialogue text, existing order transactions, IDs and issued equipment survive.
"""
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

from recover_apostol_33 import ROOT, MOD, read, write, index, upsert, walk, eoc, math, test, both
from recovery_33_translations import source

SOURCE = json.loads((ROOT / 'docs/dialogue_sources/godo-2026-10-21.json').read_text())['paragraphs']
STRINGS = {}
TOPICS = {}
LINE_CONDITIONS = {}
H = test('EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED')
G = test('EOC_BERSERK_FORGE_GUTS')
BEFORE = test('EOC_BERSERK_FORGE_BEFORE_ECLIPSE')
AFTER = test('EOC_BERSERK_FORGE_AFTER_ECLIPSE')
MET = test('EOC_BERSERK_GODO_SMITH_ACQUAINTED')
WAKE = test('EOC_BERSERK_FORGE_SCENE_WAKE_GODO_PENDING')
KNOWS = test('EOC_BERSERK_APOSTOL_GODO_KNOWS_GIFT')
SMITH = test('EOC_BERSERK_GODO_AT_SMITH')
EARLY = {'u_has_items': {'item': 'true_guts_early_sword', 'count': 1}}
SWORD = test('EOC_BERSERK_GODO_HAS_SWORD')


def neg(c): return {'not': c}
def either(*cs): return {'or': list(cs)}
def val(name, op='==', number=1): return math(f'u_berserk_godo_{name} {op} {number}')
def setv(name, number=1): return math(f'u_berserk_godo_{name} = {number}')
def run(id): return {'run_eocs': id if id.startswith('EOC_') else 'EOC_BERSERK_GODO_' + id}
def tid(id): return id if id.startswith('TALK_') else 'TALK_BERSERK_GODO' + ('_' + id if id else '')


def tr(en, ru):
    assert en and ru
    # Native '*' prepends the speaker name. These authored stage paragraphs
    # already contain Godo/the smith, so '&' displays the complete narration.
    if en.startswith('*'): en = '&' + en[1:]
    if ru.startswith('*'): ru = '&' + ru[1:]
    STRINGS[en] = ru
    return en


def russian(i):
    text = SOURCE[i].strip()
    if '\nГодо' in text: text = text[text.rfind('\nГодо') + 1:]
    if '→ Годо:' in text: text = text.split('→ Годо:', 1)[1]
    text = re.sub(r'^(?:Годо|Игрок|Гатс)[^:\n]*:\s*', '', text)
    text = re.sub(r'\n\(.*', '', text, flags=re.S)
    text = re.sub(r'\s*\((?:Разговор|Беседа|Ветка|Квест).*', '', text)
    # Paragraph 491 and other author notes never enter this function as dialogue.
    return text


def line(i, en): return tr(en, russian(i))
def choose(c, yes, no):
    # 0.I dynamic_line accepts one predicate, not logical combinators.
    if any(k in c for k in ['and','or','not']):
        digest=hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        id='EOC_BERSERK_GODO_LINE_'+digest
        LINE_CONDITIONS[id]=eoc(id,[],c)
        c=test(id)
    return {**c, 'yes': yes, 'no': no}


def response(ru, en, target, condition=None, effect=None, once=None):
    if isinstance(ru, int):
        text = SOURCE[ru]
        match = re.search('«([^»]+)»', text)
        ru = match[1] if match else russian(ru)
        ru = ru.strip('«»').removesuffix('!.') + ('!' if ru.endswith('!.') else '')
    obj = {'text': tr(en, ru), 'topic': tid(target)}
    if once:
        condition = both(condition, val('read_' + once, '!=', 1)) if condition else val('read_' + once, '!=', 1)
        effects = [] if effect is None else effect if isinstance(effect, list) else [effect]
        effect = effects + [setv('read_' + once)]
    if condition is not None: obj['condition'] = condition
    if effect is not None: obj['effect'] = effect
    return obj


def back(target='', en='I wanted to ask about something else.'):
    return response('Я хотел спросить о другом.', en, target)


def topic(id, text, responses=None, effect=None):
    obj = {'type': 'talk_topic', 'id': tid(id), 'dynamic_line': text,
           'responses': responses if responses is not None else [back()]}
    if effect: obj['speaker_effect'] = {'effect': effect}
    TOPICS[obj['id']] = obj
    return obj


def leaf(id, i, en, parent=''):
    return topic(id, line(i, en), [back(parent)])


def intros():
    # Meet is committed by a chosen response, after greeting/response predicates
    # have been evaluated. Reading the screen cannot consume the wake scene.
    first = neg(MET)
    known_hello = choose(G, line(42, 'Still alive, I see! Is your sword in one piece?'),
                         choose(AFTER, line(88, 'It has been a while. Heard what is happening? Even the daylight seems darker. Something bad has happened.'),
                                line(26, 'Back again. What is it this time?')))
    ordered = choose(val('repair_state'), tr('You left a blade here. Have you come about the repair?', 'Ты оставил здесь клинок. Насчёт ремонта пришёл?'),
                     choose(val('early_state'), tr('I am still waiting for the steel and the rest of your delivery.', 'Я всё ещё жду сталь и остальное для твоего заказа.'),
                            choose(val('early_state', '==', 2), tr('Your blade is at the forge. Ask me how the work is going.', 'Твой клинок у горна. Спрашивай, как идёт работа.'),
                                   choose(both(val('sword_state', '>', 0), val('sword_state', '<', 4)), tr('Your great blade has not been forgotten. What do you need?', 'Про твой большой клинок я не забыл. С чем пришёл?'), known_hello))))
    awake = choose(G, line(76, 'Alive.'), choose(MET, line(53, 'Awake at last. Last time you crossed the threshold on your own feet. This time someone had to carry you.'), line(64, 'Easy. You have been through enough. This is my forge. I am Godot.')))
    hello = choose(WAKE, awake, choose(both(G, BEFORE, first),
        tr('*Godot looks at your blade, then raises his eyes. "Guts. Thought I would recognize you by that iron when I could no longer make out your face. What is it? Straighten your sword again?"',
           '*Годо задерживает взгляд на вашем клинке, затем поднимает глаза. «Гатс. Думал, по этому железу тебя и узнаю, когда самого уже не разгляжу. Ну чего? Как обычно, меч тебе подлатать?»'),
        choose(first, choose(AFTER, line(90, 'If you want a forge, you have found it. Mind what you touch. I am not fond of strangers. Rickert can show you where to rest.'),
               tr('*The smith turns the billet in his tongs. Only after a few hammer blows does he notice you. "Close the door. And step away from that bucket."', '*Кузнец переворачивает заготовку клещами. Несколько ударов молота — и только после этого он обращает на вас внимание. «Дверь прикрой. И отойди от ведра».')), ordered)))
    hello = choose(both(neg(WAKE),G,AFTER,first),tr('Guts. Still alive. Sit down and catch your breath.','Гатс. Живой ещё. Садись, переведи дух.'),hello)
    meet = run('MEET_SMITH')
    rs = [
        response(78, 'Griffith... Where is that bastard?!', 'WAKE_GUTS_ANGER', both(WAKE, G), meet),
        response(79, 'Where is everyone?! What was that dream?!', 'WAKE_GUTS_DREAM', both(WAKE, G), meet),
        response('Где моя рука? Где Рикерт? Что, мать твою, произошло?!', 'Where is my hand? Where is Rickert? What the hell happened?!', 'WAKE_GUTS_REST', both(WAKE, G, test('EOC_BERSERK_DIALOGUE_MISSING_LEFT_HAND')), meet),
        response('Где Рикерт? Что произошло?', 'Where is Rickert? What happened?', 'WAKE_GUTS_REST', both(WAKE, G, neg(test('EOC_BERSERK_DIALOGUE_MISSING_LEFT_HAND'))), meet),
        response('Кто меня принёс?', 'Who brought me here?', 'WAKE_RIDER', both(WAKE, neg(G)), meet),
        response(56, 'How long have I been here?', 'WAKE_TIME', both(WAKE, neg(G)), meet),
        response(57, 'My belongings...', 'WAKE_BELONGINGS', both(WAKE, neg(G)), meet),
        response(67, 'Why did you help me?', 'WAKE_HELP', both(WAKE, neg(G), first), meet),
        response(68, 'I do not know how I can repay you.', 'WAKE_PAY', both(WAKE, neg(G), first), meet),
        response(5, 'Are you Godot? I am looking for a smith.', 'STRANGER', both(neg(WAKE), first, neg(G)), meet),
        response(6, 'I heard you can mend weapons here.', 'INTRO_REPAIR', both(neg(WAKE), first, neg(G)), meet),
        response(7, 'I was looking for somewhere to rest.', 'INTRO_REST', both(neg(WAKE), first, neg(G)), meet),
        response(33, 'It still serves me.', 'RECOGNIZE_BLADE', both(neg(WAKE), G, BEFORE, first), meet),
        response(34, 'I need a better blade.', 'RECOGNIZE_NEW', both(neg(WAKE), G, BEFORE, first), meet),
        response(35, 'Good to see you, old man.', 'RECOGNIZE_HELLO', both(neg(WAKE), G, BEFORE, first), meet),
        response(44, 'For now.', 'RETURN_BLADE', both(neg(WAKE), G, neg(first)), meet),
        response(45, 'There is work to discuss.', '', both(neg(WAKE), neg(first)), meet),
        response(46, 'Just looking in.', 'RETURN_VISIT', both(neg(WAKE), G, neg(first)), meet),
        response('Поговорим, Годо.', 'Let us talk, Godot.', '', both(neg(WAKE), first, G, AFTER), meet),
        response('Не буду мешать.', 'I will leave you to your work.', 'TALK_DONE', None, meet),
    ]
    topic('ENTER', hello, rs)
    leaf('STRANGER', 9, 'You found him. What do you want?')['responses'] = [
        response(11, 'What sort of work do you take?', 'INTRO_WORK'),
        response(12, 'I need a good sword.', 'WEAPON_REQUEST'), back()]
    leaf('INTRO_WORK', 13, 'Blades, iron, fittings. Show me the thing and I will tell you whether it is worth the work. Gears and little mechanisms are Rickert\'s business. His eyes are better than mine.')
    leaf('INTRO_REPAIR', 17, 'Rumors do not do my work for me. Show me. Put it on the edge of the table, away from the heat.')['responses'] = [response('Вот мой клинок.', 'Here is my blade.', 'REPAIR'), back()]
    leaf('INTRO_REST', 20, 'There is a place for a traveler. Rickert can show you. No sleeping in the workshop, and leave the tools alone.')['responses'] = [response(21, 'Understood. Thank you.', 'INTRO_AGREED')]
    leaf('INTRO_AGREED', 22, 'Good. Then we have an understanding.')
    for id, i, en in [
        ('RECOGNIZE_BLADE',36,'I see. A more careful owner would make it last longer. Put it here; let me look.'),
        ('RECOGNIZE_NEW',37,'Show me the old one first. What remains of it tells me more than your wishes.'),
        ('RECOGNIZE_HELLO',38,'Then stop standing in the doorway. You are letting in a draft.'),
        ('RETURN_BLADE',47,'Do not lie to me. Let me have a look.'),
        ('RETURN_VISIT',49,'Bed upstairs. You know the rest.'),
        ('WAKE_GUTS_ANGER',81,'Calm down or you will pass out again. You have no strength left.'),
        ('WAKE_GUTS_REST',83,'Easy. Rest first; we can talk when you have recovered. You can tell me what happened then.'),
        ('WAKE_TIME',59,'Long enough. I do not count the hours at the forge.'),
        ('WAKE_BELONGINGS',60,'First make sure you can stand. Then count your iron.'),
        ('WAKE_HELP',70,'You were lying in my arms, barely breathing. What else was I to do? Not the gift I would have chosen, but here we are.'),
        ('WAKE_PAY',71,'Get back on your feet first. I do not bargain with a dying man over water and a place by the wall.')]: leaf(id,i,en)
    topic('WAKE_GUTS_DREAM', tr('I cannot tell you what you saw. I only know the wounds are real.', 'Я не знаю, что ты видел. Знаю только, что раны у тебя настоящие.'))
    topic('WAKE_RIDER', choose(math('u_berserk_knight_farewell_confirmed != 1'), line(58, 'A knight. Tall, armored. He laid you down here and told us to prepare water. Ask him the rest; he is waiting outside.'),
          tr('An armored knight brought you. Said you could recover here. He has gone on his way.', 'Тебя принёс рыцарь в доспехах. Сказал, что здесь ты сможешь прийти в себя. Теперь он отправился дальше.')))


def main_menu():
    pending = either(both(val('early_state','>',0),val('early_state','<',3)), both(val('sword_state','>',0),val('sword_state','<',4)), val('repair_state'))
    topic('', choose(KNOWS, tr('Your body is no excuse for what you do with your hands. Speak, and keep your quarrels away from the boy and my hearth.', 'Твоё тело не оправдывает того, что ты делаешь своими руками. Говори. Только свои распри держи подальше от малого и моего горна.'),
                      choose(G, tr('Speak, Guts. The iron is cooling.', 'Говори, Гатс. Железо остывает.'), tr('What did you want to ask?', 'О чём хотел спросить?'))), [
        response(97, 'Weapons and work.', 'WORK'),
        response(98, 'About my order.', 'ORDERS', pending),
        response(99, 'How long have you lived at the forge?', 'HEARTH'),
        response(100, 'I wanted to ask about Rickert.', 'APPRENTICE_MENU'),
        response(101, 'There is something I need to tell you.', 'PERSONAL', test('EOC_BERSERK_GODO_PERSONAL_AVAILABLE')),
        response('Со мной происходит перемена. Я согласился на неё, чтобы выжить.', 'Something is changing in me. I accepted it to survive.', 'TALK_BERSERK_APOSTOL_GODO', both(neg(H),neg(KNOWS)), run('EOC_BERSERK_APOSTOL_TELL_GODO')),
        response('О том, что со мной происходит.', 'About what is happening to me.', 'TALK_BERSERK_APOSTOL_GODO', KNOWS),
        response(102, 'I will leave you to your work.', 'FAREWELL'),
    ], run('DIALOGUE_SYNC'))['//'] = 'Approved Godo dialogue 2026-10-21'
    for id,i,en in [('FAREWELL',519,'Come back if you have work.'),('FAREWELL_STAY',522,'Stay. Just leave the passage clear; do not stand in the way.'),('FAREWELL_MATERIALS',525,'Go on. Check the list before you leave so you do not have to make the trip twice.'),('FAREWELL_WAIT',528,'Come back and we will see what is ready by then.'),('FAREWELL_ALONE',531,'All right. Go.')]:
        topic(id,line(i,en),[response('До встречи, Годо.', 'Until next time, Godot.', 'TALK_DONE')])
    TOPICS[tid('FAREWELL')]['responses'] += [
        response('Я пока побуду здесь.', 'I will stay here a while.', 'FAREWELL_STAY'),
        response('Я пойду за материалами.', 'I will go and find the materials.', 'FAREWELL_MATERIALS', either(val('early_state'),val('sword_state'),val('sword_state','==',2))),
        response('Зайду позже.', 'I will come back later.', 'FAREWELL_WAIT', either(val('early_state','==',2),val('sword_state','==',3),val('repair_state')))]


def weapons():
    topic('WORK', tr('Show me the iron and tell me what it must endure.', 'Покажи железо и скажи, что ему предстоит выдержать.'), [
        response('Мне нужен надёжный тяжёлый меч.', 'I need a reliable heavy sword.', 'WEAPON_REQUEST', both(H,BEFORE,neg(EARLY),val('early_state','==',0))),
        response('Мне нужен меч против этих тварей.', 'I need a sword for fighting those creatures.', 'SWORD_REQUEST', both(AFTER,neg(SWORD),val('sword_state','==',0),H)),
        response('Посмотри на этот меч.', 'Have a look at this sword.', 'OWNER', either(EARLY,SWORD)),
        response('Посмотри на эту самодельную копию.', 'Have a look at this homemade copy.', 'COPY', both(test('EOC_BERSERK_GODO_HAS_COPY'),neg(test('EOC_BERSERK_GODO_MADE_COPY')))),
        response('Я сделал этот клинок сам. Что скажешь?', 'I made this blade myself. What do you think?', 'COPY_SELF', test('EOC_BERSERK_GODO_MADE_COPY')),
        response('Мой клинок нуждается в осмотре.', 'My blade needs inspection.', 'REPAIR'),
        response('Говорят, ты однажды сделал меч для убийства дракона.', 'They say you once made a sword to kill a dragon.', 'DRAGON_STORY'),
        response('Насчёт заказа.', 'About an order.', 'ORDERS'),
        response('Почему для меча нужна разная сталь?', 'Why use different steels in a sword?', 'METAL', once='metal'),
        response('Я принёс руду. Она подойдёт?', 'I brought ore. Will that do?', 'ORE', once='ore'),
        response('Моё тело меняется. Можно поговорить о новом клинке?', 'My body is changing. Can we talk about a new blade?', 'TALK_BERSERK_APOSTOL_GODO', neg(H)), back()])
    topic('WEAPON_REQUEST', line(108, '*Godot taps the anvil without turning. "Another soldier full of stories. A sword is a tool. It must be balanced and quick. Too heavy, and you will die winding up for the first swing."'), [
        response(110,'All right, forget it.','WEAPON_LEAVE'),
        response(111,'I need a powerful blade. It need not be that extreme.','WEAPON_REASONABLE'),
        response(112,'I can handle the weight. Ordinary swords break when I put all my strength into them.','WEAPON_REFUSE'),back()])
    leaf('WEAPON_LEAVE',113,'Come back if you need something. Ask Rickert, too. He may have something useful for you. Not a sword, but useful all the same.','WORK')
    leaf('WEAPON_REASONABLE',114,'There. You can listen after all. I can try, but you will have to bring the materials. I am too old to go looking for them.','WORK')['responses']=[response(117,'Will you take the work?','EARLY_SWORD'),response(118,'I need to think.','WEAPON_THINK')]
    topic('WEAPON_REFUSE',line(115,'Listen. A sword is forged for a person. It must be an extension of the hand. I have done this since I could hold tongs. I will not waste steel and heat on a useless monstrosity no one can fight with.'),[
        response('Тогда сделай клинок, с которым я справлюсь.', 'Then make a blade I can use.', 'WEAPON_REASONABLE'),response(118,'I need to think.','WEAPON_THINK'),back('WORK')])
    leaf('WEAPON_THINK',121,'Think. No need to hurry before the iron is in the fire.','WORK')
    topic('OWNER',choose(SWORD,line(203,'Put it down. Even that much iron has parts that need watching.'),choose(val('early_delivered'),line(126,'Let me see. Has the grip turned? Does the guard press into your palm? How is the swing?'),line(136,'Heavy. Familiar to you, then. The edge shows it has not been idle.'))),[
        response(128,'It serves me well.','OWNER_GOOD',EARLY),response(129,'It needs repair.','REPAIR'),
        response(130,'Could you improve it?','OWNER_UPGRADE',EARLY),response(205,'I thought it was almost impossible to break.','OWNER_BREAK',SWORD),
        response(206,'It feels different now.','OWNER_FEEL',SWORD),back('WORK')])
    for id,i,en in [('OWNER_GOOD',131,'Then the fitting was worth the work.'),('OWNER_UPGRADE',134,'Not without changing its shape and finding the balance all over again. That would mean making a new sword.'),('OWNER_BREAK',208,'Anything can break. Especially if you keep testing whether it can take one more blow.'),('OWNER_FEEL',209,'Show me the grip. Then take it again. We will see whether it is the blade or you getting used to it.')]:leaf(id,i,en,'OWNER')
    TOPICS[tid('OWNER_GOOD')]['dynamic_line']=choose(val('early_delivered'),line(131,'Then the fitting was worth the work.'),tr('Then keep looking after it. A sound blade deserves that much.', 'Тогда следи за ним и дальше. Хороший клинок того стоит.'))
    topic('COPY',tr('*Godot turns the sword, checks the grip and draws a thumb across the edge. "Someone took pains with this. Still a long way from a fine blade, but better than nothing."','*Годо поворачивает меч, проверяет посадку рукояти и проводит большим пальцем поперёк кромки. «Кто-то старался. До отличного клинка далеко, конечно, но лучше, чем ничего». '),[response('Ему нужен ремонт.', 'It needs repair.', 'REPAIR'),back('WORK')])
    topic('COPY_SELF',tr('*Godot checks the grip and the edge. "What matters is how it behaves in the hand. You worked at it, I can see. A long way from a fine blade, but better than nothing."','*Годо проверяет посадку рукояти и кромку. «Важно, как он ведёт себя в руке. Видно, старался. Далеко, конечно, до отличного клинка, но лучше, чем ничего». '),[
        response(146,'You could have praised it.','COPY_PRAISE'),response(147,'There was no other suitable weapon.','COPY_NEED'),response(148,'I wanted to learn.','COPY_LEARN'),back('WORK')])
    for id,i,en in [('COPY_PRAISE',149,'Flattery makes a worse smith. Your life depends on the blade; one mistake can end it. Do not take offense.'),('COPY_NEED',150,'A good reason to pick up a hammer. Live with it now. You will feel where you went wrong.'),('COPY_LEARN',151,'Keep it, then. Pick it up again after a few more attempts and you will see the mistakes for yourself.')]:leaf(id,i,en,'WORK')
    topic('DRAGON_STORY',line(155,'Hmph. I did. A long time ago.'),[response(157,'Do dragons even exist?','DRAGON_EXIST',once='dragon_exist'),response(158,'Why take such an order?','DRAGON_ORDER',once='dragon_order'),response(159,'Who could use it?','DRAGON_USER',once='dragon_user'),response(173,'Do you consider that sword a failure?','DRAGON_KEEP'),back('WORK')])
    for id,i,en in [('DRAGON_EXIST',163,'The puffed-up fool who sent the plans never thought about that. He wanted a toy everyone would talk about. Vanity brings plenty of foolish things into the world.'),('DRAGON_ORDER',167,'An order from above. They asked for a sword that could cut a dragon, so I forged one. I met the terms exactly. Nobody thought to ask whether an ordinary man could lift it.')]:leaf(id,i,en,'DRAGON_STORY')
    dragon_known=either(SWORD,val('sword_delivered'))
    topic('DRAGON_USER',choose(dragon_known,tr('None of those pampered lords could use it. That was then. You know what sort of hands it has reached now.','Тогда — никто из тех изнеженных лордов. Слишком тяжела оказалась железка. А в чьи руки она попала теперь, ты и сам знаешь.'),line(171,'Nobody then. Certainly none of the pampered lords who ordered it. Not a knight in the kingdom could use it. It stayed there, dead weight.')),[back('DRAGON_STORY')])
    topic('DRAGON_KEEP',choose(dragon_known,tr('The iron was what I intended: strong and deadly. But it was useless to the people it was meant for. A smith must think about the hands that will carry his work. You have reminded me of that.','Железо получилось таким, каким я его задумал: прочным, смертоносным. Но людям, которым оно предназначалось, толку от него не было. Кузнецу приходится думать о руках, в которых окажется его работа. Ты мне об этом напомнил.'),line(174,'No. The iron was exactly what I meant it to be: strong and deadly. It was useless to the people it was meant for. A smith must think about the hands that will carry his work. That blade waits for someone as mad as it is.')),[back('WORK')])
    TOPICS[tid('DRAGON_KEEP')]['dynamic_line']['no']=tr('No. The iron was what I intended: strong and deadly. It was useless to the people it was meant for. A smith must think about the hands that will carry his work. A blade like that only makes sense for someone as mad as the design.','Нет. Железо получилось таким, каким я его задумал: прочным, смертоносным. Но людям, которым оно предназначалось, толку от него не было. Кузнецу приходится думать о руках, в которых окажется его работа. Такой клинок нужен лишь тому, кто будет равен этому замыслу по безумию.')
    topic('SWORD_REQUEST',choose(both(G,test('EOC_BERSERK_GODO_WITNESSED_ECLIPSE')),line(180,'The same creatures that left those wounds on you?'),tr('A blade for fighting those creatures? Tell me why you need it.', 'Клинок против этих тварей? Скажи, зачем он тебе.')),[
        response(182,'Ordinary weapons shatter against them.','SWORD_REASON_STEEL'),response(183,'I want to reach whoever is behind this nightmare.','SWORD_REASON_VENGEANCE'),response(184,'I need to protect myself and those I care about.','SWORD_REASON_PROTECT'),back('WORK')])
    for id,i,en in [('SWORD_REASON_STEEL',187,'Creatures of the abyss are no wild beasts. If ordinary steel will not do, we must make a blade that bears the impact without dragging its owner into the grave.'),('SWORD_REASON_VENGEANCE',190,'Before the one at the top, there are those below. You order it with rage in your eyes, but you must carry it on the days when you have no strength left to be angry.'),('SWORD_REASON_PROTECT',193,'Protection is a heavier burden than revenge. Then listen. Where will you fight? How much can you carry? What balance are you used to? I need honest answers.')]:
        leaf(id,i,en,'WORK')['responses']=[response(196,'Will you make me a Dragonslayer?','SWORD_DESIGN'),back('WORK')]
    topic('SWORD_DESIGN',line(197,'I know a blade that could hew demons. That old design. I also know how much good steel and charcoal it takes. We will not finish it in an evening.'),[response(199,'Tell me what to bring. I will find it.','SWORD'),response(200,'I need time to prepare.','WEAPON_THINK'),back('WORK')])
    leaf('METAL',13,'Soft steel folds at the edge; brittle steel breaks. Heat, temper and shape must suit the work. Bring sound steel, not a promise of it.','WORK')['dynamic_line']=tr('Soft steel folds at the edge; brittle steel breaks. Heat, temper and shape must suit the work. Bring sound steel, not a promise of it.','Мягкая сталь заминается на кромке, хрупкая — ломается. Нагрев, закалка и форма должны подходить для работы. Принеси добротную сталь, а не обещание её добыть.')
    topic('ORE',tr('Ore has to be smelted first. For these orders, bring steel ready for the forge. Rickert can help you tell the pieces apart.','Руду сперва надо выплавить. Для этих заказов нужна сталь, готовая к ковке. Рикерт поможет разобраться, какие куски ты принёс.'),[back('WORK')])
    topic('STEEL',tr('Try stores of metal, old workshops, or steel you have smelted yourself. Keep the good high-carbon pieces separate from the ordinary steel.','Поищи запасы металла, старые мастерские или выплавь сталь сам. Добротные куски высокоуглеродистой стали держи отдельно от обычной.'),[back('ORDERS')])


def orders(old):
    pending = either(both(val('early_state','>',0),val('early_state','<',3)),both(val('sword_state','>',0),val('sword_state','<',4)),val('repair_state'))
    topic('ORDERS',choose(neg(H),choose(KNOWS,tr('I will return what you brought for the unfinished blade. The work is over.','Что ты принёс для незаконченного клинка — верну. За эту работу я больше не возьмусь.'),tr('Before we go on, tell me what has been troubling you.','Прежде чем продолжим, скажи, что тебя гложет.')),tr('What is needed, what you brought, and what is left to do. That is a proper order.','Что нужно, что принёс и что осталось сделать. Вот и весь правильный заказ.')),[
        response('Заказ боевого меча.', 'The battle sword order.', 'EARLY_SWORD', either(BEFORE,val('early_state','>',0))),
        response('Заказ Драконоборца.', 'The Dragonslayer order.', 'SWORD', either(AFTER,val('sword_state','>',0))),
        response('Насчёт ремонта клинка.', 'About the blade repair.', 'REPAIR', val('repair_state')),
        response('Я потерял дорожный журнал. Нужен другой.', 'I lost my road journal. I need another.', 'ORDERS',neg({'u_has_item':'berserk_campaign_journal'}),run('EOC_BERSERK_JOURNAL_REPLACE_MISSING')),back()])
    for suffix,stem,terminal,owned,waitstate,waittime in [('EARLY','early',3,EARLY,2,'twelve hours'),('SWORD','sword',4,SWORD,3,'two days')]:
        id='EARLY_SWORD' if suffix=='EARLY' else 'SWORD'
        start='START_EARLY_SWORD' if suffix=='EARLY' else 'START_SWORD'
        unknown=tr('Something has been weighing on you. If it concerns this work, tell me before we continue.','Вижу, тебя что-то тяготит. Если это касается нашей работы, расскажи, прежде чем продолжим.')
        refusal=tr('My answer has not changed. There will be no new blade.','Мой ответ не изменился. Нового клинка не будет.')
        if suffix=='EARLY':
            before_work=tr('A long battle sword, no ornaments. Bring 4 steel lumps, 1 high-steel lump, 200 charcoal and 2 leather patches, all together. Then give me twelve hours at the forge.','Длинный боевой меч, без украшений. Принеси вместе 4 куска стали, 1 кусок высокоуглеродистой стали, 200 единиц древесного угля и 2 лоскута кожи. Потом дай мне двенадцать часов у горна.')
            collecting=tr('For this delivery: 4 steel lumps, 1 high-steel lump, 200 charcoal and 2 leather patches. Bring the whole lot so I can begin.','Для этой поставки: 4 куска стали, 1 кусок высокоуглеродистой стали, 200 единиц древесного угля и 2 лоскута кожи. Принеси всё вместе, чтобы я мог начать.')
        else:
            before_work=tr('First I need 32 steel lumps, in loads of eight. Then 8 high-steel lumps, 600 charcoal and 4 leather patches. After the final delivery, give me two days.','Сперва нужны 32 куска стали — приноси партиями по восемь. Затем 8 кусков высокоуглеродистой стали, 600 единиц древесного угля и 4 лоскута кожи. После последней поставки дай мне два дня.')
            collecting=tr('I need 32 steel lumps in all. You have brought <u_val:berserk_godo_sword_iron_given>. Bring another load of eight when you can.','Всего нужны 32 куска стали. Ты принёс <u_val:berserk_godo_sword_iron_given>. Как сможешь — неси следующую партию из восьми.')
        waiting=tr('In the forge. Metal does not like haste. You can see to your own equipment while I work.','В работе. Металл спешки не любит. Пока я кую, займись своим снаряжением.')
        ready=tr('Finished. Come over here and take it by the grip.','Готово. Подойди сюда, возьми за рукоять.')
        status=choose(val(stem+'_state','==',terminal),tr('That order is settled. We have nothing more to exchange for it.','С этим заказом мы рассчитались. Больше ничего по нему передавать не нужно.'),
                      choose(owned,tr('You already have the blade. If you left materials for another, take them back.','Клинок у тебя уже есть. Если оставлял материалы для другого — забери их.'),
                      choose(val(stem+'_state','==',1),collecting,choose(val(stem+'_state','==',waitstate),choose(math(f"time('now') >= u_berserk_godo_{stem}_ready_at"),ready,waiting),before_work))))
        if suffix=='SWORD':
            status=choose(val('sword_state','==',2),tr('The ordinary steel is here. Now bring 8 high-steel lumps, 600 charcoal and 4 leather patches.','Обычная сталь здесь. Теперь нужны 8 кусков высокоуглеродистой стали, 600 единиц древесного угля и 4 лоскута кожи.'),status)
        status=choose(neg(H),choose(KNOWS,refusal,unknown),status)
        response_start=response('Возьмёшься за работу?', 'Will you take the work?', id,
                                test('EOC_BERSERK_GODO_'+start),run(start))
        rs=[response_start]
        payment_ids=['EARLY_MATERIALS'] if suffix=='EARLY' else ['SWORD_IRON','SWORD_TEMPER']
        for pay in payment_ids:
            label={'EARLY_MATERIALS':('Материалы здесь. Всё, как ты просил.','The materials are here. Everything you asked for.'),
                   'SWORD_IRON':('Вот восемь кусков стали.','Here are eight steel lumps.'),
                   'SWORD_TEMPER':('Вот высокоуглеродистая сталь, уголь и кожа.','Here are the high steel, charcoal and leather.')}[pay]
            rs.append(response(*label,suffix+'_DELIVERY',test('EOC_BERSERK_GODO_'+pay),run(pay)))
        rs += [response('Заберу готовый клинок.', 'I will take the finished blade.', suffix+'_DELIVERED',both(test('EOC_BERSERK_GODO_'+suffix+'_CLAIM'),neg(owned)),run(suffix+'_CLAIM')),
               response('Мне нужен список того, что ещё принести.', 'What do I still need to bring?', suffix+'_STATUS'),
               response('Почему так долго? Время поджимает.', 'Why so long? I am short of time.', suffix+'_WHY',
                        both(val(stem+'_state','==',waitstate),math(f"time('now') < u_berserk_godo_{stem}_ready_at")),once=stem+'_why'),
               response('Клинок уже есть. Верни неиспользованные материалы.', 'I already have the blade. Return the unused materials.', id,
                        both(owned,val(stem+'_state','>',0),val(stem+'_state','<',terminal)),run(suffix+'_REFUND')),
               response('Я изменился. Что будет с нашей договорённостью?', 'I have changed. What about our agreement?', 'TALK_BERSERK_APOSTOL_GODO',neg(H),run('EOC_BERSERK_APOSTOL_TELL_GODO')),
               response('Ты обещал вернуть материалы.', 'You promised to return the materials.', 'CHANGED_'+suffix,
                        both(neg(H),KNOWS,val(stem+'_state','>',0),val(stem+'_state','<',terminal))),
               response('Осмотри мой клинок.', 'Inspect my blade.', 'REPAIR',owned),back('ORDERS')]
        topic(id,status,rs,math(f'u_berserk_journal_order_{stem} = 1'))
        topic(suffix+'_STATUS',status,[back(id)])
        topic(suffix+'_WHY',line(236,'Because I will not give you a weapon with a hidden crack I could have found in the forge. Heat, hammering and cooling take their time. Want quick? Find a club in the woods. Want to live? Wait.'),[back(id)])
        topic(suffix+'_DELIVERY',choose(val(stem+'_state','==',waitstate),
             tr('Good. The metal is here. Now it is my work. Give me '+waittime+' and do not hover over my shoulder.',
                'Годится. Металл на месте. Теперь моя работа. Дай мне '+('двенадцать часов' if suffix=='EARLY' else 'два дня')+' и не стой над душой.'),
             tr('Good. That part is settled. Ask what is needed next before you leave.','Годится. С этой частью разобрались. Перед дорогой спроси, что потребуется дальше.')),[response('Что нужно теперь?', 'What is needed now?',id),back('ORDERS')])
        topic('CHANGED_'+suffix,choose(KNOWS,line(304,'I will return everything you brought. I have no use for what is not mine. Come here and take it.'),unknown),[
            response('Верни мои материалы.', 'Return my materials.', 'REFUND_DONE',both(KNOWS,test('EOC_BERSERK_GODO_'+suffix+'_REFUND')),run(suffix+'_REFUND')),
            response('Мне нужно объяснить, что случилось.', 'I need to explain what happened.', 'TALK_BERSERK_APOSTOL_GODO',neg(KNOWS),run('EOC_BERSERK_APOSTOL_TELL_GODO')),back('ORDERS')])
    topic('REFUND_DONE',tr('We have settled the account. There will be no blade for this order.','С долгом рассчитались. Клинка по этому заказу не будет.'),[back('ORDERS')])
    topic('EARLY_DELIVERED',line(240,'Finished. Take the grip. Now lift it... Careful! Do not swing; I still need that ceiling. How does it feel?'),[
        response('Хорошо лежит в руке.','It sits well in the hand.','EARLY_RECEIPT_GOOD'),response('Тяжелее, чем я ожидал...','Heavier than I expected...','EARLY_RECEIPT_HEAVY'),back()])
    topic('EARLY_RECEIPT_GOOD',tr('Remember that feeling. If the grip starts to shift, repair it before it loosens completely.','Запомни это ощущение. Если хват начнёт гулять — чини сразу, не жди, пока рукоять разболтается окончательно.'))
    topic('EARLY_RECEIPT_HEAVY',tr('Learn its weight in an open space, not a narrow passage full of creatures. Bring the blade back into guard after each blow.','К весу привыкай на свободном месте, не в узком проходе с тварями. После каждого удара возвращай клинок в защиту.'))
    topic('SWORD_DELIVERED',tr('*Godot clears a space beside the enormous black blade. "Finished. Come around and help me shift it. A blade for things a man was never meant to fight. Your Dragonslayer."','*Годо освобождает место рядом с огромным чёрным клинком. «Закончил. Подходи с этой стороны, помоги сдвинуть. Клинок для боя с тем, с чем человеку прежде сражаться не приходилось. Твой Драконоборец». '),[
        response('С ним у меня наконец-то будет шанс.','With this, I will finally have a chance.','SWORD_RECEIPT_CHANCE'),response(249,'I will come back, Godot.','SWORD_RECEIPT_RETURN'),response('Спасибо, Годо.','Thank you, Godot.','SWORD_RECEIPT_THANKS'),back()])
    topic('SWORD_RECEIPT_CHANCE',tr('A chance, yes. It is only iron. The rest, whether you live or die, is yours to do.','Шанс будет. Но это лишь железо. Всё остальное — выживешь ты или сдохнешь — придётся делать тебе самому.'))
    topic('SWORD_RECEIPT_RETURN',tr('Come back. We will see how this iron serves against your demons.','Возвращайся. Посмотрим, как это железо послужит против твоих демонов.'))
    topic('SWORD_RECEIPT_THANKS',tr('Keep your grip. And... take care of yourself, boy.','Береги хват. И… береги себя, парень.'))
    # Existing repair transactions are retained, including custody and deadlines.
    repair=copy.deepcopy(old['TALK_BERSERK_GODO_REPAIR'])
    repair['dynamic_line']=choose(val('repair_state'),tr('You left me a blade. Two hours at the forge; then come and ask for it.','Ты оставил мне клинок. Два часа у горна — потом приходи за ним.'),
        tr('Put it in the light. First I will inspect it. If it is sound, keep your steel. If it needs work, I need the blade, one steel lump, 50 charcoal and two hours.','Положи на свет. Сперва осмотрю. Если целый — побереги сталь. Если нужен ремонт, оставишь клинок, один кусок стали и 50 единиц древесного угля. На работу нужно два часа.'))
    labels={'Have a look at my blade.':('Осмотри мой клинок.','Have a look at my blade.'),'Is my blade ready?':('Мой клинок готов?','Is my blade ready?'),'I took the blade. Here it is again.':('Я забрал клинок. Вот, возвращаю.','I took the blade. Here it is again.'),'Close the repair order.':('Закроем заказ ремонта.','Close the repair order.')}
    repair['responses']=[r for r in repair['responses'] if r['text'] in labels]
    for r in repair['responses']:r['text']=tr(labels[r['text']][1],labels[r['text']][0])
    repair['dynamic_line']=choose(both(neg(H),SWORD,val('repair_state','!=',1)),
        choose(KNOWS,tr('I will not take new work on the Dragonslayer. I can still inspect an ordinary blade.','За новую работу над Драконоборцем я не возьмусь. Обычный клинок ещё могу осмотреть.'),
               tr('Before we discuss this blade, tell me what has been weighing on you.','Прежде чем говорить об этом клинке, расскажи, что тебя гложет.')),repair['dynamic_line'])
    repair['responses'][0]['condition']=both(val('repair_state','!=',1),either(H,neg(SWORD),KNOWS))
    repair['responses'] += [response('Я принял чужую силу. Что будет с моим мечом?','I accepted an inhuman power. What about my sword?','DEMON_OWNED',both(SWORD,neg(H)),run('EOC_BERSERK_APOSTOL_TELL_GODO')),back('WORK')]
    TOPICS[repair['id']]=repair


def hearth_and_rickert():
    topic('HEARTH',tr('The coals will keep. Ask.','Угли пока не погаснут. Спрашивай.'),[
        response(315,'Why live so far from other people?','ISOLATION'),
        response(327,'How long have you worked at the anvil?','LIFE'),
        response(337,'You are old and ill. You could have put the hammer down long ago.','KEEP_FORGING'),
        response('Позволь мне немного посидеть у твоего горна.','Let me sit by your forge a while.','SPARKS_INVITE',test('EOC_BERSERK_GODO_CAN_SPARKS')),
        response('Я помню, что ты говорил тогда у горна.','I remember what you told me at the forge.','SPARKS_RECALL',val('sparks_completed')),
        response('Можно мне здесь передохнуть?','May I rest here?','HOME'),back()])
    topic('ISOLATION',line(316,'Here I can hear my own hammer. In town, people sometimes cannot hear their own work through all the empty talk.'),[
        response(318,'Do people bother you that much?','ISOLATION_PEOPLE',once='isolation_people'),
        response(319,'But customers must be harder to find here.','ISOLATION_CUSTOMERS',once='isolation_customers'),
        response('Вам с Рикертом здесь не одиноко?','Do you and Rickert get lonely here?','ISOLATION_LONELY',once='isolation_lonely'),back('HEARTH')])
    topic('LIFE',line(328,'Since I could hold tongs. First I carried billets and water and worked the bellows. Then I was graciously allowed to spoil the iron myself.'),[
        response(330,'Did you spoil much good iron?','LIFE_IRON',once='life_iron'),response(331,'When did you know you were a master?','LIFE_MASTER',once='life_master'),back('HEARTH')])
    topic('KEEP_FORGING',line(338,'I could have. Long ago.'),[response(340,'Then why keep going?','KEEP_REASON'),back('HEARTH')])
    topic('KEEP_REASON',line(341,'Every morning I see what I did not finish the night before. I know where my day begins. By noon a shapeless lump has become a thing someone can use. Enough to feel alive.'),[
        response(343,'Did you never want a different life?','KEEP_OTHER',once='keep_other'),
        response(344,'I understand.','KEEP_UNDERSTAND',effect=setv('hearth_trust')),back('HEARTH')])
    topic('KEEP_UNDERSTAND',line(347,'If you understand, you have been luckier than most wanderers.'),[
        response('Позволь мне немного посидеть у твоего горна.','Let me sit by your forge a while.','SPARKS_INVITE',test('EOC_BERSERK_GODO_CAN_SPARKS')),back('HEARTH')])
    for id,i,en,parent in [
        ('ISOLATION_PEOPLE',322,'A man who knows why he came does not bother me. Being asked to admire a crest for half a day instead of making a sound weapon does.','ISOLATION'),
        ('ISOLATION_CUSTOMERS',323,'I have more than enough work. Extra gold will not make these hands younger.','ISOLATION'),
        ('ISOLATION_LONELY',324,'Rickert always finds a way to break the silence. Sometimes before I have had time to miss it.','ISOLATION'),
        ('LIFE_IRON',333,'Enough. Some of the rubbish I made when I was young still makes me ashamed.','LIFE'),
        ('LIFE_MASTER',334,'When I stopped blaming the steel every time a blade cracked. Steel does not lie. The smith\'s hand does.','LIFE'),
        ('KEEP_OTHER',346,'I wanted plenty of things when I was young and foolish. But I always came back to this forge of my own accord.','HEARTH')]:leaf(id,i,en,parent)
    topic('HOME',line(20,'There is a place for a traveler. Rickert can show you. No sleeping in the workshop, and leave the tools alone.'),[response('Понял. Спасибо.','Understood. Thank you.','INTRO_AGREED'),back('HEARTH')])
    topic('APPRENTICE_MENU',line(353,'He has learned a few things. Invented a few more while I grumbled about making simple things complicated.'),[
        response(355,'What sort of things?','APPRENTICE_EXAMPLES',once='rickert_examples'),
        response(356,'Do you approve of his inventions?','APPRENTICE_APPROVE',once='rickert_approve'),
        response(362,'Why did you let him stay here?','APPRENTICE_HOME'),
        response('Рикерт тяжело переживает наш разговор.','Rickert is taking our conversation hard.','APPRENTICE_GRIEF',both(AFTER,math('u_berserk_rickert_eclipse_story > 0'))),
        response(384,'Rickert decided to leave the forge and travel with me.','APPRENTICE_TRAVEL',math('berserk_godo_rickert_following == 1')),
        response(397,'Talk to Rickert. Tell him to come with me. He will listen to you.','APPRENTICE_REFUSAL',math('berserk_godo_rickert_refused == 1'),once='rickert_refused'),back()])
    leaf('APPRENTICE_EXAMPLES',358,'Fastenings, triggers, little springs. I would make a thicker piece of solid steel. He spends an hour on a drawing, removes half the iron, and the damned thing still works.','APPRENTICE_MENU')
    leaf('APPRENTICE_APPROVE',359,'If it survives a real fight, yes. If it breaks in the hand, he makes it again. Better for his hands than any praise.','APPRENTICE_MENU')
    topic('APPRENTICE_HOME',tr('The boy needed somewhere to live. There was room here and another piece of bread.','Мальцу нужно было где-то жить. А здесь нашлось свободное место и лишний кусок хлеба.'),[response(365,'Is that the only reason?','APPRENTICE_HELP'),back('APPRENTICE_MENU')])
    topic('APPRENTICE_HELP',tr('Did you want a longer, tearful story? If you can help the boy, you help. No need to make a speech.','А тебе нужна слезливая история подлиннее? Если можешь помочь мальцу — просто помогаешь. Без лишних слов.'),[back('APPRENTICE_MENU')])
    topic('APPRENTICE_GRIEF',choose(math('u_berserk_rickert_eclipse_story == 1'),line(371,'I see it. His hammer falls out of rhythm; he overheats the forge. It is hard on him.'),
        tr('He has more questions than answers. Do not make him guess what you are able to tell him.','У него вопросов больше, чем ответов. Не заставляй его гадать о том, что ты можешь рассказать.')),[
        response(373,'I did not know how to tell him.','APPRENTICE_GRIEF_WORDS',math('u_berserk_rickert_eclipse_story == 1')),
        response(374,'I have not been able to tell him everything.','APPRENTICE_GRIEF_WAIT',math('u_berserk_rickert_eclipse_story >= 2')),
        response(375,'How should I speak to him now?','APPRENTICE_GRIEF_HELP'),back('APPRENTICE_MENU')])
    for id,i,en in [('APPRENTICE_GRIEF_WORDS',377,'Nobody knows the right words for that. Losing people is a blow to the head, however you dress it up.'),('APPRENTICE_GRIEF_WAIT',378,'Do not promise some vague later if you cannot do it now. Tell him plainly: I will tell you the rest when I can. He can understand honesty.'),('APPRENTICE_GRIEF_HELP',379,'Do not expect him to understand it all and move on today. Give him time. When he can speak, let him ask his questions. Answer without hiding behind excuses.')]:leaf(id,i,en,'APPRENTICE_MENU')
    topic('APPRENTICE_TRAVEL',line(385,'He decided that himself? Without you leaning on him?'),[response(386,'Yes. It was his decision.','APPRENTICE_TRAVEL_RESPECT'),back('APPRENTICE_MENU')])
    topic('APPRENTICE_TRAVEL_RESPECT',line(387,'Remember that he has a head of his own. A companion, not spare hands for your weapon or a slave to carry loot. Treat him with respect.'),[
        response(389,'I understand, Godot.','APPRENTICE_TRAVEL_PROMISE'),response(390,'You do not want to let him go, do you?','APPRENTICE_TRAVEL_WORRY'),back('APPRENTICE_MENU')])
    leaf('APPRENTICE_TRAVEL_PROMISE',392,'Good. Do not make me search the woods for you if a hair on his head is harmed.','APPRENTICE_MENU')
    leaf('APPRENTICE_TRAVEL_WORRY',393,'I do not. I am old and used to having the boy here. But I will not lock him inside for my own comfort. His road is his to choose.','APPRENTICE_MENU')
    leaf('APPRENTICE_REFUSAL',398,'He has given his answer. Do not go around him through me. He has his own life. If he said no, respect it. Go about your business and stop begging.','APPRENTICE_MENU')


def personal():
    grief=both(test('EOC_BERSERK_GODO_WITNESSED_ECLIPSE'),H,val('trauma_done','!=',1))
    revenge=both(G,test('EOC_BERSERK_GODO_WITNESSED_ECLIPSE'),val('sword_state','>',0),val('revenge_told','!=',1))
    topic('PERSONAL',tr('Set the iron down. I am listening.','Отложи железо. Я слушаю.'),[
        response('Там, в том кошмаре, погибли мои товарищи.','My companions died in that nightmare.','TRAUMA',both(grief,G),setv('hearth_trust')),
        response('В том кошмаре гибли люди. Я до сих пор это помню.','People were dying in that nightmare. I still remember it.','TRAUMA',both(grief,neg(G)),setv('hearth_trust')),
        response('Я найду его. Чего бы мне это ни стоило.','I will find him. Whatever it costs.','REVENGE',revenge,setv('revenge_told')),
        response('Со мной происходит перемена.','Something is changing in me.','TALK_BERSERK_APOSTOL_GODO',neg(H),run('EOC_BERSERK_APOSTOL_TELL_GODO')),back()])
    topic('TRAUMA',line(403,'Sit by the fire. We can talk.'),[
        response(405,'I should have done something. Saved them.','TRAUMA_COULD'),
        response(406,'I still remember their voices.','TRAUMA_VOICES'),
        response(407,'I cannot go on talking about this now.','TRAUMA_SILENT')])
    topic('TRAUMA_COULD',line(410,'What could you have done against that abyss?'),[
        response('Я не знаю...','I do not know...','TRAUMA_UNKNOWN'),response('Я должен был умереть вместе с ними!','I should have died with them!','TRAUMA_DIED'),response('Мне нужно побыть одному.','I need to be alone.','TRAUMA_SILENT')])
    topic('TRAUMA_UNKNOWN',tr('Then do not pretend you knew the answer and chose cowardice. You did what a human body could do.','Тогда не притворяйся перед самим собой, будто знал правильный ответ и струсил. Ты сделал то, что было в человеческих силах.'),[response('Спасибо, что выслушал.','Thank you for listening.','',effect=run('END_TRAUMA'))])
    topic('TRAUMA_DIED',tr('But you are alive. By a miracle or by your teeth, you got out. Now you have to live with that. Living on is the hard part.','Но ты жив. Чудом, зубами, но выкарабкался. Теперь с этим фактом придётся жить. Жить дальше — вот что тяжело.'),[response('Мне нужно время.','I need time.','',effect=run('END_TRAUMA'))])
    topic('TRAUMA_SILENT',line(417,'If you cannot, you cannot. No need to tear the wound open. We can sit quietly by the forge. Warm yourself.'),[
        response('Посидим молча.','Let us sit quietly.','',effect=run('END_TRAUMA')),response('Мне нужно побыть одному.','I need to be alone.','FAREWELL_ALONE',effect=run('END_TRAUMA'))])
    topic('TRAUMA_VOICES',line(416,'Tell me about one of them, if you want. Who they were before that day. Remember people alive, not torn apart.'),[
        response('О Джудо.','About Judeau.','MEMORY_JUDEAU',either(G,val('witness_judeau'))),
        response('О Пиппине.','About Pippin.','MEMORY_PIPPIN',either(G,val('witness_pippin'))),
        response('О Коркусе.','About Corkus.','MEMORY_CORKUS',either(G,val('witness_corkus'))),
        response('О Гастоне.','About Gaston.','MEMORY_GASTON',either(G,val('witness_gaston'))),
        response('Я пока не готов. Спасибо, что выслушал.','Not yet. Thank you for listening.','',effect=run('END_TRAUMA'))])
    for name,en,ru in [('JUDEAU','He looked after the people beside him. Tell me about that, not just the way he died.','Он заботился о тех, кто был рядом. Расскажи об этом, а не только о том, как он погиб.'),('PIPPIN','A man who stood between danger and his companions. That is worth remembering.','Человек, который вставал между опасностью и товарищами. Это стоит помнить.'),('CORKUS','A man has more to him than a sharp tongue. What did he hope for?','Человек — это не только острый язык. На что он надеялся?'),('GASTON','A life beyond battle. Work, a place of his own. Not a foolish dream.','Жизнь без сражений. Работа, своё место. Неглупая мечта.')]:
        topic('MEMORY_'+name,tr(en,ru),[response('Я помню его.','I remember him.','TRAUMA_VOICES'),response('Спасибо. Хватит на сегодня.','Thank you. Enough for today.','',effect=run('END_TRAUMA'))])
    topic('REVENGE',line(422,'I believe you. If you have the strength, you will find him.'),[response(423,'Is that all? You will not try to stop me?','REVENGE_REPLY')])
    leaf('REVENGE_REPLY',424,'What would be the point? You did not come for my blessing. But revenge is the end of a road. When you want to talk about how to reach that day without losing your mind, I will be here at the forge.')


def demon():
    id='TALK_BERSERK_APOSTOL_GODO'
    topic(id,choose(val('demon_refused'),tr('My answer has not changed. There will be no new blade.','Мой ответ не изменился. Нового клинка не будет.'),
        choose(test('EOC_BERSERK_APOSTOL_FORM_VISIBLE'),line(267,'I can see what is happening to you. Your skin, your eyes... Why did you let that corruption in?'),line(265,'What change? Explain it properly.'))),[
        response(271,'I was given this power. My body is becoming something else.','DEMON_GIFT',both(val('demon_refused','!=',1),neg(either(math('u_berserk_apostol_path == 2'),math('u_berserk_apostol_path == 3'))))),
        response(272,'I took the power from one of those creatures.','DEMON_FLESH',both(val('demon_refused','!=',1),math('u_berserk_apostol_path == 2'))),
        response(273,'I agreed to serve those who are stronger. This is the price.','DEMON_SERVICE',both(val('demon_refused','!=',1),math('u_berserk_apostol_path == 3'))),
        response('Ты обещал вернуть материалы для боевого меча.','You promised to return the battle sword materials.','CHANGED_EARLY',both(val('early_state','>',0),val('early_state','<',3))),
        response('Ты обещал вернуть материалы для Драконоборца.','You promised to return the Dragonslayer materials.','CHANGED_SWORD',both(val('sword_state','>',0),val('sword_state','<',4))),
        response('Меч уже у меня. Ты потребуешь его назад?','I already have the sword. Will you demand it back?','DEMON_OWNED',either(EARLY,SWORD)),
        response('Можно мне остаться в кузне?','May I remain at the forge?','DEMON_STAY'),back()],run('EOC_BERSERK_APOSTOL_TELL_GODO'))
    for id,i,en in [('DEMON_GIFT',276,'Do you understand where it will end? Iron changes in the forge too. Leave it too long and it becomes slag.'),('DEMON_FLESH',277,'Defeating it was not enough? You chose to become it. The abyss can poison people even after its creatures die.'),('DEMON_SERVICE',278,'Serve them? What if your master tells you to turn that weapon on the people you came to for help?')]:
        topic(id,line(i,en),[response(281,'I needed the power to survive!','DEMON_REFUSE_NEED',effect=setv('demon_refused')),
            response(282,'I still decide what I do. My mind is my own.','DEMON_REFUSE_WILL',effect=setv('demon_refused')),
            response(283,'I do not want to argue, Godot.','DEMON_REFUSE_QUIET',effect=setv('demon_refused'))])
    for id,i,en in [('DEMON_REFUSE_NEED',286,'Maybe you did. Everyone wants to live. But I will not forge a sword for this new road of yours.'),('DEMON_REFUSE_WILL',287,'Then listen to my answer while you can. I will not make that blade.'),('DEMON_REFUSE_QUIET',288,'Then we will not argue. I have told you the work I will not take.')]:
        topic(id,line(i,en),[response(291,'You agreed to help me before. Why refuse now?','DEMON_WHY'),back()])
    topic('DEMON_WHY',line(292,'You came as a person asking for a person\'s weapon. Now you ask me to arm what you are becoming. I do not know that creature. I will not help it grow stronger.'),[
        response(294,'Are you throwing me out?','DEMON_STAY'),response(295,'Is that your final answer?','DEMON_FINAL'),back()])
    leaf('DEMON_STAY',297,'I refused to forge you a blade. The rest depends on your behavior under my roof. Act like a person and you may remain.')
    leaf('DEMON_FINAL',298,'Yes. Final.')
    topic('DEMON_OWNED',tr('It is yours. You fought with it; you answer for it. I will not tear it out of your hands. But if the Dragonslayer breaks, I will not take new work on it for this road.','Он уже твой. Ты им сражался — ты за него и отвечаешь. Вырывать его из твоих рук я не стану. Но если Драконоборец повредится, за новую работу над ним на этой твоей дороге я не возьмусь.'),[back()])


def sparks():
    available=test('EOC_BERSERK_GODO_CAN_SPARKS')
    topic('SPARKS_INVITE',line(432,'In a hurry? Stay a little. Hand me those long tongs.'),[
        response(434,'All right. Let me help.','SPARKS',available,setv('sparks_started')),
        response(435,'Sorry, old man. Another time.','SPARKS_LATER'),back('HEARTH')])
    leaf('SPARKS_LATER',435,'As you wish. Go about your business.','HEARTH')['dynamic_line']=tr('As you wish. Go about your business.','Как знаешь. Занимайся своими делами.')
    question=tr('*Godot lifts the white-hot billet from the forge. Light crosses his worn face. The hammer falls; sparks scatter across the dark earthen floor. "What do you see before you?"','*Годо вынимает из горна раскалённую добела заготовку. Свет озаряет его изрезанное морщинами лицо. Молот опускается на металл; по тёмному земляному полу рассыпаются искры. «Что ты сейчас видишь перед собой?»')
    topic('SPARKS',choose(val('sparks_closed'),tr('*Godot returns to the iron. He does not resume the conversation.','*Годо возвращается к железу. Этот разговор он больше не начинает.'),question),[
        response(441,'Iron. Fire. Sparks.','SPARKS_LIGHT',available),response(442,'I see your work, Godot.','SPARKS_WORK',available),
        response(443,'Nothing special. Let us talk about something else.','SPARKS_DISMISSED',available,run('CLOSE_SPARKS')),back('HEARTH')])
    topic('SPARKS_LIGHT',line(447,'I watched those sparks when I was a child. Thought that beauty was worth swinging a hammer all day. Fool that I was.'),[response(448,'What changed?','SPARKS_FINGERS')])
    topic('SPARKS_FINGERS',line(449,'They let me hold the billet myself. Soon learned to watch my fingers and where I was striking, not the sparks.'),[response('А что остаётся после огня?','What is left after the fire?','SPARKS_IRON')])
    topic('SPARKS_WORK',line(451,'Then look closer. The finest-looking thing here disappears the quickest.'),[response('Искры гаснут. А железо остаётся.','The sparks go out. The iron remains.','SPARKS_IRON')])
    topic('SPARKS_IRON',line(454,'A bright spark, then nothing. But the iron remains. Each morning I can see what I did yesterday. Where I straightened it. Where I ruined the steel.'),[
        response(456,'People are more complicated than iron.','SPARKS_PEOPLE'),
        response(457,'Are you saying I only look at the sparks?','SPARKS_ME'),
        response(458,'Is what remains after the fire really enough for you?','SPARKS_ENOUGH')])
    for id,i,en in [('SPARKS_PEOPLE',460,'Of course. Iron is more honest. It does not try to tell me that a crack inside has done it good.'),('SPARKS_ME',461,'I have not accused you of anything. I asked what you could see in the dark.'),('SPARKS_ENOUGH',462,'Not every day. But I can return to the anvil next morning and go on with the work.')]:
        topic(id,line(i,en),[
            response('А что ты видишь во мне?','What do you see in me?','SPARKS_GUTS_BEFORE',both(G,BEFORE)),
            response('Ты говоришь о моей злости?','Are you talking about my anger?','SPARKS_GUTS_AFTER',both(G,AFTER)),
            response('А что, по-твоему, остаётся у меня?','What do you think remains for me?','SPARKS_HUMAN',both(neg(G),neg(KNOWS))),
            response('Я изменился. И всё же это касается меня?','I have changed. Does it still apply to me?','SPARKS_DEMON',both(neg(G),KNOWS))])
    topic('SPARKS_GUTS_BEFORE',line(465,'You have lived from one battle to the next a long time. You know where to stand, where to strike, and how to reach the next dawn.'),[response(466,'It is what I do best.','SPARKS_GUTS_PEACE')])
    topic('SPARKS_GUTS_PEACE',line(467,'I see that. But what will you do with a peaceful day? One day without a fight?'),[
        response(469,'I will find something worth living for.','SPARKS_GOAL'),response(470,'I do not know. I never thought about it.','SPARKS_DONT_KNOW'),response(471,'I will decide when that day comes.','SPARKS_LATER_DECIDE')])
    topic('SPARKS_GUTS_AFTER',line(479,'Your anger got you out of the grave. But even here by the fire you sit as though you must spring up and run.'),[response(480,'While I sit here warming myself, he is out there. Alive.','SPARKS_GUTS_ALIVE')])
    topic('SPARKS_GUTS_ALIVE',line(481,'Perhaps. And you? Are you alive?'),[
        response(483,'As long as I can hold a weapon and fight.','SPARKS_FIGHT'),response(484,'If I stop for a moment, it will all come back.','SPARKS_NIGHTMARE'),response(485,'You do not understand. You were not there.','SPARKS_NOT_THERE')])
    topic('SPARKS_HUMAN',choose(AFTER,line(494,'You ask whether your blade can survive the next creature. Suppose it can. What will you do when the fighting is over?'),
        tr('You ask whether your blade will last another fight. Suppose it does. What will you do with a day when you do not have to swing it?','Ты спрашиваешь, выдержит ли клинок ещё одну схватку. Допустим, выдержит. А что будешь делать в тот день, когда махать им не понадобится?')),[
        response(495,'I want a safe place where I can just live.','SPARKS_SAFE'),response(496,'There are people I need to return to.','SPARKS_RETURN'),response(497,'For now I just want to survive tomorrow.','SPARKS_TOMORROW')])
    topic('SPARKS_DEMON',tr('You chose to change your nature for strength. What will you hold on to with that changed body?','Ты добровольно изменил свою природу ради силы. И за что собираешься удержаться этим изменённым телом?'),[
        response(501,'My own life. I want to protect it.','SPARKS_SURVIVE'),response(502,'I can protect the people I care about with this strength.','SPARKS_PROTECT'),response(503,'Freedom. Nobody will dare command me now.','SPARKS_FREEDOM')])
    for id,i,en in [
        ('SPARKS_GOAL',474,'Search hard, boy. Do not expect a purpose to appear as if by magic when you kill your last enemy.'),
        ('SPARKS_DONT_KNOW',475,'There is no shame in not knowing. At least you can begin with that admission.'),
        ('SPARKS_LATER_DECIDE',476,'Mind that the habit of killing does not decide for you before you can open your mouth.'),
        ('SPARKS_FIGHT',488,'And when your wounded body cannot raise the blade? Will you deny yourself the right to live that day? A sword cannot replace a beating heart.'),
        ('SPARKS_NIGHTMARE',489,'Fear is a poor companion. If the nightmares return, there is someone here who can sit beside you until they quiet down. You are not alone in these woods.'),
        ('SPARKS_NOT_THERE',490,'No. I was not in your hell. But I can see what is happening here. I can see how carelessly you treat the little you managed to keep.'),
        ('SPARKS_SAFE',495,'A good aim. Keep it in mind. One day you must decide what to do with your hands besides striking.'),
        ('SPARKS_RETURN',496,'Then make the journey. Try to get back before they tire of waiting or die. The road takes more time than you think.'),
        ('SPARKS_TOMORROW',497,'Fair enough. Find a few minutes even in the worst day that you do not have to give wholly to fear.'),
        ('SPARKS_SURVIVE',501,'Everyone wants to live. Then do not hurry to throw away everything human you had before this choice.'),
        ('SPARKS_PROTECT',502,'Let them speak to you as equals. Even when they say things your new nature does not like. Do not become their monster.'),
        ('SPARKS_FREEDOM',503,'Pride. Then you must answer for each step yourself. That takes more strength than empty threats.')]:
        topic(id,line(i,en),[response('Я запомню.','I will remember.','SPARKS_END',effect=run('FINISH_SPARKS'))])
    topic('SPARKS_END',tr('*Godot turns back to the anvil. "Enough talk. The iron is cooling."','*Годо поворачивается к наковальне. «Ну, хватит лясы точить. Железо остывает». '),[
        response(508,'Let me work the bellows.','SPARKS_BELLOWS'),response(509,'Thank you for the conversation, Godot.','SPARKS_THANKS'),response(510,'I should go.','FAREWELL')])
    topic('SPARKS_BELLOWS',line(508,'Steadily. Not too hard yet; do not burn through the coal.'),[back(),response('Пойду я.','I should go.','FAREWELL')])
    topic('SPARKS_THANKS',line(509,'Mm.'),[back(),response('Пойду я.','I should go.','FAREWELL')])
    topic('SPARKS_DISMISSED',line(443,'All right. Give me back the tongs and do not get in the way.'),[back()])
    topic('SPARKS_RECALL',line(514,'And what have you decided?'),[response(515,'I am still thinking. It is not simple.','SPARKS_RECALL_THINK'),response(516,'I think I have something to return to.','SPARKS_RECALL_HOME'),back('HEARTH')])
    leaf('SPARKS_RECALL_THINK',515,'I am not hurrying you. These things take time.','HEARTH')
    leaf('SPARKS_RECALL_HOME',516,'Good. Then we did not sit here for nothing.','HEARTH')


def state_hooks():
    helper=[]
    witnessed=either(math('u_berserk_eclipse_rescue_state == 2'),
        both(math('u_berserk_apostol_return_state == 2'),math('u_berserk_apostol_outcome == 2')))
    helper += [eoc('EOC_BERSERK_GODO_WITNESSED_ECLIPSE',[],witnessed),
        eoc('EOC_BERSERK_GODO_PERSONAL_AVAILABLE',[],either(
            both(witnessed,H,val('trauma_done','!=',1)),
            both(G,witnessed,val('sword_state','>',0),val('revenge_told','!=',1)))),
        eoc('EOC_BERSERK_GODO_CAN_SPARKS',[],both(SMITH,'u_at_safe_space',
            val('sparks_closed','!=',1),val('sparks_completed','!=',1),
            either(val('hearth_trust'),val('early_delivered'),val('sword_delivered')))),
        eoc('EOC_BERSERK_GODO_FINISH_SPARKS',[
            setv('sparks_completed'),
            {'u_add_morale':'morale_berserk_godo_hearth','bonus':5,'max_bonus':5,
             'duration':'2 hours','decay_start':'1 hour','capped':True},
        ],both(SMITH,val('sparks_started'),val('sparks_completed','!=',1),val('sparks_closed','!=',1))),
        eoc('EOC_BERSERK_GODO_END_TRAUMA',[
            setv('trauma_done'),{'u_add_morale':'morale_berserk_godo_hearth','bonus':3,'max_bonus':5,
             'duration':'1 hour','decay_start':'30 minutes','capped':True}],both(SMITH,witnessed,H,val('trauma_done','!=',1))),
        eoc('EOC_BERSERK_GODO_HAS_COPY',[],either(
            {'u_has_item':'forged_guts_early_sword'},{'u_has_item':'forged_guts_sword'})),
        eoc('EOC_BERSERK_GODO_MADE_COPY',[],either(
            both(val('crafted_early_copy'),{'u_has_item':'forged_guts_early_sword'}),
            both(val('crafted_dragon_copy'),{'u_has_item':'forged_guts_sword'}))),
        eoc('EOC_BERSERK_GODO_RECORD_EARLY_COPY',[setv('crafted_early_copy')],'u_is_avatar'),
        eoc('EOC_BERSERK_GODO_RECORD_DRAGON_COPY',[setv('crafted_dragon_copy')],'u_is_avatar'),
        # NPC iteration uses Rickert as ALPHA. Only global scene snapshots are
        # written here; these never turn Godo's monster variables into NPC data.
        eoc('EOC_BERSERK_GODO_READ_RICKERT',[
            {'if':'u_following','then':math('berserk_godo_rickert_following = 1')},
            {'if':math('u_berserk_rickert_recruit_refused == 1'),'then':math('berserk_godo_rickert_refused = 1')},
        ],both('u_is_npc',{'u_has_class':'NC_BERSERK_RICKERT'})),
        eoc('EOC_BERSERK_GODO_DIALOGUE_SYNC',[
            {'if':test('EOC_BERSERK_APOSTOL_FORM_VISIBLE'),'then':run('EOC_BERSERK_APOSTOL_TELL_GODO')},
            math('berserk_godo_rickert_following = 0'),math('berserk_godo_rickert_refused = 0'),
            {'u_run_npc_eocs':['EOC_BERSERK_GODO_READ_RICKERT'],'unique_ids':[],
             'local':True,'npc_range':60},
        ],SMITH),
    ]
    # The refusal scars describe a human survivor; they are not accepted gifts.
    gate=read('effects/apostol_human_equipment_eocs.json'); gate_ids=index(gate)
    blocked=gate_ids['EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED']['condition']['not']['or']
    blocked[:]=[x for x in blocked if not x.get('u_has_trait','').startswith('BERSERK_ECLIPSE_SCAR_')]
    true_demon=copy.deepcopy(blocked[1:])  # omit the old latch itself
    migration=both('u_is_avatar',math('u_berserk_apostol_outcome == 2'),math('u_berserk_apostol_return_state == 2'),
                   math('u_berserk_apostol_human_equipment_locked == 1'),neg({'or':true_demon}))
    upsert(gate,eoc('EOC_BERSERK_GODO_REPAIR_REFUSAL_CLASSIFICATION',math('u_berserk_apostol_human_equipment_locked = 0'),migration,
                   eoc_type='RECURRING',recurrence='1 minute',**{'global':True}))
    write('effects/apostol_human_equipment_eocs.json',gate)
    continuation=read('effects/apostol_continuation_eocs.json');known=index(continuation)
    # Old saves can have accepted traits while numeric growth fields are absent.
    # Explicit disclosure still records knowledge and permits the promised refund.
    known['EOC_BERSERK_APOSTOL_TELL_GODO']['condition']=both(neg(H),SMITH)
    known['EOC_BERSERK_APOSTOL_GODO_KNOWS_GIFT']['condition']=both(neg(H),either(
        math('u_berserk_apostol_godo_told == 1'),test('EOC_BERSERK_APOSTOL_FORM_VISIBLE')))
    write('effects/apostol_continuation_eocs.json',continuation)
    write('effects/godo_dialogue_33_eocs.json',helper+list(LINE_CONDITIONS.values()))
    write('effects/godo_dialogue_morale.json',[{'type':'morale_type','id':'morale_berserk_godo_hearth',
        'text':tr('At Godot\'s hearth','У горна Годо')}])
    data=read('effects/godo_eocs.json'); ids=index(data)
    repair_refusal=run('EOC_BERSERK_GODO_REPAIR_REFUSAL_CLASSIFICATION')
    if repair_refusal not in ids['EOC_BERSERK_GODO_MEET_SMITH']['effect']:
        ids['EOC_BERSERK_GODO_MEET_SMITH']['effect'].insert(0,repair_refusal)
    for stem,prefix in [('early','EARLY'),('sword','SWORD')]:
        claim=ids['EOC_BERSERK_GODO_'+prefix+'_CLAIM']
        body=next(n['else'] for n in walk(claim['effect']) if isinstance(n.get('else'),list)
                  and any('u_spawn_item' in item for item in n['else']))
        marker=setv(stem+'_delivered')
        if marker not in body:body.insert(1,marker)
    # A successful conversation is needed to register the acquaintance. Merely
    # generating a forge/marking its coordinates continues to do nothing here.
    write('effects/godo_eocs.json',data)
    for name,id in [('forged_guts_early_sword_recipe','EARLY'),('forged_guts_sword_recipe','DRAGON')]:
        rows=read('recipes/'+name+'.json')
        record='EOC_BERSERK_GODO_RECORD_'+id+'_COPY'
        if record not in rows[0].setdefault('result_eocs',[]):rows[0]['result_eocs'].append(record)
        write('recipes/'+name+'.json',rows)
    scenes=read('effects/eclipse_field_scenes.json')
    for obj in scenes:
        for name in ['JUDEAU','PIPPIN','CORKUS','GASTON']:
            if obj['id']=='EOC_BERSERK_ECLIPSE_SCENE_'+name:
                body=obj['effect'] if isinstance(obj['effect'],list) else [obj['effect']]
                marker=setv('witness_'+name.lower())
                if marker not in body:body.append(marker)
                obj['effect']=body
    write('effects/eclipse_field_scenes.json',scenes)


def translations():
    for file,localized in [('ru.po',True),('Berserk.pot',False)]:
        p=MOD/'lang/po'/file
        blocks=[b for b in p.read_text().split('\n\n') if b.strip()]
        # Replace exact msgids rather than append duplicates or keep obsolete RU
        # for a reused English label. Unrelated catalog entries remain untouched.
        remaining=dict(STRINGS); output=[]
        for block in blocks:
            key=source(block)
            if key in remaining:
                ru=remaining.pop(key)
                block='#. Approved Godo dialogue 2026-10-21\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False)
            output.append(block.strip('\n'))
        for en,ru in remaining.items():
            output.append('#. Approved Godo dialogue 2026-10-21\nmsgid '+json.dumps(en,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False))
        p.write_text('\n\n'.join(output)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)


def main():
    original=read('dialogue/godo.json'); old=index(original)
    intros();main_menu();weapons();orders(old);hearth_and_rickert();personal();demon();sparks();state_hooks()
    # Retain public IDs used by older notes and Rickert. They lead to the new
    # topics and do not contain the former technical or contradictory text.
    aliases={'RECOGNIZE':'RECOGNIZE_HELLO','CRAFT':'WORK','APPRENTICE':'APPRENTICE_MENU','RICKERT':'APPRENTICE_MENU',
             'PRICE':'ORDERS','SPARKS_RAGE':'HEARTH','SPARKS_HOME':'HEARTH',
             'TALK_BERSERK_APOSTOL_GODO_HEARTH':'HEARTH'}
    for alias,target in aliases.items():
        topic(alias,tr('Ask what you came to ask.','Спрашивай, с чем пришёл.'),[back(target)])
    # Keep Rickert-owned prosthesis topics as-is. No rewrite of his script here.
    kept={'FITTING','SELF','ARM','PRAISE','ARM_STATUS',
          'MEMORY_KEEP','MEMORY_SURVIVED'}  # Rebuilt by the October 24 playtest pass.
    for obj in original:
        id=obj['id']
        if id.startswith('TALK_BERSERK_GODO') and id not in TOPICS and id.removeprefix('TALK_BERSERK_GODO_') not in kept:
            raise RuntimeError('Unmapped old Godo topic: '+id)
    write('dialogue/godo.json',[TOPICS.pop(x['id'],x) for x in original]+list(TOPICS.values()))
    translations()
    print('Approved Godo topics built; RU source preserved. Strings:',len(STRINGS))


if __name__=='__main__':main()
