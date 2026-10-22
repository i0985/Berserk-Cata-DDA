"""The owner's marked cells, late Flora and native dialogue formatting.

Movement is a grid model, not a CDDA walk/fire/AI test.
"""
from collections import deque
import gettext
import json
from pathlib import Path
import unittest

from test_flora_dialogue_33 import Flora, EOCS
from test_godo_dialogue_33 import Conversation

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'mods/Berserk'
PROJECT=json.loads((ROOT/'docs/location_projects/flora-3.3-03.json').read_text())


def load(p):return json.loads((MOD/p).read_text())


def stitched():
    maps=load('mapgen/flora_manor.json')
    return [maps[y//24*2]['object']['rows'][y%24]+maps[y//24*2+1]['object']['rows'][y%24] for y in range(48)]


def flood(rows,start,passable,diagonal=False):
    seen={start};todo=deque([start])
    while todo:
        x,y=todo.popleft()
        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if not (dx or dy) or (not diagonal and dx and dy):continue
                p=(x+dx,y+dy)
                if 0<=p[0]<48 and 0<=p[1]<48 and p not in seen and rows[p[1]][p[0]] in passable:
                    seen.add(p);todo.append(p)
    return seen


class Oct23PlaytestFix(unittest.TestCase):
    def test_export_matches_saved_project_and_all_marked_cells(self):
        rows=stitched();self.assertEqual(rows,PROJECT['rows'])
        for x,y in PROJECT['annotation']['wall_add']:self.assertEqual(rows[y][x],'#',(x,y))
        for x,y in PROJECT['annotation']['wood_floor']:self.assertEqual(rows[y][x],'_',(x,y))

    def test_closed_house_has_no_diagonal_escape_through_wall_corners(self):
        exterior=flood(stitched(),(0,0),set('.d_r'),diagonal=True)
        for p in [(15,7),(15,15),(12,26),(18,26),(34,13),(38,8),(35,25)]:
            self.assertNotIn(p,exterior,p)

    def test_all_rooms_and_approved_exits_have_orthogonal_routes(self):
        reachable=flood(stitched(),(15,12),set('.d_r+'))
        for p in [(15,7),(12,26),(18,26),(34,13),(38,8),(35,25),
                  tuple(PROJECT['anchors']['west_exit']),*map(tuple,PROJECT['anchors']['south_exits'])]:
            self.assertIn(p,reachable,p)

    def test_furniture_is_not_placed_in_new_walls_or_on_soil(self):
        rows=stitched()
        for k,x,y in PROJECT['furniture']:
            self.assertNotIn(rows[y][x],'#WGRT+',k)
            if k in ['f_berserk_flora_aid_pantry','f_berserk_flora_manuscript']:
                self.assertIn(rows[y][x],'_r')
        self.assertEqual(PROJECT['anchors']['flora'],[15,12])
        self.assertEqual(PROJECT['anchors']['layout_marker'],[14,12])

    def test_new_marker_selects_v3_and_old_version_dispatch_remains(self):
        register=EOCS['EOC_BERSERK_FLORA_TREEHOUSE_REGISTER']['effect'][2]
        self.assertEqual(register['if']['map_furniture_id'],'f_berserk_flora_treehouse_threshold_v3')
        self.assertEqual(register['else']['if']['map_furniture_id'],'f_berserk_flora_treehouse_threshold_v2')
        updates={x['update_mapgen_id'] for p in (MOD/'mapgen').glob('flora*updates.json') for x in json.loads(p.read_text())}
        count=0
        for obj in load('effects/flora_siege_eocs.json'):
            for step in obj.get('effect',[]) if isinstance(obj.get('effect'),list) else []:
                if step.get('if')!={'math':['berserk_flora_treehouse_layout == 3']}:continue
                count+=1
                for version in [0,1,2,3]:
                    node=step
                    while 'if' in node:
                        required=int(node['if']['math'][0].rsplit(' ',1)[1])
                        node=node['then' if required==version else 'else']
                    key=node['mapgen_update'];self.assertIn(key,updates)
                    prefix=('berserk_flora_treehouse_v3_' if version==3 else 'berserk_flora_treehouse_v2_' if version==2 else 'berserk_flora_treehouse_' if version==1 else 'berserk_flora_')
                    self.assertTrue(key.startswith(prefix),(version,key))
        self.assertEqual(count,16)

    def test_eastern_wall_is_breached_only_by_v3_assault(self):
        updates=load('mapgen/flora_treehouse_v3_updates.json')
        east=next(x for x in updates if x['update_mapgen_id']=='berserk_flora_treehouse_v3_assault_east')
        self.assertIn({'point':'terrain','id':'t_berserk_flora_scorched_root_path','x':17,'y':18},east['object']['set'])
        for stage in ['warning','collapse','ruins']:
            for x in updates:
                if '_'+stage+'_' in x['update_mapgen_id']:
                    self.assertFalse(any(n['point']=='terrain' for n in x['object'].get('set',[])))

    def test_flora_does_not_generate_naturally_before_the_eclipse(self):
        special=next(x for x in load('overmap/flora_manor.json') if x['type']=='overmap_special')
        self.assertEqual(special['occurrences'],[0,0])
        self.assertIn('GLOBALLY_UNIQUE',special['flags'])

    def test_pre_eclipse_saved_marker_cannot_unlock_route_or_mission(self):
        f=Flora();f.values['berserk_eclipse_era']=0
        f.overrides['EOC_BERSERK_FLORA_KNOWN_MANOR_VALID']=True
        self.assertFalse(f.condition(EOCS['EOC_BERSERK_FLORA_ROUTE_AVAILABLE']['condition']))
        f.run('EOC_BERSERK_MISSION_FLORA');self.assertNotIn('MISSION_BERSERK_FLORA',f.missions)
        f.values['berserk_eclipse_era']=1
        self.assertTrue(f.condition(EOCS['EOC_BERSERK_FLORA_ROUTE_AVAILABLE']['condition']))
        f.values.update(u_berserk_eclipse_rescue_state=0,u_berserk_apostol_return_state=2)
        self.assertTrue(f.condition(EOCS['EOC_BERSERK_FLORA_ROUTE_AVAILABLE']['condition']))

    def test_godo_narration_does_not_receive_another_speaker_name(self):
        f=Conversation();f.overrides['EOC_BERSERK_FORGE_GUTS']=True
        english=f.line('ENTER')
        with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:
            catalog=gettext.GNUTranslations(stream)
        russian=catalog.gettext(english)
        self.assertTrue(english.startswith('&Godot'),english)
        self.assertTrue(russian.startswith('&Годо'),russian)
        self.assertEqual(english[1:].count('Godot'),1)
        self.assertEqual(russian[1:].count('Годо'),1)

    def test_reviewed_fallbacks_are_absent_but_matching_furniture_stays(self):
        objects={x.get('id'):x for p in MOD.rglob('*.json') for x in (lambda d:d if isinstance(d,list) else [d])(json.loads(p.read_text()))}
        policy=json.loads((ROOT/'docs/visual-fallbacks-2026-10-23.json').read_text())
        for x in policy['removed']:self.assertFalse(objects[x['id']].get('looks_like'),x['id'])
        for id_,look in [('t_berserk_flora_living_wall','t_wall_log'),('f_berserk_flora_wooden_chair','f_chair'),('f_berserk_flora_cosmology_shelf','f_bookcase'),('true_guts_early_sword','mc_zweihander')]:
            self.assertEqual(objects[id_]['looks_like'],look)


if __name__=='__main__':unittest.main()
