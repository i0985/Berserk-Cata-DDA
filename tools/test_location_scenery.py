"""Data/geometry checks for scenery and finite cocoons; no native game run.

The walk model treats ordinary doors as openable and walls/tent walls as
blocking. It does not reproduce pathfinding, sound, fire or map loading.
"""
import copy
import gettext
import json
import unittest
from collections import deque

from test_behelit_rewards import MOD, objects

FILES = ['behelit_sites.json','first_hunt.json','local_breach.json',
         'apostle_wyald.json','apostle_rosine.json','flora_manor.json','apostle_grunbeld.json']
PALETTES = {o['id']:o for p in (MOD/'mapgen').glob('*.json') for o in objects(p)
            if o['type']=='palette'}
FURNITURE = {o['id']:o for p in MOD.rglob('*.json')
             for o in objects(p) if o['type']=='furniture'}

def surfaces(obj):
    terrain={};furn={}
    for name in obj.get('palettes',[]):
        terrain.update(PALETTES[name].get('terrain',{}))
        furn.update(PALETTES[name].get('furniture',{}))
    terrain.update(obj.get('terrain',{}));furn.update(obj.get('furniture',{}))
    ts={(x,y):terrain.get(c,obj.get('fill_ter')) for y,row in enumerate(obj['rows']) for x,c in enumerate(row)}
    fs={(x,y):furn[c] for y,row in enumerate(obj['rows']) for x,c in enumerate(row) if c in furn}
    fs.update({(f['x'],f['y']):f['furn'] for f in obj.get('place_furniture',[])})
    return ts,fs

def walkable(ter,furn):
    if ter in ('t_wall','t_rock','t_tree','t_window_domestic','t_chainfence'):return False
    if furn in ('f_canvas_wall','f_large_canvas_wall','f_crate_o','f_rack','f_bookcase'):return False
    return FURNITURE.get(furn,{}).get('move_cost_mod',0)>=0

def reachable(ts,fs,start):
    q=deque([start]);seen={start}
    while q:
        x,y=q.popleft()
        for pos in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if pos in ts and pos not in seen and walkable(ts[pos],fs.get(pos)):
                seen.add(pos);q.append(pos)
    return seen

class CocoonGraph:
    """Exercise actual EOCs, modeling only the supported furniture transaction."""
    def __init__(self, free=True, consent=True):
        self.pos=(-231,66,0);self.avatar=(-230,66,0)
        self.furniture={self.pos:'f_berserk_rosine_cocoon_inhabited'}
        self.free=free;self.consent=consent;self.spawned=[];self.messages=[];self.loot=[]
        self.eocs={o['id']:o for o in objects(MOD/'effects/rosine_cocoon_eocs.json') if o['type']=='effect_on_condition'}
        self.transform=next(o for o in objects(MOD/'effects/rosine_cocoon_eocs.json') if o['type']=='ter_furn_transform')
    def condition(self,v):
        if 'map_furniture_id' in v:
            assert v['loc']=={'context_val':'pos'}
            return self.furniture[self.pos]==v['map_furniture_id']
        if 'u_query' in v:return self.consent
        raise AssertionError(v)
    def run(self,id):
        e=self.eocs[id]
        if 'condition' not in e or self.condition(e['condition']):self.effect(e['effect'])
    def effect(self,v):
        if isinstance(v,list):
            for child in v:self.effect(child)
        elif 'if' in v:
            if self.condition(v['if']):self.effect(v['then'])
        elif 'u_spawn_monster' in v:
            assert v['real_count']==1 and v['target_var']=={'context_val':'pos'}
            if self.free:self.spawned.append((v['u_spawn_monster'],self.pos))
            for e in v['true_eocs' if self.free else 'false_eocs']:self.run(e)
        elif 'u_transform_radius' in v:
            assert v['u_transform_radius']==0 and v['target_var']=={'context_val':'pos'}
            for t in self.transform['furniture']:
                if self.furniture[self.pos] in t['valid_furniture']:self.furniture[self.pos]=t['result']
        elif 'map_spawn_item' in v:
            assert v['loc']=={'context_val':'pos'}
            self.loot.append((v['map_spawn_item'],v['count'],self.pos))
        elif 'u_message' in v:self.messages.append(v['u_message'])
        else:raise AssertionError(v)

