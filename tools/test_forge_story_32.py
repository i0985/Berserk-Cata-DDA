"""Exercise rescue fallbacks and dialogue choices; not a native CDDA playtest."""
import collections
import json
import re
import unittest
from pathlib import Path
from test_godo_32 import Forge, MOD, objects


class Scene:
    def __init__(self, known=False, find=True, teleport=True):
        self.eocs = {r['id']: r for p in (MOD / 'effects').glob('*.json')
                     for r in objects(p.relative_to(MOD)) if r.get('type') == 'effect_on_condition'}
        self.vars = collections.defaultdict(int)
        self.vars['u_berserk_eclipse_rescue_state'] = 1
        self.vars['u_berserk_eclipse_return_origin'] = [100, 100, 0]
        self.forge = [2400, 4800, 0]
        if known: self.vars['berserk_godo_location'] = self.forge.copy()
        self.pos = [100, 100, -1]
        self.find = find; self.teleport = teleport; self.searches = 0
        self.knights = []; self.queue = []; self.calls = []; self.items = collections.Counter()

    def terrain(self, point):
        if point[2] < 0: return 'berserk_eclipse_expanded_ceremony'
        if point[2] == 0 and self.forge[0] <= point[0] < self.forge[0] + 24 and self.forge[1] <= point[1] < self.forge[1] + 24:
            return 'berserk_godo_workshop'
        return 'forest'

    def var(self, value):
        kind, name = next(iter(value.items()))
        return ('u_' if kind == 'u_val' else '_' if kind == 'context_val' else '') + name

    def value(self, expression):
        expression = expression.replace("u_val('pos_z')", str(self.pos[2]))
        expression = re.sub(r'has_var\(([^)]+)\)', lambda v: str(int(v[1] in self.vars)), expression)
        expression = re.sub(r"[un]_monsters_nearby\([^)]*\)", str(len(self.knights)), expression)
        def sub(match):
            key = match[0]
            if key.endswith(('.x', '.y', '.z')): return str(self.vars[key[:-2]]['xyz'.index(key[-1])])
            return repr(self.vars[key])
        expression = re.sub(r'\b(?:u_berserk_|berserk_|_godo_rescue_candidate)\w*(?:\.[xyz])?\b', sub, expression)
        return eval(expression, {'__builtins__': {}}, {'floor': lambda n: n // 1})

    def condition(self, c):
        if isinstance(c, str): return c in ['has_beta', 'npc_is_monster']
        if 'and' in c: return all(self.condition(v) for v in c['and'])
        if 'or' in c: return any(self.condition(v) for v in c['or'])
        if 'not' in c: return not self.condition(c['not'])
        if 'math' in c: return bool(self.value(c['math'][0]))
        if 'test_eoc' in c: return self.condition(self.eocs[c['test_eoc']]['condition'])
        if 'u_at_om_location' in c: return self.terrain(self.pos) == c['u_at_om_location']
        if 'overmap_at_point' in c: return self.terrain(self.vars[self.var(c['point'])]) == c['overmap_at_point']
        if 'compare_string' in c:
            a, b = c['compare_string']; return a == self.vars[self.var(b)]
        if 'u_has_item' in c: return self.items[c['u_has_item']] > 0
        raise AssertionError(c)

    def run(self, id):
        self.calls.append(id)
        # Combat recovery and mission placement have their own checks. This model
        # stops at their actual handoff instead of pretending to simulate them.
        if id == 'EOC_BERSERK_ECLIPSE_AFTERMATH': return
        row = self.eocs[id]
        if 'condition' not in row or self.condition(row['condition']): self.effect(row['effect'])

    def effect(self, value):
        if isinstance(value, list):
            for part in value: self.effect(part)
        elif 'if' in value:
            branch = 'then' if self.condition(value['if']) else 'else'
            if branch in value: self.effect(value[branch])
        elif 'run_eocs' in value:
            if 'time_in_future' in value: self.queue.append(value['run_eocs'])
            else: self.run(value['run_eocs'])
        elif 'copy_var' in value:
            self.vars[self.var(value['target_var'])] = self.vars[self.var(value['copy_var'])].copy()
        elif 'math' in value:
            lhs, rhs = value['math'][0].split(' = ')
            result = self.value(rhs)
            if lhs.endswith(('.x', '.y', '.z')): self.vars[lhs[:-2]]['xyz'.index(lhs[-1])] = int(result)
            else: self.vars[lhs] = result
        elif 'u_location_variable' in value:
            self.searches += 1
            self.vars[self.var(value['u_location_variable'])] = self.forge.copy() if self.find else self.pos.copy()
            for id in value.get('true_eocs', []): self.run(id)
        elif 'u_teleport' in value:
            dest = self.vars[self.var(value['u_teleport'])]
            if self.teleport or self.terrain(dest) != 'berserk_godo_workshop': self.pos = dest.copy()
        elif 'u_add_var' in value: self.vars['u_' + value['u_add_var']] = value['value']
        elif 'u_spawn_monster' in value:
            self.knights.append(self.vars[self.var(value['target_var'])].copy() if 'target_var' in value else self.pos.copy())
            for id in value.get('true_eocs', []): self.run(id)
        elif 'u_run_monster_eocs' in value:
            for actor in self.knights.copy():
                low = self.vars[self.var(value['z_min'])] if 'z_min' in value else self.pos[2]
                high = self.vars[self.var(value['z_max'])] if 'z_max' in value else self.pos[2]
                if not low <= actor[2] <= high: continue
                for row in value['u_run_monster_eocs']: self.effect(row['effect'])
                if any('u_die' in row['effect'] for row in value['u_run_monster_eocs']): self.knights.remove(actor)
        elif 'u_die' in value: pass  # Removal is scoped to the selected actor above.
        elif 'u_spawn_item' in value: self.items[value['u_spawn_item']] += value.get('count', 1)
        elif 'u_message' in value or 'reveal_map' in value: pass
        else: raise AssertionError(value)


class RescueAndFarewell(unittest.TestCase):
    def test_known_forge_reused_and_both_endings_share_return(self):
        s = Scene(known=True); s.run('EOC_BERSERK_ECLIPSE_RESCUE_RETURN')
        self.assertEqual(s.pos, [2409, 4814, 0]); self.assertEqual(s.searches, 0)
        self.assertEqual(s.vars['u_berserk_godo_rescue_relocated'], 1)
        self.assertEqual(s.vars['u_berserk_eclipse_rescue_state'], 2)
        self.assertIn('EOC_BERSERK_ECLIPSE_AFTERMATH', s.calls)
        victory = s.eocs['EOC_BERSERK_ECLIPSE_VICTORY']
        self.assertIn('EOC_BERSERK_ECLIPSE_RESCUE_RETURN', str(victory))

    def test_unknown_forge_validated_and_transfer_is_one_time(self):
        s = Scene(); s.run('EOC_BERSERK_ECLIPSE_RESCUE_RETURN')
        self.assertEqual(s.vars['berserk_godo_location'], s.forge)
        self.assertEqual(s.pos, [2409, 4814, 0]); self.assertEqual(s.searches, 1)
        s.pos = [999, 999, 0]; s.run('EOC_BERSERK_GODO_RESCUE_TRANSFER')
        self.assertEqual(s.pos, [999, 999, 0]); self.assertEqual(s.searches, 1)

    def test_wrong_candidate_and_failed_teleport_leave_safe_original_exit(self):
        for find, teleport in [(False, True), (True, False)]:
            with self.subTest(find=find, teleport=teleport):
                s = Scene(find=find, teleport=teleport); s.run('EOC_BERSERK_ECLIPSE_RESCUE_RETURN')
                self.assertEqual(s.pos, [100, 100, 0])
                self.assertEqual(s.vars['u_berserk_godo_rescue_relocated'], 0)
                self.assertEqual(s.vars['u_berserk_eclipse_rescue_state'], 2)

    def test_knight_waits_at_anchor_then_departure_blocks_retry_and_old_migration(self):
        s = Scene(known=True); s.run('EOC_BERSERK_ECLIPSE_RESCUE_RETURN')
        s.vars['u_berserk_knight_waiting'] = 'yes'
        s.run('EOC_BERSERK_ECLIPSE_PLACE_KNIGHT'); s.run('EOC_BERSERK_ECLIPSE_PLACE_KNIGHT')
        self.assertEqual(s.knights, [[2402, 4815, 0]])
        s.run('EOC_BERSERK_KNIGHT_FAREWELL')
        self.assertEqual(len(s.knights), 1)  # Not deleted while dialogue owns the actor.
        self.assertEqual(s.queue, ['EOC_BERSERK_KNIGHT_DEPART'])
        s.run(s.queue.pop()); self.assertEqual(s.knights, [])
        s.run('EOC_BERSERK_ECLIPSE_KNIGHT_RETRY'); s.run('EOC_BERSERK_RESTORE_DISMISSED_KNIGHT')
        self.assertEqual(s.knights, [])
        self.assertEqual(s.vars['u_berserk_knight_waiting'], 'gone')

    def test_confirmation_has_return_to_questions_and_no_early_removal(self):
        rows = {r['id']: r for r in json.loads((MOD / 'dialogue/skull_knight.json').read_text())}
        leave = rows['TALK_BERSERK_SKULL_KNIGHT_AFTER']['responses'][-1]
        self.assertNotIn('effect', leave)
        self.assertEqual(leave['topic'], 'TALK_BERSERK_SKULL_KNIGHT_FAREWELL')
        confirm = rows[leave['topic']]['responses']
        self.assertNotIn('effect', confirm[0]); self.assertEqual(confirm[0]['topic'], 'TALK_BERSERK_SKULL_KNIGHT_AFTER')
        self.assertEqual(confirm[1]['topic'], 'TALK_DONE')

    def test_new_anchors_are_passable_and_existing_health_policy_retained(self):
        p = json.loads((MOD.parents[1] / 'docs/location_projects/godo-3.2-01.json').read_text())
        for id in ['rescue_arrival', 'knight_wait']:
            x, y, z = p['anchors'][id]; self.assertEqual(z, 0)
            self.assertIn(p['floors']['ground'][y][x], ',p')
        e = Scene().eocs['EOC_BERSERK_ECLIPSE_RETURN_RECOVER']
        hp = [x['math'][0] for x in e['effect'] if 'math' in x and x['math'][0].startswith('u_hp(')]
        self.assertEqual(len(hp), 6); self.assertTrue(all('* 0.5' in x for x in hp))

    def test_temporary_knight_in_eclipse_does_not_replace_the_forge_guide(self):
        s = Scene(known=True); s.run('EOC_BERSERK_ECLIPSE_RESCUE_RETURN')
        s.knights = [[2409, 4814, -10]]
        s.vars['u_berserk_knight_waiting'] = 'yes'
        s.run('EOC_BERSERK_ECLIPSE_PLACE_KNIGHT')
        self.assertEqual(s.knights, [[2409, 4814, -10], [2402, 4815, 0]])


class StoryChoices(unittest.TestCase):
    def test_story_is_hidden_before_eclipse_and_does_not_change_recruitment(self):
        f = Forge()
        self.assertFalse(any(r['topic'] == 'TALK_BERSERK_RICKERT_ECLIPSE' for r in f.available('TALK_BERSERK_RICKERT')))
        f.vars['u_berserk_eclipse_rescue_state'] = 2
        topic = f.choose('TALK_BERSERK_RICKERT', 'About the Eclipse and the Band of the Hawk.')
        topic = f.choose(topic, 'They are gone, Rickert. Almost the whole Band died.')
        f.choose(topic, 'We were surrounded by mercenaries and beasts. Griffith was taken away.')
        self.assertEqual(f.vars['u_berserk_rickert_eclipse_story'], 2)
        f.choose('TALK_BERSERK_RICKERT_ECLIPSE', 'I can tell you the truth now.')
        self.assertEqual(f.vars['u_berserk_rickert_eclipse_story'], 1)
        self.assertEqual(f.vars['n_berserk_rickert_recruit_refused'], 0)

    def test_silence_can_later_be_replaced_by_truth_and_memories_are_not_consumed(self):
        f = Forge(); f.vars['u_berserk_eclipse_rescue_state'] = 2
        f.choose('TALK_BERSERK_RICKERT_ECLIPSE', 'Remain silent and turn away.')
        self.assertEqual(f.vars['u_berserk_rickert_eclipse_story'], 3)
        f.choose('TALK_BERSERK_RICKERT_ECLIPSE', 'I can tell you the truth now.')
        f.items['berserk_judeau_knife_hilt'] = 1
        choices = f.available('TALK_BERSERK_RICKERT_ECLIPSE_MEMORIES')
        self.assertEqual(len([r for r in choices if 'REMEMBER_' in r['topic']]), 1)
        f.choose('TALK_BERSERK_RICKERT_ECLIPSE_MEMORIES', "Judeau's knife hilt.")
        self.assertEqual(f.items['berserk_judeau_knife_hilt'], 1)

    def test_dismissed_sparks_cannot_restart_but_crafting_and_neutral_delay_remain(self):
        f = Forge(); f.actor = 'godo'
        f.choose('TALK_BERSERK_GODO_SPARKS', 'Let me come back to this when I can listen.')
        self.assertEqual(f.vars['u_berserk_godo_sparks_closed'], 0)
        f.choose('TALK_BERSERK_GODO_SPARKS', 'Nothing. I do not want to talk about it.')
        self.assertEqual(f.vars['u_berserk_godo_sparks_closed'], 1)
        loaded = Forge(); loaded.actor = 'godo'; loaded.vars.update(json.loads(json.dumps(f.vars)))
        for id in ['TALK_BERSERK_GODO', 'TALK_BERSERK_GODO_LIFE']:
            self.assertFalse(any(r['topic'] == 'TALK_BERSERK_GODO_SPARKS' for r in loaded.available(id)))
        self.assertEqual([r['topic'] for r in loaded.available('TALK_BERSERK_GODO_SPARKS')], ['TALK_BERSERK_GODO'])
        loaded.run('EOC_BERSERK_GODO_START_SWORD')
        self.assertEqual(loaded.vars['u_berserk_godo_sword_state'], 1)


if __name__ == '__main__': unittest.main()
