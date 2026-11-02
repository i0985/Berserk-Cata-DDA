"""Followup regressions: exported geometry and actual reachable dialogue choices.

No native game or generation seed is simulated here.
"""
import json,unittest
from test_reference_journal_33 import MOD,EOCS,walk
from test_godo_dialogue_33 import Conversation as Godo
from test_rickert_dialogue_33 import Conversation as Rickert

P='EOC_BERSERK_NOV02B_';F='EOC_BERSERK_FIX28_';G='TALK_BERSERK_GODO';R='TALK_BERSERK_RICKERT'
def load(f):return json.loads((MOD/f).read_text())
def special(f,id_):return next(x for x in load('overmap/'+f+'.json') if x.get('id')==id_)
def targets(f,topic):return {r['topic'] for r in f.available(topic)}
def reachable(f,root):
 seen=set();pending=[root]
 while pending:
  t=pending.pop()
  if t in seen or t not in f.topics:continue
  seen.add(t);pending.extend(targets(f,t)-seen)
 return seen

class Discovery(unittest.TestCase):
 def test_ordinary_start_no_longer_calls_a_creating_forge_locator(self):
  bootstrap=EOCS['EOC_BERSERK_GODO_BOOTSTRAP']
  self.assertEqual(bootstrap['effect'],{'run_eocs':'EOC_BERSERK_GODO_REGISTER'})
  # The explicit Guts direction is retained, without pretending it guarantees
  # a minimum distance for native special creation.
  start=EOCS['EOC_BERSERK_GODO_BOOTSTRAP_START']
  self.assertIn('EOC_BERSERK_GODO_GUTS_DIRECTION',json.dumps(start))
 def test_wagon_needs_no_road_and_remains_unique_hidden_and_accessible(self):
  s=special('early_caravan','berserk_early_caravan_special')
  self.assertNotIn('connections',s);self.assertIn('GLOBALLY_UNIQUE',s['flags']);self.assertEqual(s['occurrences'],[0,0])
  self.assertNotIn('reveal_map',json.dumps(EOCS[P+'WAGON_NEW_AREA']))
  self.assertNotIn('assign_mission',json.dumps(EOCS[P+'WAGON_NEW_AREA']))
 def test_oak_and_first_lair_have_real_forest_between_them_and_other_sites(self):
  for file,id_,radius in [('behelit_sites','berserk_cursed_oak_special',2),('behelit_sites','berserk_echo_cave_special',2),('first_hunt','berserk_first_hunt_special',3),('godo_workshop','berserk_godo_workshop_special',3)]:
   s=special(file,id_);parts={tuple(p['point']):p for p in s['overmaps']}
   for x in range(-radius,radius+1):
    for y in range(-radius,radius+1):
     self.assertIn((x,y,0),parts)
     if (x,y)!=(0,0):self.assertEqual(parts[x,y,0]['locations'],['forest'])
 def test_paper_is_alone_on_a_real_table_instead_of_buried_under_forge_tools(self):
  m=next(o['object'] for o in load('mapgen/godo_workshop.json') if o.get('om_terrain')=='berserk_godo_workshop')
  paper=next(x for x in m['place_item'] if x['item']=='berserk_forge_woodland_sketch')
  self.assertEqual((paper['x'],paper['y'],paper['chance']),(10,17,100))
  self.assertEqual([x['item'] for x in m['place_item'] if (x['x'],x['y'])==(10,17)],['berserk_forge_woodland_sketch'])
  self.assertIn({'furn':'f_table','x':10,'y':17},m['place_furniture'])
 def test_woodland_route_is_bounded_checks_real_success_and_keeps_previous_target(self):
  for k in ['OAK','CAVE']:
   o=EOCS[F+'FIND_'+k]['effect'];self.assertEqual(o['target_params']['search_range'],80);self.assertTrue(o['target_params']['random'])
   self.assertEqual(o['true_eocs'],[P+'WOODLAND_VERIFY'])
  guard=EOCS[P+'WOODLAND_VERIFY']['effect'];self.assertEqual(guard['else'],{'run_eocs':F+'LEAD_FAILED'})
  read=EOCS[F+'BEHELIT_LEAD_READ']['effect'][1]
  self.assertEqual(read['if'],{'math':['u_berserk_stone_route_issued == 1']});self.assertIn('reveal_map',read['then'])
 def test_removed_warning_stays_silent_but_still_consumes_its_marker(self):
  self.assertEqual(EOCS['EOC_BERSERK_ECLIPSE_SCENE_WARNING']['effect'],[])
  o=EOCS['EOC_BERSERK_ECLIPSE_GATE_WARNING'];self.assertNotIn('u_message',json.dumps(o));self.assertIn('berserk_eclipse_warning_seen',json.dumps(o))

