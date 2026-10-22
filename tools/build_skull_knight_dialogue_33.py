#!/usr/bin/env python3
"""Owner's Skull Knight script, with explicit 22 October clarifications.

Preserves rescue scenes and saved IDs. No route locator is called by a new
conversation response. The journal is a record of answers, never their source.
"""
import hashlib
import json
import re
import subprocess

from recover_apostol_33 import ROOT, MOD, read, write, index, eoc, math, test, both
from recovery_33_translations import source

SOURCE=json.loads((ROOT/'docs/dialogue_sources/skull-knight-2026-10-22.json').read_text())['paragraphs']
STRINGS={};TOPICS={};HELPERS={};RECORDS=[]
PREFIX='TALK_BERSERK_SKULL_KNIGHT_'
G=test('EOC_BERSERK_FORGE_GUTS')
BRAND={'u_has_bionics':'bio_berserk_brand_of_sacrifice'}
NORMAL=both(math('u_berserk_eclipse_rescue_state == 2'),math('u_berserk_eclipse_route != 2'))


def neg(c):return {'not':c}
def either(*c):return {'or':list(c)}
def val(s,op='==',n=1):return math(f'u_berserk_knight_{s} {op} {n}')
def setv(s,n=1):return math(f'u_berserk_knight_{s} = {n}')
def tid(s):return s if s.startswith('TALK_') else PREFIX+s
def tr(en,ru):
    assert en and ru
    STRINGS[en]=ru
    return en
