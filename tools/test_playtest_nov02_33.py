"""Regression checks for the full apostle-route playtest.

Actual exported data and a small flood-fill; no native game/AI benchmark.
"""
import json,unittest,hashlib
from collections import deque
from test_reference_journal_33 import MOD,EOCS,TOPICS,walk
from test_named_apostle_dialogues_33 import Contract
ROOT=MOD.parents[1];P='EOC_BERSERK_NOV02_'
def load(f):return json.loads((MOD/f).read_text())
class RoadAndForge(unittest.TestCase):
 def test_wagon_can_be_reached_from_its_actual_south_road(self):
  body=load('mapgen/early_caravan.json')[0]['object'];rows=body['rows'];seen={(11,23)};queue=deque(seen)
  while queue:
   x,y=queue.popleft()
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
    q=(x+dx,y+dy)
    if 0<=q[0]<24 and 0<=q[1]<24 and q not in seen and rows[q[1]][q[0]] in '.pu':seen.add(q);queue.append(q)
  self.assertIn((16,10),seen)
 def test_forge_is_unique_story_placement_and_holds_an_actual_sketch(self):
  special=next(o for o in load('overmap/godo_workshop.json') if o['type']=='overmap_special')
  self.assertEqual(special['occurrences'],[0,0]);self.assertIn('GLOBALLY_UNIQUE',special['flags'])
  room=next(o for o in load('mapgen/godo_workshop.json') if o.get('om_terrain')=='berserk_godo_workshop')
  papers=[i for i in room['object']['place_item'] if i['item']=='berserk_forge_woodland_sketch']
  self.assertEqual(len(papers),1);self.assertEqual(papers[0]['amount'],1)
class NaturalFire(unittest.TestCase):
 def test_no_blanket_ruins_update_at_any_legacy_layout(self):
  self.assertEqual(EOCS['EOC_BERSERK_FLORA_UPDATE_RUINS']['effect'],[])
 def test_escape_does_not_synchronously_generate_a_fortress(self):
  actions=list(walk(EOCS['EOC_BERSERK_FLORA_ESCAPED']['effect']))
  self.assertFalse(any(a.get('run_eocs')=='EOC_BERSERK_GRUNBELD_SEEK' for a in actions))
  queued=next(a for a in actions if a.get('run_eocs')==P+'GRUNBELD_RETRY')
  self.assertEqual(queued['time_in_future'],'5 seconds')
 def test_zodd_anchor_is_on_the_opposite_side_from_west_and_south_exits(self):
  anchors=[x for x in walk(load('effects/flora_siege_eocs.json')) if x.get('location_variable_adjust')=={'global_val':'berserk_flora_zodd_anchor'}]
  self.assertTrue(anchors);self.assertTrue(all(x['x_adjust']>=40 and x['y_adjust']<=5 for x in anchors))
class Placements(unittest.TestCase):
 def test_fortress_placement_allows_mixed_wilderness_not_six_forest_cells_only(self):
  special=next(o for o in load('overmap/grunbeld_hunt.json') if o['type']=='overmap_special')
  self.assertTrue(all(s['locations']==['wilderness'] for s in special['overmaps']))
  self.assertLess(special['spawns']['radius'][1],104)
 def test_failed_lookup_never_calls_itself_recursively(self):
  self.assertFalse(any(n.get('run_eocs')=='EOC_BERSERK_GRUNBELD_FIND' for n in walk(EOCS['EOC_BERSERK_SITE_GRUNBELD_FAILED'])))
  obj=EOCS['EOC_BERSERK_GRUNBELD_FIND']
  self.assertIn('retry_at',json.dumps(obj['condition']));self.assertIn('attempts02 < 3',json.dumps(obj['condition']))
  expressions=[n['math'][0] for n in walk(obj['condition']) if 'math' in n]
  self.assertEqual(expressions.count("time('now') >= u_berserk_grunbeld_retry_at"),1)
  self.assertEqual(obj['effect'].count({'math':['u_berserk_grunbeld_attempts02 = u_berserk_grunbeld_attempts02 + 1']}),1)
  queries=[n['target_params'] for n in walk(obj) if 'target_params' in n]
  self.assertTrue(queries);self.assertTrue(all(p['search_range']==128 for p in queries))
 def test_a_new_area_restores_a_finite_budget_without_a_journal(self):
  o=EOCS[P+'GRUNBELD_NEW_AREA'];self.assertIn('1152',json.dumps(o['condition']));self.assertIn('attempts02 = 0',json.dumps(o['effect']));self.assertNotIn('journal',json.dumps(o));self.assertEqual(o['recurrence'],'1 minute')
 def test_three_hunt_searches_are_spread_over_turns(self):
  calls=[n for n in walk(EOCS['EOC_BERSERK_KNOWN_ROUTES_NOW']) if n.get('run_eocs','').startswith('EOC_BERSERK_JOURNAL_LOCATE_') and any(k in n['run_eocs'] for k in ['COUNT','WYALD','ROSINE'])]
  self.assertEqual({n['time_in_future'] for n in calls},{'1 seconds','2 seconds','3 seconds'})
