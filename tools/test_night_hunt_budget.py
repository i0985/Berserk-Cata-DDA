"""Exercise real night EOCs against explicit time/shelter/spawn fixtures.

No CDDA binary, AI, hearing, native map placement or sleep simulation runs.
The fixture chooses successful outdoor requests; the JSON chooses all limits,
branches, counters and saved source tags.
"""
import json
import math
import re
import unittest
from test_grunbeld_breath import Actor, load


def gather(v, result):
    if isinstance(v, list):
        for item in v:
            gather(item, result)
    elif isinstance(v, dict):
        if 'id' in v and 'effect' in v:
            result[v['id']] = v
        for item in v.values():
            gather(item, result)


class NightGraph:
    def __init__(self):
        self.eocs = {}
        for path in ('effects/eclipse_brand_eocs.json', 'effects/eclipse_era_eocs.json',
                     'effects/spawn_source_diagnostics.json'):
            gather(load(path), self.eocs)
        self.avatar = Actor((0, 0, 0))
        self.alpha = self.avatar
        self.world = {'berserk_eclipse_era': 1}
        self.now = 100
        self.monsters = []
        self.circular = False
        self.requests = []
        self.outcomes = [True, True, True]
        self.brand = True
        self.day = False
        self.flora = self.ward = self.quiet = False
        self.messages = []
        self.pain = 0

    def var(self, key):
        return (self.alpha.values if key.startswith('u_') else self.world).get(
            key.removeprefix('u_'), 0)

    def evaluate(self, expression):
        # Substitute math variable names, leaving function names/literals alone.
        expression = expression.replace("'radius':", 'radius=')
        expression = re.sub(r'\b(u_)?berserk_\w+\b',
                            lambda m: 'var(' + repr(m[0]) + ')', expression)
        return eval(expression, {'__builtins__': {}},
                    {'var': self.var, 'time': lambda _: self.now, 'min': min, 'max': max,
                     'u_val': lambda key: self.alpha.pos[{'pos_x': 0, 'pos_y': 1, 'pos_z': 2}[key]],
                     'u_monsters_nearby': lambda *ids, **kw: int(self.alpha.mtype in ids),
                     'u_hp': lambda _: self.alpha.hp, 'u_pain': lambda: self.pain})

    def value(self, v):
        if isinstance(v, str):
            return v
        if 'math' in v:
            return self.evaluate(v['math'][0])
        if 'u_val' in v:
            return self.alpha.values.get(v['u_val'], '')
        raise AssertionError(v)

    def condition(self, v):
        if v == 'is_day':
            return self.day
        if not isinstance(v, dict):
            raise AssertionError(v)
        if 'and' in v:
            return all(self.condition(e) for e in v['and'])
        if 'or' in v:
            return any(self.condition(e) for e in v['or'])
        if 'not' in v:
            return not self.condition(v['not'])
        if 'math' in v:
            return bool(self.evaluate(v['math'][0]))
        if 'compare_string' in v:
            return self.value(v['compare_string'][0]) == self.value(v['compare_string'][1])
        if 'u_has_bionics' in v:
            return self.brand
        if 'u_near_om_location' in v:
            return False  # fixtures use the current independent-breach registry
        if 'test_eoc' in v:
            self.assert_flora(v['test_eoc'])
            return self.flora
        if 'x_in_y_chance' in v:
            return False  # exercise the suppressed local-breach branch
        if 'u_has_effect' in v:
            return self.alpha.effects.get(v['u_has_effect'], 0) > self.now
        raise AssertionError(v)

    @staticmethod
    def assert_flora(id):
        assert id == 'EOC_BERSERK_FLORA_NIGHT_QUIET'

    def run(self, id):
        if id == 'EOC_BERSERK_APOSTLE_CHECK_HERE':
            self.world['berserk_apostle_quiet_here'] = int(self.quiet)
            return
        e = self.eocs[id] if isinstance(id, str) else id
        passed = 'condition' not in e or self.condition(e['condition'])
        branch = 'effect' if passed else 'false_effect'
        if branch in e:
            self.effect(e[branch])

    def callbacks(self, items):
        for e in items:
            self.run(e)

    def effect(self, v):
        if isinstance(v, list):
            for e in v:
                self.effect(e)
            return
        if 'if' in v:
            key = 'then' if self.condition(v['if']) else 'else'
            if key in v:
                self.effect(v[key])
        elif 'math' in v:
            key, op, expr = re.fullmatch(r'(.+?) (\+=|=) (.+)', v['math'][0]).groups()
            if key == 'u_pain()':
                self.pain = self.evaluate(expr)
                return
            store = self.alpha.values if key.startswith('u_') else self.world
            name = key.removeprefix('u_')
            value = self.evaluate(expr)
            store[name] = value + (store.get(name, 0) if op == '+=' else 0)
        elif 'set_string_var' in v:
            self.alpha.values[v['target_var']['u_val']] = v['set_string_var']
        elif 'run_eocs' in v:
            self.run(v['run_eocs'])
        elif 'u_location_variable' in v:
            self.callbacks(v.get('true_eocs' if self.ward else 'false_eocs', []))
        elif 'u_run_monster_eocs' in v:
            saved = self.alpha
            for mon in list(self.monsters):
                distance = (math.dist(mon.pos[:2], saved.pos[:2]) if self.circular else
                            max(abs(x-y) for x, y in zip(mon.pos, saved.pos)))
                if (mon.mtype in v['mtype_ids'] and mon.pos[2] == saved.pos[2]
                        and distance <= v['monster_range']):
                    self.alpha = mon
                    self.callbacks(v['u_run_monster_eocs'])
            self.alpha = saved
        elif 'u_spawn_monster' in v:
            self.requests.append(v)
            success = self.outcomes.pop(0)
            if success:
                mon = Actor((30, len(self.monsters), 0))
                mon.mtype = 'mon_berserk_brand_wretch'
                mon.values.update(v['mon_variables'])
                self.monsters.append(mon)
            self.callbacks(v.get('true_eocs' if success else 'false_eocs', []))
        elif 'u_add_effect' in v:
            self.alpha.effects[v['u_add_effect']] = self.now + 480
        elif 'u_message' in v:
            self.messages.append(v['u_message'])
        else:
            raise AssertionError(v)

    def hunt(self):
        self.run('EOC_BERSERK_BRAND_NIGHT_HUNT')


