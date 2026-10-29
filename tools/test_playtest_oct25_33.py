"""Actual JSON traversal plus a narrow port of native 0.I placement semantics.

No CDDA binary is run. The world supplies forest/seen/maps; the native port
retains the troublesome existing-only replacement and mutable second-pass type.
"""
import copy
import hashlib
import json
import re
import unittest
from collections import deque

from test_playtest_oct24_33 import StrictActors
from test_reference_journal_33 import EOCS, MOD, TOPICS, RUSSIAN, walk
from test_rickert_dialogue_33 import Conversation as Rickert

P='EOC_BERSERK_FIX25_'
ROOT=MOD.parents[1]
PROJECT=json.loads((ROOT/'docs/location_projects/chapel-3.3-03.json').read_text())


class World(StrictActors):
    def __init__(self):
        super().__init__();self.beta=None
        self.pos=(179*24,0,0);self.values['u_berserk_eclipse_rescue_state']=2
        self.loaded={(0,0)};self.seen=set();self.local_maps={};self.searches=[]
        self.land={(249*24,30*24,0):'forest'}
        self.special_at={self.pos:'berserk_godo_workshop_special'}
        self.specials={o['id']:o for name in ['godo_workshop','first_hunt','local_breach']
            for o in json.loads((MOD/'overmap'/f'{name}.json').read_text()) if o['type']=='overmap_special'}
    def region(self,p):return p[0]//(180*24),p[1]//(180*24)
    def condition(self,c):
        if isinstance(c,dict) and 'overmap_at_point' in c:
            p=self.getvar(c['point'])
            self.loaded.add(self.region(p))  # native overmap_buffer.ter
            return self.land.get(tuple(p))==c['overmap_at_point']
        return super().condition(c)
    def value(self,s):
        s=re.sub(r'(?<!\w)(_berserk_\w+)\.([xyz])',lambda m:repr(self.values.get(m[1],(0,0,0))['xyz'.index(m[2])]),s)
        return super().value(s)
    def native_target(self,params):
        origin=self.pos;kind=params['om_terrain'];replaced=False
        if 'om_special' in params:
            id_=params['om_special'];special=self.specials[id_]
            for p,owner in self.special_at.items():
                if owner==id_ and self.land.get(p)==kind:return p,False
            radius=special['spawns']['radius'][1]
            for p,t in self.land.items():
                d=max(abs(p[i]//24-origin[i]//24) for i in [0,1])
                if t not in ['forest','forest_thick'] or d>params['search_range'] or p in self.local_maps:continue
                if any('SAFE_AT_WORLDGEN' in self.specials[owner].get('flags',[]) and
                    max(abs(p[i]//24-safe[i]//24) for i in [0,1])<=radius for safe,owner in self.special_at.items()):continue
                self.land[p]=kind;self.special_at[p]=id_;return p,True
            return origin,False
        for existing_only in [True,False]:
            def candidates(terrain,only_existing):
                out=[]
                for p,t in self.land.items():
                    d=max(abs(p[i]//24-origin[i]//24) for i in [0,1])
                    if t==terrain and params['min_distance']<=d<=params['search_range'] and (not only_existing or self.region(p) in self.loaded) and (not params.get('cant_see') or p not in self.seen):out.append(p)
                return out
            matches=candidates(kind,existing_only)
            if matches:return matches[0],replaced
            kind=params['om_terrain_replace']
            # Native replacement branch searches existing maps twice.
            matches=candidates(kind,True)
            if matches:
                p=matches[0];self.land[p]=params['om_terrain'];return p,True
        return origin,False
    def effect(self,x):
        if isinstance(x,dict) and 'target_params' in x:
            params=x['target_params'];self.searches.append(copy.deepcopy(params))
            p,replaced=self.native_target(params)
            scope,key=next(iter(x['u_location_variable'].items()))
            self.values[{'u_val':'u_','context_val':'_','global_val':''}[scope]+key]=p
            # Native location lookup loads the local map only AFTER selecting.
            self.local_maps.setdefault(p,self.land.get(p,'forge'))
            for id_ in x.get('true_eocs',[]):self.run(id_)
            return
        if isinstance(x,dict) and x.get('mapgen_update')=='berserk_chapel_remove_added_wall_v1':
            base=self.getvar(x['target_var'])
            update=json.loads((MOD/'mapgen/chapel_layout_hotfix.json').read_text())[0]
            for step in update['object']['set']:
                data=self.furniture if step['point']=='furniture' else self.terrain
                data[(base[0]+step['x'],base[1]+step['y'],base[2])]=step['id']
            return
        return super().effect(x)


class NativePlacement(unittest.TestCase):
    def test_cold_native_replace_can_return_unconverted_forest(self):
        f=World();f.land={(219*24,30*24,0):'forest'};params={'om_terrain':'berserk_first_hunt_lair','om_terrain_replace':'forest','min_distance':24,'search_range':48,'cant_see':True,'random':True}
        p,changed=f.native_target(params)
        self.assertFalse(changed);self.assertEqual(f.land[p],'forest')

    def test_native_special_generates_real_lair_and_mission_across_overmap_border(self):
        f=World();f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        p=f.values['u_berserk_first_hunt_location']
        self.assertEqual(f.land[p],'berserk_first_hunt_lair')
        self.assertEqual(f.local_maps[p],'berserk_first_hunt_lair')
        self.assertEqual(f.missions['MISSION_BERSERK_FIRST_HUNT'],p)
        self.assertNotEqual(f.region(p),f.region(f.pos))
        self.assertEqual(f.values['u_berserk_first_hunt_search_attempts'],1)

    def test_stalled_old_save_recovers_on_load_without_requiring_prosthesis(self):
        f=World();f.values.update(u_berserk_first_hunt_search_attempts=2,u_berserk_first_hunt_retry_at=999999)
        f.run(P+'LOAD');self.assertIn('MISSION_BERSERK_FIRST_HUNT',f.missions)
        self.assertNotIn('bio_berserk_arm_cannon',f.bionics)
        before=copy.deepcopy(f.missions);n=len(f.searches)
        f.run(P+'LOAD');self.assertEqual(f.missions,before);self.assertEqual(len(f.searches),n)

    def test_generated_local_maps_are_never_replaced(self):
        f=World();seen=(210*24,0,0);f.land[seen]='forest';f.seen.add(seen);f.local_maps[seen]='player_stash'
        f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertEqual(f.land[seen],'forest');self.assertEqual(f.local_maps[seen],'player_stash')

    def test_failed_attempts_have_cooldown_then_retry_without_reading_book(self):
        f=World();f.land={};f.run(P+'FIRST_RETRY');n=len(f.searches)
        self.assertFalse(f.missions)
        f.run(P+'FIRST_RETRY');self.assertEqual(len(f.searches),n)
        f.now+=3601;f.land={(249*24,30*24,0):'forest'}
        f.run(P+'FIRST_RETRY');self.assertIn('MISSION_BERSERK_FIRST_HUNT',f.missions)


class Discovery(unittest.TestCase):
    def test_expedition_and_chapel_physical_examination_teach_forge_route(self):
        for id_ in ['EOC_BERSERK_SCENERY_EXPEDITION','EOC_BERSERK_EXPEDITION_RECORD','EOC_BERSERK_CHAPEL_RECORD']:
            f=World();f.run(id_)
            self.assertEqual(f.values['u_berserk_journal_knows_godo'],1,id_)
            self.assertIn('MISSION_BERSERK_GODO',f.missions,id_)

    def test_reading_old_expedition_note_adds_new_route_once(self):
        f=World();f.values['u_berserk_journal_read_berserk_expedition_transfer_note']=1
        f.run('EOC_BERSERK_READ_EXPEDITION_TRANSFER_NOTE');n=f.calls.count('EOC_BERSERK_GODO_LEARN_TRACE')
        f.run('EOC_BERSERK_READ_EXPEDITION_TRANSFER_NOTE')
        self.assertEqual(f.calls.count('EOC_BERSERK_GODO_LEARN_TRACE'),n)
        self.assertIn('Godo',EOCS['EOC_BERSERK_READ_EXPEDITION_TRANSFER_NOTE']['effect'][0]['u_message'])

    def test_arrival_hint_is_one_popup_and_never_reads_source_or_gives_route(self):
        f=World();f.om='berserk_road_caravan'
        for _ in range(6):f.run(P+'ARRIVAL')
        self.assertEqual(len(f.messages),1)
        self.assertNotIn('u_berserk_journal_knows_godo',f.values)
        self.assertNotIn('u_berserk_journal_read_berserk_road_caravan_note',f.values)
        self.assertFalse(f.missions)
        f.values=json.loads(json.dumps(f.values));f.run(P+'ARRIVAL');self.assertEqual(len(f.messages),1)

    def test_stranger_hears_band_name_before_asking_and_guts_already_knows(self):
        f=Rickert();f.met();band='TALK_BERSERK_RICKERT_BAND'
        self.assertNotIn(band,[r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])
        f.choose('TALK_BERSERK_RICKERT','RECENT_DAYS')
        self.assertEqual(f.values['u_berserk_rickert_knows_band'],1)
        self.assertIn('Band of the Hawk',f.line('RECENT_DAYS'))
        self.assertIn(band,[r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])
        f=Rickert();f.overrides['EOC_BERSERK_FORGE_GUTS']=True
        self.assertIn(band,[r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])


class GraphicsAndChapel(unittest.TestCase):
    def test_all_five_authored_pngs_unchanged_and_bound_for_supported_tilesets(self):
        policy=json.loads((ROOT/'docs/authored-common-sprites-2026-10-25.json').read_text())
        for entry in policy['sheets']:
            self.assertEqual(hashlib.sha256((MOD/entry['file']).read_bytes()).hexdigest(),entry['sha256'])
            obj=json.loads((MOD/entry['definition']).read_text())[0]
            self.assertEqual(obj['compatibility'],policy['compatibility'])
            ids=obj['tiles-new'][0]['tiles'][0]['id'];ids=[ids] if isinstance(ids,str) else ids
            self.assertEqual(ids,entry['ids'])
        self.assertTrue(any('mon_berserk_chapel_guardian' in x['ids'] for x in policy['sheets']))

    def test_export_is_exact_project_and_crossed_furniture_is_gone(self):
        rows=json.loads((MOD/'mapgen/behelit_sites.json').read_text())
        maps=[next(x for x in rows if x.get('om_terrain')==[id_]) for id_ in ['berserk_desecrated_chapel_reliquary','berserk_desecrated_chapel_nave']]
        grid=maps[0]['object']['rows']+maps[1]['object']['rows']
        self.assertEqual(grid,PROJECT['rows'])
        for x,y in PROJECT['annotation']['wall_add']:
            self.assertEqual(grid[y][x],'+' if [x,y] in PROJECT['annotation']['doors'] else '#')
        placed={(f['x'],f['y']+24*i):f['furn'] for i,m in enumerate(maps) for f in m['object']['place_furniture']}
        self.assertFalse(any(placed.get((x,9))=='f_berserk_chapel_altar' for x in range(10,15)))
        self.assertNotIn('f_makeshift_bed',placed.values())
        for (x,y),f in placed.items():self.assertNotIn(grid[y][x],'#+',f)
        for i,m in enumerate(maps):
            for item in m['object'].get('place_loot',[]):self.assertTrue(0<=item['x']<24 and 0<=item['y']<24,item)

    def test_relic_guardian_both_exits_and_furniture_have_connected_approaches(self):
        rows=PROJECT['rows'];blocked={(f['x'],f['y']) for f in PROJECT['furniture'] if f['furn']!='f_chair'}
        start=(12,41);seen={start};q=deque([start])
        while q:
            x,y=q.popleft()
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                p=(x+dx,y+dy)
                if 0<=p[0]<24 and 0<=p[1]<48 and p not in seen and rows[p[1]][p[0]] not in '#TwG' and p not in blocked:
                    seen.add(p);q.append(p)
        for target in [(12,7),(12,12),(11,42),(12,42),(3,37),(3,38),(9,40),(18,7)]:self.assertIn(target,seen,target)
        for f in PROJECT['furniture']:
            self.assertTrue(any((f['x']+dx,f['y']+dy) in seen for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]),f)


if __name__=='__main__':unittest.main()
