"""Owner regressions: strict native leap scope and actual JSON reward/flight rules.

These are data/transition tests, not a running CDDA gameplay validation.
"""
import copy,json,unittest
from pathlib import Path
from test_behelit_rewards import RewardGraph
from test_playtest_oct25_33 import World
from test_reference_journal_33 import EOCS,TOPICS,MOD,walk
from test_skull_knight_dialogue_33 import Conversation as Knight
P='EOC_BERSERK_FIX28_'

def load(f):return json.loads((MOD/f).read_text())

class Regression(unittest.TestCase):
 def test_leap_condition_never_reads_absent_beta(self):
  count=0
  def cond(c,beta=False):
   if isinstance(c,str):
    if c=='has_beta':return beta
    if c=='npc_is_avatar':
     if not beta:raise AssertionError('native const_actor(false beta) crash')
     return True
    return False
   if 'and' in c:return all(cond(x,beta) for x in c['and'])
   if 'or' in c:return any(cond(x,beta) for x in c['or'])
   if 'not' in c:return not cond(c['not'],beta)
   if 'npc_has_trait' in c:
    if not beta:raise AssertionError('missing beta trait lookup')
    return True
   return True
  for f in (MOD/'monsters').glob('*.json'):
   data=json.loads(f.read_text());data=data if isinstance(data,list) else [data]
   for o in data:
    for a in o.get('special_attacks',[]):
     if isinstance(a,dict) and a.get('type')=='leap' and 'condition' in a:
      cond(a['condition']);count+=1
  self.assertGreater(count,0)
 def test_prisoner_has_no_invalid_rubble_terrain(self):
  self.assertFalse(any(n.get('map_terrain_id')=='t_rubble' for n in walk(load('effects/count_prisoner_33_eocs.json'))))
 def test_both_behelit_variants_block_other_cache_without_emptying_it(self):
  for held in ['berserk_behelit','berserk_behelit_distorted']:
   f=RewardGraph();f.inventory=[held];f.cache('oak');before=copy.deepcopy(f.furniture)
   f.run('EOC_BERSERK_CLAIM_OAK_BEHELIT')
   self.assertEqual(f.inventory,[held]);self.assertEqual(f.furniture,before)
 def test_projection_does_not_drop_second_behelit(self):
  f=RewardGraph();f.inventory=['berserk_behelit'];f.victim=(12,12,0)
  f.run('EOC_BERSERK_BEHELIT_BOSS_DIES');self.assertFalse(f.ground)
 def test_all_pawn_bodies_have_typed_protection_without_reversible_forms(self):
  for k in ['count','wyald','rosine','grunbeld']:
   for line in ['pawn','flesh']:
    form=next(o for o in load('mutations/apostol_'+k+'_'+line+'.json') if o['id'].endswith('_FORM'))
    self.assertGreater(form['armor'][0]['cut'],0)
    self.assertFalse(form['purifiable']);self.assertNotIn('transform',form)
    self.assertTrue(form.get('restricts_gear'));self.assertFalse(form['destroys_gear'])
 def test_mutation_message_is_inside_actual_gain_guard(self):
  for k in ['COUNT','WYALD','ROSINE','GRUNBELD']:
   o=EOCS['EOC_BERSERK_APOSTOL_'+k+'_FLESH_GROW']
   gains=[n for n in walk(o) if isinstance(n.get('then'),list) and n['then'] and 'u_add_trait' in n['then'][0]]
   self.assertTrue(gains,k)
   for node in gains:
    t=node['then'][0]['u_add_trait'];self.assertEqual(node['if'],{'not':{'u_has_trait':t}})
    self.assertTrue(node['then'][1]['u_message'].startswith('Your body changes:'))
 def test_rare_sites_are_forested_and_outside_cities(self):
  for o in load('overmap/road_stories.json'):
   if o['type']=='overmap_special':
    self.assertEqual(o['locations'],['forest']);self.assertGreaterEqual(o['city_distance'][0],10);self.assertEqual(o['occurrences'],[4,100])
  for o in load('mapgen/road_stories.json'):
   rows=o['object']['rows'];self.assertTrue(all(len(r)==24 for r in rows))
   self.assertTrue(all(c in 'Tu' for c in rows[0]+rows[-1]))
   self.assertTrue(all(r[0] in 'Tu' and r[-1] in 'Tu' for r in rows))
 def test_forest_routes_have_one_saved_choice_and_one_mission(self):
  read=EOCS[P+'BEHELIT_LEAD_READ'];choice=read['effect'][1]
  self.assertEqual(choice['if'],{'math':['u_berserk_forge_behelit_choice == 0']})
  self.assertEqual([w for _,w in choice['then']['weighted_list_eocs']],[1,1])
  found=EOCS[P+'LEAD_FOUND']['effect'][1]
  self.assertEqual(found['if'],{'not':{'math':['u_berserk_stone_route_issued == 1']}})
  m=load('missions/woodland_stone.json')[0]
  self.assertEqual(m['start']['assign_mission_target']['var'],{'u_val':'berserk_forge_behelit_route'})
 def test_spacing_has_real_special_exclusion_not_fake_min_distance(self):
  for f,r in [('first_hunt',48),('local_breach',48),('apostle_count',104),('wyald_rosine_hunts',104),('grunbeld_hunt',104)]:
   for o in load('overmap/'+f+'.json'):
    if o['type']=='overmap_special':self.assertEqual(o['spawns']['radius'],[r,r]);self.assertEqual(o['spawns']['population'],[0,0])
 def test_rosine_does_not_explain_trap_before_acceptance(self):
  self.assertNotIn('human',TOPICS['TALK_BERSERK_APOSTOL_ROSINE_PAWN_LEAVE_MORE']['dynamic_line'])
  rs=TOPICS['TALK_BERSERK_APOSTOL_ROSINE_PAWN_DECISION']['responses']
  self.assertFalse(any('human' in r['text'] for r in rs))
 def test_actual_hall_stair_entrances_are_bars(self):
  hall=next(o for o in load('mapgen/apostle_count.json') if o.get('om_terrain')==['berserk_count_hall'])
  cells={(s['x'],s['y']):s['id'] for s in hall['object']['set']}
  self.assertEqual(cells[12,21],'t_door_bar_locked');self.assertEqual(cells[13,21],'t_door_bar_locked')
 def test_chapel_owner_red_square_and_shelves(self):
  p=json.loads((MOD.parents[1]/'docs/location_projects/chapel-3.3-03.json').read_text())
  self.assertEqual(p['rows'][13][15],'#')
  self.assertNotIn('handprints on the altar', (MOD/'dialogue/road_journal.json').read_text())
  self.assertTrue(any(f['x']==16 and f['y']==5 and f['furn']=='f_bookcase' for f in p['furniture']))
 def test_knight_hides_question_when_both_people_known(self):
  f=Knight();f.values.update(u_berserk_godo_rescue_relocated=1,u_berserk_godo_personally_met=1,u_berserk_rickert_met=1)
  self.assertFalse(any(r['topic'].endswith('MASTERS') for r in f.available('AFTER')))


