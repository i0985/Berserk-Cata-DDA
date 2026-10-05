"""3.1 transition regressions using JSON and small talker models, not CDDA.

These do not measure worldgen distances, native sight, AI or disk save/loading.
"""
import copy
import re
import unittest

from test_apostle_hunts import HuntGraph
from test_behelit_rewards import MOD, objects
from test_grunbeld_hunt import DragonGraph


class CampaignGraph(HuntGraph):
    def __init__(self, flags=None):
        super().__init__({'berserk_eclipse_era': 1,
                          'u_berserk_eclipse_rescue_state': 2,
                          'u_berserk_first_hunt_done': 1, **(flags or {})})
        self.locator_calls = []

    def run(self, id):
        e = self.eocs[id]
        if 'condition' not in e or self.condition(e['condition']):
            self.effect(e['effect'])
        elif 'false_effect' in e:
            self.effect(e['false_effect'])

    def effect(self, v):
        if isinstance(v, dict):
            if 'target_params' in v:
                self.locator_calls.append(v['target_params'])
                # Native failure can return the origin to u_location_variable.
                # The terrain validation must reject that apparently valid point.
                self.context[v['u_location_variable']['context_val']] = self.avatar
                for id in v.get('true_eocs', []):
                    self.run(id)
                return
            if 'set_string_var' in v:
                target = v['target_var']
                self.context[target['context_val']] = v['set_string_var']
                return
        return super().effect(v)


class FortressGraph(DragonGraph):
    def __init__(self, flags=None):
        super().__init__({'berserk_flora_stage': 3, **(flags or {})})

    def evaluate(self, expr):
        expr = re.sub(
            r"u_monsters_nearby\('mon_berserk_grunbeld_knight', 'radius': 60, 'attitude': 'both'\)",
            str(int(self.boss == 'knight' and self.hp > 0)), expr)
        return super().evaluate(expr.replace("time('now')", '1000'))

    def condition(self, v):
        if v == 'u_is_monster':
            return self.boss is not None or self.grove_actor
        return super().condition(v)


