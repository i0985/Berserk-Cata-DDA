"""Exercise relic EOC definitions without launching CDDA.

The harness models the documented event talkers and math operations. It cannot
validate the native loader, combat attribution, enchantment cache or save files.
"""

import copy
import gettext
import json
import math
import re
import unittest

from test_behelit_rewards import MOD, objects


class RelicGraph:
    def __init__(self):
        self.eocs = {e['id']: e for p in (MOD/'effects').glob('*.json')
                     for e in objects(p) if e['type'] == 'effect_on_condition'}
        self.vars = {}
        self.effects = {}
        self.worn = set()
        self.attacker_worn = set()
        self.alpha = 'avatar'
        self.beta = None
        self.target_id = 'mon_berserk_apostle_count'
        self.target_hp = 100
        self.friendly = False
        self.neighbors = []
        self.damage = 0
        self.stamina = 2000
        self.blood = 0
        self.messages = []

    def nearby(self, *ids, radius):
        # The query's center is alpha, not the attacking avatar. A neighboring
        # demon must never qualify an ordinary zombie under attack.
        return sum(id in ids and distance <= radius and not friendly
                   for id, distance, friendly in
                   [(self.target_id, 0, self.friendly), *self.neighbors])

    def evaluate(self, expr):
        expr = re.sub(r"'radius':\s*(\d+)", r'radius=\1', expr)
        env = dict(self.vars, _damage=self.damage, floor=math.floor,
                   min=min, max=max, u_monsters_nearby=self.nearby,
                   u_hp=lambda part: self.target_hp,
                   u_effect_duration=lambda id: self.effects.get(id, 0),
                   u_val=lambda axis: self.stamina,
                   u_vitamin=lambda id: self.blood)
        return eval(expr, {'__builtins__': {}}, env)

    def condition(self, value):
        if isinstance(value, str):
            if value == 'has_beta':
                return self.beta is not None
            if value == 'u_is_monster':
                return self.alpha == 'monster'
            if value == 'npc_is_avatar':
                if self.beta is None:
                    raise AssertionError('beta read before has_beta')
                return self.beta == 'avatar'
            raise AssertionError(value)
        if 'and' in value:
            return all(self.condition(v) for v in value['and'])
        if 'math' in value:
            return bool(self.evaluate(value['math'][0]))
        if 'u_is_wearing' in value:
            return value['u_is_wearing'] in self.worn
        if 'npc_is_wearing' in value:
            return value['npc_is_wearing'] in self.attacker_worn
        raise AssertionError(value)

    def effect(self, value):
        if isinstance(value, list):
            for child in value:
                self.effect(child)
        elif 'if' in value:
            branch = 'then' if self.condition(value['if']) else 'else'
            if branch in value:
                self.effect(value[branch])
        elif 'math' in value:
            name, rhs = value['math'][0].split(' = ')
            result = self.evaluate(rhs)
            if name == "u_hp('ALL')":
                self.target_hp = result
            elif name == "u_val('stamina')":
                self.stamina = result
            elif name == "u_vitamin('blood')":
                self.blood = result
            else:
                self.vars[name] = result
        elif 'u_add_effect' in value:
            duration = value['duration']
            if isinstance(duration, dict):
                duration = self.evaluate(duration['math'][0])
            self.effects[value['u_add_effect']] = duration
        elif 'u_lose_effect' in value:
            self.effects.pop(value['u_lose_effect'], None)
        elif 'u_message' in value:
            self.messages.append(value['u_message'])
        else:
            raise AssertionError(value)

    def run(self, id):
        eoc = self.eocs[id]
        if 'condition' not in eoc or self.condition(eoc['condition']):
            self.effect(eoc['effect'])

    def hit(self, damage, hp=100, target='mon_berserk_apostle_count', killer='avatar', worn=True):
        self.alpha = 'monster'
        self.beta = killer
        self.target_id = target
        self.damage = damage
        # Native apply_damage subtracts the mitigated hit before this event.
        self.target_hp = hp-damage
        self.attacker_worn = {'berserk_count_iron_seal'} if worn else set()
        self.run('EOC_BERSERK_COUNT_RELIC_DAMAGE')
        return self.target_hp


