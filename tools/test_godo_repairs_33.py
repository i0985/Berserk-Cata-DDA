"""Exercise actual repair JSON with item-talker/map semantics; not native CDDA.

Moves copy the complete item then invalidate its old location, as 0.I does.
Includes the surprising false_eocs callback after moving a manual selection.
"""
import collections
import copy
import json
import re
import unittest
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'
P = 'EOC_BERSERK_GODO_REPAIR_'


class Repair:
    def __init__(self):
        self.eocs = {}
        for name in ['godo_eocs', 'godo_repair_eocs']:
            self.eocs.update({x['id']: x for x in json.loads((MOD / f'effects/{name}.json').read_text())})
        self.vars = collections.defaultdict(int)
        self.items = collections.Counter(steel_lump=3, charcoal=150)
        self.carried = []
        self.floor = []
        self.now = 1000
        self.actor = 'godo'
        self.at_smith = True
        self.pos = [13, 16, 0]
        self.smith_pos = [15, 16, 0]
        self.selection = None
        self.consent = True
        self.messages = []
        self.current = None

    def blade(self, hp=1000, id='true_guts_early_sword', degradation=0):
        item = {'id': id, 'hp': hp, 'max': 4000, 'degradation': degradation,
                'vars': {}, 'name': 'My named sword', 'contents': ['custom fitting'],
                'flags': ['DURABLE_MELEE'], 'owner': 'avatar', 'pos': None}
        self.carried.append(item)
        self.selection = item
        return item

    def value(self, expr):
        expr = expr.replace("time('now')", str(self.now))
        for name, field in [("n_hp('ALL')", 'hp'), ("n_hp_max('torso')", 'max'),
                            ('n_degradation()', 'degradation')]:
            if name in expr:
                assert self.current is not None
                expr = expr.replace(name, str(self.current[field]))
        def var(m):
            key = m[0]
            if key.startswith('n_'):
                assert self.current is not None
                return str(self.current['vars'].get(key[2:], 0))
            return str(self.vars[key])
        expr = re.sub(r'\b(?:[un]_)?berserk_\w+\b', var, expr)
        return eval(expr, {'__builtins__': {}}, {})

    def condition(self, obj):
        if 'and' in obj: return all(self.condition(x) for x in obj['and'])
        if 'not' in obj: return not self.condition(obj['not'])
        if 'math' in obj: return bool(self.value(obj['math'][0]))
        if 'u_query' in obj: return self.consent
        if 'u_has_items' in obj:
            x = obj['u_has_items']; return self.items[x['item']] >= x['count']
        if 'test_eoc' in obj:
            if obj['test_eoc'] == 'EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED':
                return not (self.vars['u_berserk_apostol_path'] or self.vars['u_berserk_apostol_human_equipment_locked'])
            assert obj['test_eoc'] == 'EOC_BERSERK_GODO_AT_SMITH'
            return self.actor == 'godo' and self.at_smith and self.current is None
        raise AssertionError(obj)

    def run(self, id):
        e = self.eocs[id if id.startswith('EOC_') else P + id]
        if 'condition' not in e or self.condition(e['condition']): self.effect(e['effect'])

    def effect(self, obj):
        if isinstance(obj, list):
            for x in obj: self.effect(x)
        elif 'if' in obj:
            branch = 'then' if self.condition(obj['if']) else 'else'
            if branch in obj: self.effect(obj[branch])
        elif 'run_eocs' in obj: self.run(obj['run_eocs'])
        elif 'math' in obj:
            left, right = obj['math'][0].split(' = '); value = self.value(right)
            if left == 'n_degradation()': self.current['degradation'] = value
            elif left == "n_hp('ALL')":
                self.current['hp'] = min(value, self.current['max'] - self.current['degradation'])
            elif left.startswith('n_'): self.current['vars'][left[2:]] = value
            else: self.vars[left] = value
        elif 'u_consume_item' in obj:
            id = obj['u_consume_item']; n = obj['charges']
            assert self.items[id] >= n
            self.items[id] -= n
        elif 'u_message' in obj: self.messages.append(obj['u_message'])
        elif 'npc_location_variable' in obj:
            self.vars['u_' + obj['npc_location_variable']['u_val']] = self.smith_pos[:]
        elif 'u_location_variable' in obj:
            self.vars['u_' + obj['u_location_variable']['u_val']] = self.pos[:]
        elif 'npc_teleport' in obj:
            assert self.current is not None
            old = self.current
            new = copy.deepcopy(old)
            new['pos'] = self.vars['u_' + obj['npc_teleport']['u_val']][:]
            for group in [self.carried, self.floor]:
                for i, x in enumerate(group):
                    if x is old: group.pop(i); break
            old['_invalid'] = True
            self.floor.append(new)
        elif 'u_run_inv_eocs' in obj or 'u_map_run_item_eocs' in obj:
            manual = 'u_run_inv_eocs' in obj
            candidates = list(self.carried if manual else self.floor)
            parent = self.current
            matches = []
            for item in candidates:
                if not manual:
                    center = self.vars['u_' + obj['loc']['u_val']]
                    if item['pos'][2] != center[2] or max(abs(item['pos'][j]-center[j]) for j in [0,1]) > obj['max_radius']:
                        continue
                self.current = item
                if any(item['id'] in s['id'] and ('condition' not in s or self.condition(s['condition']))
                       for s in obj['search_data']): matches.append(item)
            self.current = parent
            selected = next((x for x in matches if x is self.selection), None) if manual else None
            targets = [selected] if selected is not None else [] if manual else matches
            for item in targets:
                self.current = item
                for id in obj.get('true_eocs', []):
                    if not item.get('_invalid'): self.run(id)
            self.current = parent
            if (manual and (selected is None or selected.get('_invalid'))) or (not manual and not matches):
                for id in obj.get('false_eocs', []): self.run(id)
        else: raise AssertionError(obj)

    def collect_floor_blade(self):
        blade = self.floor.pop(0); blade['pos'] = None
        self.carried.append(blade); self.selection = blade
        return blade


