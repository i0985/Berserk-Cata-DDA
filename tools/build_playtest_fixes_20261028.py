#!/usr/bin/env python3
"""28 October owner playtest: native actor scopes, maps and readable progression."""
import copy,json
from recover_apostol_33 import ROOT,MOD,read,write,index,eoc,walk
from reference_journal_content_33 import math,allof as both,anyof as either,no as neg,eq,test
from build_playtest_fixes_20261024 import tr,localize,append_once
from build_playtest_fixes_20261025 import chapel
P='EOC_BERSERK_FIX28_'; E=[]
def run(s,**kw):return {'run_eocs':s,**kw}
def msg(en,ru,kind='info',popup=False):return {'u_message':tr(en,ru),'type':kind,'popup':popup}
def edit(file,fn):
 data=read(file);fn(data,index(data));write(file,data)

def attacks():
 # leap_actor constructs (monster, nullptr); spell/melee actors may have beta.
 # Never access a target before native has_beta short-circuits the condition.
 for path in (MOD/'monsters').glob('*.json'):
  data=json.loads(path.read_text());changed=False
  for o in (data if isinstance(data,list) else [data]):
   for attack in o.get('special_attacks',[]):
    if not isinstance(attack,dict):continue
    for node in walk(attack.get('condition',{})):
     if isinstance(node.get('and'),list) and 'npc_is_avatar' in node['and'] and node['and'][0]!='has_beta':
      node['and'].insert(0,'has_beta');changed=True
  if changed:write(str(path.relative_to(MOD)),data)
 # Invalid terrain is evaluated by prisoner gate checks even during greeting.
 def gates(data,by):
  for node in walk(data):
   if node.get('map_terrain_id')=='t_rubble':node['map_terrain_id']='t_dirt'
 edit('effects/count_prisoner_33_eocs.json',gates)
 # A refusal/betrayal releases the whole local household, including old actors.
 for k in ['COUNT','WYALD','ROSINE','GRUNBELD']:
  sp='BERSERK_'+k+'_PAWN_HOUSEHOLD'; prefix='EOC_BERSERK_APOSTOL_'+k+'_PAWN_'
  E.append(eoc(P+k+'_ALERT',[{'u_lose_effect':'berserk_apostol_parley'},math("u_val('anger') = 100"),math("u_val('morale') = 100")],both('u_is_monster',{'u_has_species':sp})))
  E.append(eoc(P+k+'_RELEASE',{'u_run_monster_eocs':[P+k+'_ALERT'],'mtype_ids':[],'monster_range':45},both('u_is_avatar',eq('berserk_apostol_'+k.lower()+'_pawn_encounter',2))))
  def release(data,by):
   for suffix in ['REFUSE','BETRAY']:append_once(by[prefix+suffix],run(P+k+'_RELEASE'))
  edit('effects/apostol_pawn_eocs.json',release)
 # Count should meet the stairs rather than wander into the blind corner.
 def count(data,by):
  for o in data:
   if o.get('om_terrain')==['berserk_count_dungeon']:
    for spawn in o['object'].get('place_monster',[]):
     if spawn['monster']=='mon_berserk_apostle_count':spawn.update(x=12,y=18)
 edit('mapgen/apostle_count.json',count)
 # Restore aggression once for surviving old Count actors when combat is active.
 E.append(eoc(P+'COUNT_COMBAT_FIX',run(P+'COUNT_RELEASE'),both('u_is_avatar',{'u_at_om_location':'berserk_count_dungeon'},eq('berserk_apostol_count_pawn_encounter',2),neg(eq('u_berserk_count_alert28')))))
 # Mark only after the actor scan; no spawning or resurrection.
 append_once(E[-1],math('u_berserk_count_alert28 = 1'))

