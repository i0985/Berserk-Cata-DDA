"""Eclipse cutscene/state regressions using a model, not the CDDA binary.

The model exercises actor scopes, effect order and blocked-cell fallbacks.
It does not simulate actual AI, lighting, damage, map loading or save files.
"""

import copy
import unittest

from test_apostle_hunts import HuntGraph
from test_behelit_rewards import MOD, objects

BOSS = 'mon_berserk_eclipse_griffith_active'
WAITING = 'berserk_eclipse_griffith_waiting'
HAND = 'bio_berserk_hand_stump'
EYE = 'bio_berserk_lost_eye'
CANNON = 'bio_berserk_arm_cannon'


class GraspGraph(HuntGraph):
    def __init__(self):
        super().__init__({'u_berserk_eclipse_trial_active': 1,
                          'u_berserk_eclipse_rescue_state': 0})
        self.omt = 'berserk_eclipse_expanded_ceremony'
        self.avatar = (50, -20, -7)
        self.actors = []
        self.current_monster = None
        self.bionics = set()
        self.bionic_additions = []
        self.player_effects = set()
        self.blocked = set()
        self.messages = []
        self.order = []
        self.recipes = set()

    def condition(self, value):
        if 'u_has_effect' in value:
            effects = self.player_effects if self.alpha == 'avatar' else self.current_monster['effects']
            return value['u_has_effect'] in effects
        if 'u_has_bionics' in value:
            assert self.alpha == 'avatar', 'wounds checked on the monster'
            return value['u_has_bionics'] in self.bionics
        return super().condition(value)

    def run(self, id):
        e = self.eocs[id]
        key = 'effect' if 'condition' not in e or self.condition(e['condition']) else 'false_effect'
        if key in e:
            self.effect(e[key])

    def position_is_free(self, pos):
        return pos != self.avatar and pos not in self.blocked and not any(m['pos'] == pos for m in self.actors)

    def effect(self, value):
        if isinstance(value, dict):
            if 'monster' in value and 'u_location_variable' in value:
                assert self.alpha == 'avatar'
                found = any(m['id'] == value['monster'] and
                            max(abs(m['pos'][i] - self.avatar[i]) for i in range(3)) <= value['target_max_radius']
                            for m in self.actors)
                for id in value['true_eocs' if found else 'false_eocs']:
                    self.run(id)
                return
            if 'location_variable_adjust' in value:
                var = value['location_variable_adjust']; key = var['context_val']
                pos = self.context[key]
                scale = 24 if value.get('overmap_tile') else 1
                self.context[key] = tuple(pos[i] + value.get(axis+'_adjust', 0)*scale
                                          for i, axis in enumerate(('x', 'y', 'z')))
                return
            if 'u_spawn_monster' in value:
                assert self.alpha == 'avatar'
                pos = self.resolve(value['target_var'])
                free = self.position_is_free(pos)
                if free:
                    m = {'id': value['u_spawn_monster'], 'pos': pos,
                         'effects': set(), 'sees_avatar': True, 'hp': 440 if value['u_spawn_monster'] == BOSS else 80}
                    self.actors.append(m)
                    self.order.append(('spawn', m['id']))
                for id in value.get('true_eocs' if free else 'false_eocs', []):
                    self.run(id)
                return
            if 'u_run_monster_eocs' in value:
                # Exact-tag native API makes the monster alpha, not beta.
                for m in list(self.actors):
                    if m['id'] not in value['mtype_ids'] or m['pos'][2] != self.avatar[2]:
                        continue
                    if max(abs(m['pos'][i]-self.avatar[i]) for i in (0, 1)) > value['monster_range']:
                        continue
                    if value.get('monster_must_see') and not m['sees_avatar']:
                        continue
                    alpha, mon = self.alpha, self.current_monster
                    self.alpha = 'monster'; self.current_monster = m
                    for id in value['u_run_monster_eocs']:
                        self.run(id)
                    self.alpha, self.current_monster = alpha, mon
                return
            if 'u_add_effect' in value or 'u_lose_effect' in value:
                effects = self.player_effects if self.alpha == 'avatar' else self.current_monster['effects']
                if 'u_add_effect' in value:
                    effects.add(value['u_add_effect'])
                else:
                    effects.discard(value['u_lose_effect'])
                    self.order.append(('release', value['u_lose_effect']))
                return
            if 'u_add_bionic' in value:
                assert self.alpha == 'avatar', 'bionic installed on the monster'
                self.bionic_additions.append(value['u_add_bionic'])
                self.bionics.add(value['u_add_bionic'])
                self.order.append(('wound', value['u_add_bionic']))
                return
            if 'u_message' in value:
                self.messages.append(value['u_message'])
                self.order.append(('popup', value['u_message']))
                return
        return super().effect(value)

    def enter(self):
        self.run('EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_START')
        return next(m for m in self.actors if m['id'] == BOSS)

    def approach(self):
        boss = next(m for m in self.actors if m['id'] == BOSS)
        self.avatar = (boss['pos'][0] - 3, boss['pos'][1], boss['pos'][2])
        self.run('EOC_BERSERK_ECLIPSE_GRASP_ON_MOVE')


