#!/usr/bin/env python3
"""Owner's second November 2 playtest: discovery and shorter forge menus."""
import copy
from recover_apostol_33 import read,write,index,walk,eoc
from build_playtest_fixes_20261024 import tr,localize
from reference_journal_content_33 import allof as both,anyof as either,no as neg,eq

P='EOC_BERSERK_NOV02B_'
E=[]
G='TALK_BERSERK_GODO'
R='TALK_BERSERK_RICKERT'
U='EOC_BERSERK_UTILITY29_'
F='EOC_BERSERK_FIX28_'
def run(id_,**kw):return {'run_eocs':id_,**kw}
def math(s):return {'math':[s]}
def edit(file,fn):
 rows=read(file);fn(rows,index(rows));write(file,rows)
def forest_border(special,radius):
 # Native fixed locations validate the real surrounding OMTs before placement.
 # Keep all actual above/below-ground parts and leave visited locations alone.
 base=[x for x in special['overmaps'] if x['overmap']!='forest']
 occupied={tuple(x['point']) for x in base}
 special['overmaps']=base+[{'point':[x,y,0],'overmap':'forest','locations':['forest']} for y in range(-radius,radius+1) for x in range(-radius,radius+1) if (x,y,0) not in occupied]
 special['city_distance']=[5,-1]

