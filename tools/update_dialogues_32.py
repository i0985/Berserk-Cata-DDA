#!/usr/bin/env python3
"""Apply 3.2 dialogue/journal edits while retaining old topic and effect IDs."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'mods/Berserk'
RU=json.loads((ROOT/'tools/godo_32_ru.json').read_text())
def t(en,ru):RU[en]=ru;return en
def read(path):return json.loads((MOD/path).read_text())
def write(path,rows):
 if path.startswith('dialogue/'):
  for row in rows:
   seen=set();unique=[]
   for r in row.get('responses',[]):
    key=json.dumps(r,sort_keys=True)
    if key not in seen:unique.append(r);seen.add(key)
   row['responses']=unique
 (MOD/path).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
def m(s):return {'math':[s]}
def run(s):return {'run_eocs':s}
def response(en,ru,id,condition=None,effect=None):
 r={'text':t(en,ru),'topic':id}
 if condition is not None:r['condition']=condition
 if effect is not None:r['effect']=effect
 return r
def topic(id,line,responses):return {'type':'talk_topic','id':id,'dynamic_line':line,'responses':responses}
def cond(c,yes,no):return {**c,'yes':yes,'no':no}
def back(id):return response('Ask something else.','Спросить о другом.',id)

knight=read('dialogue/skull_knight.json');K={r['id']:r for r in knight}
root=K['TALK_BERSERK_SKULL_KNIGHT_AFTER']
mem=next(r for r in root['responses'] if r['topic']=='TALK_BERSERK_SKULL_KNIGHT_MEMORIES')
root['responses']=[
 response('What should I do right now?','Что мне делать сейчас?','TALK_BERSERK_SKULL_KNIGHT_NOW'),
 response('Tell me what happened.','Расскажи о произошедшем.','TALK_BERSERK_SKULL_KNIGHT_ECLIPSE'),
 response('Tell me about the Brand and this world.','Расскажи о Клейме и этом мире.','TALK_BERSERK_SKULL_KNIGHT_WORLD'),
 response('I need practical help.','Мне нужна практическая помощь.','TALK_BERSERK_SKULL_KNIGHT_PRACTICAL'),
 response('Help me choose a known road.','Помоги выбрать известный путь.','TALK_BERSERK_SKULL_KNIGHT_NEXT'),mem,
 response('I need to go. Wait here.','Мне пора. Подожди здесь.','TALK_DONE')]
knight.extend([
 topic('TALK_BERSERK_SKULL_KNIGHT_WORLD',t('Ask about the wound you carry, or about the beings that cross it. One answer will not explain every creature in this changed world.','Спроси о ране, которую носишь, или о существах, проходящих сквозь неё. Один ответ не объяснит всё, что населяет этот изменившийся мир.'),[
  response('Why does the Brand call to them?','Почему Клеймо их зовёт?','TALK_BERSERK_SKULL_KNIGHT_BRAND'),
  response('Who are the apostles and the God Hand?','Кто такие апостолы и Рука Бога?','TALK_BERSERK_SKULL_KNIGHT_APOSTLES'),
  response('What changed when the worlds collided?','Что изменилось при столкновении миров?','TALK_BERSERK_SKULL_KNIGHT_WORLD_COLLISION'),back(root['id'])]),
 topic('TALK_BERSERK_SKULL_KNIGHT_PRACTICAL',t('First protect the life that escaped. We can speak of shelter, your injuries, or a craftsman who can help replace what was lost.','Сначала сбереги жизнь, которую удалось вынести оттуда. Поговорим об укрытии, твоих ранах или мастере, который поможет заменить потерянное.'),[
  response('How do I prepare a refuge?','Как подготовить пристанище?','TALK_BERSERK_SKULL_KNIGHT_WARD'),
  response('What did the Eclipse do to my body?','Что Затмение сделало с моим телом?','TALK_BERSERK_SKULL_KNIGHT_INJURIES'),
  response('Who can make a prosthetic and a weapon?','Кто сделает протез и оружие?','TALK_BERSERK_SKULL_KNIGHT_GODO'),back(root['id'])]),
 topic('TALK_BERSERK_SKULL_KNIGHT_GODO',t('There is a great master who can help with your hand and a new blade. Godot keeps a forge deep in the woods, with Rickert beside him. The road may be long. Bring useful metal rather than promises. If you already carry his work, ask him to mend it. These directions will remain in your notes after we part.','Есть великий мастер, который может помочь тебе с рукой и новым мечом. Годо держит кузницу в глубине лесов; рядом с ним работает Рикерт. Дорога может оказаться долгой. Приноси пригодный металл, а не обещания. Если его работа уже у тебя, попроси привести её в порядок. Указания останутся в записях и после нашего расставания.'),[
  response('Mark the road to the forge.','Отметь дорогу к кузнице.','TALK_BERSERK_SKULL_KNIGHT_GODO',effect=run('EOC_BERSERK_GODO_SEEK')),
  response('Can I still make the cannon myself?','Могу я по-прежнему изготовить пушку сам?','TALK_BERSERK_SKULL_KNIGHT_HAND'),back(root['id'])])
])
K['TALK_BERSERK_SKULL_KNIGHT_HAND']['dynamic_line']=t('A skilled metalworker can make the cannon: fabrication 8, mechanics 4 and the proper tools. Rickert builds that mechanism at Godot\'s forge if you bring the materials. Either way, fit the finished cannon by activating it in your inventory.','Опытный мастер может изготовить пушку: нужны производство 8, механика 4 и подходящие инструменты. Рикерт соберёт механизм в кузнице Годо, если принести материалы. В обоих случаях готовая пушка устанавливается активацией из инвентаря.')
K['TALK_BERSERK_SKULL_KNIGHT_HAND']['responses']=[r for r in K['TALK_BERSERK_SKULL_KNIGHT_HAND']['responses'] if r['topic']!='TALK_BERSERK_SKULL_KNIGHT_GODO']
K['TALK_BERSERK_SKULL_KNIGHT_HAND']['responses'].insert(0,response('Show me the craftsman.','Укажи дорогу к мастеру.','TALK_BERSERK_SKULL_KNIGHT_GODO'))
for id in ['JUDEAU','PIPPIN','CORKUS','GASTON']:
 K['TALK_BERSERK_SKULL_KNIGHT_'+id]['responses']=[
  response('There is another memory I want to ask about.','Хочу спросить ещё об одном свидетельстве.','TALK_BERSERK_SKULL_KNIGHT_MEMORIES'),back(root['id'])]
now=cond(m('u_berserk_first_hunt_done != 1'),
 t('Find shelter and tend your wounds before following the marked hollow. If replacing your hand is the greater need, seek Godot first; the hunt can wait.','Найди укрытие и позаботься о ранах, прежде чем идти в отмеченную низину. Если важнее заменить кисть, сначала найди Годо; охота подождёт.'),
 cond(m('u_berserk_breach_sealed != 1'),
 t('Follow the recovered trail to the ashen wound. Examine what remains after its keeper falls. You can also prepare your equipment at the forge before going.','Следуй по найденному следу к пепельной ране. Когда падёт её хранитель, осмотри то, что останется. Перед дорогой можно подготовить снаряжение в кузнице.'),
 cond({'not':{'test_eoc':'EOC_BERSERK_EARLY_HUNTS_CLOSED'}},
 t('Choose one unfinished trail from the records you recovered. Study its signs before entering; a quieter wound here will not silence another far away.','Выбери один незавершённый путь из найденных записей. Изучи следы перед входом: затихшая рана здесь не заставит замолчать другую вдали.'),
 cond(m('u_berserk_flora_met != 1'),
 t('The recovered records now lead to Flora. Seek her counsel at the spiritual tree and learn what help she can offer.','Найденные записи теперь ведут к Флоре. Найди её у духовного дерева и узнай, какую помощь она может предложить.'),
 cond(m('berserk_flora_stage <= 1'),
 t('Rest in the grove while you can. Understand the armor and prepare your supplies before choosing to continue.','Отдохни в роще, пока есть возможность. Разберись в свойствах доспеха и подготовь припасы, прежде чем решать, что идти дальше.'),
 cond(m('berserk_flora_stage == 2'),
 t('Leave the threatened grove by the western path or the southern garden. Keep moving until you are clear of the trees.','Уходи из рощи западной тропой или через южный сад. Не останавливайся, пока не минуешь деревья.'),
 t('Recover, then follow one known trail that remains unfinished. Your notes keep both the roads and the wounds already quieted.','Восстановись, затем выбери один известный незавершённый путь. В записях сохраняются и дороги, и раны, которым уже дали затихнуть.')))))))
# Native dynamic lines accept one condition, not logical wrappers.
closed_branch=now['no']['no']
closed_branch['test_eoc']='EOC_BERSERK_EARLY_HUNTS_CLOSED'
closed_branch.pop('not')
closed_branch['yes'],closed_branch['no']=closed_branch['no'],closed_branch['yes']
K['TALK_BERSERK_SKULL_KNIGHT_NOW']['dynamic_line']=now
K['TALK_BERSERK_SKULL_KNIGHT_NOW']['responses']=[r for r in K['TALK_BERSERK_SKULL_KNIGHT_NOW']['responses'] if r['topic']!='TALK_BERSERK_SKULL_KNIGHT_GODO']
K['TALK_BERSERK_SKULL_KNIGHT_NOW']['responses'].insert(1,response('Tell me about the forge.','Расскажи о кузнице.','TALK_BERSERK_SKULL_KNIGHT_GODO'))
K['TALK_BERSERK_SKULL_KNIGHT_NEXT']['responses']=[r for r in K['TALK_BERSERK_SKULL_KNIGHT_NEXT']['responses'] if r['topic']!='TALK_BERSERK_SKULL_KNIGHT_GODO']
K['TALK_BERSERK_SKULL_KNIGHT_NEXT']['responses'].insert(-1,response('Show me the road to Godot.','Покажи дорогу к Годо.','TALK_BERSERK_SKULL_KNIGHT_GODO'))
named=K['TALK_BERSERK_SKULL_KNIGHT_NAMED_HUNTS']
named['responses']=[r for r in named['responses'] if r['text']!="Mark the Count's residence."]
named['responses'].insert(0,response("Mark the Count's residence.",'Отметь резиденцию Графа.',named['id'],effect=run('EOC_BERSERK_COUNT_SEEK')))
for r in named['responses']:
 if r.get('topic')=='TALK_DONE':r['topic']=named['id']
K['TALK_BERSERK_SKULL_KNIGHT_FIRST_HUNT']['dynamic_line']['no']=t('A lesser apostle holds the marked forest hollow. Prepare armor, dressings and a way to retreat before entering the low ground. The directions in your notes lead to the same place.','Малый апостол занял отмеченную лесную низину. Перед спуском приготовь броню, перевязку и путь отхода. Указания в записях ведут к тому же месту.')
# Re-running this tool replaces new topics instead of duplicating their IDs.
unique={r['id']:r for r in knight};write('dialogue/skull_knight.json',list(unique.values()))

flora=read('dialogue/flora.json');F={r['id']:r for r in flora}
peace=m('berserk_flora_stage <= 1')
root=F['TALK_BERSERK_FLORA']
root['responses']=[
 response('What should I do now?','Что мне делать сейчас?','TALK_BERSERK_FLORA_NEXT',peace),
 response('Tell me about the Brand and the crossing.','Расскажи о Клейме и столкновении миров.','TALK_BERSERK_FLORA_WORLD',peace),
 response('Tell me about the armor and its price.','Расскажи о доспехе и его цене.','TALK_BERSERK_FLORA_ARMOR',peace),
 response('May I rest here and ask for help?','Можно здесь отдохнуть и попросить помощи?','TALK_BERSERK_FLORA_HOME',peace),
 response('I have questions about the things I found.','Хочу спросить о найденных вещах.','TALK_BERSERK_FLORA_RELICS',peace),
 response('I want to prepare for the road.','Хочу подготовиться к дороге.','TALK_BERSERK_FLORA_PREPARATION',{'and':[peace,m('berserk_flora_siege_state == 0')]}),
 response('Remind me how to use the charm.','Напомни, как пользоваться оберегом.','TALK_BERSERK_FLORA_PREPARED',m('berserk_flora_siege_state == 1')),
 response('Thank you. I must go.','Спасибо. Мне пора.','TALK_DONE')]
flora.append(topic('TALK_BERSERK_FLORA_WORLD',t('We can begin with the wound you carry or with the paths between these worlds. Ask what you need to understand first.','Начнём с раны, которую ты носишь, или с путей между этими мирами. Спроси о том, что сейчас важнее понять.'),[
 response('What does the Brand feel?','Что чувствует Клеймо?','TALK_BERSERK_FLORA_BRAND'),
 response('Who crosses the wounds?','Кто проходит через раны?','TALK_BERSERK_FLORA_APOSTLES'),
 response('Why did the worlds collide?','Почему миры столкнулись?','TALK_BERSERK_FLORA_WORLD_COLLISION'),back(root['id'])]))
F['TALK_BERSERK_FLORA_COST']['dynamic_line']=t('The frenzy can drive you for about two and a half minutes. Afterwards your strength and blood must recover; the price lasts much longer than the rush. The armor conceals pain, not the wound. Plan where to retreat before relying on it.','Ярость может гнать тело около двух с половиной минут. После неё силы и кровь должны восстановиться; расплата длится гораздо дольше самого рывка. Доспех скрывает боль, а не рану. Продумай отступление прежде, чем положиться на него.')
F['TALK_BERSERK_FLORA_RELICS']['dynamic_line']=t('Some trophies keep a little of the power that shaped their former master. One may help you strike a demon, another see through darkness or endure heat. Ask about a relic you actually carry; none promises safety on every road.','В некоторых трофеях остаётся часть силы прежнего хозяина. Один помогает бить демонов, другой — видеть во тьме или переносить жар. Спроси о том, что действительно носишь; ни один не обещает безопасности на любой дороге.')
prep=t('Take the time you need to prepare. Once you understand the armor, I can ready a charm for the road. Keep your supplies close and notice the western path and the southern garden before you set out.','Подготовься без спешки. Когда поймёшь свойства доспеха, я подготовлю дорожный оберег. Держи припасы рядом и приметь западную тропу и южный сад, прежде чем отправляться дальше.')
for name in ['PREPARATION','SIEGE_CONFIRM','SIEGE_OWNER_CONFIRM']:
 F['TALK_BERSERK_FLORA_'+name]['dynamic_line']=prep
 for r in F['TALK_BERSERK_FLORA_'+name]['responses']:
  if r.get('effect',{}).get('run_eocs')=='EOC_BERSERK_FLORA_PREPARE_SIEGE':r['text']=t('I have prepared. Ready the charm.','Я подготовился. Приготовь оберег.')
F['TALK_BERSERK_FLORA_PREPARED']['dynamic_line']=t('The charm is ready. Keep it while you finish preparing. Awaken it here when you choose to set out; until then you can rest or ask more questions.','Оберег готов. Держи его при себе, пока заканчиваешь подготовку. Пробуди его здесь, когда решишь отправляться дальше; до того можно отдыхать и задавать вопросы.')
F['TALK_BERSERK_FLORA_WORLD_COLLISION']['dynamic_line']=t('This house stands beside a spiritual tree. The crossing joined wounds in your world to paths in ours; the Eclipse deepened them. Quieting one wound helps those nearby, but cannot mend the whole boundary. That is why I guard this place and share what I can.','Этот дом стоит рядом с духовным деревом. Столкновение связало раны твоего мира с путями нашего; Затмение углубило их. Закрыв одну рану, можно помочь живущим рядом, но не восстановить всю границу. Поэтому я защищаю это место и делюсь тем, чем могу.')
F['TALK_BERSERK_FLORA_ARMOR']['responses']=[r for r in F['TALK_BERSERK_FLORA_ARMOR']['responses'] if r.get('topic')!='TALK_BERSERK_FLORA_RECEIVED']
# Previously receiving aid does not need another acquisition button.
F['TALK_BERSERK_FLORA_NEXT']['responses']=[r for r in F['TALK_BERSERK_FLORA_NEXT']['responses'] if r['topic']!='TALK_BERSERK_FLORA_SMITH']
F['TALK_BERSERK_FLORA_NEXT']['responses'].insert(-1,response('Can a smith help prepare my equipment?','Кузнец поможет подготовить снаряжение?','TALK_BERSERK_FLORA_SMITH'))
flora.append(topic('TALK_BERSERK_FLORA_SMITH',t('Godot and Rickert work at a woodland forge. They can help with a mechanical hand and a blade that must endure great strain. If you already own their work, ask for repairs rather than a second weapon.','Годо и Рикерт работают в лесной кузнице. Они помогут с механической рукой и клинком, которому предстоит выдержать большие нагрузки. Если их работа уже у тебя, проси о ремонте, а не о втором оружии.'),[
 response('Mark the road to the forge.','Отметь дорогу к кузнице.','TALK_BERSERK_FLORA_SMITH',effect=run('EOC_BERSERK_GODO_SEEK')),back(root['id'])]))
unique={r['id']:r for r in flora};write('dialogue/flora.json',list(unique.values()))

menus=[]
menus.append(topic('TALK_BERSERK_ROAD_JOURNAL',t('*The notes preserve roads you have learned and work you have not finished. Choose an entry.','*Записи сохраняют известные дороги и незавершённые дела. Выберите запись.'),[
 response('Review the journey so far.','Просмотреть текущие дела.','TALK_BERSERK_ROAD_JOURNAL',m('berserk_eclipse_era == 1'),run('EOC_BERSERK_CAMPAIGN_REPORT')),
 response('Find Godot and Rickert.','Найти Годо и Рикерта.','TALK_BERSERK_ROAD_JOURNAL',effect=run('EOC_BERSERK_GODO_SEEK')),
 response('Review forge orders.','Проверить заказы в кузнице.','TALK_BERSERK_JOURNAL_ORDERS'),
 response('Recall the first hunt.','Вспомнить дорогу к первой охоте.','TALK_BERSERK_ROAD_JOURNAL',m('u_berserk_eclipse_rescue_state == 2'),run('EOC_BERSERK_FIRST_HUNT_RECALL')),
 response('Recall the ashen breach.','Вспомнить дорогу к пепельному прорыву.','TALK_BERSERK_ROAD_JOURNAL',m('u_berserk_first_hunt_done == 1'),run('EOC_BERSERK_BREACH_READ_CLUE')),
 *[response(en,ru,'TALK_BERSERK_ROAD_JOURNAL',{'or':[m(f'berserk_hunt_{key}_state >= 1'),{'u_has_item':'berserk_apostle_hunt_journal'}]},run('EOC_BERSERK_'+key.upper()+'_SEEK')) for key,en,ru in [('count',"Recall the Count's trail.",'Вспомнить путь к Графу.'),('wyald',"Recall the Black Dogs' camp.",'Вспомнить лагерь Чёрных Псов.'),('rosine',"Recall the misty valley.",'Вспомнить Туманную долину.')]],
 response("Recall Flora's grove.",'Вспомнить рощу Флоры.','TALK_BERSERK_ROAD_JOURNAL',{'test_eoc':'EOC_BERSERK_FLORA_ROUTE_AVAILABLE'},run('EOC_BERSERK_FLORA_SEEK')),
 response("Recall Grunbeld's stronghold.",'Вспомнить крепость Грюнбельда.','TALK_BERSERK_ROAD_JOURNAL',{'or':[m('u_berserk_flora_escaped == 1'),m('berserk_hunt_grunbeld_site_registered == 1')]},run('EOC_BERSERK_GRUNBELD_SEEK')),
 response('Close the notes.','Закрыть записи.','TALK_DONE')
]))
menus.append(topic('TALK_BERSERK_JOURNAL_ORDERS',t('*Orders at the woodland forge. Deliver materials to Godot himself; reading these notes does not hand them over.','*Заказы лесной кузницы. Материалы передаются самому Годо; чтение записей их не расходует.'),[
 response('Arm cannon order.','Заказ руки-пушки.','TALK_BERSERK_JOURNAL_ARM'),
 response('Dragonslayer order.','Заказ Драконоборца.','TALK_BERSERK_JOURNAL_SWORD'),
 response('Return to the roads.','Вернуться к дорогам.','TALK_BERSERK_ROAD_JOURNAL')]))
for order,en,ru in [('arm','Arm cannon','Рука-пушка'),('sword','Dragonslayer','Драконоборец')]:
 if order=='arm':stages=[
  ('Order the cannon from Rickert at the forge, or make it yourself with fabrication 8 and mechanics 4.','Закажите пушку у Рикерта в кузнице или изготовьте самостоятельно с производством 8 и механикой 4.'),
  ('Deliver 8 steel lumps and 2 pipes to Rickert at the forge.','Передайте Рикерту в кузнице 8 кусков стали и 2 трубы.'),
  ('Deliver 2 springs, 4 leather patches and 200 charcoal.','Передайте 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля.'),
  ('Meet Rickert at the forge six hours after the last delivery to collect the cannon.','Встретьтесь с Рикертом в кузнице через шесть часов после последней поставки и заберите пушку.'),
  ('This order is settled. Install the cannon you received or maintain the prosthetic you already own.','Заказ завершён. Установите полученную пушку или следите за уже имеющимся протезом.')]
 else:stages=[
  ('Order the blade at the forge. Godot does not duplicate one you already own.','Закажите клинок в кузнице. Годо не выдаёт второй меч, если он уже есть.'),
  ('Steel delivered: <u_val:berserk_godo_sword_iron_given>/32. Bring loads of eight.','Сталь передана: <u_val:berserk_godo_sword_iron_given>/32. Приносите партии по восемь.'),
  ('Deliver 8 high-steel lumps, 600 charcoal and 4 leather patches.','Передайте 8 кусков высокоуглеродистой стали, 600 единиц древесного угля и 4 лоскутка кожи.'),
  ('Return two days after the last delivery to collect the blade.','Вернитесь через два дня после последней поставки и заберите клинок.'),
  ('This order is settled. Godot can repair the blade you own.','Заказ завершён. Годо может починить имеющийся клинок.')]
 text=t(*stages[4])
 for stage in range(3,-1,-1):text=cond(m(f'u_berserk_godo_{order}_state == {stage}'),t(*stages[stage]),text)
 menus.append(topic('TALK_BERSERK_JOURNAL_'+order.upper(),text,[
  response('Review the other order.','Проверить другой заказ.','TALK_BERSERK_JOURNAL_ORDERS'),
  response('Return to the roads.','Вернуться к дорогам.','TALK_BERSERK_ROAD_JOURNAL')]))
write('dialogue/road_journal.json',menus)

rows=read('effects/wyald_rosine_hunt_eocs.json')
for r in rows:
 if r['id']=='EOC_BERSERK_HUNT_JOURNAL_USE':r['effect']={'open_dialogue':{'topic':'TALK_BERSERK_ROAD_JOURNAL'}}
write('effects/wyald_rosine_hunt_eocs.json',rows)
for f in ['campaign_journal.json','apostle_hunt_journal.json']:
 rows=read('items/'+f)
 for r in rows:
  r['description']=t('Known roads, current tasks and completed hunts. Activate to choose an entry; the notes keep the same destinations when you return.','Известные дороги, текущие дела и завершённые охоты. Активируйте, чтобы выбрать запись; найденные места сохраняются при возвращении.')
  r['use_action']['effect_on_conditions']=['EOC_BERSERK_GODO_BOOK']
  r['use_action']['need_wielding']=False
 write('items/'+f,rows)

rows=read('effects/campaign_journal_eocs.json')
replacements={
 'Prepare for the first hunt; select its existing mission in the mission journal.':('Prepare armor, dressings and a retreat before following the first hunt.','Перед первой охотой приготовьте броню, перевязку и путь отхода.'),
 'No dawn observation recorded yet. The refuge journal explains the optional criteria.':('You have not yet recorded a night at your refuge. Keep water, light and an escape ready.','Ночь в пристанище ещё не отмечена. Подготовьте воду, свет и путь отхода.'),
 'Refuge readiness recorded. Check water, light, bedding and an escape yourself.':('Your refuge is prepared. Check your supplies and leave a clear route out.','Пристанище подготовлено. Проверьте запасы и оставьте свободный выход.'),
 'Choose a defensible shelter and build a ward. Refuge and dawn observations are optional, not gates for hunting.':('Choose a defensible shelter and build a ward. Preparing a refuge helps you recover between hunts.','Выберите защищаемое укрытие и устройте оберег. Пристанище поможет восстанавливаться между охотами.')}
def visit(value):
 if isinstance(value,dict):
  for key,child in list(value.items()):
   if isinstance(child,str) and child in replacements:value[key]=t(*replacements[child])
   else:visit(child)
 elif isinstance(value,list):
  for child in value:visit(child)
visit(rows)
write('effects/campaign_journal_eocs.json',rows)
# Leave legacy acquisition and siege state machinery intact.
rows=read('recipes/arm_cannon_recipes.json')
rows[0]['difficulty']=8;write('recipes/arm_cannon_recipes.json',rows)
rows=read('items/bionics/arm_cannon_cbms.json');rows[1]['material']=['steel','leather']
rows[1]['description']=t('A mechanical arm cannon made by hand or at Godot\'s forge. With your left hand missing, activate it directly in your inventory to attach it yourself. No electricity or surgical equipment is required. Making one yourself requires fabrication 8 and mechanics 4.','Механическая рука-пушка, сделанная вручную или в кузнице Годо. При отсутствующей левой кисти активируйте её прямо из инвентаря для самостоятельной установки. Электричество и хирургическое оборудование не требуются. Самостоятельное изготовление требует производства 8 и механики 4.')
write('items/bionics/arm_cannon_cbms.json',rows)
rows=read('bionics/arm_cannon.json')
rows[0]['description']=t('Your left hand is gone. This permanent interface anchors a prosthetic arm cannon; it cannot grip objects or help wield a weapon with both hands. You learn the cannon and ammunition recipes. Making the cannon yourself requires fabrication 8 and mechanics 4; Godot can build it from supplied materials. Activate the finished cannon in your inventory to attach it yourself.','Левой кисти больше нет. Это постоянное крепление позволяет установить руку-пушку, но не возвращает хват и не помогает держать оружие двумя руками. Вы изучаете рецепты пушки и её боеприпаса. Самостоятельное изготовление требует производства 8 и механики 4; Годо может сделать пушку из принесённых материалов. Готовая пушка устанавливается активацией из инвентаря.')
rows[1]['description']=t('A mechanical cannon mounted on the left arm after activating a finished prosthetic in your inventory. Activate this bionic to wield and reload its single chamber, then retract it to take up your sword again. It burns powder charges instead of bionic power.','Механическая пушка на левой руке, установленная активацией готового протеза из инвентаря. Активируйте бионику, чтобы выдвинуть оружие и зарядить единственный ствол, затем уберите его, чтобы снова взять меч. Пушка использует пороховые заряды вместо энергии бионики.')
write('bionics/arm_cannon.json',rows)
rows=read('modinfo.json');rows[0]['version']='3.2.0-dev';write('modinfo.json',rows)
from forge_story_content import apply_story_world
apply_story_world(t, write)
(ROOT/'tools/godo_32_ru.json').write_text(json.dumps(RU,ensure_ascii=False,indent=2)+'\n')
print('Updated dialogue trees, known-road menu and fabrication requirement.')
