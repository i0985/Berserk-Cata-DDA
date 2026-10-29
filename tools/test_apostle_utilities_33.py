"""Native mechanics contracts and actual exported early-source EOC transitions.

The source audit captures vanilla definitions. This is not a CDDA game run.
"""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

from test_playtest_oct25_33 import World, MOD, ROOT
from test_reference_journal_33 import EOCS, RUSSIAN
from validate_mod_assets import underlying_object_id

P = 'EOC_BERSERK_UTILITY29_'
SPEC = json.loads((ROOT/'docs/apostol-native-utilities-33.json').read_text())


def form(stem):
    return next(o for o in json.loads((MOD/('mutations/apostol_'+stem.lower()+'.json')).read_text())
                if o['id'] == 'BERSERK_'+stem+'_FORM')


class NativeBodies(unittest.TestCase):
    def test_abilities_are_native_derived_traits_not_independent_mutation_doses(self):
        native = {o['id'] for o in SPEC['native_traits']}
        for stem, data in SPEC['bodies'].items():
            body = form(stem)
            self.assertFalse(body['purifiable']); self.assertNotIn('transform', body)
            self.assertEqual(body['enchantments'][0]['mutations'], data['traits'])
            self.assertTrue(set(data['traits']) <= native)
            self.assertEqual(body['enchantments'][0]['condition'], 'ALWAYS')

    def test_glide_menu_and_safe_multi_level_descent_are_separate_from_combat_dive(self):
        flags = set(form('ROSINE_FLESH')['flags'])
        self.assertTrue({'WING_GLIDE', 'WINGS_2', 'FEATHER_FALL'} <= flags)
        self.assertNotIn('FEATHER_FALL', form('ROSINE_PAWN')['flags'])
        self.assertIn('EOC_BERSERK_APOSTOL_ROSINE_FLESH_DIVE_USE', EOCS)

    def test_anatomical_utilities_do_not_require_an_unbroken_pact(self):
        for stem in SPEC['bodies']:
            ench = form(stem)['enchantments'][0]
            self.assertNotIn('LOYALTY', json.dumps(ench))
            self.assertNotIn('favor_until', json.dumps(ench))

    def test_utility_traits_add_no_strength_and_keep_original_body_values(self):
        strength = {'COUNT_PAWN':2, 'COUNT_FLESH':4, 'WYALD_PAWN':3,
                    'WYALD_FLESH':4, 'GRUNBELD_PAWN':2, 'GRUNBELD_FLESH':3}
        for stem, value in strength.items():
            stat = next(x for x in form(stem)['enchantments'][0]['values'] if x['value']=='STRENGTH')
            self.assertEqual(stat['add'], value)
        for obj in SPEC['native_traits']:
            self.assertFalse(any(v['value']=='STRENGTH' for e in obj.get('enchantments', [])
                                 for v in e.get('values', [])))

    def test_senses_and_natural_tools_have_the_native_active_or_integrated_hooks(self):
        data = {o['id']:o for o in SPEC['native_traits']}
        self.assertTrue(data['ANTENNAE']['starts_active'])
        self.assertEqual(data['ANTENNAE']['enchantments'][0]['special_vision'][0]['distance'], 3)
        self.assertTrue(data['BURROWLARGE']['active']); self.assertTrue(data['SHELL2']['active'])
        self.assertTrue(data['CLAWS']['integrated_armor'])
        self.assertTrue(data['FANGS']['integrated_armor'])

    def test_underwater_walking_does_not_claim_underwater_breathing(self):
        self.assertNotIn('GILLS', form('GRUNBELD_FLESH')['enchantments'][0]['mutations'])
        self.assertIn('воздух всё ещё нужен', RUSSIAN.gettext(form('GRUNBELD_FLESH')['description']))

    def test_count_uses_plastic_flesh_not_aquatic_traits(self):
        for stem in ['COUNT_PAWN','COUNT_FLESH']:
            self.assertFalse(set(form(stem)['enchantments'][0]['mutations']) & {'GILLS','SLIMY'})
            self.assertIn('PSEUDOPOD_GRASP', form(stem)['flags'])
        self.assertIn('MEND_ALL', form('COUNT_FLESH')['flags'])
        self.assertNotIn('MEND_ALL', form('COUNT_PAWN')['flags'])

    def test_five_gifts_have_distinct_native_mechanics_without_debug_teleport_block(self):
        self.assertEqual(len(SPEC['bodies']), 13)
        self.assertIn('CLAIRVOYANCE', form('VOID')['flags'])
        self.assertFalse(set(form('VOID')['flags']) & {'SUPER_CLAIRVOYANCE','DIMENSIONAL_ANCHOR'})
        self.assertEqual(form('SLAN')['enchantments'][0]['mutations'], ['REGEN_LIZ','MASOCHIST'])
        self.assertIn('NO_SCENT', form('UBIK')['flags'])
        self.assertIn('LIGHTSTEP', form('UBIK')['enchantments'][0]['mutations'])
        self.assertEqual(form('CONRAD')['enchantments'][0]['mutations'], ['SAPROVORE','PARAIMMUNE'])
        self.assertTrue({'WING_GLIDE','WINGS_2','FEATHER_FALL','CLIMB_NO_LADDER'} <= set(form('FEMTO')['flags']))

    def test_native_healing_and_food_changes_keep_their_actual_limits(self):
        native = {o['id']:o for o in SPEC['native_traits']}
        self.assertIn('MEND_ALL', native['REGEN_LIZ']['flags'])
        self.assertIn('IMMUNE_SPOIL', native['SAPROVORE']['flags'])
        self.assertIn('PARAIMMUNE', native['PARAIMMUNE']['flags'])
        self.assertIn('negative effects of pain', native['MASOCHIST']['description'])
        self.assertNotIn('growth does not heal', form('SLAN')['description'])
        for stem in ['FEMTO','ROSINE_FLESH']:
            self.assertNotIn('halved', form(stem)['description'])
            self.assertIn('without falling damage', form(stem)['description'])

    def test_all_new_body_instructions_have_a_russian_translation(self):
        for stem in SPEC['bodies']:
            text = form(stem)['description']; ru = RUSSIAN.gettext(text)
            self.assertNotEqual(ru, text); self.assertIn('Возможности тела:', ru)


