"""Targeted JSON transaction checks; not native worldgen, movement or UI."""
import copy
import json
import unittest
from pathlib import Path

MOD=Path(__file__).resolve().parents[1]/'mods/Berserk'
def rows(path):return json.loads((MOD/path).read_text())
class Road:
    def __init__(self,key):
        self.eocs={r['id']:r for r in rows('effects/road_stories_eocs.json') if r['type']=='effect_on_condition'}
        self.transforms={r['id']:r for r in rows('effects/road_stories_eocs.json') if r['type']=='ter_furn_transform'}
        self.pos=(5,5,0);self.actor=(5,4,0);self.rope=False;self.loot=[]
        self.furn={self.pos:'f_berserk_road_'+key,(20,20,0):'f_berserk_road_'+key}
    def condition(self,v):
        if 'and' in v:return all(self.condition(c) for c in v['and'])
        if 'math' in v:return max(abs(a-b) for a,b in zip(self.pos,self.actor))<=1
        if 'map_furniture_id' in v:return self.furn[self.pos]==v['map_furniture_id']
        if 'u_has_items' in v:return self.rope
        raise AssertionError(v)
    def run(self,key):
        e=self.eocs['EOC_BERSERK_ROAD_'+key.upper()]
        if self.condition(e['condition']):self.effect(e['effect'])
    def effect(self,v):
        if isinstance(v,list):
            for x in v:self.effect(x)
        elif 'if' in v:
            if self.condition(v['if']):self.effect(v['then'])
        elif 'u_transform_radius' in v:
            rule=self.transforms[v['ter_furn_transform']]['furniture'][0]
            if self.furn[self.pos] in rule['valid_furniture']:self.furn[self.pos]=rule['result']
        elif 'map_spawn_item' in v:self.loot.append(v['map_spawn_item'])
        elif 'turn_cost' in v or 'u_message' in v:pass
        else:raise AssertionError(v)

class RoadStories(unittest.TestCase):
    def test_either_outcome_is_finite_and_does_not_claim_other_instances(self):
        choices={'caravan':['provisions','iron'],'scout':['pack','bundle'],'camp':['bed','blanket']}
        for key,options in choices.items():
            for picked in options:
                with self.subTest(key=key,picked=picked):
                    g=Road(key);g.rope=True;g.run(key+'_'+picked)
                    saved=copy.deepcopy(g)
                    for _ in range(2):
                        for option in options:saved.run(key+'_'+option)
                    self.assertEqual(len(saved.loot),1)
                    self.assertEqual(saved.furn[(20,20,0)],'f_berserk_road_'+key)
    def test_remote_choices_cannot_transform_or_claim(self):
        g=Road('caravan');g.actor=(0,0,0);g.run('caravan_iron')
        self.assertFalse(g.loot);self.assertEqual(g.furn[g.pos],'f_berserk_road_caravan')
    def test_rope_is_a_reusable_tool_and_small_bundle_is_an_alternative(self):
        g=Road('scout');g.run('scout_pack');self.assertFalse(g.loot)
        g.rope=True;g.run('scout_pack');self.assertTrue(g.rope);self.assertEqual(len(g.loot),1)
        g=Road('scout');g.run('scout_bundle');self.assertEqual(len(g.loot),1)
    def test_leave_response_has_no_effect(self):
        for topic in rows('dialogue/road_stories.json'):
            leave=topic['responses'][-1]
            self.assertEqual(leave['topic'],'TALK_DONE');self.assertNotIn('effect',leave)
    def test_rare_worldgen_has_no_ambush_or_eclipse_gate(self):
        specials=[r for r in rows('overmap/road_stories.json') if r['type']=='overmap_special']
        self.assertEqual(len(specials),3)
        for s in specials:
            self.assertEqual(s['flags'],['OVERMAP_UNIQUE'])
            self.assertLessEqual(s['occurrences'][0],15);self.assertEqual(s['occurrences'][1],100)
        for mapgen in rows('mapgen/road_stories.json'):
            obj=mapgen['object'];self.assertNotIn('place_monster',obj)
            self.assertEqual(len(obj['rows']),24);self.assertTrue(all(len(row)==24 for row in obj['rows']))
        text=json.dumps(rows('effects/road_stories_eocs.json'))
        self.assertNotIn('u_spawn_monster',text);self.assertNotIn('berserk_eclipse_era',text)
    def test_godo_is_global_unique_and_bootstrapped_without_revealing_it(self):
        special=next(r for r in rows('overmap/godo_workshop.json') if r['type']=='overmap_special')
        self.assertIn('GLOBALLY_UNIQUE',special['flags']);self.assertEqual(special['occurrences'],[0,1])
        self.assertEqual(special['overmaps'][0]['locations'],['forest'])
        eocs={r['id']:r for r in rows('effects/godo_eocs.json')}
        seek=eocs['EOC_BERSERK_GODO_SEEK']
        self.assertEqual(seek['effect'][0],{'run_eocs':'EOC_BERSERK_GODO_LOCATE'})
        for radius in [60,80,100]:
            locate=eocs['EOC_BERSERK_GODO_LOCATE_'+str(radius)]
            lookup=locate['effect']['target_params']
            self.assertEqual(lookup['om_special'],'berserk_godo_workshop_special')
            self.assertTrue(lookup['random']);self.assertEqual(lookup['search_range'],radius)
            self.assertEqual(lookup['min_distance'],0)
            self.assertEqual(locate['condition'],{'not':{'test_eoc':'EOC_BERSERK_GODO_KNOWN'}})
        self.assertNotIn('reveal_map',json.dumps(eocs['EOC_BERSERK_GODO_STORE_CANDIDATE']))
        self.assertEqual(eocs['EOC_BERSERK_GODO_BOOTSTRAP_START']['required_event'],'game_start')
        self.assertNotIn('berserk_eclipse_era',json.dumps(seek))

if __name__=='__main__':unittest.main()