class NewHorizon31(unittest.TestCase):
    def test_flora_requires_three_closed_breaches_not_the_first_hunt(self):
        for closed in range(4):
            flags = {'berserk_hunt_' + k + '_state': 4 if i < closed else 3
                     for i, k in enumerate(('count', 'wyald', 'rosine'))}
            g = CampaignGraph(flags)
            g.run('EOC_BERSERK_LATE_FLORA_CHECK')
            self.assertEqual('berserk_flora_directions' in g.inventory, closed == 3)
            self.assertEqual(bool(g.locator_calls), closed == 3)
            before = len(g.locator_calls)
            g.run('EOC_BERSERK_LATE_FLORA_CHECK')
            self.assertEqual(len(g.locator_calls), before)
            self.assertLessEqual(g.inventory.count('berserk_flora_directions'), 1)

    def test_underground_last_seal_defers_clue_until_surface_without_duplication(self):
        g = CampaignGraph({'berserk_hunt_' + k + '_state': 5
                           for k in ('count', 'wyald', 'rosine')})
        g.avatar = (-240, 480, -1)
        g.run('EOC_BERSERK_LATE_FLORA_CHECK')
        self.assertFalse(g.inventory)
        saved = copy.deepcopy(g)
        saved.avatar = (-240, 480, 0)
        saved.run('EOC_BERSERK_LATE_FLORA_RECOVER')
        saved.run('EOC_BERSERK_LATE_FLORA_RECOVER')
        self.assertEqual(saved.inventory.count('berserk_flora_directions'), 1)
        self.assertFalse(saved.flags.get('berserk_flora_stage'))
        self.assertFalse(saved.active_missions)  # Failed lookup is not a mission success.

    def test_valid_existing_flora_survives_new_progression_gate(self):
        g = CampaignGraph({'berserk_flora_stage': 1,
                           'berserk_flora_location': (-240, 480, 0)})
        g.terrain_locations[(-240, 480, 0)] = 'berserk_flora_manor'
        self.assertTrue(g.condition(g.eocs['EOC_BERSERK_FLORA_ROUTE_AVAILABLE']['condition']))
        g.run('EOC_BERSERK_FLORA_SEEK')
        self.assertEqual(g.flags['berserk_flora_location'], (-240, 480, 0))
        self.assertFalse(g.locator_calls)
        g.terrain_locations.clear()
        self.assertFalse(g.condition(g.eocs['EOC_BERSERK_FLORA_ROUTE_AVAILABLE']['condition']))

    def test_all_named_sites_generate_naturally_and_lookup_cannot_insert_under_player(self):
        files = ('apostle_count.json', 'wyald_rosine_hunts.json',
                 'flora_manor.json', 'grunbeld_hunt.json')
        specials = [e for f in files for e in objects(MOD/'overmap'/f)
                    if e['type'] == 'overmap_special']
        self.assertEqual(len(specials), 5)
        for s in specials:
            self.assertEqual(s['occurrences'], [1, 1])
            self.assertIn('GLOBALLY_UNIQUE', s['flags'])
        targets = {'berserk_count_hall', 'berserk_wyald_ring', 'berserk_rosine_nest',
                   'berserk_flora_manor_west', 'berserk_grunbeld_crucible'}
        def walk(v):
            if isinstance(v, dict):
                t = v.get('target_params', {})
                if t.get('om_terrain') in targets:
                    self.assertNotIn('om_special', t)
                    self.assertNotIn('om_terrain_replace', t)
                    self.assertNotIn('create_if_necessary', t)
                    self.assertFalse(t['random'])
                    self.assertNotIn('search_range', t)  # Required by native parser.
                for x in v.values(): walk(x)
            elif isinstance(v, list):
                for x in v: walk(x)
        for e in CampaignGraph().eocs.values(): walk(e)

    def test_failed_spawn_cannot_announce_or_commit_a_fortress_boss(self):
        g = FortressGraph({'berserk_hunt_grunbeld_attempts': 6})
        g.run('EOC_BERSERK_GRUNBELD_ARRIVED')
        self.assertFalse(g.flags.get('berserk_hunt_grunbeld_spawned'))
        self.assertFalse(g.flags.get('berserk_hunt_grunbeld_state'))

    def test_immediate_post_escape_fortress_entry_retires_only_the_siege_actor(self):
        g = FortressGraph()
        g.grove_actor = True
        g.begin()
        self.assertEqual(g.boss, 'knight')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_spawned'], 1)
        self.assertFalse(g.grove_actor)
        self.assertFalse(g.flags.get('berserk_apostle_grunbeld_dead'))
        self.assertFalse(g.flags.get('berserk_hunt_grunbeld_reward_claimed'))
        self.assertEqual(len(g.spawned), 1)
        g.hp = 91
        saved = copy.deepcopy(g)
        saved.run('EOC_BERSERK_GRUNBELD_ENTER')
        self.assertEqual(saved.hp, 91)
        self.assertEqual(len(saved.spawned), 1)
        self.assertEqual(saved.flags['berserk_hunt_grunbeld_presence_confirmed'], 1)

    def test_withdrawn_old_siege_actor_cannot_record_a_later_death_or_drop_a_second_shard(self):
        g = FortressGraph()
        g.run('EOC_BERSERK_GRUNBELD_WITHDRAW_GROVE')  # Actor is unloaded.
        g.alpha = None
        g.victim = (48, 48, 0)
        g.run('EOC_BERSERK_FLORA_GRUNBELD_DIES')
        self.assertFalse(g.flags.get('berserk_apostle_grunbeld_dead'))
        self.assertFalse(g.ground)
        actor = next(e for e in objects(MOD/'monsters/flora_siege.json')
                     if e['id'] == 'mon_berserk_flora_grunbeld')
        self.assertEqual(actor['death_drops'], 'EMPTY_GROUP')

    def test_actual_siege_death_retains_one_original_death_and_one_body_reward(self):
        g = FortressGraph({'berserk_flora_stage': 2})
        g.alpha = None
        g.victim = (-24, 72, 0)
        for _ in range(2): g.run('EOC_BERSERK_FLORA_GRUNBELD_DIES')
        self.assertEqual(g.flags['berserk_apostle_grunbeld_dead'], 1)
        self.assertEqual(g.ground, [('berserk_grunbeld_carapace_shard', g.victim)])
        g.alpha = 'avatar'
        g.flags['berserk_flora_stage'] = 3
        g.arena('grunbeld')
        g.run('EOC_BERSERK_GRUNBELD_ENTER')
        self.assertFalse(g.spawned)

    def test_knight_waits_for_siege_end_but_an_already_found_fortress_stays_known(self):
        g = FortressGraph({'berserk_flora_stage': 1})
        g.run('EOC_BERSERK_GRUNBELD_SEEK')
        self.assertFalse(g.locator_calls)
        g.flags['berserk_flora_stage'] = 3
        g.run('EOC_BERSERK_GRUNBELD_SEEK')
        self.assertEqual(g.locator_calls, ['grunbeld'])
        p = g.flags['berserk_hunt_grunbeld_location']
        g.flags['berserk_flora_stage'] = 1
        g.run('EOC_BERSERK_GRUNBELD_SEEK')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_location'], p)

    def test_unknown_old_spawn_flag_is_not_treated_as_a_death_or_a_free_respawn(self):
        g = FortressGraph({'berserk_hunt_grunbeld_spawned': 1,
                           'berserk_hunt_grunbeld_state': 2})
        g.arena('grunbeld')
        g.run('EOC_BERSERK_GRUNBELD_ENTER')
        self.assertFalse(g.spawned)
        self.assertFalse(g.flags.get('berserk_apostle_grunbeld_dead'))
        self.assertFalse(g.flags.get('berserk_hunt_grunbeld_reward_claimed'))

    def test_repeated_dragon_tag_records_presence_without_repeating_recovery_delay(self):
        g = FortressGraph()
        g.boss = 'dragon'
        g.hp = 600
        for _ in range(3): g.run('EOC_BERSERK_GRUNBELD_TAG_DRAGON')
        self.assertEqual(g.pause, 3)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_presence_confirmed'], 1)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_last_seen'], 1000)

    def test_knot_is_worn_night_vision_without_an_armor_requirement(self):
        item = next(e for e in objects(MOD/'items/apostle_relics.json')
                    if e['id'] == 'berserk_wyald_beast_knot')
        enc = next(e for e in objects(MOD/'enchantments/apostle_relics.json')
                   if e['id'] == item['passive_effects'][0]['id'])
        self.assertEqual(enc['has'], 'WORN')
        self.assertEqual(enc['condition'], 'ALWAYS')
        self.assertEqual(enc['values'], [{'value': 'NIGHT_VIS', 'add': 2}])


if __name__ == '__main__':
    unittest.main()
