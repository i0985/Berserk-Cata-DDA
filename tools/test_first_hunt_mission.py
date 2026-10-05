"""First-hunt data/state regressions. This models effects, not CDDA execution."""

import copy
import gettext
import unittest

from test_apostle_hunts import HuntGraph
from test_behelit_rewards import MOD, objects

MISSION = 'MISSION_BERSERK_FIRST_HUNT'
TARGET = 'u_berserk_first_hunt_location'


class MissionGraph(HuntGraph):
    def __init__(self, flags=None):
        super().__init__({'berserk_eclipse_era': 1,
                          'u_berserk_eclipse_rescue_state': 2, **(flags or {})})
        self.locations = {}
        self.search_calls = 0
        self.assign_calls = 0
        self.next_search = (240, -192, 0)
        self.return_origin_on_failure = False
        self.selected_mission = None
        self.messages = []

    def condition(self, value):
        if 'overmap_at_point' in value:
            return self.locations.get(self.resolve(value['point'])) == value['overmap_at_point']
        return super().condition(value)

    def evaluate(self, expr):
        # Native distance receives an actor string and a stored coordinate variable.
        self.context['test_avatar'] = self.avatar
        return super().evaluate(expr.replace("distance('u',", 'distance(_test_avatar,'))

    def effect(self, value):
        if isinstance(value, dict):
            if 'target_params' in value:
                if value['target_params']['om_terrain']!='berserk_first_hunt_lair':
                    return HuntGraph.effect(self,value)
                self.search_calls += 1
                if self.next_search is not None:
                    self.context[value['u_location_variable']['context_val']] = self.next_search
                    self.locations[self.next_search] = 'berserk_first_hunt_lair'
                    callbacks = value['true_eocs']
                elif self.return_origin_on_failure:
                    # Exact-tag get_om_terrain_pos returns the player's OMT on failure.
                    self.context[value['u_location_variable']['context_val']] = self.avatar
                    callbacks = value['true_eocs']
                else:
                    callbacks = value['false_eocs']
                for id in callbacks:
                    self.run(id)
                return
            if 'assign_mission' in value:
                self.assign_calls += 1
                definition = objects(MOD / 'missions/first_hunt.json')[0]
                params = definition['start']['assign_mission_target']
                pos = self.resolve(params['var'])
                self.active_missions[value['assign_mission']] = pos
                self.selected_mission = value['assign_mission']
                return
            if 'finish_mission' in value:
                id = value['finish_mission']
                if id in self.active_missions:
                    self.completed_missions.append(id)
                    del self.active_missions[id]
                return
            if 'u_message' in value:
                self.messages.append(value['u_message'])
                return
        return super().effect(value)