def line(i,en):return tr(en,SOURCE[i].strip())
def choose(c,yes,no):
    if isinstance(c,str) or any(k in c for k in ['and','or','not','compare_string']):
        key='EOC_BERSERK_KNIGHT_LINE_'+hashlib.sha1(json.dumps(c,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[key]=eoc(key,[],c);c=test(key)
    return {**c,'yes':yes,'no':no}
def response(ru,en,target='AFTER',condition=None,effect=None):
    obj={'text':tr(en,ru),'topic':tid(target)}
    if condition is not None:obj['condition']=condition
    if effect is not None:obj['effect']=effect
    return obj
def back(target='AFTER'):return response('Я хотел спросить о другом.','I wanted to ask about something else.',target)
def topic(s,text,responses=None,record=False):
    obj={'type':'talk_topic','id':tid(s),'dynamic_line':text,'responses':responses or [back()]}
    if record:
        obj['speaker_effect']={'effect':setv('read_'+s.lower())}
        RECORDS.append(s)
    TOPICS[obj['id']]=obj
    return obj
def leaf(s,i,en,parent='AFTER'):
    return topic(s,line(i,en),[back(parent)],True)


def intro():
    # Do not consume a greeting before dynamic_line has been rendered.
    met=either(val('greeted'),{'compare_string':['yes',{'u_val':'berserk_knight_spoken'}]})
    fresh=neg(met)
    first=choose(G,line(12,'You are on your feet, swordsman. After that night, that is no small thing.'),
        line(35,'You can stand again. Then the time I won for you that night was not wasted.'))
    hello=choose(NORMAL,choose(met,line(84,'Was there something else you wanted to ask?'),first),
        tr('I will hear your questions.','Я выслушаю твои вопросы.'))
    rs=[response('Это ты вытащил меня оттуда?','Was it you who carried me out?','RESCUED',both(fresh,NORMAL)),
        response('Я хочу понять, что произошло.','I want to understand what happened.','ECLIPSE',NORMAL),
        response('Расскажи о Клейме и тех, кто приходит ночью.','Tell me about the Brand and those who come at night.','BRAND',BRAND),
        response('Поможешь мне?','Will you help me?','HELP'),
        response('Где сейчас искать это зло?','Where should I look for this evil now?','NOW',NORMAL),
        response('Я нашёл кое-что среди останков.','I found something among the remains.','MEMORIES',test('EOC_BERSERK_KNIGHT_HAS_MEMORY')),
        response('Кто ты такой?','Who are you?','SELF'),
        response('Мне пора идти.','It is time for me to go.','FAREWELL'),
        response('Пока достаточно. Я ещё подойду.','That is enough for now. I will speak to you again.','TALK_DONE')]
    for r in rs:r['effect']=[setv('greeted'),{'u_add_var':'berserk_knight_spoken','value':'yes'}]
    topic('AFTER',hello,rs)['//']='Approved Skull Knight script 2026-10-22; ordinary close is not farewell.'
    rescued=choose(G,line(18,'I found an opening and carried you through before it closed. But carrying a body out of a place of sacrifice does not free it from the sacrifice itself.'),
        choose(math('u_berserk_godo_rescue_relocated == 1'),line(41,'Yes. You were among those who were not meant to leave that ceremony alive. I carried you out. The people where you woke did the rest.'),
            line(64,'I carried you somewhere I could leave you safely. We did not reach the woodland forge.')))
    topic('RESCUED',rescued,[
        response('Из-за этой метки?','Because of this mark?','BRAND',BRAND),
        response('Гриффит. Что с ним стало?','Griffith. What became of him?','GRIFFITH',G),
        response('Что со мной произошло?','What happened to me?','ECLIPSE'),
        response('Кто эти люди?','Who are these people?','MASTERS',math('u_berserk_godo_rescue_relocated == 1')),
        response('Почему ты мне помог?','Why did you help me?','PURPOSE'),
        response('О чём мне нужно знать прежде всего?','What do I need to know first?','NOW'),back()],True)
    topic('HELP',tr('Was saving your life not help enough?','Спасение твоей жизни — недостаточная помощь?'))
    # Forge directions and acquaintances are not invented by this scene.
    topic('MASTERS',choose(math('u_berserk_godo_personally_met == 1'),
        choose(math('u_berserk_rickert_met == 1'),tr('Godot and Rickert. You have already spoken with both of them. They sheltered you when I brought you here.','Годо и Рикерт. Ты уже говорил с ними обоими. Они дали тебе приют, когда я принёс тебя сюда.'),
            tr('You know Godot. The young craftsman at his forge is Rickert; you have yet to meet him yourself.','Годо ты знаешь. Молодого мастера при кузнице зовут Рикерт; с ним тебе ещё предстоит познакомиться.')),
        tr('Godot is a smith. Rickert works beside him on crossbows and mechanisms. You will have to meet them for yourself.','Годо — кузнец. Рикерт работает рядом с ним, занимается арбалетами и механизмами. Познакомиться с ними тебе ещё предстоит.')),[back()],True)


def eclipse():
    topic('ECLIPSE',line(116,'You saw the boundary where greatness is bought with other lives. Those who rose above the crowd accepted that harvest. Those feasting beneath the throne merely did what they had been permitted.'),[
        response('Эти твари когда-то были людьми?','Were those creatures once human?','APOSTLES'),
        response('А те, кто стоял над ними?','And those who stood above them?','GOD_HAND'),
        response('Почему это происходит среди наших городов?','Why is this happening among our cities?','WORLD_COLLISION'),
        response('Можно вернуть всё как было?','Can things be put back as they were?','RESTORE'),
        response('Что стало с Гриффитом?','What became of Griffith?','GRIFFITH',G),
        response('Тот, кто возглавил это, может повторить такое?','Can the one who presided over this do it again?','LEADER',neg(G)),back()],True)
    topic('APOSTLES',line(122,'Many were. They rejected their nature when an earthly existence was no longer enough. Their old failings and desires remained. Sometimes those human habits make the monsters recognizable. And vulnerable.'),[
        response('Их вообще можно уничтожить?','Can they be destroyed?','KILLABLE'),back('ECLIPSE')],True)
    topic('KILLABLE',line(131,'Their altered flesh can be destroyed. Do not mistake their bodies for true immortality. Nor should you look for human mercy where the abyss rules.'),[
        response('Как сражаться с ними обычным оружием?','How do I fight them with ordinary weapons?','FIGHT'),back('ECLIPSE')],True)
    leaf('FIGHT',137,'Wait before you step forward. Study how the enemy moves, what it protects and when it must pause for breath. Know where you will retreat. Blind fury is no substitute for a way back.','ECLIPSE')
    topic('GOD_HAND',line(146,'The God Hand. Do not confuse them with the servants admitted to the feast. Killing an ordinary apostle does not bring their overthrow a step closer.'),[
        response('Значит, сопротивление бессмысленно?','Then resistance is pointless?','RESIST'),
        response('Я уже одолел его отражение. Как он оказался там снова?','I defeated his reflection. How could he be there again?','PROJECTIONS',math('u_berserk_griffith_projection_defeated == 1')),back('ECLIPSE')],True)
    leaf('RESIST',152,'If I thought your struggle useless, I would not have carried you out of that hell.','ECLIPSE')
    leaf('WORLD_COLLISION',161,'This land had already been wounded by its own end of the world. Another darkness seeps through the open wounds. The boundary has thinned, making your home accessible to hungrier predators.','ECLIPSE')
    leaf('RESTORE',170,'The past cannot be restored, even if every passage is sealed. But you can keep the next traveler from meeting the same fate.','ECLIPSE')
    topic('GRIFFITH',line(184,'He took the throne offered to him. Your memories of the man cannot explain the abyss into which he was reborn.'),[
        response('Мне плевать, кем он стал. Я всё равно доберусь до его глотки.','I do not care what he became. I will reach his throat.','VENGEANCE'),back('ECLIPSE')],True)
    leaf('VENGEANCE',190,'Then first learn to live until the next dawn. Otherwise your oath of vengeance will be no more than the last words of a man dying in the night.','ECLIPSE')
    leaf('LEADER',204,'Do not expect what you witnessed to be the last expression of that will. Your concern now is to endure the threat already following you.','ECLIPSE')
    topic('PROJECTIONS',line(396,'You dispersed a reflection. It could take his shape and carry some of his power, but it was not the being you seek.'),[
        response('Значит, тот поединок ничего не значил?','Then that fight meant nothing?','PROJECTION_MEANING'),
        response('Как отличить отражение от настоящего?','How can I distinguish a reflection from the original?','PROJECTION_PROOF'),
        response('Такие отражения ещё встретятся?','Will there be more reflections?','PROJECTION_MORE'),back('ECLIPSE')],True)
    leaf('PROJECTION_MEANING',403,'The shape that stood before you will threaten no one else. That matters. But do not credit your victory with something it did not accomplish.','PROJECTIONS')
    leaf('PROJECTION_PROOF',410,'A face is not enough. Consider where it came from, what holds it here and what it leaves behind. A vanished shadow is not proof of an original death.','PROJECTIONS')
    leaf('PROJECTION_MORE',417,'While the boundaries between worlds remain broken, I would not call that encounter the last.','PROJECTIONS')


def brand():
    topic('BRAND',line(239,'The Brand remains a mark of sacrifice. Beings beyond the boundary can discern it where a human eye sees nothing. Night makes their journey to you easier.'),[
        response('Оно предупреждает об опасности?','Does it warn me of danger?','BRAND_PAIN'),
        response('Они будут приходить каждую ночь?','Will they come every night?','NIGHTS'),
        response('Что делать до темноты?','What should I do before dark?','PREPARE'),
        response('Как защитить пристанище?','How can I protect my refuge?','WARD'),
        response('Если я закрою разлом, Клеймо исчезнет?','Will closing a breach remove the Brand?','LOCAL_WOUNDS'),back()],True)
    leaf('BRAND_PAIN',245,'Pain and blood may come before a creature appears, especially a powerful one. Heed that warning, but do not expect it to name your enemy or show a safe road. The Brand is no friend to you. It simply is.','BRAND')
    leaf('NIGHTS',251,'Not every night is the same. Sometimes you will hear only footsteps beyond a wall. Sometimes you will have to abandon your shelter and run. Silence does not mean they have forgotten you.','BRAND')
    topic('PREPARE',line(261,'Find a place you can leave. Do not corner yourself for the imagined safety of walls. Prepare light, dressings and weapons. Keep what you need close: there will be no time to pack when you must flee.'),[
        response('Запертая дверь поможет?','Will a locked door help?','DOORS'),
        response('А утром они исчезнут?','Will they disappear in the morning?','DAWN'),back('BRAND')],True)
    leaf('DOORS',268,'Against some of them, yes. But an ordinary wall cannot keep out everything that comes from the darkness. Some creatures need no door.','BRAND')
    leaf('DAWN',275,'Dawn may end the pursuit itself. It does not promise to destroy those that already reached you. Look at what remains outside before opening the door.','BRAND')
    ward_new=tr('There are signs that hinder their approach. I will leave you the instructions. But a sign cannot replace shelter: choose somewhere you can defend and leave.','Есть знаки, затрудняющие их приближение. Я оставлю тебе сведения, по которым можно подготовить такую защиту. Но знак не заменит укрытия: выбери место, которое можно защитить и покинуть.')
    topic('WARD',choose(math('u_berserk_refuge_ready == 1'),line(300,'You have already begun preparing. Wise. But do not mistake that sign for a fortress wall. It will not destroy a creature already beside you; it hinders the way here.'),ward_new),[
        response('Тогда я смогу спать спокойно?','Then I can sleep peacefully?','WARD_LIMITS'),
        response('Расскажи, как его сложить.','Tell me how to arrange it.','WARD_BUILD'),back('BRAND')],True)
    leaf('WARD_LIMITS',290,'More peacefully. Not carelessly. Even a protected place must have an exit. Never make the sign your last hope.','BRAND')
    topic('WARD_BUILD',tr('Arrange eight stones and four bones into a sign on clear ground. Keep it close to your sleeping place. Its protection stays on the same level; it will not drive away creatures already here.','Сложи знак из восьми камней и четырёх костей на свободном месте. Держи его рядом с местом для сна. Защита не переходит с этажа на этаж и не прогоняет тех, кто уже пришёл.'),[back('BRAND')],True)
    leaf('LOCAL_WOUNDS',313,'No. You will close one road into this world, and that matters to those who live nearby. The mark on your body belongs to another bond. Closing a breach does not break it.','BRAND')


def now():
    # Advice never opens the physical journal or calls a locator. The mission
    # and its exact marker are awarded by the existing rescue/progress events.
    hint=choose(math('u_berserk_first_hunt_done != 1'),
        tr('The trail leads to the forest hollow. The direction is already in your records. Prepare before following it; I will not choose your next step for you.','След ведёт к лесной низине. Направление уже есть в твоих записях. Подготовься, прежде чем идти по нему; следующий шаг я за тебя не выберу.'),
        choose(math('u_berserk_journal_read_berserk_apostle_burned_clue != 1'),line(355,'Victory left you more than a dead enemy. Examine what remains in its lair. You may find why it came to these lands.'),
            choose(both(math('u_berserk_journal_knows_breach == 1'),math('u_berserk_breach_sealed != 1')),line(362,'You have found the trail of a passage. Now deal with the wound itself. A fallen keeper does not always mean the road behind it has closed.'),
                choose(test('EOC_BERSERK_KNIGHT_UNFINISHED_KNOWN'),tr('The roads you learned are already marked. Follow an unfinished trail when you are ready. You need not take on every enemy at once.','Дороги, о которых ты узнал, уже отмечены. Когда будешь готов, продолжи незавершённый след. Не нужно браться за всех врагов разом.'),line(378,'You have exhausted the trails you had. Revisit the evidence and speak with those you trust. The next road remains to be discovered; I will not point you toward something I do not know.')))))
    topic('NOW',choose(test('EOC_BERSERK_KNIGHT_HURT'),line(326,'First let your wounds close. Speak with the craftsmen, gather what you need and prepare for night. The road will not disappear while you learn to walk it without falling at the first step.'),hint),[back()],True)


def memories():
    rs=[]
    data=[('JUDEAU','judeau',424,425,426,'Judeau saw other people even when everything around him was turning them into prey.'),
          ('PIPPIN','pippin',432,433,434,'Sometimes a man knows he cannot hold the enemy. Still he stands between it and those who can escape.'),
          ('CORKUS','corkus',440,441,442,'A victim has a life that cannot fit inside the word victim. Desires, failings, arguments. Do not give the monsters that part of him as well.'),
          ('GASTON','gaston',448,449,450,'Such hopes are easily lost behind banners and the names of commanders. To him that future mattered no less than another man\'s dream of a kingdom.')]
    for name,stem,gi,oi,answer,en in data:
        proof=math('u_berserk_godo_witness_'+stem+' == 1')
        # Source contains embedded speaker labels and arrows: author metadata
        # must not become a spoken player line.
        def quoted(i):return re.search('«([^»]+)»',SOURCE[i]).group(1)
        gr=quoted(gi);ordinary=quoted(oi).replace('В найденной записи упоминался','Среди найденных следов упоминался')
        rs.extend([response(gr,'I found '+stem+'\'s traces. I remember him.','MEMORY_'+name,both(proof,G)),response(ordinary,'I found evidence about '+stem+'.','MEMORY_'+name,both(proof,neg(G)))])
        # Strip the source's in-paragraph speaker label, retaining exact prose.
        ru=SOURCE[answer].split(':',1)[-1].strip() if SOURCE[answer].startswith('Рыцарь-Череп:') else SOURCE[answer]
        topic('MEMORY_'+name,tr(en,ru),[response('Я хотел спросить о другом погибшем.','I wanted to ask about someone else who died.','MEMORIES')],True)
    topic('MEMORIES',tr('Tell me what you found.','Расскажи, что ты нашёл.'),rs+[back()])
    extra=[('JUDEAU',428,'Этого оказалось недостаточно.','It was not enough.', 'Not enough to stop all that happened. But you do not know how much time his act gave someone else.'),
        ('JUDEAU',429,'Я хочу, чтобы о нём помнили.','I want him remembered.','Then preserve more than how he died. Preserve who he was.'),
        ('PIPPIN',436,'Ты называешь это победой?','You call that victory?','I call it an act that cannot be measured only by who remained standing.'),
        ('PIPPIN',437,'Я должен был быть рядом.','I should have been beside him.','You may carry that thought all your life. It cannot put you beside him that night. Decide whom you will stand beside now.'),
        ('CORKUS',444,'Мы часто не ладили.','We often disagreed.','Grief does not require that you agreed on everything in life.'),
        ('CORKUS',445,'Он не был героем.','He was no hero.','They did not need to become heroes to deserve their lives.'),
        ('GASTON',452,'От этого только тяжелее.','That makes it harder.','Yes. You see not only a death but everything that can never follow it.'),
        ('GASTON',453,'Что мне делать с найденной вещью?','What should I do with the keepsake?','Keep it, give it to someone who knew him, or leave it in a worthy place. Memory does not demand you always carry its weight.')]
    for name,i,ru,en,answer in extra:
        s='MEMORY_'+name+'_'+str(i)
        answer_ru=SOURCE[i].split('Рыцарь-Череп:',1)[1].strip()
        cond=G if i in [437,444] else {'u_has_item':'berserk_gaston_sewing_roll'} if i==453 else None
        TOPICS[tid('MEMORY_'+name)]['responses'].insert(0,response(ru,en,s,cond))
        topic(s,tr(answer,answer_ru),[back('MEMORY_'+name)],True)


def personal():
    topic('SELF',line(465,'One who has long walked against them.'),[
        response('Это не имя.','That is no name.','NAME'),
        response('Почему ты спас меня?','Why did you save me?','PURPOSE',NORMAL),
        response('Почему ты не спас остальных?','Why did you not save the others?','OTHERS',NORMAL),
        response('Ты тоже когда-то был человеком?','Were you once human too?','HUMAN'),
        response('Можно изменить судьбу?','Can fate be changed?','FATE'),
        response('Почему ты не останешься?','Why will you not stay?','LEAVING'),back()],True)
    leaf('NAME',471,'No. But for now it tells you more than a name.','SELF')
    topic('PURPOSE',line(478,'I had the chance to intervene. I took it.'),[response('И ничего не потребуешь взамен?','And you want nothing in return?','DEBT'),back('SELF')],True)
    leaf('DEBT',484,'I did not carry you out of one bargain to immediately bind you to another.','SELF')
    topic('OTHERS',line(491,'Because I could not.'),[
        response('Но ты знал, что там происходит.','But you knew what was happening.','KNEW'),
        response('Я не могу с этим смириться.','I cannot accept that.','ACCEPT'),back('SELF')],True)
    leaf('KNEW',505,'Knowing of a disaster and having the power to stop it are not the same.','SELF')
    leaf('ACCEPT',512,'I am not asking you to accept it. But do not base your next step on the belief that someone could have fixed everything with a single blow.','SELF')
    topic('HUMAN',line(519,'Enough humanity remains in me to remember what I fight against.'),[response('А всё остальное?','And the rest?','PAST'),back('SELF')],True)
    leaf('PAST',525,'Not every story needs to be told at another man\'s threshold.','SELF')
    topic('FATE',line(532,'You are alive and asking that question. Begin there.'),[response('Значит, всё зависит от моего выбора?','Then everything depends on my choice?','CHOICE'),back('SELF')],True)
    leaf('CHOICE',538,'No. But your choice still belongs to you. Do not give it away merely because you cannot rule everything else.','SELF')
    topic('LEAVING',line(545,'I have my own road. Our enemies will not wait for you to recover.'),[response('Мы ещё встретимся?','Will we meet again?','MEET_AGAIN'),back('SELF')],True)
    leaf('MEET_AGAIN',551,'Perhaps. But do not build your life around waiting for me.','SELF')


def farewell():
    warned=val('farewell_warned')
    t=topic('FAREWELL',choose(warned,line(631,'Have you finished?'),line(617,'Then know this: I will continue my journey. If you still have questions, ask them now. Do not expect me to return to this threshold.')),[
        response('Подожди. Я хочу спросить ещё.','Wait. I have more questions.','AFTER'),
        response('Напомни самое необходимое.','Remind me of the essentials.','SUMMARY'),
        response('Я понял. Прощай.','I understand. Farewell.','FINAL',effect={'run_eocs':'EOC_BERSERK_KNIGHT_FAREWELL'})])
    for r in t['responses']:r['effect']=[setv('farewell_warned')]+([r['effect']] if 'effect' in r else [])
    topic('SUMMARY',choose(BRAND,line(645,'Prepare for night. Ask the craftsmen for what you lack. Then follow a trail you know. Do not try to settle your whole war in a single battle.'),
        tr('Recover before another fight. Prepare what you need, and follow a trail you already know.','Восстановись перед следующим боем. Собери необходимое и продолжи тот след, который тебе уже известен.')),[
            response('У меня ещё есть вопросы.','I still have questions.','AFTER'),
            response('Прощай.','Farewell.','FINAL',effect={'run_eocs':'EOC_BERSERK_KNIGHT_FAREWELL'})])
    topic('FINAL',choose(G,line(661,'Then preserve the life with which you intend to continue.'),line(673,'Live on. What kind of life it will be is yours to decide.')),[response('Проводить всадника взглядом.','Watch the rider leave.','TALK_DONE')])


def helpers():
    actual=both('has_beta','npc_is_monster',math("n_monsters_nearby('mon_skull_knight_rescuer', 'radius': 0, 'attitude': 'both') > 0"))
    HELPERS['EOC_BERSERK_KNIGHT_HAS_MEMORY']=eoc('EOC_BERSERK_KNIGHT_HAS_MEMORY',[],either(*[math('u_berserk_godo_witness_'+s+' == 1') for s in ['judeau','pippin','corkus','gaston']]))
    HELPERS['EOC_BERSERK_KNIGHT_HURT']=eoc('EOC_BERSERK_KNIGHT_HURT',[],either(*[math(f"u_hp('{bp}') < u_hp_max('{bp}') / 2") for bp in ['head','torso','arm_l','arm_r','leg_l','leg_r']]))
    HELPERS['EOC_BERSERK_KNIGHT_UNFINISHED_KNOWN']=eoc('EOC_BERSERK_KNIGHT_UNFINISHED_KNOWN',[],either(*[both(math('u_berserk_journal_knows_'+s+' == 1'),neg(test('EOC_BERSERK_JOURNAL_DONE_'+s.upper()))) for s in ['count','wyald','rosine','grunbeld']]))
    # The farewell handler remains callable only by the real rescue actor.
    aftermath=read('effects/eclipse_aftermath_eocs.json');by=index(aftermath)
    by['EOC_BERSERK_KNIGHT_FAREWELL']['condition']=both(actual,NORMAL,val('farewell_confirmed','!=',1))
    write('effects/eclipse_aftermath_eocs.json',aftermath)
    write('effects/skull_knight_dialogue_33_eocs.json',list(HELPERS.values()))


def archive():
    # One readable record rather than another tree of questions. Only answers
    # actually heard are appended; no later knowledge or route is unlocked.
    parts=[tr('Words recorded after speaking with the Skull Knight.','Слова, записанные после разговора с Рыцарем-Черепом.')]
    summaries={
        'RESCUED':tr('The Knight carried me out of the sacrifice. Escape did not undo its consequences.','Рыцарь вынес меня из места жертвоприношения. Спасение не отменило его последствий.'),
        'MASTERS':tr('Godot works on blades; Rickert works on crossbows and mechanisms at the woodland forge.','В лесной кузнице Годо занимается клинками, Рикерт — арбалетами и механизмами.'),
        'WARD':tr('A bone and stone sign hinders the Brand\'s night summons nearby. It does not remove creatures already here and does not replace shelter.','Знак из костей и камней сдерживает ночной зов Клейма поблизости. Он не убирает уже пришедших существ и не заменяет укрытия.'),
        'NOW':tr('Recover before a fight. Prepare for night, then follow a trail you know. Do not take on every enemy at once.','Перед боем нужно восстановиться. Подготовиться к ночи, затем продолжить известный след. Не браться за всех врагов разом.')}
    for s in RECORDS:
        text=summaries.get(s,TOPICS[tid(s)]['dynamic_line'])
        parts += [choose(val('read_'+s.lower()),{'concatenate':['\n\n',text]},'')]
    data=read('dialogue/road_journal.json');by=index(data)
    # Preserve previously heard advice in old saves; never turn one new answer
    # into permission to read the entire old encyclopedia.
    for obj in data:
        prefix='TALK_BERSERK_JOURNAL_KNIGHT_'
        suffix=obj['id'].removeprefix(prefix)
        if obj['id'].startswith(prefix) and suffix!='ADVICE':
            parts.append(choose(val('advice_'+suffix.lower()),{'concatenate':['\n\n',obj['dynamic_line']]},''))
    by['TALK_BERSERK_JOURNAL_KNIGHT_ADVICE']['dynamic_line']={'concatenate':parts}
    by['TALK_BERSERK_JOURNAL_KNIGHT_ADVICE']['responses']=[{'text':tr('Close the record.','Закрыть запись.'),'topic':'TALK_BERSERK_JOURNAL_RECORDS'}]
    write('dialogue/road_journal.json',data)
    def old_condition(c):
        if not isinstance(c,dict):return c
        if 'math' in c and 'u_berserk_knight_read_' in c['math'][0]:return None
        for op in ['or','and']:
            if op in c:
                children=[x for x in map(old_condition,c[op]) if x]
                return {op:children} if len(children)>1 else children[0] if children else None
        return c
    for obj in data:
        for r in obj['responses']:
            if r['topic']=='TALK_BERSERK_JOURNAL_KNIGHT_ADVICE':
                previous=old_condition(r.get('condition'))
                if obj['id']=='TALK_BERSERK_JOURNAL_RECORDS':
                    learned=either(*[val('read_'+s.lower()) for s in RECORDS])
                    r['condition']=either(previous,learned) if previous else learned
                elif previous:r['condition']=previous
                else:r.pop('condition',None)
    write('dialogue/road_journal.json',data)


def translations():
    # Drop the unused source paragraph introduced while constructing HELP.
    STRINGS.pop('Not used',None)
    for filename,localized in [('ru.po',True),('Berserk.pot',False)]:
        p=MOD/'lang/po'/filename;remaining=dict(STRINGS);out=[]
        for block in [b for b in p.read_text().split('\n\n') if b.strip()]:
            key=source(block)
            if key in remaining:
                ru=remaining.pop(key);block='#. Skull Knight 2026-10-22\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False)
            out.append(block.strip('\n'))
        for en,ru in remaining.items():out.append('#. Skull Knight 2026-10-22\nmsgid '+json.dumps(en,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False))
        p.write_text('\n\n'.join(out)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)


def main():
    old=read('dialogue/skull_knight.json')
    intro();eclipse();brand();now();memories();personal();farewell();archive();helpers()
    # Keep the in-Eclipse rescue/victory conversation. Retired public topics
    # are safe aliases for saved references, with no new incoming questions.
    for obj in old:
        if obj['id'] not in TOPICS:
            if obj['id'] in [tid('RESCUE'),tid('RESCUE_REPLY'),tid('VICTORY')]:
                # During the escape there is no time for the later interview.
                # This also prevents an old keepsake button reaching AFTER
                # before the real return and its rescued-person state exist.
                obj['responses']=[r for r in obj['responses'] if r['topic'] not in [tid(s) for s in ['JUDEAU','PIPPIN','CORKUS','GASTON']]]
                TOPICS[obj['id']]=obj
            else:topic(obj['id'],tr('What else did you want to ask?','О чём ещё ты хотел спросить?'),[back()])
    write('dialogue/skull_knight.json',list(TOPICS.values()))
    translations()
    print('Skull Knight: approved dialogue, explicit farewell, direct advice; strings:',len(STRINGS))


if __name__=='__main__':main()