def discovery():
 def forge(rows,by):
  # The old game_start bootstrap still CREATED a forge even with occurrences 0.
  # Keep its ID, but only register a forge the player is actually standing in.
  by['EOC_BERSERK_GODO_BOOTSTRAP']['effect']=run('EOC_BERSERK_GODO_REGISTER')
 edit('effects/godo_eocs.json',forge)
 edit('overmap/godo_workshop.json',lambda rows,by:forest_border(by['berserk_godo_workshop_special'],3))
 def wagon(rows,by):
  s=by['berserk_early_caravan_special'];s.pop('connections',None)
  s['locations']=['forest'];s['overmaps'][0]['locations']=['forest'];forest_border(s,1)
  s['//']='One hidden woodland discovery. No mandatory road connection, marker or automatic reading.'
  by['berserk_early_caravan']['name']=tr('abandoned woodland wagon','брошенная лесная повозка')
 edit('overmap/early_caravan.json',wagon)
 def retries(rows,by):
  # One migration restores attempts exhausted by the former road requirement.
  o=by[U+'EARLY_LAND_MIGRATION']
  for n in walk(o):
   if 'math' in n:n['math']=[s.replace('land_v2','land_v3') for s in n['math']]
  o=by[U+'EARLY_REQUEST']
  o['effect'][-1]['then']=run(U+'EARLY_FIND_WIDE')
 edit('effects/apostol_utilities_33_eocs.json',retries)
 # Every retry is still hidden and bounded. A new area can revive a spent search.
 land=either(*[{'u_at_om_location':t} for t in ['field','forest','forest_thick','road']])
 E.append(eoc(P+'WAGON_NEW_AREA',[math('u_berserk_early_caravan_attempts = 0'),math('u_berserk_early_caravan_retry_at = 0'),{'u_location_variable':{'u_val':'berserk_caravan_area02b'}}],both('u_is_avatar',eq('berserk_eclipse_era',0),neg(eq('berserk_early_caravan_placed')),math("u_val('pos_z') == 0"),land,either(math('has_var(u_berserk_caravan_area02b) == 0'),math("distance('u', u_berserk_caravan_area02b) >= 1152")))))
 E.append(eoc(P+'MOVE',[run(P+'WAGON_NEW_AREA'),run(U+'EARLY_TICK'),run(P+'SKETCH_NOTICE')],'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))
 # Physical note: a separate plain table near the entrance, away from tools.
 rows=read('mapgen/godo_workshop.json')
 for obj in rows:
  if obj.get('om_terrain')!='berserk_godo_workshop':continue
  body=obj['object'];body['place_item']=[x for x in body['place_item'] if x.get('item')!='berserk_forge_woodland_sketch']
  table={'furn':'f_table','x':10,'y':17}
  body['place_furniture']=[x for x in body.get('place_furniture',[]) if (x.get('x'),x.get('y'))!=(10,17)]+[table]
  body['place_item'].append({'item':'berserk_forge_woodland_sketch','x':10,'y':17,'amount':1,'chance':100})
 write('mapgen/godo_workshop.json',rows)
 note={'context_val':'forge_sketch_table02b'}
 E.append(eoc(P+'SKETCH_NOTICE',[{'u_location_variable':note},math('_forge_sketch_table02b.x = floor(_forge_sketch_table02b.x / 24) * 24 + 10'),math('_forge_sketch_table02b.y = floor(_forge_sketch_table02b.y / 24) * 24 + 17'),run(P+'SKETCH_PRESENT')],both('u_is_avatar',{'u_at_om_location':'berserk_godo_workshop'},eq('berserk_eclipse_era',0),neg(eq('u_berserk_forge_sketch_notice02b')))))
 E.append(eoc(P+'SKETCH_PRESENT',[math('u_berserk_forge_sketch_notice02b = 1'),{'u_message':tr('A folded woodland sketch lies on the small table by the entrance.','На небольшом столе у входа лежит сложенный набросок лесной дороги.'),'type':'info','popup':False}],{'map_furniture_id':'f_table','loc':note}))
 # An explicit bounded search replaces the former implicit 540-OMT search.
 def woodland(rows,by):
  for k in ['OAK','CAVE']:
   effect=by[F+'FIND_'+k]['effect'];effect['target_params'].update(random=True,search_range=80);effect['true_eocs']=[P+'WOODLAND_VERIFY']
  by[F+'LEAD_FOUND']['condition']=either({'overmap_at_point':'berserk_cursed_oak','point':{'u_val':'berserk_forge_behelit_route'}},{'overmap_at_point':'berserk_echo_cave_entrance','point':{'u_val':'berserk_forge_behelit_route'}})
  # An already issued route is kept. Re-reading does not move an active target.
  body=by[F+'BEHELIT_LEAD_READ']['effect']
  if len(body)>1:by[F+'BEHELIT_LEAD_READ']['effect']=[body[0],{'if':eq('u_berserk_stone_route_issued'),'then':{'reveal_map':{'u_val':'berserk_forge_behelit_route'},'radius':2},'else':body[1:]}]
 edit('effects/playtest_fixes_20261028_eocs.json',woodland)
 E.append(eoc(P+'WOODLAND_VERIFY',{'if':either({'overmap_at_point':'berserk_cursed_oak','point':{'u_val':'berserk_forge_behelit_route'}},{'overmap_at_point':'berserk_echo_cave_entrance','point':{'u_val':'berserk_forge_behelit_route'}}),'then':run(F+'LEAD_FOUND'),'else':run(F+'LEAD_FAILED')},'u_is_avatar'))
 def sites(rows,by):
  for id_ in ['berserk_cursed_oak_special','berserk_echo_cave_special']:forest_border(by[id_],2)
 edit('overmap/behelit_sites.json',sites)
 # Keep the successful first-hunt distance; prevent direct adjacency to groves
 # and urban buildings through actual ordinary-forest requirements.
 edit('overmap/first_hunt.json',lambda rows,by:forest_border(by['berserk_first_hunt_special'],3))
 # Remove only the requested warning. Keep the consumed warning marker.
 edit('effects/eclipse_field_scenes.json',lambda rows,by:by['EOC_BERSERK_ECLIPSE_SCENE_WARNING'].update(effect=[]))
 def warning(rows,by):
  o=by['EOC_BERSERK_ECLIPSE_GATE_WARNING'];o['effect']=[x for x in o['effect'] if not x.get('u_message','').startswith('Beyond the pale ribs')]
 edit('effects/eclipse_field_events.json',warning)

def gate(response,parent):
 rr=copy.deepcopy(response)
 if parent:rr['condition']=both(parent,rr.get('condition','u_is_avatar'))
 return rr
def nav(text,ru,target,condition=None):
 r={'text':tr(text,ru),'topic':target}
 if condition:r['condition']=condition
 return r
def available(responses):return either(*[r.get('condition','u_is_avatar') for r in responses])
def menu(id_,line,ru,rs,root):
 return {'type':'talk_topic','id':id_,'dynamic_line':tr(line,ru),'responses':rs+[nav('Back to the main topics.','К темам разговора.',root)]}

def dialogue():
 rows=read('dialogue/godo.json');by=index(rows)
 # Builders above recreate literary topics. Remove only this pass's additions.
 rows[:]=[o for o in rows if not o['id'].startswith('TALK_BERSERK_NOV02B_')];by=index(rows)
 root=by[G];old=copy.deepcopy(root['responses']);bytarget={r['topic']:r for r in old}
 # Current orders go straight to their actual order, not another selector.
 order_parent=bytarget[G+'_ORDERS'].get('condition')
 orders=[gate(r,order_parent) for r in by[G+'_ORDERS']['responses'] if r.get('topic') in [G+'_EARLY_SWORD',G+'_SWORD',G+'_REPAIR']]
 for r in orders:
  r['text']=tr(*{G+'_EARLY_SWORD':('My battle sword order.','Мой заказ боевого меча.'),G+'_SWORD':('My Dragonslayer order.','Мой заказ Драконоборца.'),G+'_REPAIR':('The blade I left for repair.','Клинок, который я оставил в ремонт.')}[r['topic']])
  field,limit={G+'_EARLY_SWORD':('early',3),G+'_SWORD':('sword',4),G+'_REPAIR':('repair',2)}[r['topic']]
  r['condition']=both(r.get('condition','u_is_avatar'),math('u_berserk_godo_'+field+'_state > 0'),math('u_berserk_godo_'+field+'_state < '+str(limit)))
 private_targets={G+'_PERSONAL','TALK_BERSERK_APOSTOL_GODO','TALK_BERSERK_COMMON33_GODO_MENU','TALK_BERSERK_COMMON33_GODO_SUSPICION'}
 private_parent=bytarget[G+'_PERSONAL'].get('condition')
 private=[gate(r,private_parent) for r in by[G+'_PERSONAL']['responses'] if r.get('topic')!=G]
 private += [copy.deepcopy(r) for r in old if r['topic'] in private_targets-{G+'_PERSONAL'}]
 personal='TALK_BERSERK_NOV02B_GODO_PERSONAL'
 rows.append(menu(personal,'What is weighing on you?','Что тебя гложет?',private,G))
 local=[copy.deepcopy(r) for r in old if r['topic'] in ['TALK_BERSERK_FIX28_GODO_SKETCH',G+'_FLORA_REFERRAL']]
 localid='TALK_BERSERK_NOV02B_GODO_LOCAL'
 rows.append(menu(localid,'What have you heard?','Что ты слышал?',local,G))
 root['responses']=[bytarget[G+'_WORK']]+orders+[bytarget[G+'_HEARTH'],nav('About what has happened to me.','О том, что со мной произошло.',personal,available(private)),nav('About these woods and the road ahead.','Об этих лесах и дальнейшей дороге.',localid,available(local)),bytarget[G+'_FAREWELL']]
 hearth=by[G+'_HEARTH'];r=copy.deepcopy(bytarget[G+'_APPRENTICE_MENU'])
 if not any(x.get('topic')==r['topic'] for x in hearth['responses']):hearth['responses'].insert(-1,r)
 # Once an order exists, do not make the player repeat its opening pitch.
 for r in by[G+'_WORK']['responses']:
  if r.get('topic')==G+'_WEAPON_REQUEST':r['condition']=both(r.get('condition','u_is_avatar'),eq('u_berserk_godo_early_state',0))
  if r.get('topic')==G+'_SWORD_REQUEST':r['condition']=both(r.get('condition','u_is_avatar'),eq('u_berserk_godo_sword_state',0))
 by[G+'_WORK']['responses'][:0]=copy.deepcopy(orders)
 # The sketch remains a tangible object: talking no longer silently reads it.
 sketch=by['TALK_BERSERK_FIX28_GODO_SKETCH']
 sketch['responses']=[r for r in sketch['responses'] if 'BEHELIT_LEAD_READ' not in str(r.get('effect',{}))]
 sketch['responses'].append(nav('I will look at it later.','Посмотрю позже.',localid))
 # Rickert keeps first introductions and bedside choices; only his established
 # menu is grouped. Child effects and state guards are copied unchanged.
 rr=by[R];old=copy.deepcopy(rr['responses'])
 groups={
  'PAST':([R+'_BAND',R+'_ECLIPSE',R+'_CEREMONY_WITNESS',R+'_REUNION_LATER','TALK_BERSERK_COMMON33_RICKERT_FINDS'],('The Band and what happened.','Об отряде и случившемся.'),('What did you want to talk about?','О чём ты хотел поговорить?')),
  'SELF':([R+'_RECENT_DAYS',R+'_PERSONAL',R+'_TRUST_RECOVERY'],('How are you holding up?','Как ты держишься?'),('I am listening.','Я слушаю.')),
  'CHANGES':(['TALK_BERSERK_APOSTOL_RICKERT',R+'_VISIBLE_HANDS',R+'_VISIBLE_SHELL',R+'_VISIBLE_WINGS','TALK_BERSERK_COMMON33_RICKERT_MENU','TALK_BERSERK_COMMON33_RICKERT_SUSPICION'],('About the stone and my condition.','О камне и моём состоянии.'),('What is troubling you?','Что тебя тревожит?')),
 }
 moved={t for ts,_,_ in groups.values() for t in ts}
 rebuilt=[r for r in old if r['topic'] not in moved and r['topic']!=R+'_ORDER_STATUS']
 for key,(targets,label,line) in groups.items():
  children=[r for r in old if r['topic'] in targets]
  id_='TALK_BERSERK_NOV02B_RICKERT_'+key
  rows.append(menu(id_,*line,children,R));rebuilt.insert(-1,nav(*label,id_,available(children)))
 # Expose each running order in one click, keeping the root's acquaintance and
 # wake gates as well as each job's own anatomy/state requirements.
 status=next(r for r in old if r['topic']==R+'_ORDER_STATUS')
 for r in reversed(by[R+'_ORDER_STATUS']['responses']):
  if r.get('topic') in ['TALK_BERSERK_GODO_ARM',R+'_BOLTS',R+'_ARM_REGROWN_ORDER']:
   direct=gate(r,status.get('condition'))
   if r['topic']=='TALK_BERSERK_GODO_ARM':
    direct['topic']='TALK_BERSERK_GODO_ARM_STATUS';direct['condition']=both(direct['condition'],math('u_berserk_godo_arm_state > 0'),math('u_berserk_godo_arm_state < 4'))
   rebuilt.insert(0,direct)
 rr['responses']=rebuilt
 # Equipment help opens the actionable prosthesis page; the engineering
 # discussion remains separately available under the same anatomy guard.
 for r in by[R+'_ORDERS']['responses']:
  if r.get('topic')=='TALK_BERSERK_GODO_ARM':r['topic']='TALK_BERSERK_GODO_ARM_STATUS'
 by[R+'_ORDERS']['responses'].insert(-1,nav('How would the hand work?','Как будет устроена рука?','TALK_BERSERK_GODO_ARM',{'test_eoc':'EOC_BERSERK_DIALOGUE_MISSING_LEFT_HAND'}))
 # A short, explicit return is available after reading an answer. It returns
 # to that section, with a separate one-click route to the main topics.
 sections={G+'_WORK':[r['topic'] for r in by[G+'_WORK']['responses'] if r['topic'] not in [G,G+'_WORK',G+'_ORDERS']],G+'_HEARTH':[r['topic'] for r in by[G+'_HEARTH']['responses'] if r['topic']!=G],personal:[r['topic'] for r in private],localid:[r['topic'] for r in local],R+'_MECHANISMS':[r['topic'] for r in by[R+'_MECHANISMS']['responses'] if r['topic']!=R],R+'_ORDERS':[r['topic'] for r in by[R+'_ORDERS']['responses'] if r['topic']!=R]}
 for key,(targets,_,_) in groups.items():sections['TALK_BERSERK_NOV02B_RICKERT_'+key]=targets
 current=index(rows);labels={};stops={G,R,G+'_ORDERS',R+'_ORDER_STATUS',*sections}
 for section,starts in sections.items():
  pending=list(starts);seen=set()
  while pending:
   id_=pending.pop()
   if id_ in seen or id_ in stops or id_ not in current or 'GOODBYE' in id_ or 'FAREWELL' in id_:continue
   seen.add(id_);labels.setdefault(id_,set()).add(section)
   pending += [r.get('topic') for r in current[id_].get('responses',[]) if r.get('topic')]
 section_roots={G,G+'_WORK',G+'_HEARTH',R,R+'_ORDERS',R+'_MECHANISMS',*sections}
 for obj in rows:
  id_=obj['id']
  owner=R if 'RICKERT' in id_ or id_.startswith(G+'_ARM') or id_ in [G+'_FITTING',G+'_SELF',G+'_PRAISE'] else G
  backs=[r for r in obj.get('responses',[]) if r.get('text')=='I wanted to ask about something else.']
  for r in backs:
   target=r.get('topic')
   if target in [G,R] and len(labels.get(id_,set()))==1:r['topic']=next(iter(labels[id_]));target=r['topic']
   r['text']=tr('Back to the main topics.','К темам разговора.') if target in [G,R] else tr('Back.','Назад.')
  if backs and id_ not in section_roots and not any(r.get('topic')==owner for r in obj['responses']):obj['responses'].append(nav('Back to the main topics.','К темам разговора.',owner))
 # Remove duplicate notebook handouts scattered across craft selectors. The
 # same harmless replacement remains in each main menu, once.
 for owner in [G,R]:
  source=next((copy.deepcopy(r) for o in rows for r in o.get('responses',[]) if r.get('text')=='I lost my road notes. Could I have a new notebook?' and o['id'].startswith(owner)),None)
  if source:
   for o in rows:
    if o['id'].startswith(owner):o['responses']=[r for r in o.get('responses',[]) if r.get('text')!=source['text']]
   source['topic']=owner;by[owner]['responses'].insert(-1,source)
 write('dialogue/godo.json',rows)

def main():
 discovery();dialogue();write('effects/playtest_nov02b_eocs.json',E);localize()
 print('November 2 followup: no hidden startup forge, woodland discoveries and shorter forge navigation.')
if __name__=='__main__':main()
