"""Exercise first-conversation order and siege refusals without running CDDA.

The order below follows dialogue::opt at tag 0.I-1: generate responses, apply
speaker effects, choose a response, then generate the next topic. This is a
data interpreter, not a native UI/save/load/AI test.
"""

import copy
import unittest

from test_flora import ARMOR, native_om_location
from test_flora_siege import SiegeGraph, ready
from test_behelit_rewards import MOD, objects
from validate_mod_assets import ValidationError, validate_om_location_conditions


class FloraDialogueStates(unittest.TestCase):
    def topics(self):
        return {t['id']: t for t in objects(MOD/'dialogue/flora.json')}

    def available(self, graph, topic):
        return [r for r in self.topics()[topic]['responses']
                if 'condition' not in r or graph.condition(r['condition'])]

    def open_conversation(self, graph):
        entry = objects(MOD/'monsters/flora.json')[0]['chat_topics'][0]
        responses = self.available(graph, entry)
        self.assertEqual(responses[0]['topic'], 'TALK_BERSERK_FLORA')
        # Responses have already been generated, as in the actual engine.
        graph.effect(self.topics()[entry]['speaker_effect']['effect'])
        return self.available(graph, responses[0]['topic'])

    def post_eclipse(self):
        graph = SiegeGraph({'berserk_eclipse_era':1,'u_berserk_eclipse_rescue_state':2})
        return graph

    def test_first_manual_meeting_registers_before_gift_and_readiness_menu(self):
        g = self.post_eclipse()
        menu = self.open_conversation(g)
        self.assertEqual(sum(r['topic']=='TALK_BERSERK_FLORA_ARMOR' for r in menu),1)
        self.assertTrue(any(r['topic']=='TALK_BERSERK_FLORA_OFFER'
                            for r in self.available(g,'TALK_BERSERK_FLORA_ARMOR')))
        self.assertTrue(any(r['topic']=='TALK_BERSERK_FLORA_PREPARATION' for r in menu))
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
        self.assertEqual(g.flags['berserk_flora_center'],(-72,72,0))
        self.assertEqual(g.flags['u_berserk_flora_met'],1)
        self.assertFalse(g.inventory)
        self.assertFalse(g.spawns)
        self.assertFalse(g.siege_updates)

    def test_story_discovery_is_reused_when_another_flora_is_debug_placed(self):
        g=self.post_eclipse();g.flags['u_berserk_first_hunt_done']=1
        g.flags['u_berserk_first_hunt_location']=(-576,48,0)
        g.run('EOC_BERSERK_FLORA_SEEK')
        self.assertEqual(g.location_calls,1)
        g.victim=(1015,1020,0)
        menu=self.open_conversation(g)
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
        self.assertEqual(g.flags['berserk_flora_center'],(-72,72,0))
        self.assertFalse(any('SIEGE_' in r['topic'] for r in menu))
        self.assertFalse(g.inventory)

    def test_charm_is_invoked_in_place_without_power_or_automatic_consumption(self):
        item=objects(MOD/'items/flora_escape_charm.json')[0]
        self.assertIn('ALLOWS_REMOTE_USE',item['flags'])
        self.assertEqual(item['charges_per_use'],0)
        self.assertNotIn('SINGLE_USE',item['flags'])
        self.assertNotIn('BIONIC_ITEM',item['subtypes'])
        self.assertNotIn('need_wielding',item['use_action'])

    def test_all_manor_quadrants_register_the_same_origin(self):
        for omt,pos in [('berserk_flora_manor_west',(-81,60,0)),
                        ('berserk_flora_manor_east',(-57,60,0)),
                        ('berserk_flora_garden_west',(-81,84,0)),
                        ('berserk_flora_garden_east',(-57,84,0))]:
            with self.subTest(omt=omt):
                g=self.post_eclipse();g.beta_omt=omt;g.omt=omt
                g.victim=pos;g.avatar=pos
                self.open_conversation(g)
                self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
                self.assertEqual(g.flags['berserk_flora_center'],(-72,72,0))
                g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
                g.run('EOC_BERSERK_FLORA_START_SIEGE')
                self.assertEqual(g.flags['berserk_flora_siege_state'],2)

    def test_unrelated_actor_or_flora_in_a_field_cannot_register_a_manor(self):
        for beta,omt in [(None,'berserk_flora_manor_west'),
                         ('mon_skull_knight_rescuer','berserk_flora_manor_west'),
                         ('mon_berserk_flora','field')]:
            g=self.post_eclipse();g.beta=beta;g.beta_omt=omt
            self.open_conversation(g)
            self.assertNotIn('berserk_flora_location',g.flags)
            self.assertFalse(g.inventory)
            self.assertFalse(g.siege_updates)

    def test_old_gift_and_complete_or_packed_suit_have_owner_readiness(self):
        for owned,flags in [(ARMOR,{}),({'berserk_armor_bundle'},{}),
                            (set(),{'u_berserk_flora_armor_resolved':1,
                                    'berserk_flora_armor_claimed':1})]:
            g=self.post_eclipse();g.worn=set(owned);g.flags.update(flags)
            menu=self.open_conversation(g)
            self.assertEqual(sum(r['topic']=='TALK_BERSERK_FLORA_PREPARATION' for r in menu),1)
            self.assertFalse(any('SIEGE_' in r['topic'] for r in menu))
            g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
            self.assertEqual(g.inventory,['berserk_flora_escape_charm'])
            self.assertEqual(g.flags['u_berserk_flora_armor_resolved'],1)
            self.assertEqual(g.worn,set(owned))
            self.assertFalse(g.spawns)

    def test_gift_and_wearing_armor_do_not_confirm_readiness(self):
        g=self.post_eclipse();self.open_conversation(g)
        g.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
        self.assertEqual(set(g.inventory),ARMOR)
        g.inventory=['berserk_flora_escape_charm'];g.worn=set(ARMOR)
        g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertIn('charm is not prepared yet',g.messages[-1])
        self.assertEqual(g.inventory,['berserk_flora_escape_charm'])
        self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        self.assertEqual(g.inventory,['berserk_flora_escape_charm'])
        g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertEqual(g.flags['berserk_flora_siege_state'],2)

    def test_old_save_center_is_repaired_without_resetting_progress_or_anchors(self):
        for state,stage in [(0,1),(1,1),(2,2),(5,3)]:
            g=ready();g.flags.update(berserk_flora_siege_state=state,berserk_flora_stage=stage)
            g.flags.pop('berserk_flora_center')
            g.flags['berserk_flora_zodd_anchor']=(-82,50,0)
            self.open_conversation(g)
            self.assertEqual(g.flags['berserk_flora_center'],(-72,72,0))
            self.assertEqual(g.flags['berserk_flora_siege_state'],state)
            self.assertEqual(g.flags['berserk_flora_stage'],stage)
            self.assertEqual(g.flags['berserk_flora_zodd_anchor'],(-82,50,0))
        g=ready();g.flags.pop('berserk_flora_location');g.flags.pop('berserk_flora_center')
        self.open_conversation(g)
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))

    def test_specific_refusals_do_not_start_or_consume_anything(self):
        cases=[({'berserk_eclipse_era':0},None,None,'survivor of the Eclipse'),
               ({'berserk_flora_siege_state':0},None,None,'charm is not prepared'),
               ({'berserk_flora_siege_state':2,'berserk_flora_stage':2},None,None,'already begun'),
               ({'berserk_flora_siege_state':5,'berserk_flora_stage':3},None,None,'already complete'),
               ({},'field',None,'outside the registered manor'),
               ({},'berserk_flora_manor_west',(1000,1000,0),'outside the registered manor')]
        for flags,omt,pos,expected in cases:
            with self.subTest(expected=expected,pos=pos):
                g=ready();g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
                g.flags.update(flags)
                if omt:g.omt=omt
                if pos:g.avatar=pos
                original=copy.deepcopy(g.flags);items=list(g.inventory)
                g.run('EOC_BERSERK_FLORA_START_SIEGE')
                self.assertIn(expected,g.messages[-1])
                self.assertEqual(g.flags,original)
                self.assertEqual(g.inventory,items)
                self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)
        g=ready();g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE');g.flags.pop('berserk_flora_location')
        g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertIn('not been registered',g.messages[-1])
        self.assertEqual(g.flags['berserk_flora_siege_state'],1)

    def test_one_preparation_then_activation_and_escape_updates_the_journal_once(self):
        g=ready();g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)
        g=copy.deepcopy(g)  # persistence of abstract state, not a native save
        g.confirm=False;g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertEqual(g.flags['berserk_flora_siege_state'],2)
        g.avatar=(-105,62,0);g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_state'],5)
        self.assertEqual(g.inventory.count('berserk_apostle_hunt_journal'),1)
        self.assertTrue(any('You have escaped' in m for m in g.messages))
        messages=list(g.messages)
        g.run('EOC_BERSERK_FLORA_ESCAPED')
        self.assertEqual(g.inventory.count('berserk_apostle_hunt_journal'),1)
        self.assertEqual(g.messages,messages)

    def test_native_normalization_rejects_full_directional_condition_names(self):
        g = self.post_eclipse()
        for raw, expected in [('berserk_flora_manor_west','berserk_flora_manor'),
                              ('berserk_flora_manor_east','berserk_flora_manor'),
                              ('berserk_flora_garden_west','berserk_flora_garden'),
                              ('berserk_flora_garden_east','berserk_flora_garden')]:
            g.beta_omt = raw
            self.assertEqual(native_om_location(raw), expected)
            self.assertFalse(g.condition({'npc_at_om_location':raw}))
            self.assertTrue(g.condition({'npc_at_om_location':expected}))

    def test_validator_distinguishes_condition_names_from_mission_target_ids(self):
        path = MOD/'effects/flora_eocs.json'
        for field in ('overmap_at_point','u_at_om_location','npc_at_om_location',
                      'u_near_om_location','npc_near_om_location'):
            with self.subTest(field=field):
                with self.assertRaises(ValidationError):
                    validate_om_location_conditions(path,[{field:'berserk_flora_manor_west'}])
                validate_om_location_conditions(path,[{field:'berserk_flora_manor'}])
        validate_om_location_conditions(path,[{'target_params':{
            'om_terrain':'berserk_flora_manor_west','search_range':48,'random':True}}])

    def test_previously_exhausted_locator_recovers_and_binds_the_same_mission(self):
        g = self.post_eclipse()
        g.flags.update(u_berserk_first_hunt_done=1,
                       u_berserk_site_flora_placement_v2=1,
                       u_berserk_site_flora_tries=2,
                       u_berserk_site_flora_search_origin=g.avatar)
        g.run('EOC_BERSERK_FLORA_SEEK')
        target = (-96,48,0)
        self.assertEqual(g.location_calls,1)
        self.assertEqual(g.flags['berserk_flora_location'],target)
        self.assertEqual(g.active_missions['MISSION_BERSERK_FLORA'],target)
        saved = copy.deepcopy(g)
        saved.run('EOC_BERSERK_FLORA_SEEK')
        self.assertEqual(saved.location_calls,1)
        self.assertEqual(saved.active_missions['MISSION_BERSERK_FLORA'],target)
        self.assertFalse(saved.inventory)

    def test_manual_meeting_repairs_unconfirmed_field_coordinate(self):
        g = self.post_eclipse()
        g.flags.update(berserk_flora_location=(600,600,0),berserk_flora_stage=1,
                       berserk_flora_armor_claimed=1,u_berserk_flora_armor_resolved=1)
        menu = self.open_conversation(g)
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
        self.assertTrue(any(r['topic']=='TALK_BERSERK_FLORA_PREPARATION' for r in menu))
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        self.assertEqual(g.inventory,['berserk_flora_escape_charm'])

    def test_incomplete_manor_cannot_be_registered_from_one_named_tile(self):
        g = self.post_eclipse()
        del g.terrain_locations[(-72,72,0)]
        self.open_conversation(g)
        self.assertNotIn('berserk_flora_location',g.flags)
        self.assertFalse(g.active_missions)
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        self.assertIn("Flora's home",g.messages[-1])
        self.assertFalse(g.inventory)

    def test_new_preparation_branch_explains_an_outside_meeting(self):
        g = self.post_eclipse();g.omt = g.beta_omt = 'field'
        menu = self.open_conversation(g)
        self.assertTrue(any(r['topic']=='TALK_BERSERK_FLORA_PREPARATION' for r in menu))
        g.run('EOC_BERSERK_FLORA_PREPARATION_REFUSAL')
        self.assertIn('meeting her elsewhere is not enough',g.messages[-1])
        self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)

    def test_prepared_save_can_resume_without_second_gift_or_charm(self):
        g = self.post_eclipse();self.open_conversation(g)
        g.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
        self.open_conversation(g)
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        saved = copy.deepcopy(g)
        self.open_conversation(saved)
        saved.run('EOC_BERSERK_FLORA_PREPARATION_REFUSAL')
        self.assertIn('already confirmed',saved.messages[-1])
        saved.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        self.assertEqual(saved.inventory,g.inventory)
        self.assertFalse(saved.spawns);self.assertFalse(saved.siege_updates)


if __name__=='__main__':unittest.main()