class CountAndChoices(unittest.TestCase):
 def test_all_shared_door_symbols_are_actual_bars(self):
  palette=next(o for o in load('mapgen/apostle_count_palettes.json') if o['id']=='berserk_count_palette')
  self.assertEqual(palette['terrain']['+'],'t_door_bar_locked')
 def test_accepted_line_can_speak_without_accepting_another_line(self):
  for k in ['COUNT','WYALD','ROSINE']:
   f=Contract(k);f.values['u_berserk_apostol_path']=1
   available=f.available('TALK_BERSERK_NOV02_'+k)
   self.assertEqual(len(available),2)
   self.assertTrue(all(r['topic']=='TALK_DONE' and 'effect' not in r for r in available))
 def test_opening_does_not_interrupt_an_already_wounded_boss(self):
  for k in ['COUNT','WYALD','ROSINE']:
   o=EOCS[P+k+'_SEEN'];self.assertIn('u_hp_max',json.dumps(o['effect']['if']))
   self.assertFalse(any(n.get('run_eocs')==P+k+'_OPEN' for n in walk(o['effect']['else'])))
class FurnitureAndItems(unittest.TestCase):
 def test_papers_are_items_on_real_tables_and_keep_the_original_readers(self):
  source=json.loads((ROOT/'docs/location_projects/flora-3.3-05.json').read_text());f={(x,y):k for k,x,y in source['furniture']}
  maps=load('mapgen/flora_manor.json');all_items=[]
  for i,o in enumerate(maps):
   all_items.extend((x['item'],x['x']+(i%2)*24,x['y']+(i//2)*24) for x in o['object']['place_item'])
  for note in source['loose_notes']:
   self.assertEqual(f[note['x'],note['y']],'f_table')
   self.assertTrue(any((x,y)==(note['x'],note['y']) for _,x,y in all_items))
  for item in load('items/flora_loose_papers.json'):
   self.assertTrue(item['use_action']['effect_on_conditions']);self.assertEqual(item['subtypes'],['TOOL']);self.assertIn('str_sp',item['name'])
 def test_books_and_dried_vegetables_are_really_present(self):
  items=[x for o in load('mapgen/flora_manor.json') for x in o['object']['place_item']]
  self.assertFalse(any(x['item']=='dry_meat' for x in items));self.assertTrue(any(x['item']=='dry_veggy' for x in items))
  self.assertTrue({'textbook_botany','fairy_tales','isherwood_herbal_remedies'}<={x['item'] for x in items})
 def test_cardinal_native_sprites_are_pinned_and_do_not_rotate_again(self):
  spec=json.loads((ROOT/'docs/flora-native-furniture-2026-11-02.json').read_text())
  self.assertEqual(hashlib.sha256((MOD/spec['sheet']).read_bytes()).hexdigest(),spec['sha256'])
  tile=load('flora_oriented_tileset.json')[0]['tiles-new'][0];self.assertTrue(all(t.get('rotates') is False for t in tile['tiles']))
  self.assertEqual(len(tile['tiles']),7)
if __name__=='__main__':unittest.main()