def geography():
 group='GROUP_BERSERK_STORY_PLACEMENT_BUFFER'
 for file in ['first_hunt','local_breach','apostle_count','wyald_rosine_hunts','grunbeld_hunt']:
  data=read('overmap/'+file+'.json')
  for o in data:
   if o.get('type')!='overmap_special':continue
   flags=o.setdefault('flags',[])
   for f in ['SAFE_AT_WORLDGEN','GLOBALLY_UNIQUE']:
    if f not in flags:flags.append(f)
   radius=48 if file in ['first_hunt','local_breach'] else 104
   o['spawns']={'group':group,'population':[0,0],'radius':[radius,radius]}
   o['city_distance']=[10,-1]
  write('overmap/'+file+'.json',data)
 for file in ['effects/playtest_fixes_20261024_eocs.json','effects/local_breach_eocs.json','effects/apostle_hunt_eocs.json','effects/wyald_rosine_hunt_eocs.json','effects/grunbeld_hunt_eocs.json']:
  data=read(file)
  for node in walk(data):
   params=node.get('target_params')
   if not params:continue
   if params.get('om_terrain') in ['berserk_first_hunt_lair','berserk_local_breach']:params.update(search_range=96,min_distance=0)
   elif params.get('om_terrain') in ['berserk_count_hall','berserk_wyald_ring','berserk_rosine_nest','berserk_grunbeld_crucible']:params.update(search_range=208,min_distance=0)
  write(file,data)
 # Natural small encounters: forest, outside city limits; no visible highway.
 data=read('overmap/road_stories.json')
 for o in data:
  if o.get('type')=='overmap_special':
   o['locations']=['forest'];o['city_distance']=[10,-1];o['occurrences']=[4,100]
 write('overmap/road_stories.json',data)
 # Approved saved geometry is the export source; never redraw on rebuild.
 project=json.loads((ROOT/'docs/location_projects/road-stories-3.3-01.json').read_text())
 write('mapgen/road_stories.json',project['maps'])

def chapel_and_prison():
 # Export the saved project; later approved cell edits must survive rebuilds.
 chapel('chapel-3.3-03.json')
 data=read('furniture/chapel_layout_version.json');data.append({'type':'furniture','id':'f_berserk_chapel_record_v3','copy-from':'f_berserk_chapel_record_v2','looks_like':'f_berserk_chapel_record_v2'});write('furniture/chapel_layout_version.json',data)
 def altar(data,by):
  for id_ in ['f_berserk_chapel_relic','f_berserk_chapel_relic_empty']:
   by[id_]['looks_like']='f_table';by[id_]['move_cost_mod']=-1
  by['f_berserk_chapel_relic'].update(name=tr('altar with a red stone','алтарь с красным камнем'),description=tr('A red stone with a human face rests in a shallow recess on the stone altar.','В неглубокой выемке каменного алтаря лежит красный камень с человеческим лицом.'))
 edit('furniture/behelit_sites.json',altar)
 def details(data,by):
  by['f_berserk_chapel_altar']['looks_like']='f_table'
  by['f_berserk_chapel_altar']['description']=tr('Black wax coats the altar. Beneath a torn cloth, old carvings have been gouged out.','Алтарь покрыт чёрным воском. Под разорванной тканью видны выскобленные старые изображения.')
 edit('furniture/behelit_adventure_details.json',details)
 edit('effects/location_interactions_eocs.json',lambda d,b:b['EOC_BERSERK_READ_CHAPEL_RITUAL_NOTE']['effect'][0].update(u_message=tr('We called the stone a miracle because we needed one. We laid it on the altar and barred the doors. Then the whispering began. By morning, nobody dared take it away.','Мы назвали камень чудом, потому что нуждались в чуде. Положили его на алтарь и заперли двери. Потом начался шёпот. К утру никто уже не решался его унести.')))
 edit('effects/location_scenery_eocs.json',lambda d,b:b['EOC_BERSERK_SCENERY_CHAPEL']['effect'][0].update(u_message=tr('Names have been scraped from the memorial. Old words offering shelter remain beneath the damage. Black wax covers the altar; the books in the sacristy still bear their donors\' names.','Имена на памятной плите выскоблены. Под повреждениями сохранились старые слова о приюте для путников. Алтарь залит чёрным воском; в книгах ризницы ещё можно прочесть имена дарителей.')))
 # The screenshot shows the southwest entrance to the stair room, not the cell.
 data=read('mapgen/apostle_count.json')
 for o in data:
  if o.get('om_terrain') not in [['berserk_count_prison'],['berserk_count_hall']]:continue
  body=o['object'];rr=body['rows'];gates=[]
  for y,row in enumerate(rr):
   for x,char in enumerate(row):
    if char=='+':gates.append({'point':'terrain','id':'t_door_bar_locked','x':x,'y':y})
  body['set']=[s for s in body.get('set',[]) if s not in gates]+gates
 write('mapgen/apostle_count.json',data)