class ApostleRelics(unittest.TestCase):
    def test_seal_bonus_is_post_defense_rounded_and_non_recursive(self):
        g = RelicGraph()
        for hit, expected in ((0, 100), (4, 96), (5, 94), (17, 80), (50, 40)):
            self.assertEqual(g.hit(hit), expected)
        # A bonus-only kill clamps at zero; an already lethal hit is untouched.
        self.assertEqual(g.hit(50, hp=55), 0)
        self.assertEqual(g.hit(100, hp=55), -45)
        eoc = g.eocs['EOC_BERSERK_COUNT_RELIC_DAMAGE']
        self.assertEqual(eoc['required_event'], 'monster_takes_damage')
        self.assertNotIn('u_deal_damage', json.dumps(eoc))
        self.assertNotIn('run_eocs', json.dumps(eoc['effect']))

    def test_seal_rejects_backpack_npc_source_missing_source_and_other_targets(self):
        g = RelicGraph()
        for killer in (None, 'npc', 'monster'):
            self.assertEqual(g.hit(50, killer=killer), 50)
        self.assertEqual(g.hit(50, worn=False), 50)
        g.neighbors = [('mon_berserk_apostle_count', 1, False)]
        for target in ('mon_zombie', 'mon_skull_knight', 'mon_skull_knight_rescuer',
                       'mon_berserk_count_witness'):
            self.assertEqual(g.hit(50, target=target), 50)
        g.friendly = True
        self.assertEqual(g.hit(50), 50)

    def test_whitelist_uses_existing_ids_and_covers_projections(self):
        g = RelicGraph()
        text = json.dumps(g.eocs['EOC_BERSERK_COUNT_RELIC_DAMAGE']['condition'])
        whitelist = set(re.findall(r"'(mon_[^']+)'", text))
        known = {e['id'] for p in (MOD/'monsters').glob('*.json') for e in objects(p)}
        self.assertTrue(whitelist)
        self.assertLessEqual(whitelist, known)
        for target in whitelist:
            self.assertEqual(g.hit(50, target=target), 40)
        self.assertIn('mon_berserk_projection_griffith', whitelist)
        self.assertNotIn('GROUP_NETHER', text)

    def test_knot_snapshots_duration_and_does_not_reset_an_existing_rage(self):
        for knot, expected in ((False, 150), (True, 210)):
            g = RelicGraph()
            if knot:
                g.worn.add('berserk_wyald_beast_knot')
            g.run('EOC_BERSERK_MODE_START')
            self.assertEqual(g.effects['berserk_mode_rush'], expected)
            self.assertEqual(g.vars['u_berserk_mode_countdown'], expected+1)
            g.worn.symmetric_difference_update({'berserk_wyald_beast_knot'})
            g.effects['berserk_mode_rush'] -= 1
            g.run('EOC_BERSERK_MODE_COUNTDOWN')
            self.assertEqual(g.effects['berserk_mode_rush'], expected-1)
            saved = copy.deepcopy(g)
            self.assertEqual(saved.vars['u_berserk_mode_duration'], expected)
            self.assertEqual(saved.effects['berserk_mode_rush'], expected-1)
            # This deepcopy is a data continuity check, not a native save test.

    def test_countdown_covers_both_lengths_and_legacy_active_state(self):
        for duration in (150, 210):
            g = RelicGraph()
            # Old active saves need no new duration variable to count down.
            g.vars['u_berserk_mode_countdown'] = duration+1
            expected = [s for s in (180,150,120,90,60,30,*range(10,0,-1)) if s < duration]
            for remaining in range(duration-1, 0, -1):
                g.effects['berserk_mode_rush'] = remaining
                g.run('EOC_BERSERK_MODE_COUNTDOWN')
                g.run('EOC_BERSERK_MODE_COUNTDOWN')  # duplicate callback
            self.assertEqual(len(g.messages), len(expected))
            self.assertEqual([int(re.search(r'(\d+)', s)[0]) for s in g.messages], expected)
        g = RelicGraph()
        g.vars['u_berserk_mode_countdown'] = 211
        g.effects['berserk_mode_rush'] = 7
        g.run('EOC_BERSERK_MODE_COUNTDOWN')
        self.assertEqual(g.messages, ['Berserk mode: 7 seconds remaining.'])

    def test_finish_keeps_exhaustion_blood_loss_and_three_day_lockout(self):
        for blood, expected in ((0,-15000), (-10000,-17500), (-20000,-20000)):
            g = RelicGraph()
            g.blood = blood
            g.effects['berserk_mode_rush'] = 90
            g.run('EOC_BERSERK_MODE_FINISH')
            self.assertEqual(g.stamina, 0)
            self.assertEqual(g.blood, expected)
            self.assertNotIn('berserk_mode_rush', g.effects)
            self.assertEqual(g.effects['berserk_mode_recovery'], '3 days')
            self.assertEqual(g.effects['winded'], '30 minutes')

    def test_worn_only_native_enchantments_and_no_fire_immunity(self):
        items = objects(MOD/'items/apostle_relics.json')
        for item in items:
            self.assertEqual(item['max_worn'], 1)
            self.assertEqual(item['armor'][0]['coverage'], 0)
            self.assertNotIn('HEAT_IMMUNE', item['flags'])
        ench = {e['id']:e for e in objects(MOD/'enchantments/apostle_relics.json')}
        for e in ench.values():
            self.assertEqual(e['has'], 'WORN')
        veil = ench['ench_berserk_rosine_mistvale_veil']
        self.assertEqual(veil['values'], [{'value':'DODGE_CHANCE','add':1}])
        shard = ench['ench_berserk_grunbeld_carapace_shard']
        self.assertEqual(shard['values'], [{'value':'CLIMATE_CONTROL_CHILL','add':10}])
        self.assertEqual(shard['incoming_damage_mod'], [{'type':'heat','multiply':-0.2}])
        for hit in (10, 30, 100):
            self.assertGreater(hit*(1+shard['incoming_damage_mod'][0]['multiply']), 0)

    def test_count_existing_loot_and_future_unconnected_rewards(self):
        groups = {e['id']:e for p in (MOD/'monsterdrops').glob('*.json') for e in objects(p)}
        self.assertEqual(groups['berserk_count_trophy_drops']['items'],
                         [{'item':'berserk_count_iron_seal','prob':100}])
        all_monsters = json.dumps([e for p in (MOD/'monsters').glob('*.json') for e in objects(p)])
        for group in ('berserk_wyald_relic_drops','berserk_rosine_relic_drops'):
            self.assertIn(group, groups)
            self.assertNotIn(group, all_monsters)
        grunbeld = next(e for e in objects(MOD/'monsters/flora_siege.json') if e['id']=='mon_berserk_flora_grunbeld')
        self.assertEqual(grunbeld['death_drops'],'berserk_grunbeld_relic_drops')

    def test_new_player_strings_have_compiled_russian_and_chinese_translations(self):
        items = objects(MOD/'items/apostle_relics.json')
        g = RelicGraph()
        strings = [i['description'] for i in items]
        strings.append(g.eocs['EOC_BERSERK_MODE_START']['effect'][-1]['u_message'])
        strings.append(g.eocs['EOC_BERSERK_COUNT_TROPHY_READ']['effect']['u_message'])
        strings.extend(f'Berserk mode: {s} seconds remaining.' for s in (150,180))
        for locale in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo').open('rb') as f:
                catalog = gettext.GNUTranslations(f)
            for msg in strings:
                self.assertNotEqual(catalog.gettext(msg), msg)
            for item in items:
                for number in (1,2,5):
                    self.assertNotIn(catalog.ngettext(item['name']['str'], item['name']['str_pl'], number),
                                     item['name'].values())


if __name__ == '__main__':
    unittest.main()
