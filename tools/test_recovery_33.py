"""Focused 3.3 recovery tests. Data interpreter, not a CDDA runtime test."""
import json
import re
import unittest
from collections import Counter
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'


def load(name):
    return json.loads((MOD / name).read_text())


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values(): yield from walk(child)
    elif isinstance(value, list):
        for child in value: yield from walk(child)


class StateGraph:
    """Executes actual data; only explicitly set environmental conditions mocked."""
    def __init__(self):
        self.eocs = {o['id']: o for p in (MOD / 'effects').glob('*.json')
                     for o in (lambda x: x if isinstance(x, list) else [x])(json.loads(p.read_text()))}
        self.values = {}; self.traits = set(); self.inventory = Counter()
        self.bionics=set();self.effects=set();self.messages=[]
        self.overrides = {'EOC_BERSERK_FORGE_GUTS': False,
                          'EOC_BERSERK_GODO_AT_SMITH': True,
                          'EOC_BERSERK_GODO_KNOWN': False}
        self.now = 100; self.avatar = True

    def evaluate(self, expr):
        expr = re.sub(r'has_var\((\w+)\)', lambda m: str(int(m[1] in self.values)), expr)
        expr = re.sub(r'\b(?:u_)?berserk_\w+\b', lambda m: str(self.values.get(m[0], 0)), expr)
        return eval(expr, {'__builtins__': {}}, {'time': lambda x: self.now if x == 'now' else 0,
                                               'min': min, 'max': max})

    def condition(self, value):
        if value == 'u_is_avatar': return self.avatar
        if value in ('has_alpha', 'has_beta', 'npc_is_monster'): return True
        if not isinstance(value, dict): raise AssertionError(value)
        if 'and' in value: return all(self.condition(x) for x in value['and'])
        if 'or' in value: return any(self.condition(x) for x in value['or'])
        if 'not' in value: return not self.condition(value['not'])
        if 'test_eoc' in value:
            name = value['test_eoc']
            return self.overrides[name] if name in self.overrides else self.condition(self.eocs[name]['condition'])
        if 'math' in value: return bool(self.evaluate(value['math'][0]))
        if 'u_has_trait' in value: return value['u_has_trait'] in self.traits
        if 'u_has_bionics' in value:return value['u_has_bionics'] in self.bionics
        if 'u_profession' in value: return False
        if 'u_has_flag' in value: return False
        if 'u_has_items' in value:
            item = value['u_has_items']; return self.inventory[item['item']] >= item.get('count', 1)
        if 'u_has_item' in value: return self.inventory[value['u_has_item']] > 0
        if 'u_has_mission' in value: return False
        raise AssertionError(value)

    def run(self, name):
        obj = self.eocs[name]
        if 'condition' not in obj or self.condition(obj['condition']): self.effect(obj['effect'])

    def effect(self, value):
        if isinstance(value, list):
            for child in value: self.effect(child)
        elif 'if' in value:
            branch = 'then' if self.condition(value['if']) else 'else'
            if branch in value: self.effect(value[branch])
        elif 'math' in value:
            name, op, expr = re.fullmatch(r'(\w+) (=|\+=) (.+)', value['math'][0]).groups()
            self.values[name] = self.evaluate(expr) + (self.values.get(name, 0) if op == '+=' else 0)
        elif 'u_add_trait' in value: self.traits.add(value['u_add_trait'])
        elif 'u_lose_trait' in value: self.traits.discard(value['u_lose_trait'])
        elif 'u_lose_bionic' in value:self.bionics.discard(value['u_lose_bionic'])
        elif 'u_lose_effect' in value:self.effects.discard(value['u_lose_effect'])
        elif 'run_eocs' in value: self.run(value['run_eocs'])
        elif 'u_spawn_item' in value:
            count = value.get('count', 1)
            if isinstance(count, dict): count = self.values.get('u_' + count['u_val'], 0)
            self.inventory[value['u_spawn_item']] += count
        elif 'u_message' in value:self.messages.append(value['u_message'])
        else: raise AssertionError(value)