class EarlyHelp(unittest.TestCase):
 def test_shelter_paper_is_once_and_never_reads_itself(self):
  f=World();f.om='shelter_1b_vandal';f.values['berserk_eclipse_era']=0;f.values['u_berserk_eclipse_rescue_state']=0
  f.run(P+'SHELTER_NOTICE');f.run(P+'SHELTER_NOTICE')
  self.assertEqual(f.inventory['berserk_road_caravan_note'],1)
  self.assertNotIn('u_berserk_journal_knows_godo',f.values)
  self.assertFalse(f.missions)
 def test_injury_tip_follows_actual_anatomy_and_does_not_repeat(self):
  f=World();f.run(P+'INJURY_TIP');self.assertFalse(f.messages)
  f=World();f.bionics.update(['bio_berserk_hand_stump','bio_berserk_lost_eye'])
  f.run(P+'INJURY_TIP');count=len(f.messages);self.assertEqual(count,2)
  f.run(P+'INJURY_TIP');self.assertEqual(len(f.messages),count)

class Flight(World):
 def __init__(self):
  super().__init__();self.pos=(0,0,2);self.selected=(6,0,2);self.charges=0;self.blocked={};self.occupied=set();self.can_see=True
  self.overrides['EOC_BERSERK_APOSTOL_ROSINE_FLESH_LINE']=True;self.traits.add('BERSERK_ROSINE_FLESH_DIVE')
 def value(self,s):
  import re
  for a,n in zip(['x','y','z'],self.pos):s=s.replace("u_val('pos_"+a+"')",str(n))
  s=s.replace("u_val('stamina')",'10000');s=re.sub(r"u_encumbrance\('[^']+'\)",'0',s)
  return super().value(s)
 def condition(self,c):
  if isinstance(c,dict):
   if 'u_has_flag' in c:return c['u_has_flag']=='BERSERK_ROSINE_FLESH_FORM_ACTIVE'
   if 'map_terrain_with_flag' in c:
    pos=tuple(self.getvar(c['loc']));flags=self.blocked.get(pos,{'FLAT'})
    return c['map_terrain_with_flag'] in flags
   if 'u_can_see_location' in c or 'line_of_sight' in c:return self.can_see
  return super().condition(c)
 def run(self,id_):
  if id_=='EOC_BERSERK_APOSTOL_ROSINE_FLESH_DIVE_RESULT':self.charges+=1;return
  super().run(id_)
 def effect(self,x):
  if isinstance(x,dict):
   if 'u_query_tile' in x:
    if self.selected is not None:self.values['_berserk_wing_landing']=self.selected
    return
   if 'u_teleport' in x:
    self.assert_safe=x.get('force_safe') is False
    target=tuple(self.getvar(x['u_teleport']))
    if target not in self.occupied and 'WALL' not in self.blocked.get(target,set()):self.pos=target
    return
  return super().effect(x)