class Navigation(unittest.TestCase):
 def test_active_godo_order_takes_one_choice_without_an_order_selector(self):
  f=Godo();f.values['u_berserk_godo_early_state']=1
  self.assertIn(G+'_EARLY_SWORD',targets(f,G));self.assertNotIn(G+'_ORDERS',targets(f,G));self.assertNotIn(G+'_SWORD',targets(f,G))
  f.choose(G,G+'_EARLY_SWORD')
 def test_a_started_order_does_not_repeat_its_first_sales_pitch(self):
  f=Godo();f.values['u_berserk_godo_early_state']=1
  self.assertIn(G+'_EARLY_SWORD',targets(f,G+'_WORK'));self.assertNotIn(G+'_WEAPON_REQUEST',targets(f,G+'_WORK'))
 def test_hand_help_is_actionable_without_repeating_the_mechanism_lecture(self):
  f=Rickert();f.met();f.bionics.add('bio_berserk_hand_stump');f.values['u_berserk_godo_arm_state']=1
  self.assertIn(G+'_ARM_STATUS',targets(f,R));f.choose(R,G+'_ARM_STATUS')
  self.assertIn(G+'_ARM_STATUS',targets(f,R+'_ORDERS'))
 def test_intact_hand_has_no_path_to_prosthesis_order_through_any_new_menu(self):
  f=Rickert();f.met();seen=reachable(f,R)
  self.assertNotIn(G+'_ARM_STATUS',seen);self.assertNotIn(G+'_ARM',seen)
 def test_known_band_is_reachable_but_a_stranger_must_first_hear_about_it(self):
  f=Rickert();f.met();past='TALK_BERSERK_NOV02B_RICKERT_PAST'
  self.assertNotIn(R+'_BAND',targets(f,past))
  f.choose(R,'TALK_BERSERK_NOV02B_RICKERT_SELF');f.choose('TALK_BERSERK_NOV02B_RICKERT_SELF',R+'_RECENT_DAYS')
  self.assertIn(R+'_BAND',targets(f,past));self.assertIn(past,targets(f,R))
 def test_return_from_a_side_answer_does_not_require_asking_for_the_same_section_again(self):
  f=Rickert();f.met();rs=f.available(R+'_TACTICS')
  self.assertIn(R+'_MECHANISMS',{r['topic'] for r in rs});self.assertIn(R,{r['topic'] for r in rs})
 def test_new_group_menus_always_have_a_real_available_question_when_shown(self):
  for f,root in [(Rickert(),R),(Godo(),G)]:
   if isinstance(f,Rickert):f.met()
   for r in f.available(root):
    t=r['topic']
    if t.startswith('TALK_BERSERK_NOV02B_'):self.assertTrue(targets(f,t)-{root},t)
 def test_sketch_dialogue_hands_over_paper_without_silently_reading_it(self):
  f=Godo();t='TALK_BERSERK_FIX28_GODO_SKETCH';rs=f.available(t)
  self.assertTrue(any('u_spawn_item' in json.dumps(r) for r in rs))
  self.assertFalse(any('BEHELIT_LEAD_READ' in json.dumps(r.get('effect')) for r in rs))
if __name__=='__main__':unittest.main()