class RecoveryGameplay(unittest.TestCase):
    def pawn(self, line, number):
        g = StateGraph(); g.values.update(u_berserk_apostol_schema=1,
            u_berserk_apostol_path=3, u_berserk_apostol_lineage=number,
            u_berserk_apostol_stage=1)
        return g, 'EOC_BERSERK_APOSTOL_' + line + '_PAWN_'

    def test_all_four_pawns_finish_immediately_and_remain_finished_after_reload(self):
        for number, line in enumerate(('COUNT','WYALD','ROSINE','GRUNBELD'), 10):
            with self.subTest(line=line):
                g, prefix = self.pawn(line, number); g.run(prefix + 'BEGIN')
                self.assertTrue(g.condition({'test_eoc': 'EOC_BERSERK_APOSTOL_PAWN_COMPLETE'}))
                before = set(g.traits); started = g.values['u_berserk_apostol_started_at']
                g.values = json.loads(json.dumps(g.values)); g.now += 99999
                g.run(prefix + 'BEGIN'); g.run(prefix + 'GROW')
                self.assertEqual(g.traits, before)
                self.assertEqual(g.values['u_berserk_apostol_started_at'], started)
                self.assertEqual(g.values['u_berserk_apostol_growth_running'], 0)

    def test_old_partial_pawns_finish_without_recreating_broken_loyalty(self):
        for number, line in enumerate(('COUNT','WYALD','ROSINE','GRUNBELD'), 10):
            g, prefix = self.pawn(line, number)
            g.values.update(u_berserk_apostol_stage=2, u_berserk_apostol_pawn_oath_broken=1,
                            u_berserk_apostol_started_at=12, u_berserk_apostol_growth_running=1)
            g.run(prefix + 'GROW')
            self.assertNotIn('BERSERK_' + line + '_PAWN_LOYALTY', g.traits)
            self.assertEqual(g.values['u_berserk_apostol_started_at'], 12)
            self.assertEqual(g.values['u_berserk_apostol_stage'], 3)

    def test_conrad_damages_monsters_and_npcs_without_old_living_only_eoc(self):
        spells = {o['id']: o for o in load('spells/apostol_gifts.json')}
        touch = spells['berserk_apostol_conrad_strike']; cloud = spells['berserk_apostol_conrad_cloud']
        for spell in (touch, cloud):
            self.assertEqual(spell['effect'], 'attack')
            self.assertGreater(spell['min_damage'], 0)
            self.assertNotIn('effect_str', spell)
            self.assertIn('hostile', spell['valid_targets'])
        self.assertEqual(cloud['field_id'], 'fd_toxic_gas')
        self.assertIn('ally', cloud['valid_targets'])

    def test_femto_damage_precedes_push_so_victim_is_not_missed(self):
        spells = {o['id']: o for o in load('spells/apostol_gifts.json')}
        spell = spells['berserk_apostol_femto_pulse']
        self.assertEqual(spell['effect'], 'attack')
        child = spells[spell['extra_effects'][0]['id']]
        self.assertEqual(child['effect'], 'directed_push')
        self.assertEqual(child['min_damage'], 5)

    def test_no_body_mutation_becomes_reversible_or_purifiable(self):
        for p in (MOD / 'mutations').glob('apostol_*.json'):
            data = json.loads(p.read_text())
            if not isinstance(data, list): continue
            for obj in data:
                if obj.get('type') != 'mutation': continue
                self.assertFalse(obj.get('purifiable', True), obj['id'])
                if obj['id'].endswith('_FORM'):
                    self.assertFalse(obj.get('active', False), obj['id'])

    def test_early_sword_uses_the_restored_vanilla_sprite(self):
        self.assertEqual(load('items/true_guts_early_sword.json')[0]['looks_like'], 'mc_zweihander')

    def test_no_new_literary_dialogue_topics_in_gameplay_recovery(self):
        # Scenario texts from October are a later task, not auto-generated content.
        self.assertFalse((MOD / 'dialogue/flora_rewrite.json').exists())


