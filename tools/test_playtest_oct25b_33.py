"""Regressions from the second 25 October playtest.

Movement uses raw map-square positions: native overmap_tile scales offsets
and does NOT snap coordinates. Special placement distinguishes seen OMTs
from generated local maps, matching can_place_special in official 0.I.
"""
import copy
import json
import unittest

from test_playtest_oct25_33 import World, MOD, ROOT, P
from test_skull_knight_dialogue_33 import Conversation as Knight


class ExactMovement(unittest.TestCase):
    def test_native_overmap_tile_adjusts_without_rounding(self):
        f=World();f.values['_point']=(13,35,2)
        f.effect({'location_variable_adjust':{'context_val':'point'},'overmap_tile':True,'x_adjust':1,'y_adjust':-1,'z_adjust':1})
        self.assertEqual(f.values['_point'],(37,11,3))

    def test_chapel_hint_once_across_every_cell_of_both_omts(self):
        f=World();base=(-48,72,0)
        for y in range(48):
            f.om='berserk_desecrated_chapel_reliquary' if y<24 else 'berserk_desecrated_chapel_nave'
            for x in range(24):
                f.pos=(base[0]+x,base[1]+y,0);f.run(P+'ARRIVAL')
        self.assertEqual(len(f.messages),1)
        self.assertEqual(tuple(f.values['u_berserk_hint_chapel']),base)
        f.values=json.loads(json.dumps(f.values));f.run(P+'LOCAL_LOAD')
        self.assertEqual(len(f.messages),1)

    def test_old_raw_cached_coordinate_is_recognized_without_another_popup(self):
        f=World();f.om='berserk_desecrated_chapel_nave';f.pos=(-1,119,0)
        # The old cache saved a raw position with the nave's 24-square offset.
        f.values['u_berserk_hint_chapel']=(-13,80,0)
        f.run(P+'HINT_CHAPEL');self.assertFalse(f.messages)

    def test_caravan_and_expedition_do_not_repeat_on_each_step(self):
        for terrain in ['berserk_road_caravan','berserk_lost_expedition']:
            f=World();f.om=terrain
            for x in range(24):
                f.pos=(48+x,84,0);f.run(P+'ARRIVAL')
            self.assertEqual(len(f.messages),1,terrain)


class NativeSpecialPlacement(unittest.TestCase):
    def test_revealed_but_ungenerated_forest_works_for_stranger_and_guts(self):
        for guts in [False,True]:
            f=World();f.guts=guts;f.seen=set(f.land)
            f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
            target=f.missions['MISSION_BERSERK_FIRST_HUNT']
            self.assertIn(target,f.seen)
            self.assertEqual(f.local_maps[target],'berserk_first_hunt_lair')
            self.assertNotIn('cant_see',f.searches[0])
            self.assertNotIn('om_terrain_replace',f.searches[0])

    def test_dense_forest_is_a_valid_special_location(self):
        f=World();f.land={(249*24,30*24,0):'forest_thick'}
        f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertIn('MISSION_BERSERK_FIRST_HUNT',f.missions)

    def test_placement_buffer_rejects_forest_next_to_forge(self):
        f=World();near=(190*24,0,0);far=next(iter(f.land))
        f.land={near:'forest',far:'forest'}
        f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertEqual(f.missions['MISSION_BERSERK_FIRST_HUNT'],far)
        self.assertEqual(f.land[near],'forest')
        for id_ in ['berserk_first_hunt_special','berserk_local_breach_special']:
            special=f.specials[id_]
            self.assertEqual(special['spawns']['population'],[0,0])
            self.assertEqual(special['spawns']['radius'],[48,48])
            self.assertIn('SAFE_AT_WORLDGEN',special['flags'])

    def test_debug_reveal_never_allows_overwriting_generated_local_map(self):
        f=World();first=next(iter(f.land));second=(249*24,-30*24,0)
        f.land[second]='forest';f.seen=set(f.land);f.local_maps[first]='player_stash'
        f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertEqual(f.local_maps[first],'player_stash')
        self.assertEqual(f.land[first],'forest')
        self.assertEqual(f.missions['MISSION_BERSERK_FIRST_HUNT'],second)