def behelits():
 own=either({'u_has_item':'berserk_behelit'},{'u_has_item':'berserk_behelit_distorted'})
 def change(data,by):
  available=by['EOC_BERSERK_BEHELIT_AVAILABLE'];available['condition']=available['condition'] if neg(own) in list(walk(available['condition'])) else both(available['condition'],neg(own))
  claim=by['EOC_BERSERK_BEHELIT_SITE_CLAIM'];claim['effect']=claim['effect'] if claim['effect'].get('if')==own else {'if':own,'then':msg('The stone you carry stirs. Leave this one where it rests.','Камень, который вы несёте, шевелится. Этот лучше оставить на месте.'),'else':claim['effect']}
 edit('effects/behelit_reward_eocs.json',change)
 # A paper in the forge offers one saved route, not another campaign controller.
 E.append(eoc(P+'BEHELIT_LEAD_READ',[
  msg('An old woodland sketch marks a place the writer feared to approach. The turns are clear enough to follow.','На старом лесном наброске отмечено место, к которому автор боялся приближаться. Повороты обозначены достаточно ясно.'),
  {'if':eq('u_berserk_forge_behelit_choice',0),'then':{'weighted_list_eocs':[[P+'LEAD_OAK',1],[P+'LEAD_CAVE',1]]}},
  {'if':eq('u_berserk_forge_behelit_choice',1),'then':run(P+'FIND_OAK'),'else':run(P+'FIND_CAVE')}],both('u_is_avatar',eq('berserk_eclipse_era',0))))
 for key,number,terrain,special in [('OAK',1,'berserk_cursed_oak','berserk_cursed_oak_special'),('CAVE',2,'berserk_echo_cave_entrance','berserk_echo_cave_special')]:
  E.append(eoc(P+'LEAD_'+key,math('u_berserk_forge_behelit_choice = '+str(number))))
  E.append(eoc(P+'FIND_'+key,{'u_location_variable':{'u_val':'berserk_forge_behelit_route'},'target_params':{'om_terrain':terrain,'om_special':special,'random':False,'z':0},'true_eocs':[P+'LEAD_FOUND'],'false_eocs':[P+'LEAD_FAILED']},'u_is_avatar'))
 E.append(eoc(P+'LEAD_FOUND',[{'reveal_map':{'u_val':'berserk_forge_behelit_route'},'radius':2},
  {'if':neg(eq('u_berserk_stone_route_issued')),'then':[{'assign_mission':'MISSION_BERSERK_WOODLAND_STONE'},math('u_berserk_stone_route_issued = 1')]}],'u_is_avatar'))
 E.append(eoc(P+'LEAD_FAILED',msg('The sketch is saved, but you cannot yet establish the route.','Набросок сохранён, но дорогу пока установить не удалось.')))
 write('missions/woodland_stone.json',[{'type':'mission_definition','id':'MISSION_BERSERK_WOODLAND_STONE','name':tr('The place on the woodland sketch','Место на лесном наброске'),'description':tr('Reach the place marked on the old sketch and examine it.','Доберитесь до места на старом наброске и осмотрите его.'),'goal':'MGOAL_GO_TO','difficulty':2,'value':0,'start':{'assign_mission_target':{'om_terrain':'forest','var':{'u_val':'berserk_forge_behelit_route'},'reveal_radius':2}},'origins':['ORIGIN_SECONDARY']}])
 write('items/forge_woodland_leads.json',[{'type':'GENERIC','id':'berserk_forge_woodland_sketch','name':{'str':tr('old woodland sketch','старый лесной набросок')},'description':tr('A folded sketch of an unsettling place in the woods. Read the directions before setting out.','Сложенный набросок тревожного места в лесу. Перед дорогой стоит прочитать указания.'),'weight':'5 g','volume':'1 ml','symbol':'?','color':'brown','material':['paper'],'use_action':{'type':'effect_on_conditions','effect_on_conditions':[P+'BEHELIT_LEAD_READ']}}])
 def talk(data,by):
  root=by['TALK_BERSERK_GODO'];root['responses'][:]=[r for r in root['responses'] if r.get('topic')!='TALK_BERSERK_FIX28_GODO_SKETCH'];root['responses'].insert(-1,{'text':tr('Have you heard of anything strange in these woods?','Ты слышал о странных местах в этих лесах?'),'topic':'TALK_BERSERK_FIX28_GODO_SKETCH','condition':both(eq('berserk_eclipse_era',0),neg(own))})
  data[:]=[o for o in data if o.get('id')!='TALK_BERSERK_FIX28_GODO_SKETCH'];data.append({'type':'talk_topic','id':'TALK_BERSERK_FIX28_GODO_SKETCH','dynamic_line':tr('People leave all kinds of nonsense with their orders. Someone drew this and never returned for it. Take it if you must. I would spend the daylight on a sound blade.','С заказами всякую дурь оставляют. Кто-то нарисовал это и больше не вернулся. Забирай, если надо. Я бы лучше потратил светлый день на хороший клинок.'),'responses':[{'text':tr('Read the directions here.','Прочитать указания здесь.'),'topic':'TALK_BERSERK_GODO','effect':run(P+'BEHELIT_LEAD_READ')},{'text':tr('Take the sketch with me.','Взять набросок с собой.'),'topic':'TALK_BERSERK_GODO','condition':neg(eq('u_berserk_forge_sketch_given')),'effect':[{'if':neg(eq('u_berserk_forge_sketch_given')),'then':[{'u_spawn_item':'berserk_forge_woodland_sketch'},math('u_berserk_forge_sketch_given = 1')]}]}]})
 edit('dialogue/godo.json',talk)
 # Additional access at vanilla shelters keeps rare forest sites optional.
 E.append(eoc(P+'SHELTER_NOTICE',[{'u_spawn_item':'berserk_road_caravan_note'},math('u_berserk_smith_notice28 = 1'),msg('Among the surviving papers is an order for a woodland smith. You keep it to read before leaving.','Среди уцелевших бумаг нашёлся заказ лесному кузнецу. Вы оставляете его себе, чтобы прочитать перед дорогой.')],both('u_is_avatar',either(*[{'u_at_om_location':t} for t in ["shelter","shelter_vandal","shelter_unfinished","shelter_survivor","shelter_1","shelter_1_vandal","shelter_1_unfinished","shelter_1_survivor","shelter_1b","shelter_1b_vandal","shelter_1b_unfinished","shelter_1b_survivor","shelter_2","shelter_2_vandal","shelter_2_unfinished","shelter_2_survivor"]]),eq('berserk_eclipse_era',0),neg(eq('u_berserk_smith_notice28')),neg(eq('u_berserk_journal_knows_godo')))))

