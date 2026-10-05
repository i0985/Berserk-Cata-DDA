"""Regressions for reported 0.I-1 loading and rescue faults; no game binary."""
import json
import unittest
from pathlib import Path
from test_behelit_rewards import MOD, objects
from validate_mod_assets import (ValidationError, validate_location_target_params,
                                 validate_early_map_ids)

class OctoberPlaytest(unittest.TestCase):
    def test_engine_struct_member_is_rejected_as_json_but_seen_only_search_is_allowed(self):
        p=MOD/'effects/hunt_site_placement_eocs.json'
        obj={'type':'effect_on_condition','effect':{'u_location_variable':{'context_val':'p'},'target_params':{'om_terrain':'forest','create_if_necessary':False}}}
        with self.assertRaises(ValidationError):validate_location_target_params(p,[obj])
        obj['effect']['target_params']={'om_terrain':'forest','must_see':True}
        validate_location_target_params(p,[obj])

    def test_palette_conversion_and_forward_furniture_inheritance_need_loaded_base(self):
        a=MOD/'00_test.json';b=MOD/'mapgen/zz_test.json'
        base={'type':'furniture','id':'f_base'}
        palette={'type':'palette','id':'p','furniture':{'X':'f_base'}}
        with self.assertRaises(ValidationError):validate_early_map_ids({a:[palette],b:[base]})
        validate_early_map_ids({a:[base],b:[palette]})
        child={'type':'furniture','id':'f_child','copy-from':'f_base'}
        with self.assertRaises(ValidationError):validate_early_map_ids({a:[child],b:[base]})

    def test_return_adds_half_max_hp_once_after_commit_without_removing_story_wounds(self):
        es={e['id']:e for e in objects(MOD/'effects/eclipse_aftermath_eocs.json')}
        restore=es['EOC_BERSERK_ECLIPSE_RETURN_RECOVER']
        self.assertIn('u_berserk_eclipse_rescue_state == 2',str(restore['condition']))
        self.assertIn('u_berserk_eclipse_return_recovered != 1',str(restore['condition']))
        math=[x['math'][0] for x in restore['effect'] if 'math' in x]
        for part in ['head','torso','arm_l','arm_r','leg_l','leg_r']:
            self.assertIn(f"u_hp('{part}') = min(u_hp_max('{part}'), u_hp('{part}') + floor(u_hp_max('{part}') * 0.5))",math)
        for v in ['blood','redcells']:self.assertIn(f"u_vitamin('{v}') = 0",math)
        erase=next(x for x in restore['effect'] if 'u_lose_effect' in x)
        self.assertEqual(erase['target_part'],'ALL')
        self.assertTrue({'blind','bleed','stunned','downed','winded'}<=set(erase['u_lose_effect']))
        self.assertNotIn('berserk_mode_recovery',erase['u_lose_effect'])
        self.assertNotIn('u_lose_bionic',json.dumps(restore))
        self.assertEqual(es['EOC_BERSERK_ECLIPSE_AFTERMATH']['effect'][0]['run_eocs'],restore['id'])
        # recover_energy/STAMINA calls mod_stamina (clamped), not set_stamina.
        spell=objects(MOD/'spells/eclipse_return_recovery.json')[0]
        self.assertEqual((spell['effect'],spell['effect_str']),('recover_energy','STAMINA'))
        self.assertEqual(spell['valid_targets'],['self'])

    def test_story_bionics_have_item_versions_without_installable_loot(self):
        items=objects(MOD/'items/bionics/eclipse_story_records.json')
        self.assertEqual({i['id'] for i in items},{'bio_berserk_brand_of_sacrifice','bio_berserk_lost_eye'})
        for i in items:self.assertNotIn('BIONIC_ITEM',i.get('subtypes',[]))

    def test_projection_history_is_only_set_for_avatar_kill_and_reward_remains_gated(self):
        e=objects(MOD/'effects/griffith_projection_history.json')[0]
        self.assertEqual(e['effect'][0]['if'],{'and':['has_alpha','u_is_avatar']})
        self.assertEqual(e['effect'][1]['run_eocs'],'EOC_BERSERK_BEHELIT_BOSS_DIES')
        topics={t['id']:t for t in objects(MOD/'dialogue/skull_knight.json')}
        question=next(r for r in topics['TALK_BERSERK_SKULL_KNIGHT_AFTER']['responses'] if r['topic'].endswith('_PROJECTIONS'))
        self.assertIn('u_berserk_griffith_projection_defeated == 1',str(question['condition']))

if __name__=='__main__':unittest.main()