class ChapelRepair(unittest.TestCase):
    def legacy(self):
        f=World();f.om='berserk_desecrated_chapel_nave';f.pos=(1003,2002,0)
        base=(984,1992,0);cells=[(base[0]+7,base[1]+y,0) for y in range(7,11)]
        for pos in cells:f.terrain[pos]='t_wall';f.furniture[pos]='f_null'
        f.furniture[(base[0]+12,base[1]+16,0)]='f_berserk_chapel_record'
        f.terrain[(1,1,0)]='t_wall';f.inventory['keepsake']=1
        return f,cells

    def test_only_four_wrong_cells_change_once_without_touching_items(self):
        f,cells=self.legacy();before=copy.deepcopy(f.inventory)
        f.run(P+'WALL_HOTFIX')
        self.assertTrue(all(f.terrain[p]=='t_floor' for p in cells))
        self.assertEqual(f.terrain[(1,1,0)],'t_wall');self.assertEqual(f.inventory,before)
        self.assertEqual(f.values['berserk_chapel_wall_hotfix25b'],1)
        # A player's later reconstruction must survive subsequent movement.
        for p in cells:f.terrain[p]='t_wall'
        f.run(P+'WALL_HOTFIX');self.assertTrue(all(f.terrain[p]=='t_wall' for p in cells))

    def test_repair_does_not_erase_furniture_or_a_different_layout(self):
        f,cells=self.legacy();f.furniture[cells[1]]='f_chair'
        f.run(P+'WALL_HOTFIX');self.assertTrue(all(f.terrain[p]=='t_wall' for p in cells))
        self.assertNotIn('berserk_chapel_wall_hotfix25b',f.values)

    def test_other_old_chapel_is_repaired_independently(self):
        f,cells=self.legacy();f.run(P+'WALL_HOTFIX')
        first_plaque=(996,2008,0)
        self.assertEqual(f.furniture[first_plaque],'f_berserk_chapel_record_v2')
        # Another instance must not inherit a global "all chapels fixed" latch.
        f.pos=(1243,2002,0)
        other=[(p[0]+240,p[1],p[2]) for p in cells]
        for pos in other:f.terrain[pos]='t_wall';f.furniture[pos]='f_null'
        f.furniture[(1236,2008,0)]='f_berserk_chapel_record'
        f.run(P+'WALL_HOTFIX')
        self.assertTrue(all(f.terrain[p]=='t_floor' for p in other))
        self.assertEqual(f.furniture[first_plaque],'f_berserk_chapel_record_v2')

    def test_project_v2_removes_the_thin_stroke_wall_only(self):
        old=json.loads((ROOT/'docs/location_projects/chapel-3.3-01.json').read_text())
        new=json.loads((ROOT/'docs/location_projects/chapel-3.3-02.json').read_text())
        changed={(x,y) for y in range(48) for x in range(24) if old['rows'][y][x]!=new['rows'][y][x]}
        self.assertEqual(changed,{(7,y) for y in range(31,35)})
        self.assertEqual([f for f in new['furniture'] if f['furn']!='f_berserk_chapel_record_v2'],old['furniture'])
        self.assertEqual(new['anchors'],old['anchors'])


class Farewell(unittest.TestCase):
    def test_explicit_enough_choice_is_the_single_farewell_entry(self):
        for guts in [False,True]:
            f=Knight();f.overrides['EOC_BERSERK_FORGE_GUTS']=guts
            finish=[r for r in f.available('AFTER') if r['topic'].endswith('FAREWELL')]
            self.assertEqual(len(finish),1)
            self.assertIn('That is enough',finish[0]['text'])
            self.assertNotIn('TALK_DONE',f.targets('AFTER'))
            f.choose('AFTER','FAREWELL');self.assertEqual(f.retired,0)
            f.choose('FAREWELL','FINAL');self.assertEqual(f.retired,1)
            self.assertFalse(f.scheduled)


if __name__=='__main__':unittest.main()