class EarlyWorld(World):
    def __init__(self):
        super().__init__(); self.values['berserk_eclipse_era']=0
        self.pos=(0,0,0); self.om='field'; self.land={(10*24,0,0):'forest'}
        self.special_at={}; self.local_maps={}; self.roads={(10*24,24,0)}
        self.city_distance={(10*24,0,0):5}; self.created=0; self.revealed=[]
        self.intro=json.loads((MOD/'overmap/early_caravan.json').read_text())[1]

    def value(self, text):
        text=re.sub(r"time\('(\d+) minutes'\)", lambda m:str(int(m[1])*60), text)
        return super().value(text)

    def effect(self, effect):
        if isinstance(effect,dict) and 'remove_active_mission' in effect:
            self.missions.pop(effect['remove_active_mission'],None)
            return
        if isinstance(effect,dict) and 'reveal_map' in effect:
            self.revealed.append(effect)
            return
        if isinstance(effect,dict) and effect.get('target_params',{}).get('om_special')=='berserk_early_caravan_special':
            params=effect['target_params']; self.searches.append(copy.deepcopy(params))
            origin=(*self.pos[:2], params['z'])
            for point, terrain in list(self.land.items()):
                dist=max(abs(point[i]-origin[i])//24 for i in [0,1])
                beside_road=any((point[0]+dx,point[1]+dy,0) in self.roads
                                for dx,dy in [(24,0),(-24,0),(0,24),(0,-24)])
                if (terrain not in ['forest','forest_thick','field'] or point in self.local_maps
                    or self.city_distance.get(point,0)<3 or not beside_road
                    or dist>params['search_range']): continue
                self.land[point]='berserk_early_caravan'; self.created+=1
                self.values['_early_caravan_candidate']=point
                self.local_maps[point]='berserk_early_caravan'
                for name in effect['true_eocs']: self.run(name)
                return
            # Match native get_om_terrain_pos: failed mission lookup returns
            # origin, and f_location_variable still executes true_eocs.
            self.values['_early_caravan_candidate']=(origin[0]//24*24,origin[1]//24*24,0)
            for name in effect.get('true_eocs',[]): self.run(name)
            return
        return super().effect(effect)


class EarlySource(unittest.TestCase):
    def test_surface_start_places_one_source_and_not_the_forge_or_paper_inventory(self):
        f=EarlyWorld(); f.run(P+'EARLY_GAME_START')
        self.assertEqual(f.created,1); self.assertEqual(f.inventory['berserk_road_caravan_note'],0)
        self.assertFalse(f.missions); self.assertFalse(f.revealed); self.assertFalse(f.messages)
        self.assertNotIn('u_berserk_journal_knows_godo',f.values)
        self.assertNotIn('u_berserk_godo_personally_met',f.values)
        self.assertEqual(f.values['berserk_early_caravan_location'],(240,0,0))

    def test_underground_or_rooftop_start_waits_for_the_first_surface_exit(self):
        for z in [-5,3]:
            f=EarlyWorld(); f.pos=(0,0,z); f.run(P+'EARLY_GAME_START')
            self.assertEqual(f.created,0); self.assertFalse(f.searches)
            f.pos=(0,0,0); f.run(P+'EARLY_AVATAR_MOVES'); self.assertEqual(f.created,1)

    def test_open_water_start_waits_for_a_suitable_land_tile(self):
        f=EarlyWorld(); f.outside=True; f.om='lake_surface'; f.run(P+'EARLY_GAME_START')
        self.assertFalse(f.created); self.assertFalse(f.searches)
        f.om='field'; f.run(P+'EARLY_AVATAR_MOVES'); self.assertEqual(f.created,1)

    def test_load_and_movement_do_not_repeat_location_mission_or_popup(self):
        f=EarlyWorld(); f.run(P+'EARLY_GAME_START'); count=len(f.messages)
        for event in ['EARLY_GAME_LOAD','EARLY_AVATAR_MOVES']*3: f.run(P+event)
        self.assertEqual(f.created,1); self.assertEqual(len(f.messages),count)
        self.assertFalse(f.missions); self.assertFalse(f.revealed)

    def test_carrier_interior_deck_and_ocean_never_spend_attempts(self):
        for terrain,z in [('aircraft_carrier_1a',0),('aircraft_carrier_1a_3',3),
                          ('aircraft_carrier_4c_-1',-1),('lake_surface',0),('ocean',0)]:
            for outside in [True,False]:
                f=EarlyWorld(); f.om=terrain; f.pos=(0,0,z); f.outside=outside
                for event in ['EARLY_GAME_START','EARLY_GAME_LOAD','EARLY_AVATAR_MOVES']:
                    f.run(P+event)
                self.assertFalse(f.searches,(terrain,outside))
                self.assertNotIn('u_berserk_early_caravan_attempts',f.values)
                f.om='road'; f.pos=(0,0,0); f.run(P+'EARLY_AVATAR_MOVES')
                self.assertEqual(f.created,1)
                self.assertFalse(f.missions); self.assertFalse(f.revealed)

    def test_second_land_attempt_uses_larger_radius_without_marking_the_source(self):
        f=EarlyWorld(); p=(70*24,0,0)
        f.land={p:'forest'}; f.roads={(p[0],24,0)}; f.city_distance={p:5}
        f.run(P+'EARLY_GAME_START'); self.assertFalse(f.created)
        f.now+=1801; f.run(P+'EARLY_AVATAR_MOVES')
        self.assertEqual([x['search_range'] for x in f.searches],[48,96])
        self.assertEqual(f.created,1); self.assertFalse(f.revealed); self.assertFalse(f.missions)

    def test_old_wagon_mission_is_retired_without_reading_note_or_moving_location(self):
        f=EarlyWorld(); old=(240,0,0)
        f.values.update(berserk_early_caravan_placed=1, berserk_early_caravan_location=old)
        f.missions['MISSION_BERSERK_EARLY_CARAVAN']=old
        f.missions['MISSION_BERSERK_GODO']=(24,24,0)
        f.run(P+'EARLY_GAME_LOAD')
        self.assertNotIn('MISSION_BERSERK_EARLY_CARAVAN',f.missions)
        self.assertIn('MISSION_BERSERK_GODO',f.missions)
        self.assertEqual(f.values['berserk_early_caravan_location'],old)
        self.assertFalse(f.searches)
        self.assertNotIn('u_berserk_journal_read_berserk_road_caravan_note',f.values)

    def test_old_exhausted_water_search_gets_one_new_budget_only_after_landing(self):
        f=EarlyWorld(); f.om='aircraft_carrier_1a'
        f.values.update(u_berserk_early_caravan_attempts=3,u_berserk_early_caravan_retry_at=999999)
        f.run(P+'EARLY_GAME_LOAD'); self.assertEqual(f.values['u_berserk_early_caravan_attempts'],3)
        f.om='field'; f.roads=set(); f.run(P+'EARLY_AVATAR_MOVES')
        self.assertEqual(f.values['u_berserk_early_caravan_attempts'],1)
        for _ in range(5): f.now+=1801; f.run(P+'EARLY_GAME_LOAD')
        self.assertEqual(f.values['u_berserk_early_caravan_attempts'],3)

    def test_old_notification_id_cannot_reveal_or_assign_anything(self):
        f=EarlyWorld(); f.values['berserk_early_caravan_placed']=1; f.run(P+'EARLY_NOTIFY')
        self.assertFalse(f.missions); self.assertFalse(f.messages); self.assertFalse(f.revealed)

    def test_city_or_unconnected_forest_is_never_used(self):
        for why in ['city','road']:
            f=EarlyWorld()
            if why=='city': f.city_distance[(240,0,0)]=0
            else: f.roads=set()
            f.run(P+'EARLY_GAME_START')
            self.assertFalse(f.created); self.assertFalse(f.missions)
            self.assertNotIn('berserk_early_caravan_placed',f.values)

    def test_existing_local_player_map_is_not_replaced(self):
        f=EarlyWorld(); f.local_maps[(240,0,0)]='player_home'; f.run(P+'EARLY_GAME_START')
        self.assertEqual(f.local_maps[(240,0,0)],'player_home'); self.assertEqual(f.land[(240,0,0)],'forest')

    def test_failed_search_has_cooldown_and_finite_retries(self):
        f=EarlyWorld(); f.roads=set(); f.run(P+'EARLY_GAME_START'); count=len(f.searches)
        f.run(P+'EARLY_AVATAR_MOVES'); self.assertEqual(len(f.searches),count)
        for _ in range(6): f.now+=1801; f.run(P+'EARLY_AVATAR_MOVES')
        self.assertEqual(f.values['u_berserk_early_caravan_attempts'],3)

    def test_arrival_is_a_hint_and_never_reads_source(self):
        f=EarlyWorld(); f.om='berserk_early_caravan'; f.run(P+'EARLY_ARRIVAL'); f.run(P+'EARLY_ARRIVAL')
        self.assertEqual(len(f.messages),1)
        self.assertNotIn('u_berserk_journal_read_berserk_road_caravan_note',f.values)
        self.assertNotIn('u_berserk_journal_knows_godo',f.values)

    def test_reading_physical_order_opens_forge_without_retaining_paper(self):
        f=EarlyWorld(); f.run(P+'EARLY_GAME_START'); f.inventory.clear()
        f.run('EOC_BERSERK_ROAD_READ_CARAVAN')
        self.assertIn('MISSION_BERSERK_GODO',f.missions)
        self.assertNotIn('u_berserk_godo_personally_met',f.values)
        mission=json.loads((MOD/'missions/early_caravan.json').read_text())[0]
        self.assertTrue(f.condition(mission['goal_condition']))

    def test_another_forge_direction_resolves_optional_wagon_goal_without_reading_it(self):
        f=EarlyWorld(); f.run(P+'EARLY_GAME_START')
        f.values['u_berserk_journal_knows_godo']=1
        mission=json.loads((MOD/'missions/early_caravan.json').read_text())[0]
        self.assertTrue(f.condition(mission['goal_condition']))
        self.assertNotIn('u_berserk_journal_read_berserk_road_caravan_note',f.values)


class NativeSprites(unittest.TestCase):
    def test_native_overlays_resolve_real_mutations_and_reject_unknown_ids(self):
        for sex in ['female','male']:
            self.assertEqual(underlying_object_id('overlay_'+sex+'_mutation_BERSERK_COUNT_FLESH_FORM'),
                             'BERSERK_COUNT_FLESH_FORM')
            self.assertEqual(underlying_object_id('overlay_'+sex+'_mutation_NO_SUCH_MUTATION'),
                             'NO_SUCH_MUTATION')

    def test_source_sheet_and_authored_sprites_match_their_saved_hashes(self):
        manifest=json.loads((ROOT/'docs/apostol-native-sprite-sources-33.json').read_text())
        self.assertEqual(hashlib.sha256((MOD/manifest['sheet']).read_bytes()).hexdigest(),manifest['sha256'])
        policy=json.loads((ROOT/'docs/authored-common-sprites-2026-10-25.json').read_text())
        for entry in policy['sheets']:
            self.assertEqual(hashlib.sha256((MOD/entry['file']).read_bytes()).hexdigest(),entry['sha256'])

    def test_early_project_reuses_the_approved_wagon_geometry(self):
        approved=json.loads((ROOT/'docs/location_projects/road-stories-3.3-01.json').read_text())['maps'][0]['object']
        new=json.loads((ROOT/'docs/location_projects/early-caravan-3.3-01.json').read_text())['maps'][0]['object']
        self.assertEqual(approved['rows'],new['rows']); self.assertEqual(approved['place_furniture'],new['place_furniture'])
        self.assertIn({'item':'berserk_road_caravan_note','x':16,'y':10,'amount':1},new['place_item'])


if __name__ == '__main__': unittest.main()