class Repairs(unittest.TestCase):
    def test_seventy_and_above_need_no_materials(self):
        for hp in [2800, 2801, 4000]:
            f = Repair(); blade = f.blade(hp); f.items.clear(); f.run('PICK')
            self.assertIs(f.carried[0], blade); self.assertFalse(f.floor)
            self.assertNotEqual(f.vars['u_berserk_godo_repair_state'], 1)
            self.assertIn('Still in good condition', f.messages[-1])

    def test_just_below_seventy_is_taken_not_instantly_healed(self):
        f = Repair(); f.blade(2799); f.run('PICK')
        self.assertFalse(f.carried); self.assertEqual(f.floor[0]['hp'], 2799)
        self.assertEqual(f.vars['u_berserk_godo_repair_ready_at'], 8200)
        self.assertEqual(f.items['steel_lump'], 2); self.assertEqual(f.items['charcoal'], 100)

    def test_both_missing_supplies_and_cancellation_leave_blade(self):
        for supply in ['steel_lump', 'charcoal', None]:
            f = Repair(); b = f.blade(); before = copy.deepcopy(f.items)
            if supply: f.items[supply] = 0; before = f.items.copy()
            else: f.consent = False
            f.run('PICK'); self.assertIs(f.carried[0], b)
            self.assertEqual(f.items, before); self.assertFalse(f.floor)

    def test_inventory_selection_cancel_is_free(self):
        f = Repair(); f.blade(); f.selection = None; f.run('PICK')
        self.assertEqual(f.items['steel_lump'], 3); self.assertEqual(len(f.carried), 1)

    def test_two_hour_boundary_and_repeat_claim(self):
        f = Repair(); f.blade(); f.run('PICK'); f.now = 8199; f.run('CLAIM')
        self.assertEqual(f.floor[0]['hp'], 1000)
        self.assertEqual(f.vars['u_berserk_godo_repair_state'], 1)
        f.now = 8200
        for _ in range(3): f.run('CLAIM')
        self.assertEqual(len(f.floor), 1); self.assertEqual(f.floor[0]['hp'], 4000)
        self.assertEqual(f.floor[0]['pos'], f.pos)
        self.assertEqual(f.vars['u_berserk_godo_repair_state'], 2)

    def test_specific_blade_metadata_and_degradation_preserved_or_repaired(self):
        f = Repair(); original = copy.deepcopy(f.blade(degradation=1300)); other = f.blade(600)
        f.selection = f.carried[0]; f.run('PICK'); f.now += 7200; f.run('CLAIM')
        result = f.floor[0]
        for key in ['name', 'contents', 'flags', 'owner', 'id']: self.assertEqual(result[key], original[key])
        self.assertEqual(result['hp'], 4000); self.assertEqual(result['degradation'], 0)
        self.assertIs(f.carried[0], other); self.assertEqual(other['hp'], 600)

    def test_all_supported_blades(self):
        for id in ['true_guts_early_sword', 'true_guts_sword', 'forged_guts_sword',
                   'forged_guts_early_sword']:
            f = Repair(); f.blade(id=id); f.run('PICK'); f.now += 7200; f.run('CLAIM')
            self.assertEqual(f.floor[0]['id'], id); self.assertEqual(f.floor[0]['hp'], 4000)

    def test_save_reload_and_long_trip(self):
        f = Repair(); f.blade(); f.run('PICK')
        saved = json.loads(json.dumps({'vars': f.vars, 'floor': f.floor, 'items': f.items}))
        loaded = Repair(); loaded.vars.update(saved['vars']); loaded.floor = saved['floor']
        loaded.items = collections.Counter(saved['items']); loaded.now += 86400
        loaded.at_smith = False; loaded.run('CLAIM')
        self.assertEqual(loaded.floor[0]['hp'], 1000)
        loaded.at_smith = True; loaded.run('CLAIM')
        self.assertEqual(loaded.floor[0]['hp'], 4000)

    def test_second_order_cannot_start_while_one_is_active(self):
        f = Repair(); f.blade(); f.run('PICK'); f.blade(); f.run('PICK')
        self.assertEqual(len(f.floor), 1); self.assertEqual(len(f.carried), 1)
        self.assertEqual(f.items['steel_lump'], 2)

    def test_missing_or_replaced_blade_does_not_spawn_reward(self):
        f = Repair(); f.blade(); f.run('PICK'); f.floor.clear()
        other = f.blade(); other['pos'] = f.smith_pos; f.carried.remove(other); f.floor.append(other)
        f.now += 7200; f.run('CLAIM')
        self.assertEqual(other['hp'], 1000); self.assertEqual(len(f.floor), 1)
        self.assertEqual(f.vars['u_berserk_godo_repair_state'], 1)
        self.assertIn('not beside my tools', f.messages[-1])

    def test_taking_blade_early_requires_return_and_wait_without_second_payment(self):
        f = Repair(); f.blade(); f.run('PICK'); f.now += 7200
        taken = f.collect_floor_blade(); f.run('CLAIM')
        self.assertEqual(taken['hp'], 1000)
        f.run('REDEPOSIT'); self.assertFalse(f.carried)
        self.assertEqual(f.vars['u_berserk_godo_repair_ready_at'], f.now + 7200)
        self.assertEqual(f.items['steel_lump'], 2)
        f.run('CLAIM'); self.assertEqual(f.floor[0]['hp'], 1000)
        f.now += 7200; f.run('CLAIM'); self.assertEqual(f.floor[0]['hp'], 4000)

    def test_another_characters_order_does_not_match(self):
        f = Repair(); f.blade(); f.run('PICK')
        other = copy.deepcopy(f.floor[0]); other['vars']['berserk_godo_repair_job'] += 1
        f.floor.insert(0, other); f.now += 7200; f.run('CLAIM')
        self.assertEqual(other['hp'], 1000); self.assertEqual(f.floor[1]['hp'], 4000)

    def test_abandoned_order_can_never_be_claimed(self):
        f = Repair(); f.blade(); f.run('PICK'); f.run('ABANDON'); f.now += 7200; f.run('CLAIM')
        self.assertEqual(f.floor[0]['hp'], 1000); self.assertEqual(f.items['steel_lump'], 2)
        f.blade(); f.run('PICK'); self.assertEqual(f.vars['u_berserk_godo_repair_job'], 2)

    def test_journal_and_wrong_speaker_cannot_hand_in_or_claim(self):
        for actor in ['book', 'rickert']:
            f = Repair(); f.blade(); f.actor = actor; f.run('PICK')
            self.assertFalse(f.floor); self.assertEqual(f.items['steel_lump'], 3)

    def test_demonic_path_keeps_repair_of_owned_blade_available(self):
        f = Repair(); f.vars['u_berserk_apostol_path'] = 1
        f.blade(); f.run('PICK'); f.now += 7200; f.run('CLAIM')
        self.assertEqual(f.floor[0]['hp'], 4000)

    def test_demonic_path_refuses_new_dragonslayer_work_but_honors_existing_order(self):
        f = Repair(); f.vars['u_berserk_apostol_path'] = 1; f.blade(id='true_guts_sword')
        f.run('PICK'); self.assertEqual(len(f.carried),1); self.assertFalse(f.floor)
        self.assertEqual(f.items['steel_lump'],3)
        f.vars['u_berserk_apostol_path']=0; f.run('PICK')
        f.vars['u_berserk_apostol_path']=1; f.now+=7200; f.run('CLAIM')
        self.assertEqual(f.floor[0]['hp'],4000)

    def test_no_replacement_spawn_and_teleport_is_last(self):
        for id, e in Repair().eocs.items():
            if not id.startswith(P): continue
            self.assertNotIn('u_spawn_item', json.dumps(e))
            if isinstance(e['effect'], list):
                teleports = [i for i, part in enumerate(e['effect']) if 'npc_teleport' in part]
                if teleports: self.assertEqual(teleports, [len(e['effect']) - 1])


if __name__ == '__main__': unittest.main()
