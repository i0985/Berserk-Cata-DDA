"""Static story-state/map regressions; no CDDA loader or binary is run."""

import copy
import gettext
import json
import re
import unittest

from test_apostle_hunts import HuntGraph, connected, stitched
from test_behelit_rewards import MOD, objects

ARMOR = {'berserk_helmet','berserk_chestplate','berserk_gloves',
         'berserk_armguards','berserk_legguards','berserk_boots'}


class FloraGraph(HuntGraph):
    def __init__(self, flags=None):
        super().__init__(flags)
        self.worn = set()
        self.nested = set()
        self.beta = 'mon_berserk_flora'
        self.beta_omt = 'berserk_flora_manor_west'
        self.victim = (-81,60,0)
        self.profession = 'berserk'
        self.location_calls = 0
        self.can_locate = True
        self.spawns = []

    def condition(self, value):
        if isinstance(value, str):
            if value == 'has_beta':
                return self.beta is not None
            if value == 'npc_is_monster':
                if self.beta is None:
                    raise AssertionError('beta accessed without has_beta')
                return self.beta.startswith('mon_')
            raise AssertionError(value)
        if 'u_has_item' in value:
            return value['u_has_item'] in set(self.inventory) | self.worn | self.nested
        if 'u_profession' in value:
            return self.profession == value['u_profession']
        if 'npc_at_om_location' in value:
            return self.beta_omt == value['npc_at_om_location']
        return super().condition(value)

    def evaluate(self, expr):
        if expr.startswith('n_monsters_nearby'):
            ids = re.findall(r"'(mon_[^']+)'", expr)
            self.assert_beta()
            return self.beta in ids
        # Native distance accepts the explicit actor strings "u" and "npc".
        self.context['flora_test_avatar'] = self.avatar
        self.context['flora_test_speaker'] = self.victim
        expr = expr.replace("distance('u',", 'distance(_flora_test_avatar,')
        expr = expr.replace("distance('npc',", 'distance(_flora_test_speaker,')
        return super().evaluate(expr)

    def assert_beta(self):
        if self.beta is None:
            raise AssertionError('missing beta talker')

    def run(self, id):
        obj = self.eocs[id]
        key = 'effect' if 'condition' not in obj or self.condition(obj['condition']) else 'false_effect'
        if key in obj:
            self.effect(obj[key])

    def effect(self, value):
        if isinstance(value, dict):
            if 'target_params' in value:
                if value['target_params']['om_terrain'] != 'berserk_flora_manor_west':
                    return HuntGraph.effect(self, value)
                self.location_calls += 1
                if self.can_locate:
                    # Mock the native locator finding the ward inside northwest.
                    self.flags['berserk_flora_location'] = (-81,60,0)
                    for id in value['true_eocs']:
                        self.run(id)
                else:
                    for id in value['false_eocs']:
                        self.run(id)
                return
            if 'location_variable_adjust' in value:
                key = value['location_variable_adjust']['global_val']
                pos = self.flags[key]
                if value.get('overmap_tile'):
                    pos = (pos[0]//24*24,pos[1]//24*24,pos[2])
                    scale = 24
                else:
                    scale = 1
                self.flags[key] = tuple(pos[i]+value.get(axis+'_adjust',0)*scale
                                        for i,axis in enumerate(('x','y','z')))
                return
            if 'u_learn_recipe' in value:
                self.flags['recipe_'+value['u_learn_recipe']] = True
                return
            if 'u_add_var' in value:
                self.flags['u_'+value['u_add_var']] = value['value']
                return
            if 'u_spawn_monster' in value:
                self.spawns.append(value['u_spawn_monster'])
                for id in value.get('true_eocs',[]):
                    self.run(id)
                return
        return super().effect(value)


def after():
    return FloraGraph({'berserk_eclipse_era':1,'u_berserk_eclipse_rescue_state':2,
                       'u_berserk_first_hunt_done':1,'berserk_flora_stage':1})


class FloraStory(unittest.TestCase):
    def test_missing_parts_once_including_worn_and_nested_inventory(self):
        for owned in (set(), {'berserk_gloves'}, ARMOR-{'berserk_boots'}):
            g = after()
            owned = sorted(owned)
            g.worn = set(owned[::2]); g.nested = set(owned[1::2])
            g.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
            self.assertEqual(set(g.inventory), ARMOR-set(owned))
            self.assertEqual(len(g.inventory), len(ARMOR-set(owned)))
            self.assertEqual(g.flags['berserk_flora_armor_claimed'],1)
            saved = copy.deepcopy(g)  # definition/state continuity, not native save I/O
            saved.inventory.clear();saved.worn.clear();saved.nested.clear()
            saved.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
            self.assertFalse(saved.inventory)

    def test_complete_or_packed_armor_needs_no_duplicate_and_keeps_world_gift(self):
        for owned in (ARMOR, {'berserk_armor_bundle'}):
            g = after();g.worn = set(owned)
            self.assertTrue(g.condition(g.eocs['EOC_BERSERK_FLORA_FULL_SET']['condition']))
            g.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
            self.assertFalse(g.inventory)
            self.assertNotIn('berserk_flora_armor_claimed',g.flags)
            g.run('EOC_BERSERK_FLORA_ACKNOWLEDGE_ARMOR')
            self.assertEqual(g.flags['u_berserk_flora_armor_resolved'],1)
            self.assertEqual(g.worn,set(owned))

    def test_before_eclipse_fake_speaker_and_shared_claim_block_reward(self):
        for configure in (
            lambda g:g.flags.update(u_berserk_eclipse_rescue_state=0),
            lambda g:setattr(g,'beta',None),
            lambda g:setattr(g,'beta','mon_skull_knight_rescuer'),
            lambda g:g.flags.update(berserk_flora_armor_claimed=1),
        ):
            g = after();configure(g);g.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
            self.assertFalse(g.inventory)

    def test_locator_reuses_one_world_location_and_failure_does_not_claim(self):
        g = after();g.flags.pop('berserk_flora_stage')
        g.can_locate = False;g.run('EOC_BERSERK_FLORA_SEEK')
        self.assertEqual(g.location_calls,1)
        self.assertNotIn('berserk_flora_stage',g.flags)
        self.assertNotIn('berserk_flora_armor_claimed',g.flags)
        g.can_locate = True;g.run('EOC_BERSERK_FLORA_SEEK')
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
        self.assertEqual(g.flags['berserk_flora_stage'],1)
        g.avatar = (1500,-700,0)
        g.run('EOC_BERSERK_FLORA_SEEK')
        self.assertEqual(g.location_calls,2)
        self.assertFalse(g.inventory)  # discovery never grants armor

    def test_meeting_debug_placed_flora_registers_once_without_resetting_later_stages(self):
        g = FloraGraph();g.run('EOC_BERSERK_FLORA_REGISTER_HERE')
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
        self.assertEqual(g.flags['berserk_flora_stage'],1)
        g.victim = (900,900,0)
        g.run('EOC_BERSERK_FLORA_REGISTER_HERE')
        self.assertEqual(g.flags['berserk_flora_location'],(-96,48,0))
        g.flags['berserk_flora_stage'] = 3
        g.run('EOC_BERSERK_FLORA_REGISTER_HERE')
        self.assertEqual(g.flags['berserk_flora_stage'],3)
        self.assertFalse(g.inventory)

    def test_post_start_is_idempotent_and_does_not_replace_equipment_or_old_state(self):
        g = FloraGraph({'berserk_flora_stage':1,'berserk_hunt_count_state':4})
        g.inventory = ['berserk_armor_bundle','true_guts_sword']
        original = list(g.inventory)
        g.run('EOC_BERSERK_POST_ECLIPSE_START')
        g.run('EOC_BERSERK_POST_ECLIPSE_START')
        self.assertEqual(g.spawns,['mon_skull_knight_rescuer'])
        self.assertEqual(g.flags['berserk_eclipse_era'],1)
        self.assertEqual(g.flags['u_berserk_eclipse_rescue_state'],2)
        self.assertEqual(g.flags['u_berserk_eclipse_behelit_spent'],1)
        self.assertEqual(g.flags['u_berserk_knight_waiting'],'placed')
        self.assertEqual(g.flags['berserk_hunt_count_state'],4)
        self.assertEqual(g.flags['berserk_flora_stage'],1)
        self.assertEqual(g.inventory,original+['berserk_first_hunt_directions'])
        g = FloraGraph();g.profession = 'berserk_before_eclipse'
        g.run('EOC_BERSERK_POST_ECLIPSE_START')
        self.assertFalse(g.flags);self.assertFalse(g.spawns)

    def test_profession_ids_and_parent_child_bionics_and_legacy_challenge(self):
        professions = {e['id']:e for e in objects(MOD/'professions/professions.json')}
        self.assertLessEqual({'berserk','berserk_prosthesis','berserk_fan'},professions.keys())
        post = professions['berserk'];pre = professions['berserk_before_eclipse']
        self.assertEqual(post['CBMs'],['bio_berserk_hand_stump','bio_berserk_arm_cannon',
                                      'bio_berserk_lost_eye','bio_berserk_brand_of_sacrifice'])
        self.assertEqual(post['effect_on_conditions'],['EOC_BERSERK_POST_ECLIPSE_START'])
        self.assertNotIn('CBMs',pre);self.assertNotIn('effect_on_conditions',pre)
        pitems = {e['item'] for e in pre['items']['both']['entries']}
        self.assertFalse(pitems & ARMOR)
        self.assertIn('true_guts_early_sword',pitems)
        self.assertEqual(professions['berserk_prosthesis']['CBMs'],['bio_berserk_hand_stump'])
        self.assertNotIn('effect_on_conditions',professions['berserk_prosthesis'])
        self.assertNotIn('copy-from',professions['berserk_prosthesis'])
        scenarios = {e['id']:e for p in (MOD/'scenarios').glob('*.json') for e in objects(p)}
        self.assertEqual(scenarios['berserk_story_start']['professions'],['berserk_before_eclipse','berserk'])
        self.assertEqual(scenarios['berserk_lost_hand_start']['professions'],['berserk_prosthesis'])
        early = objects(MOD/'items/true_guts_early_sword.json')[0]
        self.assertNotIn('ALWAYS_TWOHAND',early['flags'])
        self.assertEqual(early['melee_damage'],{'bash':16,'cut':52})

    def test_manor_stitches_two_exits_and_places_only_one_friendly_flora(self):
        maps,rows = stitched('flora_manor.json',[
            ['berserk_flora_manor_west','berserk_flora_manor_east'],
            ['berserk_flora_garden_west','berserk_flora_garden_east']])
        seen = connected(rows,(15,12),blocked='#TWrBbA')
        self.assertIn((0,14),seen);self.assertIn((24,47),seen)
        self.assertIn((31,20),seen);self.assertIn((34,35),seen)
        for obj in maps.values():
            self.assertEqual(len(obj['rows']),24)
            self.assertTrue(all(len(r)==24 for r in obj['rows']))
        actors = [m for obj in maps.values() for m in obj.get('place_monster',[])]
        self.assertEqual(len(actors),1)
        self.assertEqual(actors[0]['monster'],'mon_berserk_flora')
        self.assertTrue(actors[0]['friendly']);self.assertTrue(actors[0]['one_or_none'])
        special = next(e for e in objects(MOD/'overmap/flora_manor.json') if e['type']=='overmap_special')
        self.assertEqual(special['flags'],['GLOBALLY_UNIQUE'])
        self.assertEqual(special['occurrences'],[0,100])
        self.assertFalse(special['rotate'])
        self.assertEqual(len(special['overmaps']),4)

    def test_sanctuary_filters_neighbor_targets_without_removing_existing_monsters(self):
        g = after();g.flags.update(berserk_flora_stage=1,berserk_flora_location=(-96,48,0))
        query = g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']
        for point,expected in (((-96,48,0),True),((-72,72,0),True),((400,400,0),False)):
            g.context['berserk_quiet_target'] = point
            self.assertEqual(g.condition(query),expected)
        g.context['berserk_quiet_target'] = (-96,48,0)
        g.flags['berserk_flora_stage'] = 2
        self.assertTrue(g.condition(query))
        g.flags['berserk_flora_stage'] = 3
        self.assertFalse(g.condition(query))
        flora_text = (MOD/'effects/flora_eocs.json').read_text()
        self.assertNotIn('npc_die',flora_text)
        self.assertNotIn('u_lose_bionic',flora_text)
        self.assertNotIn('map_spawn_field',flora_text)

    def test_dialogue_topics_and_no_accidental_attack_on_acceptance(self):
        topics = {t['id']:t for t in objects(MOD/'dialogue/flora.json')}
        for t in topics.values():
            for r in t['responses']:
                if r['topic'] != 'TALK_DONE':self.assertIn(r['topic'],topics)
        for id in ('BRAND','ARMOR','COST','APOSTLES','RELICS','NEXT','OWNED'):
            self.assertIn('TALK_BERSERK_FLORA_'+id,topics)
        gift = after().eocs['EOC_BERSERK_FLORA_GIVE_ARMOR']
        self.assertNotIn('berserk_flora_stage = 2',str(gift))
        self.assertNotIn('u_spawn_monster',str(gift))
        self.assertNotIn('mapgen_update',str(gift))

    def test_compiled_names_descriptions_dialogues_and_scenario_contexts(self):
        paths = ['dialogue/flora.json','monsters/flora.json','overmap/flora_manor.json',
                 'effects/flora_eocs.json','furniture/flora.json','items/flora_directions.json',
                 'items/true_guts_early_sword.json']
        texts = set()
        def collect(v):
            if isinstance(v,list):
                for child in v:collect(child)
            elif isinstance(v,dict):
                for key,child in v.items():
                    if key in ('name','description','dynamic_line','text','u_message','menu_text'):
                        if isinstance(child,str):texts.add(child)
                        elif isinstance(child,dict):texts.update(s for k,s in child.items() if k in ('str','str_sp'))
                    collect(child)
        for p in paths:collect(objects(MOD/p))
        profs = [e for e in objects(MOD/'professions/professions.json') if e['id'] in ('berserk','berserk_before_eclipse')]
        scenario = objects(MOD/'scenarios/berserk_story_starts.json')[0]
        for locale in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo').open('rb') as f:cat = gettext.GNUTranslations(f)
            self.assertFalse([s for s in texts if cat.gettext(s)==s],locale)
            for prof in profs:
                for context in ('profession_male','profession_female'):
                    self.assertNotEqual(cat.pgettext(context,prof['name']),prof['name'])
                for context in ('prof_desc_male','prof_desc_female'):
                    self.assertNotEqual(cat.pgettext(context,prof['description']),prof['description'])
            for context,key in (('scenario_male','name'),('scenario_female','name'),
                                ('scen_desc_male','description'),('scen_desc_female','description'),
                                ('start_name','start_name')):
                self.assertNotEqual(cat.pgettext(context,scenario[key]),scenario[key])


if __name__ == '__main__':
    unittest.main()
