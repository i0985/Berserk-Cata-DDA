#!/usr/bin/env python3
"""Build the 3.2 Godot content and its RU strings; no existing map is redrawn."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/Berserk'
RU = {}
def t(en, ru):
    RU[en] = ru
    return en
def save(path, data):
    (MOD / path).parent.mkdir(parents=True, exist_ok=True)
    (MOD / path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
def m(expr): return {'math': [expr]}
def allof(*c): return {'and': list(c)}
def anyof(*c): return {'or': list(c)}
def neg(c): return {'not': c}
def run(id): return {'run_eocs': id}
def has(id, count=1): return {'u_has_items': {'item': id, 'count': count}}
def consume(id, count, charges=False): return {'u_consume_item': id, 'charges' if charges else 'count': count}
def spawn(id, count=1): return {'u_spawn_item': id, 'count': count, 'suppress_message': True}
def call(id): return {'test_eoc': id}
def msg(en, ru, kind='info'): return {'u_message': t(en,ru), 'type': kind, 'popup': False}
def eoc(id, effect, condition=None, **fields):
    value={'type':'effect_on_condition','id':'EOC_BERSERK_GODO_'+id,'effect':effect,**fields}
    if condition is not None:value['condition']=condition
    return value
def response(en, ru, topic, condition=None, effect=None):
    value={'text':t(en,ru),'topic':topic}
    if condition is not None:value['condition']=condition
    if effect is not None:value['effect']=effect
    return value
topics=[]
def topic(id,line,responses,**extra):
    topics.append({'type':'talk_topic','id':id,'dynamic_line':line,'responses':responses,**extra})
def back(target='TALK_BERSERK_GODO'):
    labels={
      'TALK_BERSERK_GODO_ARM':('Return to the arm cannon order.','Вернуться к заказу руки-пушки.'),
      'TALK_BERSERK_GODO_SWORD':('Return to the sword order.','Вернуться к заказу меча.'),
      'TALK_BERSERK_GODO_REPAIR':('Return to repairs.','Вернуться к ремонту.'),
      'TALK_BERSERK_GODO_SPARKS':('Return to the sparks.','Вернуться к разговору об искрах.')}
    en,ru=labels.get(target,('Ask something else.','Спросить о другом.'))
    return response(en,ru,target)
def line(en,ru): return t(en,ru)

effects=[
 eoc('AT_SMITH',[],allof('has_beta','npc_is_monster',m("n_monsters_nearby('mon_berserk_godo', 'radius': 0, 'attitude': 'both') > 0"))),
 eoc('HAS_ARM',[],anyof(has('bio_berserk_arm_cannon'),{'u_has_bionics':'bio_berserk_arm_cannon'})),
 eoc('HAS_SWORD',[],has('true_guts_sword')),
 eoc('KNOWN',[],allof(m('has_var(berserk_godo_location)'),{'overmap_at_point':'berserk_godo_workshop','point':{'global_val':'berserk_godo_location'}})),
 eoc('REGISTER',[
   {'u_location_variable':{'global_val':'berserk_godo_location'}},
   m('berserk_godo_location.x = floor(berserk_godo_location.x / 24) * 24'),
   m('berserk_godo_location.y = floor(berserk_godo_location.y / 24) * 24'),
   m('berserk_godo_location.z = 0'),
   {'reveal_map':{'global_val':'berserk_godo_location'},'radius':1}
 ],anyof({'u_at_om_location':'berserk_godo_workshop'},{'u_at_om_location':'berserk_godo_loft'})),
 eoc('FOUND',[
   {'copy_var':{'context_val':'godo_candidate'},'target_var':{'global_val':'berserk_godo_location'}},
   m('berserk_godo_location.x = floor(berserk_godo_location.x / 24) * 24'),
   m('berserk_godo_location.y = floor(berserk_godo_location.y / 24) * 24'),
   {'reveal_map':{'global_val':'berserk_godo_location'},'radius':1},
   run('EOC_BERSERK_GODO_ROUTE_MISSION'),
   {'if':m('u_berserk_godo_route_announced != 1'),'then':[
     m('u_berserk_godo_route_announced = 1'),
     msg("Godot's woodland forge is marked on your map.",'Лесная кузница Годо отмечена на карте.')
   ]}
 ],{'overmap_at_point':'berserk_godo_workshop','point':{'context_val':'godo_candidate'}}),
 eoc('SEEK',[
   {'if':call('EOC_BERSERK_GODO_KNOWN'),'then':[
      {'reveal_map':{'global_val':'berserk_godo_location'},'radius':1},run('EOC_BERSERK_GODO_ROUTE_MISSION')
    ],'else':{
      'u_location_variable':{'context_val':'godo_candidate'},
      'target_params':{'om_terrain':'berserk_godo_workshop','random':False,'min_distance':0,'z':0},
      'true_eocs':['EOC_BERSERK_GODO_FOUND'],
      'false_eocs':[{'id':'EOC_BERSERK_GODO_SEARCH_FAILED','effect':[
        msg('The old directions do not yet show the forge. Keep the notes and return to them after exploring farther.','По старым указаниям пока не удалось найти кузницу. Сохраните запись и вернитесь к ней после дальнейшей разведки.')
      ]}]
    }},
   {'if':neg(has('berserk_godo_order_book')),'then':spawn('berserk_godo_order_book')}
 ]),
 eoc('BEGIN',[
   run('EOC_BERSERK_GODO_REGISTER'),m('u_berserk_godo_met = 1'),
   {'if':neg(has('berserk_godo_order_book')),'then':spawn('berserk_godo_order_book')},
   run('EOC_BERSERK_GODO_ROUTE_MISSION'),run('EOC_BERSERK_GODO_ORDER_SYNC')
 ]),
]

missions=[]
def mission(id,en,ru,desc,ru_desc,goal):
    missions.append({'type':'mission_definition','id':id,'name':t(en,ru),'description':t(desc,ru_desc),
       'goal':'MGOAL_CONDITION','goal_condition':m(goal),'difficulty':3,'value':0,
       'origins':['ORIGIN_GAME_START'],'has_generic_rewards':False,'invisible_on_complete':False,
       'start':{'assign_mission_target':{'om_terrain':'berserk_godo_workshop','var':{'global_val':'berserk_godo_location'},'reveal_radius':0}}})
mission('MISSION_BERSERK_GODO','Seek Godot and Rickert','Найти Годо и Рикерта',
        'Visit the woodland forge. Godot can build an arm cannon, forge a Dragonslayer and repair your existing equipment. Rickert can explain the fitting.',
        'Посетите лесную кузницу. Годо может изготовить руку-пушку, выковать Драконоборца и починить имеющееся снаряжение. Рикерт объяснит установку протеза.','u_berserk_godo_met == 1')
contracts=[
 ('ARM_METAL','Metal for an arm cannon','Металл для руки-пушки','Bring Godot 8 lumps of steel and 2 pipes. He accepts them together.','Принесите Годо 8 кусков стали и 2 трубы. Они передаются вместе.','arm',1,2),
 ('ARM_FITTINGS','Fit the prosthetic','Подготовить крепление протеза','Bring 2 springs, 4 leather patches and 200 charcoal. Godot needs six hours after this delivery.','Принесите 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля. После доставки Годо потребуется шесть часов.','arm',2,3),
 ('ARM_COLLECT','Collect the arm cannon','Забрать руку-пушку','Return to Godot six hours after the fittings were delivered. Activate the finished prosthetic in your inventory to fit it yourself.','Вернитесь к Годо через шесть часов после передачи деталей. Готовый протез можно самостоятельно установить активацией из инвентаря.','arm',3,4),
 ('SWORD_IRON','Steel for a Dragonslayer','Сталь для Драконоборца','Bring 32 lumps of steel. Deliver eight at a time if the full load is too heavy.','Принесите 32 куска стали. Их можно передавать партиями по восемь, если весь груз слишком тяжёлый.','sword',1,2),
 ('SWORD_TEMPER','Steel that will hold an edge','Сталь для стойкого лезвия','Bring 8 lumps of high steel, 600 charcoal and 4 leather patches. High steel can be recovered or smelted using ordinary metalworking recipes; no unique defeated boss is required.','Принесите 8 кусков высокоуглеродистой стали, 600 единиц древесного угля и 4 лоскутка кожи. Сталь можно найти или выплавить по обычным рецептам обработки металла; победа над определённым боссом не обязательна.','sword',2,3),
 ('SWORD_COLLECT','Collect the Dragonslayer','Забрать Драконоборца','Give Godot two days to forge and temper the blade, then return. A sword you already own is repaired, not duplicated.','Дайте Годо два дня на ковку и закалку, затем вернитесь. Если меч уже есть, кузнец поможет с ремонтом вместо выдачи второго.','sword',3,4),
]
mission_sync=[]
for key,en,ru,desc,rudesc,order,state,end in contracts:
    mid='MISSION_BERSERK_GODO_'+key
    mission(mid,en,ru,desc,rudesc,f'u_berserk_godo_{order}_state >= {end}')
    mission_sync.append({'if':m(f'u_berserk_godo_{order}_state >= {end}'),
      'then':{'if':{'u_has_mission':mid},'then':{'finish_mission':mid,'success':True}},
      'else':{'if':allof(m(f'u_berserk_godo_{order}_state == {state}'),neg({'u_has_mission':mid})),
              'then':{'assign_mission':mid}}})
effects += [
 eoc('ROUTE_MISSION',{'if':m('u_berserk_godo_met == 1'),
       'then':{'if':{'u_has_mission':'MISSION_BERSERK_GODO'},'then':{'finish_mission':'MISSION_BERSERK_GODO','success':True}},
       'else':{'if':neg({'u_has_mission':'MISSION_BERSERK_GODO'}),'then':{'assign_mission':'MISSION_BERSERK_GODO'}}},call('EOC_BERSERK_GODO_KNOWN')),
 eoc('ORDER_SYNC',mission_sync,call('EOC_BERSERK_GODO_KNOWN')),
 eoc('START_ARM',[m('u_berserk_godo_arm_state = 1'),run('EOC_BERSERK_GODO_ORDER_SYNC')],
     allof(m('u_berserk_godo_arm_state == 0'),neg(call('EOC_BERSERK_GODO_HAS_ARM')),{'u_has_bionics':'bio_berserk_hand_stump'})),
 eoc('START_SWORD',[m('u_berserk_godo_sword_state = 1'),m('u_berserk_godo_sword_iron_given = 0'),run('EOC_BERSERK_GODO_ORDER_SYNC')],
     allof(m('u_berserk_godo_sword_state == 0'),neg(call('EOC_BERSERK_GODO_HAS_SWORD')))),
 eoc('ARM_METAL',[
     consume('steel_lump',8,True),consume('pipe',2),m('u_berserk_godo_arm_state = 2'),run('EOC_BERSERK_GODO_ORDER_SYNC')
 ],allof(m('u_berserk_godo_arm_state == 1'),has('steel_lump',8),has('pipe',2),neg(call('EOC_BERSERK_GODO_HAS_ARM')))),
 eoc('ARM_FITTINGS',[
     consume('spring',2),consume('leather',4),consume('charcoal',200,True),
     m("u_berserk_godo_arm_ready_at = time('now') + 21600"),m('u_berserk_godo_arm_state = 3'),run('EOC_BERSERK_GODO_ORDER_SYNC')
 ],allof(m('u_berserk_godo_arm_state == 2'),has('spring',2),has('leather',4),has('charcoal',200),neg(call('EOC_BERSERK_GODO_HAS_ARM')))),
 eoc('SWORD_IRON',[
     consume('steel_lump',8,True),m('u_berserk_godo_sword_iron_given = u_berserk_godo_sword_iron_given + 8'),
     {'if':m('u_berserk_godo_sword_iron_given >= 32'),'then':m('u_berserk_godo_sword_state = 2')},run('EOC_BERSERK_GODO_ORDER_SYNC')
 ],allof(m('u_berserk_godo_sword_state == 1'),m('u_berserk_godo_sword_iron_given < 32'),has('steel_lump',8),neg(call('EOC_BERSERK_GODO_HAS_SWORD')))),
 eoc('SWORD_TEMPER',[
     consume('hc_steel_lump',8,True),consume('charcoal',600,True),consume('leather',4),
     m("u_berserk_godo_sword_ready_at = time('now') + 172800"),m('u_berserk_godo_sword_state = 3'),run('EOC_BERSERK_GODO_ORDER_SYNC')
 ],allof(m('u_berserk_godo_sword_state == 2'),has('hc_steel_lump',8),has('charcoal',600),has('leather',4),neg(call('EOC_BERSERK_GODO_HAS_SWORD')))),
]
# Ownership discovered while an order is in progress never produces a second item.
# Deposits are returned exactly once, including partial eight-lump deliveries.
for order,item in [('arm','bio_berserk_arm_cannon'),('sword','true_guts_sword')]:
    refunds=[]
    if order=='arm':
        refunds=[{'if':m('u_berserk_godo_arm_state >= 2'),'then':[spawn('steel_lump',8),spawn('pipe',2)]},
                 {'if':m('u_berserk_godo_arm_state >= 3'),'then':[spawn('spring',2),spawn('leather',4),spawn('charcoal',200)]}]
    else:
        refunds=[{'if':m('u_berserk_godo_sword_iron_given > 0'),'then':spawn('steel_lump',{'u_val':'berserk_godo_sword_iron_given'})},
                 {'if':m('u_berserk_godo_sword_state >= 3'),'then':[spawn('hc_steel_lump',8),spawn('charcoal',600),spawn('leather',4)]}]
    effects.append(eoc(order.upper()+'_REFUND',refunds+[m(f'u_berserk_godo_{order}_state = 4'),run('EOC_BERSERK_GODO_ORDER_SYNC')],
        allof(m(f'u_berserk_godo_{order}_state > 0'),m(f'u_berserk_godo_{order}_state < 4'),call('EOC_BERSERK_GODO_HAS_'+order.upper()))))
    effects.append(eoc(order.upper()+'_CLAIM',[
        {'if':call('EOC_BERSERK_GODO_HAS_'+order.upper()),'then':run('EOC_BERSERK_GODO_'+order.upper()+'_REFUND'),
         'else':[spawn(item),m(f'u_berserk_godo_{order}_state = 4'),run('EOC_BERSERK_GODO_ORDER_SYNC')]}
    ],allof(m(f'u_berserk_godo_{order}_state == 3'),m(f"time('now') >= u_berserk_godo_{order}_ready_at"))))
effects += [
 eoc('REPAIR_PICK',{
     'u_run_inv_eocs':'manual','title':t('Choose equipment for Godot to repair','Выберите снаряжение для ремонта у Годо'),
     'search_data':[{'id':['true_guts_sword','true_guts_early_sword','forged_guts_sword','bio_berserk_arm_cannon'],
                     'condition':m("n_hp('ALL') < n_hp_max('torso')")}],
     'true_eocs':['EOC_BERSERK_GODO_REPAIR_ITEM']
 }),
 eoc('REPAIR_ITEM',[
     consume('steel_lump',1,True),consume('charcoal',50,True),m("n_hp('ALL') = n_hp_max('torso')"),
     {'turn_cost':'1 minute'},msg('Godot straightens the damaged metal and restores the edge.','Годо выправляет повреждённый металл и восстанавливает лезвие.','good')
 ],allof(has('steel_lump',1),has('charcoal',50),m("n_hp('ALL') < n_hp_max('torso')"))),
]

topic('TALK_BERSERK_GODO_ENTER',line("*The old smith rests his hammer against the anvil. Rickert glances up from a leather strap.",'*Старый кузнец кладёт молот на наковальню. Рикерт отвлекается от кожаного ремня.'),[
 response('May we talk?','Можно поговорить?','TALK_BERSERK_GODO'),response('I will come back later.','Зайду позже.','TALK_DONE')
],speaker_effect={'effect':run('EOC_BERSERK_GODO_BEGIN')})
topic('TALK_BERSERK_GODO',line("If you came for a miracle, you've taken the wrong road. If you need honest iron, tell me what it has to do.",'Если пришёл за чудом, ошибся дорогой. Если нужен добрый металл — говори, какую работу ему предстоит делать.'),[
 response('I need a prosthetic for my missing hand.','Мне нужен протез потерянной кисти.','TALK_BERSERK_GODO_ARM'),
 response('Can you forge a weapon for fighting demons?','Можешь выковать оружие против демонов?','TALK_BERSERK_GODO_SWORD'),
 response('Can you repair what I already have?','Можешь починить моё снаряжение?','TALK_BERSERK_GODO_REPAIR'),
 response('Why do you keep forging?','Почему ты продолжаешь ковать?','TALK_BERSERK_GODO_SPARKS'),
 response('May I rest here? And who is Rickert?','Можно здесь отдохнуть? Кто такой Рикерт?','TALK_BERSERK_GODO_HOME'),
 response('I will leave you to your work.','Не буду мешать работе.','TALK_DONE')
])
topic('TALK_BERSERK_GODO_SPARKS',line("For years I thought about nothing but the next piece of iron. Heat it, strike it, watch the sparks die. Then I began to notice how much those brief lights resemble a life: bright for a moment, gone before your hand can catch them. I still forge. It's the work I know how to give to the living.",'Годами я думал только о следующем куске железа. Нагреть, ударить, смотреть, как гаснут искры. Потом заметил, как эти короткие огни похожи на жизнь: вспыхнут — и исчезнут прежде, чем успеешь протянуть руку. Я всё ещё кую. Это работа, которую я умею отдавать живым.'),[
 response('Does a weapon give a life meaning?','Оружие придаёт жизни смысл?','TALK_BERSERK_GODO_PRICE'),
 response('Were you always a smith?','Ты всегда был кузнецом?','TALK_BERSERK_GODO_LIFE'),back()
])
topic('TALK_BERSERK_GODO_PRICE',line("A blade doesn't decide why you live. Keep swinging only to fill the silence, and you'll lose whatever waited beyond the battle. I can make the iron endure. The reason to come home is your own work.",'Клинок не решает, ради чего ты живёшь. Будешь махать им только ради того, чтобы заглушить тишину, — потеряешь всё, что ждало за пределами боя. Я могу сделать металл стойким. Найти причину вернуться домой придётся тебе.'),[
 response('Then make something I can return with.','Тогда сделай то, с чем я смогу вернуться.','TALK_BERSERK_GODO_SWORD'),back()
])
topic('TALK_BERSERK_GODO_LIFE',line("I've served men who wanted a beautiful blade and men who wanted an impossible one. Iron is more honest than either. Out here Rickert and I can make something useful without a lord counting every blow of the hammer.",'Я работал на людей, которым нужен был красивый меч, и на тех, кому нужен был невозможный. Железо честнее и тех и других. Здесь мы с Рикертом можем делать полезную работу, пока над душой не стоит господин, считающий каждый удар молота.'),[response('Tell me more about the sparks.','Расскажи ещё об искрах.','TALK_BERSERK_GODO_SPARKS'),back()])
topic('TALK_BERSERK_GODO_HOME',line('The forge is downstairs; sleep upstairs if you need to. Keep the stair and doors clear. Rickert helps with the small moving parts and straps. We can offer a roof and a quiet corner, but walls alone will not silence that mark.',
 'Внизу кузница; если нужен отдых, поднимайся наверх. Не заставляй лестницу и двери. Рикерт помогает с мелкими подвижными деталями и ремнями. Крышу и тихий угол мы предложить можем, но одни стены не заставят Клеймо замолчать.'),[
 response('Can Rickert help me fit the cannon?','Рикерт поможет установить пушку?','TALK_BERSERK_GODO_FITTING'),back()
])
topic('TALK_BERSERK_GODO_FITTING',line('He will show you the fastenings. Once you have the finished cannon and the mount on your missing left hand, activate the cannon in your inventory. You do not have to wield it, use electricity or seek a surgeon.',
 'Он покажет крепления. Когда будет готова пушка и крепление на месте потерянной левой кисти, активируй пушку из инвентаря. Брать её в руку, искать электричество или хирурга не требуется.'),[
 response('What if I want to make it myself?','А если я хочу изготовить её сам?','TALK_BERSERK_GODO_SELF'),back()
])
topic('TALK_BERSERK_GODO_SELF',line('Making that mechanism is advanced work: fabrication 8 and mechanics 4, with the proper metalworking tools. Bring the materials and I can do it without requiring you to master the craft. Fitting a finished cannon remains something you can do yourself.',
 'Такой механизм требует серьёзного мастерства: производство 8 и механика 4, а также подходящие инструменты. Принесёшь материалы — я изготовлю его, даже если ты сам ещё не освоил ремесло. Установить готовую пушку ты по-прежнему можешь самостоятельно.'),[back('TALK_BERSERK_GODO_ARM'),back()])
arm_line={'test_eoc':'EOC_BERSERK_GODO_HAS_ARM','yes':line('That mechanism is already made. Let me see how it was put together. You need not pay for a second one.','Механизм у тебя уже есть. Дай посмотреть, как его собрали. Платить за второй тебе ни к чему.'),
 'no':{'math':['u_berserk_godo_arm_state == 4'],'yes':line('Your order is settled. Look after the cannon I gave you; Rickert can explain its fitting.','Твой заказ завершён. Береги полученную пушку; Рикерт объяснит крепление.'),
 'no':{'math':['u_berserk_godo_arm_state == 3'],'yes':line('The metal and fittings are here. Give me six hours from the last delivery; then come back for the finished cannon.','Металл и крепления уже у меня. Дай шесть часов с последней поставки, потом возвращайся за готовой пушкой.'),
 'no':line('I can make a cannon and a grip to fit the stump. First bring 8 lumps of steel and 2 pipes; then 2 springs, 4 leather patches and 200 charcoal. Rickert will prepare the straps.','Я могу сделать пушку с креплением для культи. Сначала нужны 8 кусков стали и 2 трубы, затем 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля. Рикерт подготовит ремни.')}}}
topic('TALK_BERSERK_GODO_ARM',arm_line,[
 response('I made this prosthetic myself.','Этот протез я изготовил сам.','TALK_BERSERK_GODO_PRAISE',call('EOC_BERSERK_GODO_HAS_ARM')),
 response('I want to order the arm cannon.','Я хочу заказать руку-пушку.','TALK_BERSERK_GODO_ARM',allof(m('u_berserk_godo_arm_state == 0'),neg(call('EOC_BERSERK_GODO_HAS_ARM')),{'u_has_bionics':'bio_berserk_hand_stump'}),run('EOC_BERSERK_GODO_START_ARM')),
 response('Deliver 8 steel lumps and 2 pipes.','Передать 8 кусков стали и 2 трубы.','TALK_BERSERK_GODO_ARM',allof(m('u_berserk_godo_arm_state == 1'),has('steel_lump',8),has('pipe',2),neg(call('EOC_BERSERK_GODO_HAS_ARM'))),run('EOC_BERSERK_GODO_ARM_METAL')),
 response('Deliver the springs, leather and charcoal.','Передать пружины, кожу и уголь.','TALK_BERSERK_GODO_ARM',allof(m('u_berserk_godo_arm_state == 2'),has('spring',2),has('leather',4),has('charcoal',200),neg(call('EOC_BERSERK_GODO_HAS_ARM'))),run('EOC_BERSERK_GODO_ARM_FITTINGS')),
 response('Collect the finished arm cannon.','Забрать готовую руку-пушку.','TALK_BERSERK_GODO_FITTING',allof(m('u_berserk_godo_arm_state == 3'),m("time('now') >= u_berserk_godo_arm_ready_at")),run('EOC_BERSERK_GODO_ARM_CLAIM')),
 response('I already have one. Return my unused materials.','У меня уже есть протез. Верни неиспользованные материалы.','TALK_BERSERK_GODO_ARM',allof(call('EOC_BERSERK_GODO_HAS_ARM'),m('u_berserk_godo_arm_state > 0'),m('u_berserk_godo_arm_state < 4')),run('EOC_BERSERK_GODO_ARM_REFUND')),
 response('Remind me what I still owe.','Напомни, что ещё нужно принести.','TALK_BERSERK_GODO_ARM_STATUS'),
 response('Can I make it myself?','Могу я изготовить её сам?','TALK_BERSERK_GODO_SELF'),back()
])
topic('TALK_BERSERK_GODO_PRAISE',{'u_has_bionics':'bio_berserk_hand_stump','yes':line("You made this with one hand? Hah! That isn't luck; those joints took skill. Keep watching the fit and don't let that skill die with the first thing you've built.",'Одной рукой это собрал? Ха! Это не везение — такие сочленения требуют мастерства. Следи за креплением и не дай своему умению заглохнуть на первой сделанной вещи.'),
 'no':line('Clean work. The fitting matters more than a fine polish; keep it in good order.','Добротная работа. Хорошая подгонка важнее красивой полировки; следи за механизмом.')},[back('TALK_BERSERK_GODO_ARM'),back()])
topic('TALK_BERSERK_GODO_ARM_STATUS',{'math':['u_berserk_godo_arm_state == 4'],
 'yes':line('There is nothing left to deliver for this order. Ask about fitting or repairs if you need help.','По этому заказу больше ничего приносить не нужно. Если нужна помощь, спроси об установке или ремонте.'),
 'no':{'math':['u_berserk_godo_arm_state == 2'],
 'yes':line('The metal is paid for. Bring 2 springs, 4 leather patches and 200 charcoal.','Металл уже передан. Остались 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля.'),
 'no':{'math':['u_berserk_godo_arm_state >= 3'],'yes':line('The supplies are complete. If the cannon is not yet finished, wait until six hours have passed from your last delivery.','Все материалы переданы. Если пушка ещё не готова, дождись, пока с последней поставки пройдёт шесть часов.'),
 'no':line('The first delivery is 8 lumps of steel and 2 pipes. After that I need springs, leather and charcoal. Keep the order notes; you need not remember the list.','Первая поставка — 8 кусков стали и 2 трубы. Потом понадобятся пружины, кожа и уголь. Сохрани запись о заказе, список не нужно держать в голове.')}}},[back('TALK_BERSERK_GODO_ARM'),back()])
topic('TALK_BERSERK_GODO_SWORD',{'test_eoc':'EOC_BERSERK_GODO_HAS_SWORD',
 'yes':line('You already carry that great blade. I will not forge another to lie beside it. We can restore its edge and keep you supplied for the next journey.','Большой клинок у тебя уже есть. Не стану ковать второй, чтобы он лежал рядом без дела. Лучше выправим лезвие и подготовим тебя к следующему пути.'),
 'no':line('A Dragonslayer is a great piece of work, not an ordinary sword recipe. Bring 32 lumps of steel in loads of eight, then 8 lumps of high steel, 600 charcoal and 4 leather patches. After that I need two days to forge and temper it.','Драконоборец — большая работа, не обычный рецепт меча. Принеси 32 куска стали партиями по восемь, затем 8 кусков высокоуглеродистой стали, 600 единиц древесного угля и 4 лоскутка кожи. После этого нужны два дня на ковку и закалку.')},[
 response('Accept my order for a Dragonslayer.','Прими заказ на Драконоборца.','TALK_BERSERK_GODO_SWORD',allof(m('u_berserk_godo_sword_state == 0'),neg(call('EOC_BERSERK_GODO_HAS_SWORD'))),run('EOC_BERSERK_GODO_START_SWORD')),
 response('Deliver a load of 8 steel lumps.','Передать партию из 8 кусков стали.','TALK_BERSERK_GODO_SWORD_STATUS',allof(m('u_berserk_godo_sword_state == 1'),has('steel_lump',8),neg(call('EOC_BERSERK_GODO_HAS_SWORD'))),run('EOC_BERSERK_GODO_SWORD_IRON')),
 response('Deliver the high steel, charcoal and leather.','Передать качественную сталь, уголь и кожу.','TALK_BERSERK_GODO_SWORD_STATUS',allof(m('u_berserk_godo_sword_state == 2'),has('hc_steel_lump',8),has('charcoal',600),has('leather',4),neg(call('EOC_BERSERK_GODO_HAS_SWORD'))),run('EOC_BERSERK_GODO_SWORD_TEMPER')),
 response('Collect the Dragonslayer.','Забрать Драконоборца.','TALK_BERSERK_GODO_PRICE',allof(m('u_berserk_godo_sword_state == 3'),m("time('now') >= u_berserk_godo_sword_ready_at")),run('EOC_BERSERK_GODO_SWORD_CLAIM')),
 response('I found a blade already. Return my unused materials.','Клинок у меня уже есть. Верни неиспользованные материалы.','TALK_BERSERK_GODO_SWORD',allof(call('EOC_BERSERK_GODO_HAS_SWORD'),m('u_berserk_godo_sword_state > 0'),m('u_berserk_godo_sword_state < 4')),run('EOC_BERSERK_GODO_SWORD_REFUND')),
 response('What remains to be delivered?','Что ещё осталось принести?','TALK_BERSERK_GODO_SWORD_STATUS'),
 response('Where can I find the right steel?','Где взять подходящую сталь?','TALK_BERSERK_GODO_STEEL'),
 response('Can you repair my existing blade?','Починишь имеющийся клинок?','TALK_BERSERK_GODO_REPAIR',call('EOC_BERSERK_GODO_HAS_SWORD')),back()
])
topic('TALK_BERSERK_GODO_SWORD_STATUS',{'math':['u_berserk_godo_sword_state == 1'],
 'yes':line('I have received <u_val:berserk_godo_sword_iron_given> of the 32 steel lumps. Bring the next load of eight.','Получено <u_val:berserk_godo_sword_iron_given> из 32 кусков стали. Приноси следующую партию из восьми.'),
 'no':{'math':['u_berserk_godo_sword_state == 2'],
 'yes':line('The ordinary steel is here. Bring 8 lumps of high steel, 600 charcoal and 4 leather patches.','Обычная сталь уже у меня. Остались 8 кусков высокоуглеродистой стали, 600 единиц древесного угля и 4 лоскутка кожи.'),
 'no':{'math':['u_berserk_godo_sword_state == 3'],
 'yes':line('The material is ready. I need two days from the last delivery before you can collect the blade.','Материалы собраны. Забрать клинок можно через два дня с последней поставки.'),
 'no':line('If you want a new blade, place the order first. A blade I already made for you is work to maintain, not a reason to begin a second copy.','Если нужен новый клинок, сначала закажи его. Уже сделанный для тебя меч нужно поддерживать в порядке, а не дублировать.')}}},[back('TALK_BERSERK_GODO_SWORD'),back()])
topic('TALK_BERSERK_GODO_STEEL',line('Separate ordinary steel from high-carbon steel. Look in metal stores and working smithies, or smelt high steel with the ordinary metalworking recipes. I do not need a magic stone or the head of an apostle. Eight good lumps matter more than a pile of poor metal.',
 'Не смешивай обычную сталь с высокоуглеродистой. Ищи в запасах металла и кузницах или выплавляй качественную сталь по обычным рецептам обработки металла. Волшебный камень или голова апостола мне не нужны. Восемь хороших кусков важнее груды плохого металла.'),[back('TALK_BERSERK_GODO_SWORD'),back()])
topic('TALK_BERSERK_GODO_REPAIR',line('Bring one steel lump and 50 charcoal for a damaged blade or an uninstalled cannon. Show me the piece you want repaired. I do not replace it with a copy, and choosing nothing costs you nothing. Rickert will help maintain an installed prosthetic with the right tools.',
 'Для повреждённого клинка или ещё не установленной пушки нужны один кусок стали и 50 единиц древесного угля. Покажи вещь, которую нужно починить. Я не заменяю её копией; если ничего не выберешь, ничего не потратишь. За установленным протезом Рикерт поможет следить с подходящими инструментами.'),[
 response('Show you a damaged piece.','Показать повреждённую вещь.','TALK_BERSERK_GODO_REPAIR',allof(has('steel_lump',1),has('charcoal',50)),run('EOC_BERSERK_GODO_REPAIR_PICK')),
 response('What can you offer if I already own your sword?','Чем поможешь, если твой меч уже у меня?','TALK_BERSERK_GODO_OWNER'),back()
])
topic('TALK_BERSERK_GODO_OWNER',line('Use the bench and anvil. I can restore the blade you brought; Rickert can explain its fittings and the cannon. Upstairs there is room to rest. Keeping a weapon usable is worth more than collecting a second one.',
 'Пользуйся верстаком и наковальней. Я могу выправить принесённый клинок, Рикерт — объяснить крепления пушки. Наверху найдётся место для отдыха. Поддерживать оружие в порядке полезнее, чем складывать рядом второй экземпляр.'),[back('TALK_BERSERK_GODO_REPAIR'),back()])

topic('TALK_BERSERK_RICKERT',line('Godot handles the great pieces. I work on the joints, straps and things that have to move without catching. What do you need?','Годо работает с большими заготовками. Я занимаюсь сочленениями, ремнями и тем, что должно двигаться без заеданий. Чем помочь?'),[
 response('How do I fit the arm cannon?','Как установить руку-пушку?','TALK_BERSERK_RICKERT_ARM'),
 response('How do I keep the mechanism working?','Как следить за механизмом?','TALK_BERSERK_RICKERT_CARE'),
 response('What is it like working with Godot?','Каково работать рядом с Годо?','TALK_BERSERK_RICKERT_GODO'),
 response('Where may I leave supplies and rest?','Где оставить припасы и отдохнуть?','TALK_BERSERK_RICKERT_HOME'),
 response('Thank you.','Спасибо.','TALK_DONE')
],speaker_effect={'effect':run('EOC_BERSERK_GODO_BEGIN')})
topic('TALK_BERSERK_RICKERT_ARM',line('Keep the finished cannon in your pack and activate it there. The left-hand stump mount must be empty. You can fasten it with your remaining hand; no electricity is involved. Bring the metal to Godot if you cannot make the mechanism yourself.',
 'Держи готовую пушку в рюкзаке и активируй её оттуда. Крепление на месте левой кисти должно быть свободным. Закрепить пушку можно оставшейся рукой, электричество не требуется. Если не можешь изготовить механизм сам, принеси металл Годо.'),[
 response('What if I already have a cannon?','А если пушка уже есть?','TALK_BERSERK_RICKERT_CARE'),back('TALK_BERSERK_RICKERT')])
topic('TALK_BERSERK_RICKERT_CARE',line('Keep grit out of the hinge and replace straps before they split. Godot can repair a loose cannon or blade you carry. An installed cannon is a different job; I will not ask you to tear it off just to collect another one.',
 'Не допускай песка в шарнир и меняй ремни, прежде чем они лопнут. Годо может починить принесённую пушку или клинок. Установленная пушка — другое дело; ради второго экземпляра срывать её с руки не нужно.'),[back('TALK_BERSERK_RICKERT')])
topic('TALK_BERSERK_RICKERT_GODO',line("He says little until the iron is ready. Then one bad joint can earn more words than a whole day at the fire. Listen when he talks about coming home. The things we make are for people who still have somewhere to return.",'Он молчит, пока железо не готово. А потом один плохой шарнир может вызвать больше слов, чем целый день у горна. Послушай, когда он заговорит о возвращении домой. Мы делаем вещи для людей, у которых ещё есть куда вернуться.'),[back('TALK_BERSERK_RICKERT')])
topic('TALK_BERSERK_RICKERT_HOME',line('The stair leads to the sleeping loft. The forge and working tools stay below. Do not pile supplies across the stair, and keep a way to the door if your Brand wakes you at night.',
 'Лестница ведёт на спальный чердак. Кузница и рабочие инструменты остаются внизу. Не складывай припасы на лестнице и оставь путь к двери, если Клеймо разбудит тебя ночью.'),[back('TALK_BERSERK_RICKERT')])

# A player-held book uses native topic menus, never a chain of Yes/No windows.
effects.append(eoc('BOOK',{'open_dialogue':{'topic':'TALK_BERSERK_ROAD_JOURNAL'}}))
from rickert_content import apply_rickert
apply_rickert(effects, topics, missions, t, save)
from forge_story_content import apply_forge_story
apply_forge_story(effects, topics, t)
for row in effects:
 if row['id'].removeprefix('EOC_BERSERK_GODO_') in {
   'START_ARM','START_SWORD','ARM_METAL','ARM_FITTINGS','SWORD_IRON','SWORD_TEMPER',
   'ARM_CLAIM','SWORD_CLAIM','ARM_REFUND','SWORD_REFUND','REPAIR_PICK'
 }:
  owner = 'EOC_BERSERK_GODO_AT_RICKERT_FORGE' if row['id'].removeprefix('EOC_BERSERK_GODO_') in {
    'START_ARM','ARM_METAL','ARM_FITTINGS','ARM_CLAIM','ARM_REFUND'
  } else 'EOC_BERSERK_GODO_AT_SMITH'
  row['condition']=allof(call(owner),row['condition']) if 'condition' in row else call(owner)
save('effects/godo_eocs.json',effects)
save('dialogue/godo.json',topics)
save('missions/godo.json',missions)
save('items/godo_orders.json',[{
 'type':'ITEM','subtypes':['TOOL'],'id':'berserk_godo_order_book','category':'tools',
 'name':{'str':t("Godot's order notes",'записи о заказах у Годо')},
 'description':t('Directions to the woodland forge and materials for Rickert and Godot: a prosthesis from the engineer, a blade from the smith. Read to choose a road or review an order.','Дорога к лесной кузнице и материалы для Рикерта и Годо: протез у механика, клинок у кузнеца. Прочитайте, чтобы выбрать путь или проверить заказ.'),
 'material':['paper'],'weight':'25 g','volume':'50 ml','symbol':'?','color':'brown','charges_per_use':0,
 'flags':['ALLOWS_REMOTE_USE'],'use_action':{'type':'effect_on_conditions','need_wielding':False,'effect_on_conditions':['EOC_BERSERK_GODO_BOOK']}
}])
monsters=[]
for id,name,ru_name,symbol,desc,ru_desc,chat in [
 ('mon_berserk_godo','Godot','Годо','G','An old smith at his woodland forge. His tools are worn from honest work; his gaze measures metal before it measures a traveler.','Старый кузнец в лесной мастерской. Его инструменты потёрты долгой работой; он оценивает металл прежде, чем пришедшего путника.','TALK_BERSERK_GODO_ENTER'),
 ('mon_berserk_rickert','Rickert','Рикерт','R','A young craftsman helping Godot with mechanisms and fittings. He survived outside the Eclipse and now works beside the smith.','Молодой мастер помогает Годо с механизмами и креплениями. Он пережил события вне Затмения и теперь работает рядом с кузнецом.','TALK_BERSERK_RICKERT')]:
    monsters.append({'type':'MONSTER','id':id,'name':{'str_sp':t(name,ru_name)},'description':t(desc,ru_desc),
      'default_faction':'player','bodytype':'human','species':['HUMAN'],'material':['hflesh'],
      'volume':'70 L','weight':'70 kg','hp':150,'speed':100,'symbol':symbol,'color':'brown',
      'aggression':-100,'aggro_character':False,'morale':100,'melee_dice':0,'melee_dice_sides':0,
      'vision_day':30,'vision_night':12,'chat_topics':['TALK_BERSERK_RICKERT_LEGACY' if id=='mon_berserk_rickert' else chat],
      'flags':['SEES','HEARS','WARM','CONVERSATION','IMMOBILE','PACIFIST'],'looks_like':'mon_civilian_stationary'})
save('monsters/godo.json',monsters)
overmap=[]
for id,en,ru in [('berserk_godo_workshop',"Godot's woodland forge",'лесная кузница Годо'),('berserk_godo_loft',"Godot's sleeping loft",'спальный чердак Годо'),('berserk_godo_roof',"Godot's roof",'крыша дома Годо')]:
 overmap.append({'type':'overmap_terrain','id':id,'name':t(en,ru),'sym':'G','color':'brown','see_cost':'high','travel_cost_type':'forest','flags':['NO_ROTATE']})
overmap.append({'type':'overmap_special','id':'berserk_godo_workshop_special','occurrences':[20,100],
 'flags':['GLOBALLY_UNIQUE'],'rotate':False,'overmaps':[
 {'point':[0,0,0],'overmap':'berserk_godo_workshop','locations':['forest']},
 {'point':[0,0,1],'overmap':'berserk_godo_loft','locations':['open_air']},
 {'point':[0,0,2],'overmap':'berserk_godo_roof','locations':['open_air']} ]})
save('overmap/godo_workshop.json',overmap)

# Exact project rows are saved; changes to architecture must change this project too.
grid=[['.']*24 for _ in range(24)]
for y in range(4,21):
 for x in range(4,20):grid[y][x]='#' if x in (4,19) or y in (4,20) else ','
for x,y in [(4,15),(4,16),(19,15),(19,16)]:grid[y][x]='D'
for x,y in [(8,4),(9,4),(16,4),(17,4),(4,7),(4,8),(19,7),(19,8)]:grid[y][x]='w'
for y in range(3,22):
 for x in range(0,24):
  if grid[y][x]=='.' and (y in (15,16) or (x in (2,3,20,21) and y>=12)):grid[y][x]='p'
for x,y in [(1,2),(2,3),(21,2),(22,4),(1,8),(22,10),(0,20),(2,22),(21,22),(23,18)]:grid[y][x]='T'
furniture={'F':'f_forge','A':'f_anvil','b':'f_workbench','r':'f_rack_wood','c':'f_crate_c','s':'f_straw_bed','t':'f_table','h':'f_chair','k':'f_fireplace_stone'}
for x,y,char in [(17,6,'F'),(14,8,'A'),(16,11,'b'),(17,11,'b'),(6,6,'r'),(7,6,'r'),(6,18,'c'),(7,18,'c'),(16,18,'c')]:grid[y][x]=char
grid[18][11]='<'
ground=[''.join(row) for row in grid]
loft=[['.']*24 for _ in range(24)]
for y in range(4,21):
 for x in range(4,20):loft[y][x]='#' if x in (4,19) or y in (4,20) else ','
for y in range(5,20):loft[y][12]='#'
loft[13][12]='D'
for x,y in [(8,4),(9,4),(16,4),(17,4),(4,8),(19,8)]:loft[y][x]='w'
for x,y,char in [(6,7,'s'),(7,7,'s'),(15,7,'s'),(16,7,'s'),(6,10,'r'),(15,10,'r'),(6,17,'c'),(16,17,'c'),(8,13,'t'),(8,14,'h'),(17,18,'k')]:loft[y][x]=char
loft[18][11]='>'
upper=[''.join(row) for row in loft]
terrain={'.':'t_grass','p':'t_dirt','#':'t_wall_wood','D':'t_door_c','w':'t_window','T':'t_tree',',':'t_floor','<':'t_stairs_up','>':'t_stairs_down'}
for char in furniture:terrain[char]='t_floor'
mapgen=[]
for id,rows,is_ground in [('berserk_godo_workshop',ground,True),('berserk_godo_loft',upper,False)]:
 mapping=dict(terrain)
 if not is_ground:mapping['.']='t_open_air'
 obj={'fill_ter':'t_grass' if is_ground else 't_open_air','rows':rows,'terrain':mapping,'furniture':furniture}
 if is_ground:
  obj['place_monster']=[{'monster':'mon_berserk_godo','x':12,'y':9,'chance':100}]
  obj['place_npcs']=[{'class':'berserk_rickert','x':15,'y':12,'unique_id':'BERSERK_RICKERT'}]
  obj['place_item']=[{'item':id,'x':x,'y':y,'amount':1} for id,x,y in [('hammer',16,11),('metalworking_tongs',17,11),('swage',16,11),('hotcut',17,11),('metal_file',17,11),('clay_pot',6,18),('waterskin',7,18)]]
  obj['place_item'] += [{'item':'charcoal','x':16,'y':18,'amount':150}]
 else:
  obj['place_item']=[{'item':id,'x':x,'y':y,'amount':1} for id,x,y in [('fur_blanket',6,7),('fur_blanket',15,7),('pillow',7,7),('pillow',16,7),('clay_pot',8,13)]]
 mapgen.append({'type':'mapgen','om_terrain':id,'method':'json','object':obj})
roof=[['.']*24 for _ in range(24)]
for y in range(4,21):
 for x in range(4,20):roof[y][x]='^'
mapgen.append({'type':'mapgen','om_terrain':'berserk_godo_roof','method':'json',
 'object':{'fill_ter':'t_open_air','rows':[''.join(row) for row in roof],
           'terrain':{'.':'t_open_air','^':'t_wood_roof'}}})
save('mapgen/godo_workshop.json',mapgen)
project={'format':'berserk-location-design','version':'godo-3.2-01','size':[24,24],
 'floors':{'ground':ground,'loft':upper},'terrain':terrain,'furniture':furniture,
 'anchors':{'godo':[12,9,0],'rickert':[15,12,0],'stairs':[11,18,0],'west_exit':[4,15,0],'east_exit':[19,15,0],
            'rescue_arrival':[9,14,0],'knight_wait':[2,15,0]},
 'note':'This is the saved workshop project, not an import format for an unspecified map editor. Ground plan and loft share continuous orthogonal walls; no diagonally joined wall outlines.'}
(ROOT/'docs/location_projects').mkdir(exist_ok=True)
(ROOT/'docs/location_projects/godo-3.2-01.json').write_text(json.dumps(project,ensure_ascii=False,indent=2)+'\n')
(ROOT/'tools/godo_32_ru.json').write_text(json.dumps(RU,ensure_ascii=False,indent=2)+'\n')
print('Built Godot orders, dialogue, missions, forge and loft.')
