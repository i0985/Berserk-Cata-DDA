"""Replay the field EOCs' finite-cell transactions, without launching CDDA.

Only the location/spawn/transform subset used here is interpreted. This checks
retry and save-state behavior; it does not simulate native AI or map loading.
"""
import copy
import json
import unittest
from pathlib import Path

MOD=Path(__file__).resolve().parents[1]/'mods/Berserk'
OBJECTS=json.loads((MOD/'effects/eclipse_field_events.json').read_text())
EOCS={o['id']:o for o in OBJECTS if o['type']=='effect_on_condition'}
TRANSFORMS={o['id']:o for o in OBJECTS if o['type']=='ter_furn_transform'}
SCENES=('FEAST_ONE','FEAST_TWO','FEAST_THREE','SIDE_HUNTER','CACHE_ONE','CACHE_TWO')


class FieldTransaction:
    def __init__(self):
        self.vars={};self.furniture={};self.visible=set();self.occupied=set()
        self.monsters={};self.messages=[];self.avatar=(0,0)

    def add_scene(self,name,pos):
        id=EOCS['EOC_BERSERK_ECLIPSE_'+name+'_SCAN']['effect']['furniture']
        self.furniture[pos]=id

    def loc(self,v):return self.vars[v['context_val']]

    def condition(self,c):
        if 'not' in c:return not self.condition(c['not'])
        if 'map_furniture_id' in c:return self.furniture.get(self.loc(c['loc']))==c['map_furniture_id']
        if 'u_can_see_location' in c:return self.loc(c['u_can_see_location']) in self.visible
        raise AssertionError(c)

    def run(self,id):
        e=EOCS[id]
        if 'condition' not in e or self.condition(e['condition']):self.effect(e['effect'])

    def effect(self,e):
        if isinstance(e,list):
            for v in e:self.effect(v)
        elif 'if' in e:
            if self.condition(e['if']):self.effect(e['then'])
        elif 'u_location_variable' in e:
            found=[p for p,f in self.furniture.items() if f==e['furniture']
                   and max(abs(p[0]-self.avatar[0]),abs(p[1]-self.avatar[1]))<=e['target_max_radius']]
            if found:
                self.vars[e['u_location_variable']['context_val']]=found[0]
                for id in e['true_eocs']:self.run(id)
        elif 'location_variable_adjust' in e:
            x,y=self.loc(e['location_variable_adjust'])
            self.vars[e['output_var']['context_val']]=(x+e['x_adjust'],y+e['y_adjust'])
        elif 'u_spawn_monster' in e:
            pos=self.loc(e['target_var'])
            if pos not in self.occupied and pos not in self.monsters:
                self.monsters[pos]={'id':e['u_spawn_monster'],'hp':100}
                for id in e['true_eocs']:self.run(id)
        elif 'u_transform_radius' in e:
            assert e['u_transform_radius']==0,e
            pos=self.loc(e['target_var'])
            for t in TRANSFORMS[e['ter_furn_transform']]['furniture']:
                if self.furniture.get(pos) in t['valid_furniture']:self.furniture[pos]=t['result']
        elif 'u_message' in e:self.messages.append(e['u_message'])
        else:raise AssertionError(e)

    def scan(self,name):self.run('EOC_BERSERK_ECLIPSE_'+name+'_SCAN')


class EclipseSidepathTests(unittest.TestCase):
    def test_hidden_occupied_cell_retries_without_consuming_the_scene(self):
        for name in SCENES:
            with self.subTest(scene=name):
                g=FieldTransaction();g.add_scene(name,(-92,38));g.avatar=(-92,38)
                start=EOCS['EOC_BERSERK_ECLIPSE_'+name+'_START']['effect'][0]
                pocket=(-92+start['x_adjust'],38+start['y_adjust'])
                original=g.furniture[(-92,38)];g.occupied.add(pocket)
                for _ in range(3):g.scan(name)
                self.assertFalse(g.monsters);self.assertEqual(g.furniture[(-92,38)],original)
                g.occupied.clear();g.scan(name)
                self.assertEqual(len(g.monsters),1);self.assertNotEqual(g.furniture[(-92,38)],original)

    def test_visible_pocket_waits_and_saved_spent_scene_never_replaces_a_wounded_monster(self):
        for name in SCENES:
            with self.subTest(scene=name):
                g=FieldTransaction();g.add_scene(name,(62,-108));g.avatar=(62,-108)
                start=EOCS['EOC_BERSERK_ECLIPSE_'+name+'_START']['effect'][0]
                pocket=(62+start['x_adjust'],-108+start['y_adjust'])
                g.visible.add(pocket);g.scan(name);self.assertFalse(g.monsters)
                g.visible.clear();g.scan(name);g.monsters[pocket]['hp']=31
                saved=copy.deepcopy(g)
                for _ in range(8):saved.scan(name)
                self.assertEqual(saved.monsters,{pocket:{'id':g.monsters[pocket]['id'],'hp':31}})
                saved.monsters.clear();saved.scan(name);self.assertFalse(saved.monsters)

    def test_the_two_baggage_tokens_complete_independently(self):
        g=FieldTransaction();g.add_scene('CACHE_ONE',(64,11));g.add_scene('CACHE_TWO',(65,11))
        g.avatar=(65,10);g.occupied.add((62,7))
        g.scan('CACHE_ONE');g.scan('CACHE_TWO')
        self.assertEqual(set(g.monsters),{(61,7)})
        g.occupied.clear();g.scan('CACHE_ONE');g.scan('CACHE_TWO')
        self.assertEqual(set(g.monsters),{(61,7),(62,7)})
        for _ in range(5):g.scan('CACHE_ONE');g.scan('CACHE_TWO')
        self.assertEqual(len(g.monsters),2)

    def test_adjacent_overmap_entry_does_not_trigger_the_inner_pocket(self):
        for name in SCENES:
            g=FieldTransaction();g.add_scene(name,(64,11));g.avatar=(48,11)
            g.scan(name);self.assertFalse(g.monsters)
            g.avatar=(64,11);g.scan(name);self.assertEqual(len(g.monsters),1)


if __name__=='__main__':unittest.main()