def bodies():
 import gettext
 ru=gettext.GNUTranslations(open(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo','rb'))
 specs={('count','pawn'):(4,7,4),('rosine','pawn'):(3,6,4),('wyald','pawn'):(2,4,2),('grunbeld','pawn'):(6,10,6),('count','flesh'):(10,14,8),('rosine','flesh'):(4,8,5),('wyald','flesh'):(4,7,4),('grunbeld','flesh'):(12,18,12)}
 descriptions={
 ('count','pawn'):('Heavy pliant flesh cushions blows: bash 4, cut 7, stab 4. Strength +2. Your slower movement and rigid torso armor restriction remain.','Тяжёлая податливая плоть смягчает удары: дробящий 4, режущий 7, колющий 4. Сила +2. Сохраняются замедление и ограничение жёсткой брони на торсе.'),
 ('rosine','pawn'):('Chitin protects your body: bash 3, cut 6, stab 4. Dexterity +2, speed +12. Fragile joints and difficulties with speech and crafting remain. Rigid helmets and gloves no longer fit.','Хитин защищает тело: дробящий 3, режущий 6, колющий 4. Ловкость +2, скорость +12. Суставы уязвимы; речь и ремесло затруднены. Жёсткие шлемы и перчатки больше не подходят.'),
 ('wyald','pawn'):('Dense hide protects you: bash 2, cut 4, stab 2. Strength +3 and melee damage +15%. Dexterity -2; stamina still recovers slowly. Rigid gloves and footwear do not fit.','Плотная шкура защищает тело: дробящий 2, режущий 4, колющий 2. Сила +3, урон в ближнем бою +15%. Ловкость -2; выносливость по-прежнему восстанавливается медленно. Жёсткие перчатки и обувь не подходят.'),
 ('grunbeld','pawn'):('A heavy shell protects your body: bash 6, cut 10, stab 6; heat damage is reduced by 25%. Strength +2. Slow movement, increased hunger and rigid armor restrictions remain.','Тяжёлый панцирь защищает тело: дробящий 6, режущий 10, колющий 6; урон от жара снижен на 25%. Сила +2. Сохраняются медлительность, повышенный голод и ограничения жёсткой брони.'),
 ('count','flesh'):('Thick pliant flesh protects you: bash 10, cut 14, stab 8. Strength +4; movement remains slower. Rigid torso and arm armor no longer fits. Use Draw flesh together to mend wounds.','Толстая податливая плоть защищает тело: дробящий 10, режущий 14, колющий 8. Сила +4; движение остаётся медленным. Жёсткая броня торса и рук не подходит. Способность «Стянуть плоть» позволяет залечивать раны.')}
 descriptions.update({
 ('wyald','flesh'):('A beastlike body grants strength +4, melee damage +15% and dexterity -2. Thick hide protects against bash 4, cut 7 and stab 4. Stamina still recovers slowly; rigid gloves and footwear do not fit.','Звериное тело даёт +4 силы, +15% урона в ближнем бою и -2 ловкости. Шкура защищает от дробящего урона на 4, режущего на 7 и колющего на 4. Выносливость восстанавливается медленно; жёсткие перчатки и обувь не подходят.'),
 ('rosine','flesh'):('Wings grant dexterity +2, speed +15 and halve falling damage. Chitin protects against bash 4, cut 8 and stab 5. Short flights require torso encumbrance no greater than 20. Your fragile tissues remain; rigid head, torso and hand armor does not fit.','Крылья дают +2 ловкости, +15 скорости и вдвое снижают урон от падения. Хитин защищает от дробящего урона на 4, режущего на 8 и колющего на 5. Для коротких перелётов скованность торса должна быть не выше 20. Ткани остаются хрупкими; жёсткая броня головы, торса и кистей не подходит.'),
 ('grunbeld','flesh'):('A fiery carapace grants strength +3 and protects against bash 12, cut 18 and stab 12. Heat damage is halved. Speed -15; hunger and slow recovery remain. Ordinary rigid armor no longer fits the shell. Fire is still dangerous.','Огненный панцирь даёт +3 силы и защищает от дробящего урона на 12, режущего на 18 и колющего на 12. Урон от жара снижен вдвое. Скорость -15; повышенный голод и медленное восстановление сохраняются. Обычная жёсткая броня не подходит к панцирю. Огонь всё ещё опасен.')})
 for (k,line),armor in specs.items():
  file='mutations/apostol_'+k+'_'+line+'.json';data=read(file);form=index(data)['BERSERK_'+k.upper()+'_'+line.upper()+'_FORM']
  form['armor']=[{'parts':['head','eyes','mouth','torso','arm_l','arm_r','hand_l','hand_r','leg_l','leg_r','foot_l','foot_r'],'bash':armor[0],'cut':armor[1],'stab':armor[2]}]
  vals=form['enchantments'][0]['values'];vals[:]=[v for v in vals if v['value']!='ARMOR_ALL']
  for v in vals:
   if v['value']=='STRENGTH':v['add']={'count':4 if line=='flesh' else 2,'wyald':4 if line=='flesh' else 3,'grunbeld':3 if line=='flesh' else 2}.get(k,v.get('add',0))
   if (k,line)==('rosine','pawn') and v['value'] in ['DEXTERITY','SPEED']:v['add']=2 if v['value']=='DEXTERITY' else 12
  if (k,line)==('wyald','pawn') and not any(v['value']=='MELEE_DAMAGE' for v in vals):vals.append({'value':'MELEE_DAMAGE','multiply':0.15})
  if (k,line) in descriptions:form['description']=tr(*descriptions[k,line])
  else:
   # Retain the existing strengths and limitations; replace obsolete armor text.
   en=form['description'].split('\n\n')[0].split(' Natural protection:')[0]+f' Natural protection: bash {armor[0]}, cut {armor[1]}, stab {armor[2]}.'
   form['description']=tr(en,ru.gettext(form['description']).split('\n\n')[0]+f' Естественная защита: дробящий {armor[0]}, режущий {armor[1]}, колющий {armor[2]}.')
  write(file,data)
 # Native add_trait does not announce mutation gain. Report each real addition,
 # including old interrupted growth, with no replay on sync/load.
 for file in ['effects/apostol_flesh_eocs.json','effects/apostol_pawn_eocs.json']:
  data=read(file)
  traits={o['id']:o for path in (MOD/'mutations').glob('apostol_*.json') for o in json.loads(path.read_text()) if o.get('type')=='mutation'}
  def change(node):
   if isinstance(node,list):return [change(x) for x in node]
   if not isinstance(node,dict):return node
   prior=node.get('if',{}).get('not',{}).get('u_has_trait') if isinstance(node.get('if'),dict) else None
   if prior in traits and isinstance(node.get('then'),list) and any(isinstance(v,dict) and v.get('u_message','').startswith('Your body changes:') for v in node['then']):
    return change({'u_add_trait':prior})
   trait=node.get('u_add_trait')
   if trait in traits and not trait.endswith(('LOYALTY','COMPANION_TRUCE')):
    name=traits[trait]['name'];name=name.get('str',name.get('str_sp','')) if isinstance(name,dict) else name
    return {'if':neg({'u_has_trait':trait}),'then':[node,msg('Your body changes: '+name+'.','Ваше тело меняется: '+ru.gettext(name)+'.','warning')]}
   return {key:change(value) for key,value in node.items()}
  write(file,change(data))

def flight():
 origin={'u_val':'berserk_apostol_flesh_dash_origin'};target={'context_val':'berserk_wing_landing'}
 def change(data,by):
  use=by['EOC_BERSERK_APOSTOL_ROSINE_FLESH_DIVE_USE'];then=use['effect'][0]['then']
  condition=use['effect'][0]['if']
  use['effect'][0]['then']=[{'u_location_variable':origin},{'copy_var':origin,'target_var':target},
   {'u_query_tile':'anywhere','target_var':target,'z_level':True},run(P+'WING_CHECK')]
  # Result still handles actual movement costs, impact and cooldown.
  result=by['EOC_BERSERK_APOSTOL_ROSINE_FLESH_DIVE_RESULT']
  E.append(eoc(P+'WING_LAND',[
   {'u_teleport':target,'force_safe':False,'fail_message':tr('There is no room to land there.','Там негде приземлиться.')},
   {'if':both(math("u_val('pos_x') == _berserk_wing_landing.x"),math("u_val('pos_y') == _berserk_wing_landing.y"),math("u_val('pos_z') == _berserk_wing_landing.z")),
    'then':[math('u_berserk_apostol_cast_confirmed = 1'),run(result['id'])]}],
   both(condition,math('distance(u_berserk_apostol_flesh_dash_origin, _berserk_wing_landing) > 0'),
    math('distance(u_berserk_apostol_flesh_dash_origin, _berserk_wing_landing) <= 7'),
    math('_berserk_wing_landing.z <= u_berserk_apostol_flesh_dash_origin.z'),math('_berserk_wing_landing.z >= u_berserk_apostol_flesh_dash_origin.z - 1'),
    {'map_terrain_with_flag':'FLAT','loc':target},neg({'map_terrain_with_flag':'NO_FLOOR','loc':target}),
    {'line_of_sight':8,'loc_1':origin,'loc_2':target,'with_fields':False})))
 # Check each segment against transparent walls/windows too; LOS alone
 # allows glass. Teleport is safe without force/force_safe relocation.
 edit('effects/apostol_flesh_eocs.json',change)
 land=E[-1]
 extra=[{'u_can_see_location':target}]
 setup=[]
 for i in range(1,8):
  point={'context_val':'berserk_wing_path_'+str(i)}
  setup.append({'copy_var':origin,'target_var':point})
  for a in 'xyz':setup.append(math('_berserk_wing_path_'+str(i)+'.'+a+' = u_berserk_apostol_flesh_dash_origin.'+a+' + floor((_berserk_wing_landing.'+a+' - u_berserk_apostol_flesh_dash_origin.'+a+') * '+str(i)+' / 7 + 0.5)'))
  for flag in ['WALL','WINDOW','DOOR']:
   extra.append(neg({'map_terrain_with_flag':flag,'loc':point}))
 land['condition']=both(land['condition'],*extra)
 E.append(eoc(P+'WING_CHECK',setup+[{'if':math('distance(u_berserk_apostol_flesh_dash_origin, _berserk_wing_landing) > 0'),'then':{'if':test(P+'WING_LAND'),'then':run(P+'WING_LAND'),'else':msg('You cannot reach a clear landing place that way.','Так не добраться до свободного места посадки.')}}],'u_is_avatar'))
 def desc(data,by):by['BERSERK_ROSINE_FLESH_DIVE']['description']=tr('Fly up to 7 tiles to a visible landing place, staying at the same height or descending one level. Walls and occupied landing places stop you. Costs 1500 stamina; recovers in 20 seconds. This is a short flight, not hovering.','Перелетите до 7 клеток к видимому месту посадки на той же высоте или на один уровень ниже. Стены и занятая посадочная клетка помешают. Стоимость: 1500 выносливости; восстановление 20 секунд. Это короткий перелёт, а не зависание.')
 edit('mutations/apostol_rosine_flesh.json',desc)

def narrative():
 def knight(data,by):
  for o in data:
   for r in o.get('responses',[]):
    if r.get('topic')=='TALK_BERSERK_SKULL_KNIGHT_MASTERS':
     r['condition']=both(r.get('condition','u_is_avatar'),neg(both(eq('u_berserk_godo_personally_met'),eq('u_berserk_rickert_met'))))
 edit('dialogue/skull_knight.json',knight)
 # An explicitly technical, anatomy-dependent reminder after the farewell.
 E.append(eoc(P+'INJURY_TIP',[
  {'if':{'u_has_bionics':'bio_berserk_hand_stump'},'then':msg('You lost your left hand. Rickert can make a prosthesis; this is a good first step before another hunt. Read the injury and prosthesis descriptions in the Bionics menu.','Вы лишились левой кисти. Рикерт может изготовить протез — лучше заняться этим перед следующей охотой. Описание травмы и протеза доступно во вкладке «Бионика».','info',True)},
  {'if':{'u_has_bionics':'bio_berserk_lost_eye'},'then':msg('Your lost eye also affects your sight. Its effects are described in the Bionics menu.','Потерянный глаз тоже влияет на зрение. Последствия описаны во вкладке «Бионика».')},math('u_berserk_injury_tip28 = 1')],both('u_is_avatar',neg(eq('u_berserk_injury_tip28')))))
 edit('effects/eclipse_aftermath_eocs.json',lambda d,b:append_once(b['EOC_BERSERK_KNIGHT_FAREWELL'],run(P+'INJURY_TIP')))
 # Rosine's promise remains alluring; the narrator carries the warning.
 def contracts(data,by):
  replacements={
   'TALK_BERSERK_APOSTOL_ROSINE_PAWN_CHANGE':('Here you will have wings and a place among us. You will not need those roads again. Stay, and I will show you.','Здесь у тебя будут крылья и место среди нас. Те дороги тебе больше не понадобятся. Останься — я покажу.'),
   'TALK_BERSERK_APOSTOL_ROSINE_PAWN_PRICE':('What price? You have already paid enough out there. Here you only need to stop running and let me help.','Какая ещё цена? Там ты уже достаточно заплатил. Здесь нужно только перестать убегать и позволить мне помочь.'),
   'TALK_BERSERK_APOSTOL_ROSINE_PAWN_LEAVE_MORE':('Beyond these trees there is only the same fear. Here you will always have a place.','За этими деревьями всё тот же страх. Здесь у тебя всегда будет дом.'),
   'TALK_BERSERK_APOSTOL_ROSINE_PAWN_LEAVE':('You can go where you like. But why return to a world that has never kept you safe?','Можешь идти куда захочешь. Но зачем возвращаться в мир, который никогда тебя не защищал?')}
  for id_,pair in replacements.items():
   if id_ in by:by[id_]['dynamic_line']=tr(*pair)
  for o in data:
   if 'ROSINE_PAWN' not in o['id']:continue
   for r in o.get('responses',[]):
    if r.get('topic')=='TALK_BERSERK_APOSTOL_ROSINE_PAWN_ACCEPTED':r['text']=tr('I will stay. Let me be one of you.','Я останусь. Позволь мне стать одним из вас.')
 edit('dialogue/apostol_contracts.json',contracts)
 # Narrated final confirmation is deliberately separate from the apostle's lie.
 def pact(data,by):
  for k in ['COUNT','WYALD','ROSINE','GRUNBELD']:
   for node in walk(by['EOC_BERSERK_APOSTOL_'+k+'_PAWN_ACCEPT']):
    if 'u_query' in node:node['u_query']=tr('The creatures nearby bear little resemblance to the people they once were. Whatever is offered, it will change your body forever. Accept?','Существа вокруг мало похожи на людей, которыми когда-то были. Что бы вам ни обещали, тело изменится навсегда. Согласиться?')
 edit('effects/apostol_pawn_eocs.json',pact)
 # The optional reference book keeps a copy of the physical source.
 def archive(data,by):
  for node in walk(data):
   for key,value in list(node.items()):
    if value=='The handprints on the altar were not left during prayer.\n\n':
     node[key]=tr('Black wax coats the altar; the old carvings have been gouged out.\n\n','Алтарь покрыт чёрным воском; старые изображения выскоблены.\n\n')
 edit('dialogue/road_journal.json',archive)
 # Put collection guidance in both the mission and the successful seal event.
 for file in ['effects/apostle_hunt_eocs.json','effects/wyald_rosine_hunt_eocs.json','effects/grunbeld_hunt_eocs.json','effects/local_breach_eocs.json']:
  data=read(file)
  for o in data:
   if o['id'].endswith(('SEAL_COMMIT','REGISTER_SEAL','SEAL_DONE')):
    append_once(o,msg('Something remains in the quieted scar. Examine it once more to recover it.','В затихшем рубце что-то осталось. Осмотрите его ещё раз, чтобы забрать находку.'))
  write(file,data)
 # Reveal a physical first-lair clue without requiring the paper inventory.
 edit('effects/first_hunt_eocs.json',lambda d,b:append_once(b['EOC_BERSERK_FIRST_HUNT_COMPLETE'],msg('A scorched scrap survived among the remains. Read it, or examine the trail in the lair, to learn where it leads.','Среди останков уцелел обгоревший клочок. Прочитайте его или осмотрите след в логове, чтобы узнать продолжение пути.')))

def old_chapel():
 north={'context_val':'chapel28_north'};south={'context_val':'chapel28_south'};plaque={'context_val':'chapel28_plaque'}
 actions=[{'u_location_variable':north},math('_chapel28_north.x = floor(_chapel28_north.x / 24) * 24'),math('_chapel28_north.y = floor(_chapel28_north.y / 24) * 24'),
  {'if':{'u_at_om_location':'berserk_desecrated_chapel_nave'},'then':{'location_variable_adjust':north,'y_adjust':-24}},
  {'copy_var':north,'target_var':south},{'location_variable_adjust':south,'y_adjust':24},
  {'copy_var':south,'target_var':plaque},{'location_variable_adjust':plaque,'x_adjust':12,'y_adjust':16}]
 checks=[{'map_furniture_id':'f_berserk_chapel_record_v2','loc':plaque}]
 steps=[{'point':'terrain','id':'t_wall','x':15,'y':13}]
 for i,(x,y) in enumerate([(15,13),(17,4),(18,4),(16,5),(16,6)]):
  v={'context_val':'chapel28_point_'+str(i)}
  actions += [{'copy_var':north,'target_var':v},{'location_variable_adjust':v,'x_adjust':x,'y_adjust':y}]
  checks += [{'map_terrain_id':'t_floor','loc':v},{'map_furniture_id':'f_null','loc':v}]
  if i==0:checks.append(either(math("u_val('pos_x') != _chapel28_point_0.x"),math("u_val('pos_y') != _chapel28_point_0.y")))
  else:steps.append({'point':'furniture','id':'f_bookcase','x':x,'y':y})
 actions += [{'if':both(*checks),'then':[{'mapgen_update':'berserk_chapel_owner28_north','target_var':north},run(P+'CHAPEL_MARK')]}]
 actual=[{'map_terrain_id':'t_wall','loc':{'context_val':'chapel28_point_0'}}]+[{'map_furniture_id':'f_bookcase','loc':{'context_val':'chapel28_point_'+str(i)}} for i in range(1,5)]
 E.append(eoc(P+'CHAPEL_MARK',{'mapgen_update':'berserk_chapel_owner28_mark','target_var':south},both(*actual)))
 E.append(eoc(P+'CHAPEL_UPGRADE',actions,both('u_is_avatar',either({'u_at_om_location':'berserk_desecrated_chapel_nave'},{'u_at_om_location':'berserk_desecrated_chapel_reliquary'}))))
 write('mapgen/chapel_owner28_upgrade.json',[{'type':'mapgen','update_mapgen_id':'berserk_chapel_owner28_north','object':{'set':steps}},
  {'type':'mapgen','update_mapgen_id':'berserk_chapel_owner28_mark','object':{'set':[{'point':'furniture','id':'f_berserk_chapel_record_v3','x':12,'y':16}]}}])


def main():
 attacks();geography();chapel_and_prison();behelits();bodies();flight();narrative();old_chapel()
 tick=[run(P+'COUNT_COMBAT_FIX'),run(P+'SHELTER_NOTICE'),run(P+'CHAPEL_UPGRADE')]
 E.append(eoc(P+'MOVE',tick,'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))
 write('effects/playtest_fixes_20261028_eocs.json',E);localize()
 print('28 October: actor-safe leaps, woodland sites, body armor, controlled flight and readable leads.')
if __name__=='__main__':main()