class LocationSceneryTests(unittest.TestCase):
    def test_maps_have_complete_24_square_rows_and_mapped_symbols(self):
        for file in FILES:
            for o in objects(MOD/'mapgen'/file):
                if 'om_terrain' not in o:continue
                m=o['object'];ts,fs=surfaces(m)
                self.assertEqual(len(m['rows']),24,o['om_terrain'])
                self.assertTrue(all(len(row)==24 for row in m['rows']),o['om_terrain'])
                self.assertNotIn(None,ts.values(),o['om_terrain'])
                for actor in m.get('place_monster',[]):
                    p=(actor['x'],actor['y'])
                    self.assertTrue(walkable(ts[p],fs.get(p)),(o['om_terrain'],p))

    def test_cocoon_once_per_cell_blocked_retry_decline_and_state_copy(self):
        for consent in (False,True):
            g=CocoonGraph(consent=consent);g.run('EOC_BERSERK_COCOON_OPEN')
            self.assertEqual(len(g.spawned),int(consent))
            saved=copy.deepcopy(g);saved.consent=True
            for _ in range(5):saved.run('EOC_BERSERK_COCOON_OPEN')
            self.assertEqual(len(saved.spawned),1)
            self.assertEqual(saved.loot,[('rag',2,saved.pos)])
            self.assertEqual(saved.furniture[saved.pos],'f_berserk_rosine_cocoon')
        g=CocoonGraph(free=False)
        for _ in range(3):g.run('EOC_BERSERK_COCOON_OPEN')
        self.assertFalse(g.spawned);self.assertEqual(g.furniture[g.pos],'f_berserk_rosine_cocoon_inhabited')
        g.free=True;g.run('EOC_BERSERK_COCOON_OPEN');self.assertEqual(len(g.spawned),1)

    def test_empty_and_destroyed_cocoons_are_inert_with_no_recurring_spawns(self):
        for id in ('f_berserk_rosine_cocoon','f_berserk_rosine_cocoon_destroyed','f_berserk_rosine_cocoon_sealed'):
            self.assertNotIn('examine_action',FURNITURE[id])
            g=CocoonGraph();g.furniture[g.pos]=id;g.run('EOC_BERSERK_COCOON_OPEN')
            self.assertFalse(g.spawned)
        for o in objects(MOD/'effects/rosine_cocoon_eocs.json'):
            self.assertNotIn('recurrence',o);self.assertNotIn('global',o)
        for id in ('f_berserk_rosine_cocoon','f_berserk_rosine_cocoon_inhabited','f_berserk_rosine_cocoon_sealed'):
            self.assertEqual(FURNITURE[id]['bash']['furn_set'],'f_berserk_rosine_cocoon_destroyed')

    def test_two_ravagers_are_inside_cocoons_not_preplaced(self):
        o=next(m['object'] for m in objects(MOD/'mapgen/apostle_rosine.json') if m.get('om_terrain')==['berserk_rosine_cocoons'])
        _,fs=surfaces(o)
        self.assertEqual(sum(f=='f_berserk_rosine_cocoon_inhabited' for f in fs.values()),2)
        self.assertFalse(o['place_monster'])
        self.assertIn('f_berserk_rosine_cocoon',fs.values())
        self.assertIn('f_berserk_rosine_cocoon_sealed',fs.values())

    def test_expedition_is_canvas_camp_with_accessible_relic_and_sleeping_gear(self):
        m=next(x['object'] for x in objects(MOD/'mapgen/behelit_sites.json') if x.get('om_terrain')==['berserk_lost_expedition'])
        ts,fs=surfaces(m);seen=reachable(ts,fs,(11,23))
        self.assertNotIn('t_wall',ts.values());self.assertIn('f_canvas_wall',fs.values())
        self.assertTrue(any(p in seen for p in ((17,6),(19,6),(18,5),(18,7))))
        self.assertGreaterEqual(sum(x['item']=='sleeping_bag_roll' for x in m['place_loot']),4)
        self.assertIn((2,20),seen)  # Alarm outside the medical tent.
        self.assertEqual(fs[(2,20)],'f_berserk_expedition_noisemaker')
        for pos in ((5,6),(18,6),(8,17),(19,18)):
            self.assertEqual(ts[pos],'t_berserk_expedition_groundsheet')

    def test_eight_story_features_are_reachable_from_the_site_approach(self):
        expected={o['id'] for o in objects(MOD/'furniture/location_scenery.json')}
        found=set()
        for file in FILES:
            for o in objects(MOD/'mapgen'/file):
                if 'om_terrain' not in o:continue
                ts,fs=surfaces(o['object'])
                features=[(p,f) for p,f in fs.items() if f in expected]
                if not features:continue
                # Select the largest edge-connected walkable component.
                edges=[p for p in ts if (p[0] in (0,23) or p[1] in (0,23)) and walkable(ts[p],fs.get(p))]
                seen=max((reachable(ts,fs,p) for p in edges),key=len)
                for p,f in features:
                    self.assertTrue(p in seen or any(q in seen for q in ((p[0]-1,p[1]),(p[0]+1,p[1]),(p[0],p[1]-1),(p[0],p[1]+1))),f)
                    found.add(f)
        self.assertEqual(found,expected)

    def test_flora_escape_paths_survive_furniture_and_each_siege_patch(self):
        raw=objects(MOD/'mapgen/flora_manor.json')
        tiles={o['om_terrain'][0]:o['object'] for o in raw}
        parts={'west':(0,0),'east':(24,0),'garden_west':(0,24),'garden_east':(24,24)}
        ts={};fs={}
        for name,(dx,dy) in parts.items():
            id='berserk_flora_'+('manor_'+name if not name.startswith('garden_') else name)
            t,f=surfaces(tiles[id]);ts.update({(x+dx,y+dy):v for (x,y),v in t.items()});fs.update({(x+dx,y+dy):v for (x,y),v in f.items()})
        for phase in ('peaceful','warning','collapse','ruins'):
            t=copy.deepcopy(ts);f=copy.deepcopy(fs)
            for o in objects(MOD/'mapgen/flora_siege_updates.json'):
                prefix='berserk_flora_'+phase+'_'
                if not o['update_mapgen_id'].startswith(prefix):continue
                dx,dy=parts[o['update_mapgen_id'][len(prefix):]]
                for change in o['object'].get('set',[]):
                    for y in range(change['y'],change.get('y2',change['y'])+1):
                        for x in range(change['x'],change.get('x2',change['x'])+1):
                            (t if 'terrain' in change.values() else f)[(x+dx,y+dy)]=change['id']
            # Custom ruined wall is also impassable in the model.
            t={p:'t_wall' if v=='t_berserk_flora_charred_wall' else v for p,v in t.items()}
            seen=reachable(t,f,(15,12))
            self.assertIn((0,14),seen,phase);self.assertIn((24,47),seen,phase)

    def test_new_messages_are_available_in_both_compiled_catalogs(self):
        messages=set()
        def walk(v):
            if isinstance(v,list):
                for x in v:walk(x)
            elif isinstance(v,dict):
                for k,x in v.items():
                    if k in ('name','description','u_message','u_query') and isinstance(x,str):messages.add(x)
                    walk(x)
        for path in ('furniture/location_scenery.json','effects/location_scenery_eocs.json','furniture/rosine_cocoons.json','effects/rosine_cocoon_eocs.json'):
            walk(objects(MOD/path))
        for lang in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{lang}/LC_MESSAGES/Berserk.mo').open('rb') as f:cat=gettext.GNUTranslations(f)
            self.assertFalse([m for m in messages if cat.gettext(m)==m],lang)

if __name__=='__main__':unittest.main()