class FirstHuntMission(unittest.TestCase):
    def test_assignment_reuses_exact_saved_target_and_never_searches_again(self):
        g = MissionGraph({'u_berserk_first_hunt_marked': 1, TARGET: (-480, 216, 0)})
        g.locations[g.flags[TARGET]] = 'berserk_first_hunt_lair'
        g.active_missions['MISSION_OTHER'] = (48, 24, 0)
        for _ in range(5):
            g.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertEqual(g.assign_calls, 1)
        self.assertEqual(g.search_calls, 0)
        self.assertEqual(g.active_missions[MISSION], (-480, 216, 0))
        self.assertEqual(g.active_missions['MISSION_OTHER'], (48, 24, 0))
        self.assertEqual(g.inventory.count('berserk_first_hunt_directions'), 1)

    def test_target_and_other_selected_mission_survive_reload_and_recall(self):
        g = MissionGraph(); g.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        target = g.active_missions[MISSION]
        g.selected_mission = 'MISSION_OTHER'
        g = copy.deepcopy(g)
        g.run('EOC_BERSERK_FIRST_HUNT_RECALL')
        self.assertEqual(g.assign_calls, 1)
        self.assertEqual(g.search_calls, 1)
        self.assertEqual(g.active_missions[MISSION], target)
        self.assertEqual(g.selected_mission, 'MISSION_OTHER')

    def test_invalid_saved_target_is_not_replaced(self):
        g = MissionGraph({'u_berserk_first_hunt_marked': 1, TARGET: (24, 24, 0)})
        g.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertEqual(g.flags[TARGET], (24, 24, 0))
        self.assertEqual(g.search_calls, 0)
        self.assertFalse(g.active_missions)
        self.assertIn('could not be verified', g.messages[-1])
        messages = len(g.messages)
        g.run('EOC_BERSERK_FIRST_HUNT_FIND')
        self.assertEqual(len(g.messages), messages)

    def test_failed_locator_returning_origin_cannot_assign_a_false_target(self):
        g = MissionGraph(); g.next_search = None; g.return_origin_on_failure = True
        for _ in range(10):
            g.run('EOC_BERSERK_FIRST_HUNT_FIND')
        self.assertEqual(g.search_calls, 3)
        self.assertNotIn(TARGET, g.flags)
        self.assertFalse(g.active_missions)
        self.assertNotEqual(g.flags.get('u_berserk_first_hunt_marked'), 1)
        self.assertIn('berserk_first_hunt_directions', g.inventory)

    def test_bounded_retry_requires_travel_then_notes_can_start_a_new_search(self):
        g = MissionGraph(); g.next_search = None
        for _ in range(3):
            g.run('EOC_BERSERK_FIRST_HUNT_FIND')
        g.run('EOC_BERSERK_FIRST_HUNT_RECALL')
        self.assertEqual(g.search_calls, 3)
        g.avatar = (24, 0, 0); g.next_search = (264, -192, 0)
        g.run('EOC_BERSERK_FIRST_HUNT_RECALL')
        self.assertEqual(g.search_calls, 4)
        self.assertEqual(g.flags['u_berserk_first_hunt_search_attempts'], 1)
        self.assertIn(MISSION, g.active_missions)

    def test_death_completes_once_without_changing_independent_hunts(self):
        g = MissionGraph({'berserk_hunt_count_state': 4, 'berserk_hunt_rosine_state': 2})
        g.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        for _ in range(3):
            g.run('EOC_BERSERK_FIRST_HUNT_APOSTLE_DIES')
        self.assertEqual(g.completed_missions, [MISSION])
        self.assertNotIn(MISSION, g.active_missions)
        self.assertEqual(g.flags['berserk_hunt_count_state'], 4)
        self.assertEqual(g.flags['berserk_hunt_rosine_state'], 2)
        g.run('EOC_BERSERK_FIRST_HUNT_RECALL')
        self.assertEqual(g.assign_calls, 1)
        self.assertIn('burned scrap', g.messages[-1])

    def test_already_completed_old_save_gets_no_new_mission_or_lair(self):
        g = MissionGraph({'u_berserk_first_hunt_done': 1})
        g.run('EOC_BERSERK_FIRST_HUNT_RECALL')
        g.run('EOC_BERSERK_FIRST_HUNT_FIND')
        self.assertEqual(g.assign_calls, 0)
        self.assertEqual(g.search_calls, 0)

    def test_pre_eclipse_and_underground_never_assign(self):
        for flags, pos in [({'berserk_eclipse_era': 0}, (0, 0, 0)),
                           ({'u_berserk_eclipse_rescue_state': 1}, (0, 0, 0)),
                           ({}, (0, 0, -1))]:
            g = MissionGraph(flags); g.avatar = pos
            g.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
            self.assertEqual(g.search_calls, 0)
            self.assertFalse(g.active_missions)

    def test_immediate_hooks_and_native_schema_do_not_generate_a_second_site(self):
        g = MissionGraph()
        for id in ('EOC_BERSERK_ECLIPSE_AFTERMATH', 'EOC_BERSERK_POST_ECLIPSE_START'):
            self.assertEqual(g.eocs[id]['effect'][-1]['run_eocs'], 'EOC_BERSERK_FIRST_HUNT_REQUEST')
        mission = objects(MOD / 'missions/first_hunt.json')[0]
        self.assertEqual(mission['origins'], ['ORIGIN_GAME_START'])
        self.assertEqual(mission['goal'], 'MGOAL_CONDITION')
        self.assertNotIn('deadline', mission)
        self.assertFalse(mission['has_generic_rewards'])
        params = mission['start']['assign_mission_target']
        self.assertEqual(params['var'], {'u_val': 'berserk_first_hunt_location'})
        self.assertNotIn('om_special', params)
        self.assertNotIn('om_terrain_replace', params)
        search = g.eocs['EOC_BERSERK_FIRST_HUNT_LOCATE']['effect'][-1]['target_params']
        self.assertEqual((search['min_distance'], search['search_range']), (8, 16))
        self.assertTrue(search['cant_see'])
        self.assertEqual(search['om_special'], 'berserk_first_hunt_special')
        self.assertNotIn('om_terrain_replace',search)

    def test_new_text_is_translated_in_compiled_catalogs(self):
        sources = set()
        def visit(value):
            if isinstance(value, list):
                for v in value: visit(v)
            elif isinstance(value, dict):
                for key, v in value.items():
                    if key in ('u_message', 'name', 'description', 'menu_text', 'str_sp') and isinstance(v, str):
                        sources.add(v)
                    visit(v)
        for path in ('effects/first_hunt_eocs.json', 'missions/first_hunt.json', 'items/first_hunt_directions.json'):
            visit(objects(MOD / path))
        for locale in ('ru', 'zh_CN'):
            with (MOD / f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo').open('rb') as f:
                catalog = gettext.GNUTranslations(f)
            self.assertFalse([s for s in sources if catalog.gettext(s) == s], locale)