class NightBudgetTests(unittest.TestCase):
    def test_open_field_and_closed_house_spawn_outdoors_far_away(self):
        for shelter in ('field', 'ordinary_house'):
            with self.subTest(shelter=shelter):
                g = NightGraph(); g.hunt()
                self.assertEqual(len(g.requests), 3)
                for request in g.requests:
                    self.assertTrue(request['outdoor_only'])
                    self.assertEqual((request['min_radius'], request['max_radius']), (20, 30))
                    self.assertEqual(request['real_count'], 1)
                    self.assertNotIn('summoner_is_alpha', request)
                self.assertEqual(g.avatar.values['berserk_brand_night_spawned'], 3)

    def test_protected_sign_flora_daylight_and_underground_have_distinct_reasons(self):
        for mode, reason in [('ward','shelter_ward'), ('flora','flora_ward'),
                             ('day','daylight'), ('underground','underground')]:
            g = NightGraph()
            if mode == 'underground': g.avatar.pos = (0,0,-1)
            else: setattr(g, mode, True)
            g.hunt(); self.assertFalse(g.requests)
            self.assertEqual(g.avatar.values['berserk_brand_night_status'], reason)
            self.assertFalse(g.messages)

    def test_far_edge_sources_share_budget_and_only_remaining_slot_is_requested(self):
        g = NightGraph()
        for i in range(7):
            mon = Actor((30, i, 0)); mon.mtype = 'mon_berserk_eclipse_wretch'
            if i < 3: mon.values['berserk_spawn_source'] = 'brand'
            elif i < 5: mon.mtype = 'mon_beast_of_darkness_1'  # old untagged armor
            g.monsters.append(mon)
        g.hunt()
        self.assertEqual(len(g.requests), 1)
        self.assertEqual(g.world['berserk_era_nearby_count'], 8)
        self.assertEqual(g.world['berserk_spawn_brand_nearby'], 4)
        self.assertEqual(g.world['berserk_spawn_armor_nearby'], 2)
        self.assertEqual(g.world['berserk_spawn_world_or_site_nearby'], 2)
        g.now += 3600; g.hunt(); self.assertEqual(len(g.requests), 1)
        self.assertEqual(g.avatar.values['berserk_brand_night_status'], 'active_budget')

    def test_partial_success_does_not_lie_about_count_or_retry_every_second(self):
        g = NightGraph(); g.outcomes = [False, True, False]; g.hunt()
        self.assertEqual(g.avatar.values['berserk_brand_night_spawned'], 1)
        self.assertEqual(g.avatar.values['berserk_brand_night_no_cell_total'], 2)
        # Serialize saved character/world variables, then try again in the same hour.
        g.avatar.values = json.loads(json.dumps(g.avatar.values))
        g.world = json.loads(json.dumps(g.world)); g.now += 30; g.hunt()
        self.assertEqual(len(g.requests), 3)
        self.assertEqual(g.avatar.values['berserk_brand_night_status'], 'hour_cooldown')
        g.now = 3700; g.outcomes = [False, False, False]; g.hunt()
        self.assertEqual(len(g.requests), 6)
        self.assertEqual(g.avatar.values['berserk_brand_night_status'], 'no_outdoor_cell')

    def test_closed_breach_suppression_does_not_erase_existing_monsters(self):
        g = NightGraph(); g.quiet = True
        mon = Actor((2,0,0)); mon.mtype = 'mon_berserk_eclipse_wretch'; g.monsters.append(mon)
        g.hunt(); self.assertEqual(g.monsters, [mon]); self.assertFalse(g.requests)
        self.assertEqual(g.avatar.values['berserk_brand_night_status'], 'local_breach_quiet')

    def test_diagonal_spawn_square_is_counted_in_both_distance_modes(self):
        for circular in (False, True):
            g=NightGraph(); g.circular=circular
            for i in range(8):
                mon=Actor((30,30-i,0));mon.mtype='mon_berserk_brand_wretch';g.monsters.append(mon)
            # A dead creature and a different floor do not add to the count.
            dead=Actor((1,0,0),hp=0);dead.mtype='mon_berserk_eclipse_hunter';g.monsters.append(dead)
            above=Actor((0,0,1));above.mtype='mon_berserk_eclipse_hunter';g.monsters.append(above)
            g.hunt();self.assertFalse(g.requests)
            self.assertEqual(g.world['berserk_era_nearby_count'],8)
            self.assertEqual(g.world['berserk_spawn_brand_nearby'],8)

    def test_night_roles_keep_combat_factions_sprites_and_relic_bonus(self):
        roles=load('monsters/brand_night_demons.json')
        regular={o['id']:o for o in load('monsters/eclipse_demons.json')}
        scan=NightGraph().eocs['EOC_BERSERK_ECLIPSE_ERA_COUNT_NEARBY']['effect'][-1]
        relic=json.dumps(load('effects/apostle_relic_eocs.json'))
        for role in roles:
            self.assertIn(role['copy-from'],regular)
            self.assertEqual(role['looks_like'],role['copy-from'])
            self.assertEqual(role['vision_night'],35)
            self.assertFalse(set(role)&{'hp','speed','armor','melee_damage','special_attacks','flags','default_faction'})
            self.assertIn(role['id'],scan['mtype_ids']);self.assertIn(role['id'],relic)


if __name__ == '__main__':
    unittest.main()