class FlightRegression(unittest.TestCase):
 def use(self,f):f.run('EOC_BERSERK_APOSTOL_ROSINE_FLESH_DIVE_USE')
 def test_same_level_and_one_level_descent_charge_once(self):
  for p in [(6,0,2),(6,0,1)]:
   f=Flight();f.selected=p;self.use(f);self.assertEqual(f.pos,p);self.assertEqual(f.charges,1);self.assertTrue(f.assert_safe)
 def test_upward_deep_or_far_target_never_moves_or_charges(self):
  for p in [(6,0,3),(6,0,-4),(9,0,2)]:
   f=Flight();f.selected=p;self.use(f);self.assertEqual(f.pos,(0,0,2));self.assertEqual(f.charges,0)
 def test_cancel_empty_air_occupied_and_glass_never_charge(self):
  for case in ['cancel','air','occupied','glass','unseen']:
   f=Flight()
   if case=='cancel':f.selected=None
   if case=='air':f.blocked[f.selected]={'NO_FLOOR'}
   if case=='occupied':f.occupied.add(f.selected)
   if case=='glass':f.blocked[3,0,2]={'WINDOW','TRANSPARENT'}
   if case=='unseen':f.can_see=False
   self.use(f);self.assertEqual(f.pos,(0,0,2),case);self.assertEqual(f.charges,0,case)

class ChapelUpgrade(World):
 def value(self,s):
  import re
  s=re.sub(r'(_chapel28_\w+)\.([xyz])',lambda m:repr(self.values[m[1]]['xyz'.index(m[2])]),s)
  for a,n in zip('xy',self.pos):s=s.replace("u_val('pos_"+a+"')",str(n))
  return super().value(s)
 def effect(self,x):
  if isinstance(x,dict) and x.get('mapgen_update','').startswith('berserk_chapel_owner28_'):
   base=self.getvar(x['target_var']);obj=next(o for o in load('mapgen/chapel_owner28_upgrade.json') if o['update_mapgen_id']==x['mapgen_update'])
   for step in obj['object']['set']:
    dest=self.terrain if step['point']=='terrain' else self.furniture
    dest[base[0]+step['x'],base[1]+step['y'],base[2]]=step['id']
   return
  return super().effect(x)
class ExistingMaps(unittest.TestCase):
 def old(self):
  f=ChapelUpgrade();f.pos=(12,40,0);f.om='berserk_desecrated_chapel_nave';f.furniture[12,40,0]='f_berserk_chapel_record_v2'
  for x,y in [(15,13),(17,4),(18,4),(16,5),(16,6)]:f.terrain[x,y,0]='t_floor';f.furniture[x,y,0]='f_null'
  f.inventory['keepsake']=1;return f
 def test_approved_old_chapel_patch_is_once_and_does_not_touch_items(self):
  f=self.old();f.run(P+'CHAPEL_UPGRADE');self.assertEqual(f.terrain[15,13,0],'t_wall');self.assertEqual(f.inventory['keepsake'],1)
  self.assertEqual(f.furniture[12,40,0],'f_berserk_chapel_record_v3')
  f.terrain[15,13,0]='t_floor';f.run(P+'CHAPEL_UPGRADE');self.assertEqual(f.terrain[15,13,0],'t_floor')
 def test_players_furniture_prevents_old_chapel_patch(self):
  f=self.old();f.furniture[16,5,0]='f_chair';f.run(P+'CHAPEL_UPGRADE')
  self.assertEqual(f.terrain[15,13,0],'t_floor');self.assertEqual(f.furniture[16,5,0],'f_chair')

if __name__=='__main__':unittest.main()