class EclipseGrasp(unittest.TestCase):
    def test_griffith_waits_without_starting_combat_and_distant_player_is_unchanged(self):
        g = GraspGraph(); boss = g.enter()
        self.assertEqual(boss['pos'], (63, -7, -7))
        self.assertIn(WAITING, boss['effects'])
        self.assertEqual(g.flags['u_berserk_eclipse_final_spawned'], 1)
        self.assertNotEqual(g.flags.get('u_berserk_eclipse_final_started'), 1)
        g.run('EOC_BERSERK_ECLIPSE_GRASP_ON_MOVE')
        self.assertFalse(g.bionics)
        self.assertEqual(len(g.actors), 1)
        self.assertFalse(g.messages)

    def test_ring_popup_wounds_then_release_in_that_order(self):
        g = GraspGraph(); boss = g.enter(); hp = boss['hp']; g.approach()
        neighbors = {(g.avatar[0]+dx, g.avatar[1]+dy, -7)
                     for dx in (-1, 1) for dy in (-1, 1)}
        mob_positions = {m['pos'] for m in g.actors if m['id'] != BOSS}
        self.assertEqual(mob_positions, neighbors)
        self.assertEqual(sum(m['id'] == 'mon_berserk_eclipse_wretch' for m in g.actors), 4)
        self.assertEqual(sum(m['id'] == 'mon_berserk_eclipse_halfbreed' for m in g.actors), 0)
        self.assertFalse(any(m['pos'] in {(g.avatar[0]+dx,g.avatar[1]+dy,-7)
                         for dx,dy in ((-1,0),(1,0),(0,-1),(0,1))} for m in g.actors))
        self.assertEqual(g.bionics, {HAND, EYE})
        self.assertIn('berserk_missing_left_hand', g.player_effects)
        self.assertNotIn(WAITING, boss['effects'])
        self.assertEqual(boss['hp'], hp)
        self.assertEqual(g.flags['u_berserk_eclipse_grasp_state'], 2)
        self.assertEqual(g.flags['u_berserk_eclipse_final_started'], 1)
        kinds = [kind for kind, _ in g.order]
        self.assertLess(kinds.index('popup'), kinds.index('wound'))
        self.assertLess(max(i for i,k in enumerate(kinds) if k == 'wound'), kinds.index('release'))
        self.assertLess(max(i for i,k in enumerate(kinds) if k == 'spawn'), kinds.index('popup'))
        self.assertNotIn('berserk_eclipse_era', g.flags)
        self.assertNotIn('bio_berserk_brand_of_sacrifice', g.bionics)

    def test_save_reload_and_reenter_do_not_repeat_ring_wounds_or_boss(self):
        g = GraspGraph(); g.enter(); g = copy.deepcopy(g)
        g.run('EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_START')
        self.assertEqual(sum(m['id'] == BOSS for m in g.actors), 1)
        g.approach(); g = copy.deepcopy(g)
        count, wounds, messages = len(g.actors), list(g.bionic_additions), len(g.messages)
        for id in ('EOC_BERSERK_ECLIPSE_GRASP_ON_MOVE', 'EOC_BERSERK_ECLIPSE_GRASP_RETRY',
                   'EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_START'):
            g.run(id)
        self.assertEqual((len(g.actors),g.bionic_additions,len(g.messages)),(count,wounds,messages))

    def test_existing_wounds_and_cannon_are_kept(self):
        for existing in ({HAND}, {EYE}, {HAND,EYE}, {HAND,CANNON}, {HAND,CANNON,EYE}, {CANNON}):
            g = GraspGraph(); g.bionics = set(existing); g.enter(); g.approach()
            self.assertTrue(set(existing) <= g.bionics)
            self.assertEqual(g.bionic_additions.count(EYE), 0 if EYE in existing else 1)
            self.assertEqual(g.bionic_additions.count(HAND), 0 if HAND in existing or CANNON in existing else 1)
            g.run('EOC_BERSERK_ECLIPSE_APPLY_STORY_WOUNDS')
            self.assertEqual(g.bionic_additions.count(EYE), 0 if EYE in existing else 1)

    def test_walls_and_occupied_neighbors_are_not_overwritten_or_retried(self):
        g = GraspGraph(); boss = g.enter()
        g.avatar=(boss['pos'][0]-3,boss['pos'][1],-7)
        wall=(g.avatar[0]-1,g.avatar[1]-1,-7); npc=(g.avatar[0]+1,g.avatar[1]+1,-7)
        g.blocked.add(wall);g.actors.append({'id':'friendly_npc_mock','pos':npc,'effects':set(),'hp':100})
        g.run('EOC_BERSERK_ECLIPSE_GRASP_ON_MOVE')
        self.assertFalse(any(m['pos']==wall for m in g.actors))
        self.assertEqual(sum(m['pos']==npc for m in g.actors),1)
        self.assertEqual(sum(m['id'] in ('mon_berserk_eclipse_wretch','mon_berserk_eclipse_halfbreed') for m in g.actors),2)
        g.run('EOC_BERSERK_ECLIPSE_GRASP_RETRY')
        self.assertEqual(len(g.actors),4)

    def test_blocked_center_does_not_claim_a_started_encounter_and_retry_is_bounded(self):
        g = GraspGraph();g.blocked.add((63,-7,-7))
        g.run('EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_START')
        for _ in range(8):g.run('EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_RETRY')
        self.assertEqual(g.flags['u_berserk_eclipse_final_spawn_attempts'],3)
        self.assertNotEqual(g.flags.get('u_berserk_eclipse_final_spawned'),1)
        self.assertNotEqual(g.flags.get('u_berserk_eclipse_final_started'),1)
        self.assertEqual(len(g.messages),1)
        g.blocked.clear();g.enter()
        self.assertEqual(g.flags['u_berserk_eclipse_final_spawned'],1)

    def test_legacy_active_combat_is_not_frozen_or_restarted(self):
        g = GraspGraph();g.flags['u_berserk_eclipse_final_started']=1
        g.actors.append({'id':BOSS,'pos':(63,-7,-7),'effects':set(),'sees_avatar':True,'hp':120})
        g.run('EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_START');g.approach()
        self.assertEqual(len(g.actors),1)
        self.assertFalse(g.bionics)
        self.assertEqual(g.actors[0]['hp'],120)
        self.assertFalse(g.actors[0]['effects'])

    def test_completed_rescue_wrong_area_or_no_line_of_sight_cannot_trigger(self):
        for mode in ('rescued','outside','hidden'):
            g=GraspGraph();boss=g.enter();g.avatar=(boss['pos'][0]-3,boss['pos'][1],-7)
            if mode=='rescued':g.flags['u_berserk_eclipse_rescue_state']=2
            elif mode=='outside':g.omt='berserk_eclipse_expanded_threshold'
            else:boss['sees_avatar']=False
            g.run('EOC_BERSERK_ECLIPSE_GRASP_ON_MOVE')
            self.assertFalse(g.bionics);self.assertEqual(len(g.actors),1)

    def test_stage_one_recovery_does_not_spawn_another_ring(self):
        g=GraspGraph();g.enter();g.flags['u_berserk_eclipse_grasp_state']=1
        g.run('EOC_BERSERK_ECLIPSE_GRASP_RETRY')
        self.assertEqual(len(g.actors),1)
        self.assertFalse(g.messages)
        self.assertEqual(g.bionics,{HAND,EYE})
        self.assertEqual(g.flags['u_berserk_eclipse_grasp_state'],2)

    def test_waiting_blocks_movement_and_both_attack_types_with_no_permanent_flag(self):
        effect=objects(MOD/'effects/eclipse_story_effects.json')[0]
        self.assertEqual(set(effect['flags']),{'CANNOT_MOVE','CANNOT_ATTACK'})
        boss=objects(MOD/'monsters/griffith_eclipse_active.json')[0]
        self.assertNotIn('IMMOBILE',boss['flags'])
        g=GraspGraph();phase=g.eocs['EOC_BERSERK_ECLIPSE_GRASP_ON_MOVE']
        self.assertEqual(phase['required_event'],'avatar_moves')
        self.assertEqual(g.eocs['EOC_BERSERK_ECLIPSE_GRIFFITH_WAIT']['effect']['duration'],'PERMANENT')
        trigger=g.eocs['EOC_BERSERK_ECLIPSE_GRASP_SCAN']['effect']['else']
        self.assertEqual(trigger['monster_range'],3)
        self.assertTrue(trigger['monster_must_see'])
        # Both existing death and low-health paths still reach the original rescue.
        self.assertEqual(boss['death_function']['eoc'],'EOC_BERSERK_ECLIPSE_GRIFFITH_DIES')
        for id in ('EOC_BERSERK_ECLIPSE_RESCUE_THRESHOLD','EOC_BERSERK_ECLIPSE_RESCUE_PREVENT_DEATH'):
            self.assertIn('u_berserk_eclipse_final_started == 1',str(g.eocs[id]['condition']))