class HumanEquipment(unittest.TestCase):
    allowed = 'EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED'

    def test_acceptance_at_the_first_stage_blocks_all_three_actual_paths(self):
        for path, line in [(1,1), (2,6), (3,10)]:
            g = StateGraph(); g.values.update(u_berserk_apostol_path=path,
                u_berserk_apostol_lineage=line, u_berserk_apostol_stage=1)
            self.assertFalse(g.condition({'test_eoc': self.allowed}))

    def test_behelit_ownership_and_refusal_scars_do_not_block_human_rewards(self):
        g = StateGraph(); g.inventory.update(berserk_behelit=1, berserk_behelit_distorted=1)
        g.traits.update(['DEAF', 'INSOMNIA'])
        g.values['u_berserk_apostol_refusal_done'] = 1
        self.assertTrue(g.condition({'test_eoc': self.allowed}))

    def test_legacy_traits_latch_the_block_even_if_old_numeric_fields_are_missing(self):
        for trait in ['BERSERK_SLAN_SEED', 'BERSERK_CONRAD_APOSTLE',
                      'BERSERK_COUNT_FLESH_FORM', 'BERSERK_ROSINE_PAWN_PAWN']:
            g = StateGraph(); g.traits.add(trait)
            self.assertFalse(g.condition({'test_eoc': self.allowed}))
            g.run('EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_LATCH')
            g.traits.clear()
            self.assertFalse(g.condition({'test_eoc': self.allowed}))

    def test_existing_equipment_is_never_removed(self):
        g = StateGraph(); g.values['u_berserk_apostol_path'] = 1
        g.inventory.update(true_guts_sword=1, true_guts_early_sword=1, berserk_armor_bundle=1)
        before = g.inventory.copy(); g.run('EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_LATCH')
        self.assertEqual(before, g.inventory)

    def test_early_paid_order_refunds_once_without_awarding_a_sword(self):
        g = StateGraph(); g.values.update(u_berserk_apostol_path=3, u_berserk_godo_early_state=2)
        g.run('EOC_BERSERK_GODO_EARLY_CLAIM')
        self.assertFalse(g.inventory)
        g.run('EOC_BERSERK_GODO_EARLY_REFUND'); before = g.inventory.copy()
        g.run('EOC_BERSERK_GODO_EARLY_REFUND')
        self.assertEqual(g.inventory, before)
        self.assertEqual(g.inventory['steel_lump'], 4)
        self.assertEqual(g.inventory['charcoal'], 200)
        self.assertEqual(g.inventory['true_guts_early_sword'], 0)

    def test_dragonslayer_refunds_actual_partial_and_full_payments_once(self):
        for state, paid in [(1,8), (2,32), (3,32)]:
            g = StateGraph(); g.values.update(u_berserk_apostol_path=2,
                u_berserk_godo_sword_state=state, u_berserk_godo_sword_iron_given=paid)
            g.run('EOC_BERSERK_GODO_SWORD_CLAIM'); self.assertFalse(g.inventory)
            g.run('EOC_BERSERK_GODO_SWORD_REFUND'); before = g.inventory.copy()
            g.run('EOC_BERSERK_GODO_SWORD_REFUND')
            self.assertEqual(g.inventory, before)
            self.assertEqual(g.inventory['steel_lump'], paid)
            self.assertEqual(g.inventory['hc_steel_lump'], 8 if state == 3 else 0)
            self.assertEqual(g.inventory['true_guts_sword'], 0)

    def test_new_weapon_delivery_and_armor_conditions_use_shared_gate(self):
        g = StateGraph()
        for suffix in ['START_SWORD','SWORD_IRON','SWORD_TEMPER','SWORD_CLAIM',
                       'START_EARLY_SWORD','EARLY_MATERIALS','EARLY_CLAIM']:
            condition = g.eocs['EOC_BERSERK_GODO_' + suffix]['condition']
            self.assertIn({'test_eoc': self.allowed}, list(walk(condition)))
        self.assertIn({'test_eoc': self.allowed}, list(walk(g.eocs['EOC_BERSERK_FLORA_CAN_RECEIVE']['condition'])))
        ready = g.eocs['EOC_BERSERK_FLORA_CAN_PREPARE_SIEGE']['condition']
        self.assertIn({'not': {'test_eoc': self.allowed}}, list(walk(ready)))
        self.assertFalse((MOD / 'item_groups.json').exists())

    def test_rickert_services_are_not_gated_by_accepted_path(self):
        g = StateGraph()
        for name, obj in g.eocs.items():
            if name in ['EOC_BERSERK_GODO_START_ARM', 'EOC_BERSERK_GODO_ARM_CLAIM',
                        'EOC_BERSERK_RICKERT_ORDER_BOLTS']:
                self.assertNotIn({'test_eoc': self.allowed}, list(walk(obj)))


if __name__ == '__main__': unittest.main()
