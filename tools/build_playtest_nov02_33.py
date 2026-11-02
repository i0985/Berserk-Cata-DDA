#!/usr/bin/env python3
"""Owner's complete apostle-path playtest: bounded placement and tangible papers."""
import copy,json
from recover_apostol_33 import ROOT,MOD,read,write,index,walk,eoc
from build_playtest_fixes_20261024 import tr,localize
from reference_journal_content_33 import allof as both,anyof as either,no as neg,eq
P='EOC_BERSERK_NOV02_'
def run(n,**kw):return {'run_eocs':n,**kw}
def math(s):return {'math':[s]}
def edit(file,fn):
 rows=read(file);fn(rows,index(rows));write(file,rows)
def main():
 E=[]
 # Natural worldgen could place the unique forge a few tiles from any start.
 def forge(rows,by):
  s=by['berserk_godo_workshop_special'];s['occurrences']=[0,0];s['spawns']={'group':'GROUP_BERSERK_STORY_PLACEMENT_BUFFER','population':[0,0],'radius':[32,32]}
 edit('overmap/godo_workshop.json',forge)
 # A 104-OMT safety square was checked at every candidate; six adjacent forest
 # requirements made the final special particularly hard to place.
 for file in ['apostle_count','wyald_rosine_hunts','grunbeld_hunt']:
  rows=read('overmap/'+file+'.json')
  for s in rows:
   if s.get('type')!='overmap_special':continue
   n=48 if file=='grunbeld_hunt' else 64;s['spawns']['radius']=[n,n]
   if file=='grunbeld_hunt':
    s['locations']=['wilderness']
    for part in s['overmaps']:part['locations']=['wilderness']
  write('overmap/'+file+'.json',rows)
 # Exactly one native placement attempt per call, finite cooldown retries.
 rows=read('effects/grunbeld_hunt_eocs.json');by=index(rows);find=by['EOC_BERSERK_GRUNBELD_FIND']
 find['condition']=both(eq('berserk_eclipse_era'),either(eq('u_berserk_flora_escaped'),eq('berserk_flora_stage',3),eq('berserk_hunt_grunbeld_site_registered')),math("time('now') >= u_berserk_grunbeld_retry_at"),math('u_berserk_grunbeld_attempts02 < 3'))
 for node in walk(find):
  if 'target_params' in node:node['target_params']['search_range']=128
 # Earlier passes preserve FIND rather than rebuilding it. Replace only our
 # top-level preamble, including duplicates from an interrupted development run.
 preamble=[math("u_berserk_grunbeld_retry_at = time('now') + time('30 minutes')"),math('u_berserk_grunbeld_attempts02 = u_berserk_grunbeld_attempts02 + 1'),math('u_berserk_site_grunbeld_tries = 0')]
 find['effect']=preamble+[action for action in find['effect'] if action not in preamble]
 # Fresh bounded budget repairs old exhausted saves; once only.
 E.append(eoc(P+'GRUNBELD_MIGRATE',[math('u_berserk_site_grunbeld_tries = 0'),math('u_berserk_grunbeld_locator02 = 1')],both('u_is_avatar',neg(eq('u_berserk_grunbeld_locator02')),neg(eq('berserk_hunt_grunbeld_site_registered')))))
 # Reset legacy per-origin tries at each *permitted* attempt, not every step.
 write('effects/grunbeld_hunt_eocs.json',rows)
 edit('effects/hunt_site_placement_eocs.json',lambda rows,by:by['EOC_BERSERK_SITE_GRUNBELD_FAILED'].update(effect=run('EOC_BERSERK_SITE_GRUNBELD_MESSAGE')))
 E.append(eoc(P+'GRUNBELD_RETRY',[run(P+'GRUNBELD_MIGRATE'),run('EOC_BERSERK_GRUNBELD_SEEK')],both('u_is_avatar',eq('u_berserk_flora_escaped'),neg(eq('berserk_hunt_grunbeld_site_registered')),math("u_val('pos_z') == 0"),math("time('now') >= u_berserk_grunbeld_retry_at"),math('u_berserk_grunbeld_attempts02 < 3')),global_=False))
 E[-1].pop('global_',None);E[-1].update(**{'global':True,'recurrence':'1 minute'});E[-1]['effect'].insert(0,run(P+'GRUNBELD_NEW_AREA'))
 # A new area gets a fresh bounded budget; failed placement never strands a
 # traveller forever, and staying in place cannot trigger repeated generation.
 E.append(eoc(P+'GRUNBELD_NEW_AREA',[math('u_berserk_grunbeld_attempts02 = 0'),math('u_berserk_grunbeld_retry_at = 0'),math('u_berserk_site_grunbeld_tries = 0'),{'u_location_variable':{'u_val':'berserk_grunbeld_area02'}}],both('u_is_avatar',eq('u_berserk_flora_escaped'),neg(eq('berserk_hunt_grunbeld_site_registered')),math("u_val('pos_z') == 0"),either(math('has_var(u_berserk_grunbeld_area02) == 0'),math("distance('u', u_berserk_grunbeld_area02) >= 1152"))),**{'global':True,'recurrence':'1 minute'}))
 # No broad painting of a departed house. Natural fire does the damage.
 rows=read('effects/flora_siege_eocs.json');by=index(rows)
 by['EOC_BERSERK_FLORA_UPDATE_RUINS']['effect']=[]
 # Zodd approaches the northeast side, away from the west/south escape routes.
 for o in rows:
  for node in walk(o):
   if node.get('location_variable_adjust')=={'global_val':'berserk_flora_zodd_anchor'}:node.update(x_adjust=44,y_adjust=3)
 # Schedule the fortress search after the escape scene instead of blocking it.
 for node in walk(by['EOC_BERSERK_FLORA_ESCAPED']['effect']):
  if node.get('run_eocs')=='EOC_BERSERK_GRUNBELD_SEEK':node.update(run_eocs=P+'GRUNBELD_RETRY',time_in_future='5 seconds')
 write('effects/flora_siege_eocs.json',rows)
 # Split the three new routes over separate turns; all remain ordinary missions.
 rows=read('effects/direct_hunt_missions_33_eocs.json')
 for node in walk(index(rows)['EOC_BERSERK_KNOWN_ROUTES_NOW']):
  name=node.get('run_eocs','')
  for i,k in enumerate(['COUNT','WYALD','ROSINE'],1):
   if name=='EOC_BERSERK_JOURNAL_LOCATE_'+k:node['time_in_future']=str(i)+' seconds'
 write('effects/direct_hunt_missions_33_eocs.json',rows)
 # Palette is authoritative regardless of placement ordering of individual sets.
 edit('mapgen/apostle_count_palettes.json',lambda rows,by:rows[0]['terrain'].update({'+':'t_door_bar_locked'}))
 # An accepted demonic lineage cannot be replaced by a second contract. Give it
 # a confrontation, with no recruitment action, rather than silently skipping.
 rows=read('effects/apostol_pawn_eocs.json');by=index(rows)
 for k,site,monster in [('COUNT','berserk_count_dungeon','mon_berserk_apostle_count'),('WYALD','berserk_wyald_ring','mon_berserk_apostle_wyald'),('ROSINE','berserk_rosine_nest','mon_berserk_apostle_rosine')]:
  E.append(eoc(P+k+'_CHALLENGE',[math('berserk_apostol_'+k.lower()+'_pawn_encounter = 2'),run('EOC_BERSERK_FIX28_'+k+'_RELEASE')],both('u_is_avatar',{'u_at_om_location':site},math('u_berserk_apostol_path > 0'),eq('berserk_apostol_'+k.lower()+'_pawn_encounter',0),math("u_monsters_nearby('"+monster+"', 'radius': 10, 'attitude': 'both') > 0"))))
 # Accepted lines get a real confrontation without reopening a contract.
 topics=[]
 for k,monster in [('COUNT','mon_berserk_apostle_count'),('WYALD','mon_berserk_apostle_wyald'),('ROSINE','mon_berserk_apostle_rosine')]:
  predicate=P+k+'_DEMON';E.append(eoc(predicate,[],math('u_berserk_apostol_path > 0')))
  root_id='TALK_BERSERK_NOV02_'+k
  old=index(read('dialogue/apostol_contracts.json'))['TALK_BERSERK_APOSTOL_'+k+'_PAWN_ROOT']
  lines={
   'COUNT':('That power did not come from my hand. You already carry another will into my house. Tell me why I should let you leave it.','Эта сила получена не из моих рук. Ты уже принёс в мой дом чужую волю. Скажи, почему я должен позволить тебе уйти?'),
   'WYALD':('Ha! You already reek of them. Then spare me the begging. Let us see what that gift is worth when someone tears at your throat.','Ха! От тебя уже разит ими. Тогда избавь меня от просьб. Посмотрим, чего стоит этот дар, когда тебе вцепятся в глотку.'),
   'ROSINE':('You brought something strange into my valley. I cannot make you one of my children. Why did you come here?','Ты принёс в мою долину что-то чужое. Я не могу сделать тебя одним из своих детей. Зачем ты пришёл?')}
  human=[dict(r,condition=both(r.get('condition','u_is_avatar'),neg({'test_eoc':predicate}))) for r in copy.deepcopy(old['responses'])]
  topics.append({'type':'talk_topic','id':root_id,'dynamic_line':{'test_eoc':predicate,'yes':tr(*lines[k]),'no':copy.deepcopy(old['dynamic_line'])},'responses':human+[{'text':tr('I came to end this.','Я пришёл положить этому конец.'),'topic':'TALK_DONE','condition':{'test_eoc':predicate}},{'text':tr('There is nothing to discuss.','Нам не о чем говорить.'),'topic':'TALK_DONE','condition':{'test_eoc':predicate}}]})
  for file in (MOD/'monsters').glob('*.json'):
   data=json.loads(file.read_text());objects=data if isinstance(data,list) else [data];changed=False
   for obj in objects:
    if obj.get('id')==monster:obj['chat_topics']=[root_id,'TALK_BERSERK_APOSTOL_'+k+'_PAWN_ROOT'];changed=True
   if changed:write(str(file.relative_to(MOD)),data)
  opening=P+k+'_OPEN';seen=P+k+'_SEEN'
  E.append(eoc(seen,{'if':math("u_hp('torso') >= u_hp_max('torso')"),'then':run(opening,alpha_talker='avatar',beta_talker='u'),'else':[math('berserk_apostol_'+k.lower()+'_pawn_encounter = 2'),run('EOC_BERSERK_FIX28_'+k+'_RELEASE',alpha_talker='avatar',beta_talker='')]},'u_is_monster'))
  E.append(eoc(opening,[math('berserk_apostol_'+k.lower()+'_pawn_encounter = 2'),'open_dialogue',run('EOC_BERSERK_FIX28_'+k+'_RELEASE')],both('u_is_avatar','has_beta',eq('berserk_apostol_'+k.lower()+'_pawn_encounter',0))))
  c=next(o for o in E if o['id']==P+k+'_CHALLENGE');c['effect']={'u_run_monster_eocs':[seen],'mtype_ids':[monster],'monster_range':10,'monster_must_see':True}
 write('dialogue/apostol_confrontation02.json',topics)
 # A one-time release also removes obsolete parley freezes on older actors.
 E.append(eoc(P+'COUNT_COMBAT',run('EOC_BERSERK_FIX28_COUNT_RELEASE'),both('u_is_avatar',{'u_at_om_location':'berserk_count_dungeon'},math('u_berserk_apostol_path > 0'),eq('berserk_apostol_count_pawn_encounter',2),neg(eq('u_berserk_count_combat02')))))
 E[-1]['effect']=[run('EOC_BERSERK_FIX28_COUNT_RELEASE'),math('u_berserk_count_combat02 = 1')]
 # Clear inherited fear triggers; native AI behaviour still needs a playtest.
 rows=read('monsters/apostle_count.json')
 for o in rows:
  if o.get('id') in ['mon_berserk_count_servant','mon_berserk_apostle_count']:o.update(aggression=100,morale=200,fear_triggers=[])
 write('monsters/apostle_count.json',rows)
 E.append(eoc(P+'MOVE',[run(P+k+'_CHALLENGE') for k in ['COUNT','WYALD','ROSINE']]+[run(P+'COUNT_COMBAT')], 'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))
 # An actual sketch rests on the forge worktable, in addition to Godot's topic.
 rows=read('mapgen/godo_workshop.json')
 for o in rows:
  if o.get('om_terrain')=='berserk_godo_workshop':
   items=o['object'].setdefault('place_item',[])
   if not any(x.get('item')=='berserk_forge_woodland_sketch' for x in items):items.append({'item':'berserk_forge_woodland_sketch','x':14,'y':10,'amount':1})
 write('mapgen/godo_workshop.json',rows)
 # The physical paper and Godot's handout are two ways to get the same note.
 def sketch(rows,by):
  item=by['berserk_forge_woodland_sketch'];item['name']={'str_sp':item['name'].get('str',item['name'].get('str_sp'))}
 edit('items/forge_woodland_leads.json',sketch)
 rows=read('dialogue/godo.json')
 for obj in rows:
  if obj.get('id')=='TALK_BERSERK_FIX28_GODO_SKETCH':
   for response in obj['responses']:
    if 'berserk_forge_woodland_sketch' in str(response.get('effect',{})):
     response['condition']=both(response.get('condition','u_is_avatar'),neg({'u_has_item':'berserk_forge_woodland_sketch'}))
 write('dialogue/godo.json',rows)
 furnishings_and_papers(E)
 write('effects/playtest_nov02_eocs.json',E);localize()
 print('November 2: bounded routes, accessible wagon, tangible papers and natural fire.')

def furnishings_and_papers(E):
 project=json.loads((ROOT/'docs/location_projects/flora-3.3-05.json').read_text())
 names={o.get('id'):o for p in MOD.rglob('*.json') for o in (lambda d:d if isinstance(d,list) else [d])(json.loads(p.read_text())) if isinstance(o,dict)}
 items=[];extra=[]
 for n in project['loose_notes']:
  original=names[n['furniture_id']]
  if n['furniture_id']=='f_berserk_flora_manuscript':item='berserk_flora_rescued_manuscript'
  else:
   item=n['furniture_id'].removeprefix('f_')+'_paper';name=original['name'];name=name.get('str',name) if isinstance(name,dict) else name
   reader=original.get('examine_action',{}).get('effect_on_conditions',[])
   if not reader:raise ValueError(n)
   items.append({'type':'ITEM','subtypes':['TOOL'],'id':item,'name':{'str_sp':name},'description':tr('Handwritten pages, left on a table where they can be read. You can take them with you.','Рукописные страницы, оставленные на столе для чтения. Их можно взять с собой.'),'weight':'5 g','volume':'1 ml','material':['paper'],'symbol':'?','color':'light_gray','looks_like':'paper','charges_per_use':0,'flags':['ALLOWS_REMOTE_USE'],'use_action':{'type':'effect_on_conditions','need_wielding':False,'effect_on_conditions':reader}})
  extra.append(dict(item=item,x=n['x'],y=n['y'],amount=1))
 rows=read('mapgen/flora_manor.json')
 for i,o in enumerate(rows):
  ox=(i%2)*24;oy=(i//2)*24
  o['object'].setdefault('place_item',[]).extend([dict(v,x=v['x']-ox,y=v['y']-oy) for v in extra if ox<=v['x']<ox+24 and oy<=v['y']<oy+24])
 write('mapgen/flora_manor.json',rows);write('items/flora_loose_papers.json',items)
 E.append(eoc(P+'MANUSCRIPT_TAKEN',math('berserk_flora_manuscript_rescued = 1'),both('u_is_avatar',{'u_has_item':'berserk_flora_rescued_manuscript'},neg(eq('berserk_flora_manuscript_rescued'))),**{'global':True,'recurrence':'10 seconds'}))
 variants=[];tiles=[]
 for i,face in enumerate(['south','west','north','east']):
  id_='f_berserk_flora_chair_'+face;variants.append({'type':'furniture','id':id_,'copy-from':'f_berserk_flora_wooden_chair','looks_like':'f_chair'});tiles.append({'id':id_,'fg':i,'rotates':False})
 for face,i in [('south',4),('west',5)]:
  id_='f_berserk_flora_cupboard_'+face;variants.append({'type':'furniture','id':id_,'copy-from':'f_berserk_flora_wooden_cupboard','looks_like':'f_dresser'});tiles.append({'id':id_,'fg':i,'rotates':False})
 write('furniture/flora_oriented.json',variants)
 tiles.append({'id':'f_berserk_flora_ward_shelf','fg':8,'rotates':False})
 write('flora_oriented_tileset.json',[{'type':'mod_tileset','compatibility':['UltimateCataclysm'],'tiles-new':[{'file':'tileset/flora_native_furniture.png','sprite_width':32,'sprite_height':64,'sprite_offset_y':-32,'tiles':tiles}]}])
if __name__=='__main__':main()
