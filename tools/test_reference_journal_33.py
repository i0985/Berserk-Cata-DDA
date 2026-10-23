"""Execute the actual reference/source/mission JSON, without a CDDA binary.

The environment supplies inventory, terrain, actors and mission placement.
Unknown effects raise; book-only tests therefore catch accidental gameplay.
"""
import collections
import copy
import gettext
import json
import re
import unittest
from pathlib import Path

from reference_journal_content_33 import build, MANUSCRIPT, LETTER_ITEMS

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'
P = 'EOC_BERSERK_REF_'
T = 'TALK_BERSERK_REF_'
EOCS = {x['id']: x for p in (MOD / 'effects').glob('*.json') for x in json.loads(p.read_text())
        if x.get('type') == 'effect_on_condition'}
TOPICS = {x['id']: x for p in (MOD / 'dialogue').glob('*.json') for x in json.loads(p.read_text())}
CATALOG = json.loads((MOD.parents[1] / 'docs/dialogue_sources/road-journal-legacy-33.json').read_text())
MANIFEST = json.loads((MOD.parents[1] / 'docs/dialogue_sources/reference-journal-bindings-33.json').read_text())


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v, list):
        for x in v: yield from walk(x)


class Book:
    def __init__(self, old=False):
        self.values = {} if old else {'u_berserk_ref_schema': 1}
        self.inventory = collections.Counter()
        self.traits = set(); self.bionics = set(); self.om = ''; self.outside = False
        self.messages = []; self.opened = []; self.calls = []; self.missions = {}; self.finished = []
        self.now = 1000; self.guts = False; self.full_armor = False; self.actor = 'avatar'
        self.terrain = {}; self.furniture = {}; self.fields = {}; self.learned = set()
        self.overrides = {}; self.pos = (0, 0, 0); self.safe = True
        self.beta_pos = (1, 0, 0); self.can_see = True

    def getvar(self, v):
        if 'u_val' in v: return self.values.get('u_' + v['u_val'], 0)
        if 'global_val' in v: return self.values.get(v['global_val'], 0)
        if 'context_val' in v: return self.values.get('_' + v['context_val'], 0)
        raise AssertionError(v)

    def value(self, s):
        s = re.sub(r'has_var\((\w+)\)', lambda m: str(int(m[1] in self.values)), s)
        s = s.replace("time('now')", str(self.now))
        s = s.replace("u_val('pos_z')", str(self.pos[2]))
        s = re.sub(r"u_monsters_nearby\([^)]*\)", '0', s)
        def distance(m):
            a, b = m[1], m[2]
            aa = self.pos if a == "'u'" else self.values.get(a, (99999, 99999, 99))
            bb = self.pos if b == "'u'" else self.values.get(b, (99999, 99999, 99))
            return str(max(abs(aa[i] - bb[i]) for i in range(3)))
        s = re.sub(r"distance\(([^,]+),\s*([^\)]+)\)", distance, s)
        def variable(m):
            name = m[0]
            if name.endswith(('.x', '.y', '.z')):
                base, axis = name.rsplit('.', 1)
                return repr(self.values.get(base, (0, 0, 0))['xyz'.index(axis)])
            return repr(self.values.get(name, 0))
        s = re.sub(r'\b(?:[un]_)?berserk_\w+(?:\.[xyz])?|_ref_\w+(?:\.[xyz])?', variable, s)
        return eval(s, {'__builtins__': {}}, {'min': min, 'max': max, 'floor': lambda n: n // 1})

    def condition(self, c):
        if isinstance(c, str):
            if c == 'u_is_avatar': return self.actor == 'avatar'
            if c == 'u_is_outside': return self.outside
            if c == 'u_at_safe_space': return self.safe
            if c in ['has_alpha', 'has_beta']: return True
            if c in ['npc_is_npc', 'npc_is_monster', 'u_is_npc', 'u_is_monster']: return False
            raise AssertionError(c)
        if 'and' in c: return all(self.condition(x) for x in c['and'])
        if 'or' in c: return any(self.condition(x) for x in c['or'])
        if 'not' in c: return not self.condition(c['not'])
        if 'test_eoc' in c:
            id_ = c['test_eoc']
            if id_ in self.overrides: return self.overrides[id_]
            if id_ == 'EOC_BERSERK_FORGE_GUTS': return self.guts
            if id_ == 'EOC_BERSERK_SOLAR_DAY': return True
            if id_ == 'EOC_BERSERK_GODO_KNOWN': return 'berserk_godo_location' in self.values
            if id_ == 'EOC_BERSERK_FLORA_FULL_SET': return self.full_armor
            return self.condition(EOCS[id_]['condition'])
        if 'math' in c: return bool(self.value(c['math'][0]))
        if 'u_has_item' in c: return self.inventory[c['u_has_item']] > 0
        if 'u_has_items' in c:
            x = c['u_has_items']; return self.inventory[x['item']] >= x.get('count', 1)
        if 'u_has_trait' in c: return c['u_has_trait'] in self.traits
        if 'u_has_bionics' in c: return c['u_has_bionics'] in self.bionics
        if 'u_has_flag' in c: return False
        if 'u_profession' in c: return False
        if 'u_at_om_location' in c: return self.om == c['u_at_om_location']
        if 'u_has_mission' in c: return c['u_has_mission'] in self.missions
        if 'u_can_see_location' in c: return self.can_see and self.getvar(c['u_can_see_location']) != 0
        if 'overmap_at_point' in c: return self.getvar(c['point']) in self.terrain and self.terrain[self.getvar(c['point'])] == c['overmap_at_point']
        for field, data in [('map_terrain_id', self.terrain), ('map_furniture_id', self.furniture), ('map_field_id', self.fields)]:
            if field in c: return data.get(self.getvar(c['loc'])) == c[field]
        if 'compare_string' in c:
            a, b = c['compare_string']; return (self.getvar(a) if isinstance(a, dict) else a) == (self.getvar(b) if isinstance(b, dict) else b)
        raise AssertionError(c)

    def run(self, id_):
        if not id_.startswith('EOC_'): id_ = P + id_
        self.calls.append(id_)
        if id_ == 'EOC_BERSERK_GODO_LEARN_TRACE':
            self.values['u_berserk_journal_knows_godo'] = 1
            self.values['berserk_godo_location'] = (1200, 1200, 0)
            self.missions.setdefault('MISSION_BERSERK_GODO', (1200, 1200, 0))
            return
        if id_ == 'EOC_BERSERK_GODO_ROUTE_MISSION': return
        if id_ == 'EOC_BERSERK_JOURNAL_BREACH_LOCATE':
            self.values.setdefault('u_berserk_local_breach_location', (240, 0, 0))
            self.missions.setdefault('MISSION_BERSERK_BREACH', self.values['u_berserk_local_breach_location'])
            return
        if id_ == 'EOC_BERSERK_KNOWN_ROUTES_NOW': return
        obj = EOCS[id_]
        if 'condition' not in obj or self.condition(obj['condition']): self.effect(obj['effect'])

    def effect(self, x):
        if isinstance(x, list):
            for v in x: self.effect(v)
        elif 'if' in x:
            branch = 'then' if self.condition(x['if']) else 'else'
            if branch in x: self.effect(x[branch])
        elif 'math' in x:
            left, right = x['math'][0].split(' = ', 1)
            if left.endswith(('.x', '.y', '.z')):
                base, axis = left.rsplit('.', 1); pos = list(self.values[base])
                pos['xyz'.index(axis)] = self.value(right); self.values[base] = tuple(pos)
            else: self.values[left] = self.value(right)
        elif 'run_eocs' in x:
            old = self.actor
            if x.get('alpha_talker') == 'avatar': self.actor = 'avatar'
            self.run(x['run_eocs'])
            self.actor = old
        elif 'npc_location_variable' in x or 'u_location_variable' in x:
            field = 'npc_location_variable' if 'npc_location_variable' in x else 'u_location_variable'
            k, v = next(iter(x[field].items()))
            self.values[{'u_val': 'u_', 'global_val': '', 'context_val': '_'}[k] + v] = self.beta_pos if field.startswith('npc_') else self.pos
        elif 'copy_var' in x:
            k, v = next(iter(x['target_var'].items()))
            self.values[{'u_val': 'u_', 'global_val': '', 'context_val': '_'}[k] + v] = self.getvar(x['copy_var'])
        elif 'open_dialogue' in x: self.opened.append(x['open_dialogue']['topic'])
        elif 'u_message' in x: self.messages.append(copy.deepcopy(x))
        elif 'u_spawn_item' in x: self.inventory[x['u_spawn_item']] += x.get('count', 1)
        elif 'u_learn_recipe' in x: self.learned.add(x['u_learn_recipe'])
        elif 'assign_mission' in x:
            id_ = x['assign_mission']; assert id_ not in self.missions
            self.missions[id_] = self.values.get('u_berserk_first_hunt_location' if id_ == 'MISSION_BERSERK_FIRST_TRACE' else 'berserk_godo_location')
        elif 'finish_mission' in x:
            id_ = x['finish_mission']; assert id_ in self.missions
            self.finished.append((id_, x.get('success', True))); self.missions.pop(id_)
        else: raise AssertionError('Unexpected book/source effect: ' + str(x))

    def line(self, id_):
        def resolve(x):
            if isinstance(x, str): return x
            if 'concatenate' in x: return ''.join(resolve(y) for y in x['concatenate'])
            return resolve(x['yes'] if self.condition({k: v for k, v in x.items() if k not in ['yes', 'no']}) else x.get('no', ''))
        return resolve(TOPICS[id_ if id_.startswith('TALK_') else T + id_]['dynamic_line'])

    def available(self, id_):
        return [x for x in TOPICS[id_ if id_.startswith('TALK_') else T + id_]['responses']
                if 'condition' not in x or self.condition(x['condition'])]

    def titles(self, section):
        out = []
        for r in self.available(section.upper()):
            if 'truefalsetext' in r:
                x = r['truefalsetext']; out.append(x['true' if self.condition(x['condition']) else 'false'])
        return out

    def enter(self, id_):
        id_ = id_ if id_.startswith('TALK_') else T + id_
        line = self.line(id_)
        for x in [TOPICS[id_].get('speaker_effect')]:
            if x: self.effect(x['effect'])
        return line

    def sync(self): self.run('SYNC')
    def source(self, stem):
        readers = CATALOG['readers'].get('berserk_' + stem, ['EOC_BERSERK_ECLIPSE_LAST_STAND_READ'])
        self.run(readers[0])


class ReferenceBook(unittest.TestCase):
    def test_blank_book_has_only_close_and_no_spoilers(self):
        f = Book(); f.sync()
        self.assertEqual([r['topic'] for r in f.available('ROOT')], ['TALK_DONE'])
        self.assertIn('нет записей', f.line('ROOT')); self.assertFalse(f.missions)
        self.assertFalse(f.inventory); self.assertFalse(f.traits)

    def test_caravan_source_without_a_book_assigns_one_route_not_acquaintance(self):
        f = Book(); f.source('road_caravan_note')
        self.assertIn('MISSION_BERSERK_GODO', f.missions)
        self.assertEqual(f.titles('people'), [])
        self.assertIn('Лесная кузница — Новое', f.titles('places'))
        self.assertEqual(f.titles('past'), ['Заказ с разграбленного обоза — Новое'])
        self.assertFalse(f.opened)
        self.assertEqual(f.values.get('u_berserk_rickert_met', 0), 0)

    def test_source_rereading_does_not_replay_route_or_duplicate_book(self):
        f = Book(); f.source('road_caravan_note')
        before = copy.deepcopy((f.missions, f.inventory, f.learned)); f.calls.clear(); f.messages.clear()
        for _ in range(3): f.source('road_caravan_note')
        self.assertEqual((f.missions, f.inventory, f.learned), before)
        self.assertNotIn('EOC_BERSERK_GODO_LEARN_TRACE', f.calls)
        self.assertEqual(len(f.messages), 3); self.assertTrue(all(m['popup'] for m in f.messages))
        self.assertFalse(f.opened)

    def test_unread_papers_and_world_flags_do_not_reveal_people_or_future(self):
        f = Book(); f.inventory.update({'berserk_' + s: 1 for s in LETTER_ITEMS})
        f.values.update(berserk_eclipse_era=1, berserk_hunt_count_state=5, berserk_hunt_wyald_state=5,
                        berserk_apostle_grunbeld_dead=1, berserk_flora_stage=3)
        f.sync()
        self.assertFalse(f.titles('people')); self.assertFalse(f.titles('places')); self.assertFalse(f.titles('past'))

    def test_manual_house_discovery_has_no_flora_name_or_fire(self):
        f = Book(); f.om = 'berserk_flora_manor'; f.run('VISIT'); f.sync()
        self.assertIn('Дом у огромного дерева — Новое', f.titles('places'))
        line = f.line('M11')
        self.assertNotIn('Флора', line); self.assertNotIn('огонь', line.lower()); self.assertNotIn('атакован', line)
        self.assertEqual(f.values.get('u_berserk_flora_met', 0), 0)

    def test_marker_visit_and_two_personal_introductions_are_independent(self):
        f = Book(); f.values['u_berserk_journal_knows_godo'] = 1; f.sync()
        self.assertFalse(f.titles('people'))
        f.om = 'berserk_godo_workshop'; f.run('VISIT')
        self.assertFalse(f.titles('people')); self.assertIn('Кто здесь работает', f.line('M01'))
        f.values['u_berserk_godo_personally_met'] = 1; f.sync()
        self.assertIn('Годо — Новое', f.titles('people')); self.assertNotIn('Рикерт — Новое', f.titles('people'))
        f.values['u_berserk_rickert_met'] = 1; f.sync(); self.assertIn('Рикерт — Новое', f.titles('people'))

    def test_records_keep_first_learned_order_and_new_badge_is_per_record(self):
        f = Book(); f.om = 'berserk_desecrated_chapel_nave'; f.run('VISIT')
        f.om = 'berserk_cursed_oak'; f.run('VISIT'); f.source('road_caravan_note')
        self.assertEqual(f.titles('places'), ['Лесная часовня — Новое', 'Дуб со сплетёнными корнями — Новое', 'Лесная кузница — Новое'])
        f.enter('M05'); self.assertEqual(f.titles('places')[0], 'Лесная часовня')
        f.source('chapel_ritual_note'); self.assertEqual(f.titles('places')[0], 'Лесная часовня — Новое')
        old = f.values['u_berserk_ref_rank_m05']; f = copy.deepcopy(f); f.sync()
        self.assertEqual(f.values['u_berserk_ref_rank_m05'], old)
        f.enter('M05'); f.sync(); self.assertEqual(f.titles('places')[0], 'Лесная часовня')

    def test_navigation_stays_in_section_and_close_is_unconditional(self):
        for r in MANIFEST['records']:
            options = TOPICS[T + r['key'].upper()]['responses']
            self.assertEqual([x['topic'] for x in options], [T + r['section'].upper(), 'TALK_DONE'])
            self.assertNotIn('effect', options[-1])
        for s in ['ROOT', 'PLACES', 'PEOPLE', 'PAST']:
            self.assertEqual(TOPICS[T + s]['responses'][-1], {'text': 'Закрыть журнал', 'topic': 'TALK_DONE'})

    def test_book_loss_and_restoration_preserve_progress_and_do_not_repeat_initial_issue(self):
        f = Book(); f.source('road_caravan_note'); f.inventory.clear(); f.values['u_berserk_godo_sword_iron_given'] = 16
        state = copy.deepcopy((f.values, f.missions, f.traits))
        f.run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL'); self.assertFalse(f.inventory)
        f.run('RESTORE'); self.assertEqual(f.inventory['berserk_campaign_journal'], 1)
        f.run('RESTORE'); self.assertEqual(f.inventory['berserk_campaign_journal'], 1)
        self.assertEqual((f.values, f.missions, f.traits), state)
        self.assertEqual(sum(m['u_message'] == 'Вы заново записываете то, что сохранили в памяти.' for m in f.messages), 1)

    def test_book_opening_cannot_start_growth_reroll_a_gift_or_award_equipment(self):
        f = Book(); f.values.update(u_berserk_apostol_path=1, u_berserk_apostol_lineage=4,
                                   u_berserk_apostol_stage=1, u_berserk_apostol_growth_step=0)
        before = copy.deepcopy((f.values, f.traits, f.inventory, f.missions))
        f.run('EOC_BERSERK_JOURNAL_OPEN'); f.run('EOC_BERSERK_JOURNAL_OPEN')
        self.assertEqual(f.values['u_berserk_apostol_lineage'], 4)
        self.assertEqual(f.values['u_berserk_apostol_growth_step'], 0)
        self.assertEqual((f.traits, f.inventory, f.missions), before[1:])
        self.assertNotIn('Пепельное разложение', f.line('T01'))
        self.assertFalse(any('_BEGIN' in s or '_FIND' in s or '_LOCATE' in s for s in f.calls))

    def test_normal_and_alternative_memories_do_not_cross(self):
        f = Book(); f.values.update(u_berserk_eclipse_route=2, u_berserk_apostol_return_state=2, u_berserk_apostol_outcome=1,
                                   u_berserk_apostol_path=1, u_berserk_apostol_lineage=2); f.sync()
        self.assertNotIn('Рыцарь-Череп — Новое', f.titles('people'))
        self.assertNotIn('Затмение — Новое', f.titles('past'))
        self.assertIn('Церемониальный круг — Новое', f.titles('past'))
        self.assertNotIn('Рыцарь', f.line('C04')); self.assertNotIn('кисть', f.line('C04'))
        f = Book(); f.values.update(u_berserk_eclipse_rescue_state=2, u_berserk_eclipse_route=1); f.sync()
        self.assertIn('Затмение — Новое', f.titles('past')); self.assertNotIn('Церемониальный круг — Новое', f.titles('past'))

    def test_refusal_scars_remain_human_and_only_actual_scars_are_described(self):
        f = Book(); f.values.update(u_berserk_eclipse_route=2, u_berserk_apostol_return_state=2, u_berserk_apostol_outcome=2)
        f.traits.update(['BERSERK_ECLIPSE_SCAR_HEARING', 'BERSERK_ECLIPSE_SCAR_MEMORIES']); f.sync()
        line = f.line('C06'); self.assertIn('глуше', line); self.assertIn('Воспоминания', line)
        self.assertNotIn('Зрение', line); self.assertNotIn('дрожь', line)
        self.assertNotIn('Моё тело — Новое', f.titles('past'))
        self.assertNotIn('u_berserk_apostol_human_equipment_locked', f.values)

    def test_five_godhand_figures_are_recorded_only_individually_after_talking(self):
        f = Book(); f.values['u_berserk_apostol_hand_slan_introduced'] = 1; f.sync()
        line = f.line('C05'); self.assertIn('Слан', line)
        for name in ['Войд', 'Убик', 'Конрад', 'Фемто']: self.assertNotIn(name, line)

    def test_all_thirteen_forms_share_one_record_with_no_other_form_prose(self):
        forms = [('VOID', 'APOSTLE'), ('SLAN', 'APOSTLE'), ('UBIK', 'APOSTLE'), ('CONRAD', 'APOSTLE'), ('FEMTO', 'APOSTLE'),
                 ('COUNT_FLESH', 'APOSTLE'), ('WYALD_FLESH', 'APOSTLE'), ('ROSINE_FLESH', 'APOSTLE'), ('GRUNBELD_FLESH', 'APOSTLE'),
                 ('COUNT_PAWN', 'PAWN'), ('WYALD_PAWN', 'PAWN'), ('ROSINE_PAWN', 'PAWN'), ('GRUNBELD_PAWN', 'PAWN')]
        prose = [MANUSCRIPT[f'Т{i:02}']['paragraphs'][0] for i in range(4, 17)]
        for n, (stem, final) in enumerate(forms):
            with self.subTest(form=stem):
                f = Book(); f.traits.add('BERSERK_' + stem + '_' + final)
                f.values.update(u_berserk_apostol_path=1 if n < 5 else 2 if n < 9 else 3, u_berserk_apostol_body_checked=1,
                                u_berserk_apostol_lineage=n + 1, u_berserk_apostol_stage=3)
                f.sync(); text = f.line('T01')
                self.assertIn(prose[n], text)
                for j, other in enumerate(prose):
                    if j != n: self.assertNotIn(other, text)
                self.assertEqual(sum('Моё тело' in s for s in f.titles('past')), 1)

    def test_owned_flesh_is_not_eaten_and_pawn_has_no_future_growth_promise(self):
        f = Book(); f.inventory['berserk_apostol_count_flesh'] = 1; f.sync()
        self.assertFalse(f.titles('past'))
        f.traits.add('BERSERK_COUNT_PAWN_PAWN'); f.values.update(u_berserk_apostol_path=3, u_berserk_apostol_lineage=10,
            u_berserk_apostol_stage=3, u_berserk_apostol_pawn_oath_broken=1); f.sync()
        self.assertIn('Изменённое тело осталось', f.line('T01')); self.assertNotIn('Перемена продолжается сама', f.line('T01'))

    def test_rickert_lie_silence_and_confession_have_distinct_memories(self):
        f = Book(); f.values.update(u_berserk_rickert_met=1, u_berserk_rickert_eclipse_story=2); f.sync()
        self.assertIn('умолчал', f.line('L02')); self.assertNotIn('Он услышал о предательстве', f.line('L02'))
        f.values.update(u_berserk_rickert_eclipse_story=1, u_berserk_rickert_lied_before=1); f.sync()
        self.assertIn('признался', f.line('L02')); self.assertNotIn('снова стало возможно доверие', f.line('L02'))
        f.values['u_berserk_ref_rickert_trust_restored'] = 1; f.sync(); self.assertIn('снова стало возможно доверие', f.line('L02'))

    def test_intact_hand_has_no_prosthesis_information_without_device_experience(self):
        f = Book(); f.values['u_berserk_rickert_met'] = 1; f.sync()
        self.assertNotIn('Протез и рука-пушка — Новое', f.titles('people'))
        f.inventory['bio_berserk_arm_cannon'] = 1; f.sync()
        self.assertIn('ещё не стало частью', f.line('L09')); self.assertNotIn('закреплён', f.line('L09'))
        f.bionics.add('bio_berserk_arm_cannon'); f.sync()
        self.assertIn('закреплён', f.line('L09')); self.assertNotIn('я собрал сам', f.line('L09'))

    def test_knight_archive_has_only_heard_answers_and_no_progression_effects(self):
        f = Book(); f.values.update(u_berserk_eclipse_rescue_state=2, u_berserk_eclipse_route=1); f.sync()
        self.assertNotIn('The God Hand', f.line('L03'))
        f.values['u_berserk_knight_read_god_hand'] = 1; f.sync()
        self.assertIn('The God Hand', f.line('L03'))
        self.assertNotIn('come every night', f.line('L03'))
        f.values['u_berserk_knight_farewell_confirmed'] = 1; f.sync()
        self.assertIn('продолжил свой путь', f.line('L03'))

    def test_legacy_books_do_not_unlock_unknown_hunts_or_orders(self):
        for suffix in ['LEGACY_HUNTS', 'LEGACY_ORDERS', 'OPEN_CURRENT', 'OPEN_REFUGE']:
            f = Book(); f.run('EOC_BERSERK_JOURNAL_' + suffix)
            self.assertFalse(f.titles('places')); self.assertFalse(f.titles('people')); self.assertFalse(f.missions)
            self.assertFalse(any('_LEARN_' in s for s in f.calls))

    def test_all_thirty_archived_texts_match_approved_source_and_have_no_side_effect(self):
        for i, stem in enumerate(LETTER_ITEMS, 1):
            with self.subTest(source=stem):
                f = Book(); f.values['u_berserk_journal_read_berserk_' + stem] = 1; f.sync()
                before = copy.deepcopy((f.inventory, f.missions, f.traits, f.learned))
                text = f.enter(f'P{i:02}')
                for para in MANUSCRIPT[f'П{i:02}']['paragraphs']: self.assertIn(para, text)
                self.assertEqual((f.inventory, f.missions, f.traits, f.learned), before)

    def test_fire_records_do_not_declare_flora_dead_or_resurrect_unread_manuscript(self):
        f = Book(); f.values.update(u_berserk_flora_escaped=1, u_berserk_flora_fire_summary_seen=1); f.sync()
        self.assertIn('дом у духовного дерева потерян', f.line('C17'))
        self.assertNotIn('Флора погибла', f.line('C17')); self.assertNotIn('Спасённая рукопись — Новое', f.titles('past'))
        self.assertFalse(f.inventory)

    def test_known_deaths_replace_present_work_only_when_actually_seen(self):
        for who, met, record, present, past in [
            ('GODO', 'u_berserk_godo_personally_met', 'L01', 'Годо — хозяин', 'Годо был хозяином'),
            ('RICKERT', 'u_berserk_rickert_met', 'L02', 'Рикерт работает', 'Рикерт работал'),
            ('FLORA', 'u_berserk_flora_met', 'L04', 'Флора — ведьма', 'Флора была ведьмой'),
            ('PRISONER', 'u_berserk_ref_prisoner_met', 'L05', 'Он знает привычки', 'Он знал привычки'),
        ]:
            with self.subTest(person=who):
                f = Book(); f.values[met] = 1; f.sync(); f.enter(record)
                old_rank = f.values['u_berserk_ref_rank_' + record.lower()]
                self.assertIn(present, f.line(record))
                f.can_see = False; f.run(who + '_DEATH')
                self.assertIn(present, f.line(record)); self.assertNotIn(past, f.line(record))
                f.can_see = True; f.run(who + '_DEATH')
                self.assertIn(past, f.line(record)); self.assertNotIn(present, f.line(record))
                self.assertIn('погиб', f.line(record))
                self.assertEqual(f.values['u_berserk_ref_rank_' + record.lower()], old_rank)
                self.assertTrue(any('Новое' in s for s in f.titles('people')))
                self.assertFalse(f.inventory); self.assertFalse(f.missions)
        f = Book(); f.run('GODO_DEATH'); self.assertFalse(f.titles('people'))
        f = Book(); f.guts = True; f.values['u_berserk_godo_personally_met'] = 1
        f.run('GODO_DEATH'); self.assertIn('Годо погиб.', f.line('L01'))

    def test_npc_rickert_death_uses_npc_position_before_switch_to_avatar(self):
        f = Book(); f.actor = 'npc'; f.pos = (144, 280, 0)
        f.values['u_berserk_rickert_met'] = 1
        f.run('EOC_BERSERK_RICKERT_DEATH')
        self.assertEqual(f.values['_ref_death_pos'], (144, 280, 0))
        self.assertEqual(f.actor, 'npc'); self.assertEqual(f.values['berserk_rickert_dead'], 1)
        self.assertEqual(f.values['u_berserk_ref_rickert_dead'], 1)

    def test_boss_death_does_not_prove_captive_is_freed(self):
        f = Book(); f.values.update(u_berserk_ref_prisoner_met=1, u_berserk_ref_dead_count=1)
        f.sync(); self.assertNotIn('Власть Графа над ним закончилась', f.line('L05'))
        f.enter('TALK_BERSERK_COUNT_AFTER'); f.sync()
        self.assertNotIn('Власть Графа над ним закончилась', f.line('L05'))
        # Actual escape is exercised by the native-captive model, not a death report.
        f.values['u_berserk_ref_prisoner_freed'] = 1; f.sync()
        self.assertIn('Власть Графа над ним закончилась', f.line('L05'))
        f.run('PRISONER_DEATH'); self.assertNotIn('Что он сделает с этой свободой', f.line('L05'))

    def test_legacy_post_eclipse_diary_opens_past_without_progression(self):
        obj = json.loads((MOD / 'items/post_eclipse_journal.json').read_text())[0]
        f = Book()
        for id_ in obj['use_action']['effect_on_conditions']: f.run(id_)
        self.assertEqual(f.opened, [T + 'PAST']); self.assertFalse(f.missions)

    def test_global_death_and_missing_actor_never_claim_grunbeld_died_at_flora(self):
        f = Book(); f.values.update(u_berserk_ref_visit_grunbeld=1, berserk_apostle_grunbeld_dead=1); f.sync()
        self.assertNotIn('погиб у духовного дерева', f.line('M12')); self.assertNotIn('Грюнбельд пал', f.line('M12'))

    def test_unknown_grunbeld_outcome_stays_unknown_after_escape(self):
        f = Book(); f.values.update(u_berserk_ref_grunbeld_siege_seen=1, u_berserk_flora_escaped=1,
            u_berserk_flora_fire_summary_seen=1); f.sync()
        self.assertIn('не знаю', f.line('C17')); self.assertNotIn('Грюнбельд погиб.', f.line('C17'))

    def test_repair_and_bolt_tasks_use_exact_forge_coordinates_without_a_book(self):
        f = Book(); pos = (2400, 1200, 0); f.values.update(berserk_godo_location=pos, u_berserk_godo_repair_state=1)
        f.run('ORDERS_SYNC'); self.assertEqual(f.missions['MISSION_BERSERK_GODO_REPAIR_COLLECT'], pos)
        f.values['u_berserk_rickert_bolts_requested'] = 1; f.run('ORDERS_SYNC')
        self.assertIn('MISSION_BERSERK_RICKERT_BOLTS_MATERIALS', f.missions)
        f.values['u_berserk_rickert_bolts_pending'] = 1; f.run('ORDERS_SYNC')
        self.assertNotIn('MISSION_BERSERK_RICKERT_BOLTS_MATERIALS', f.missions)
        self.assertEqual(f.missions['MISSION_BERSERK_RICKERT_BOLTS_COLLECT'], pos)
        self.assertFalse(f.inventory)

    def test_order_reloading_completion_repeat_and_abandonment(self):
        f = Book(); f.values.update(berserk_godo_location=(2400, 1200, 0), u_berserk_godo_repair_state=1)
        f.run('ORDERS_SYNC'); f = copy.deepcopy(f); f.run('ORDERS_SYNC'); self.assertEqual(len(f.missions), 1)
        f.values['u_berserk_godo_repair_state'] = 2; f.run('ORDERS_SYNC'); self.assertEqual(f.finished[-1][1], True)
        f.values['u_berserk_godo_repair_state'] = 1; f.run('ORDERS_SYNC'); self.assertEqual(len(f.missions), 1)
        f.values['u_berserk_godo_repair_state'] = 0; f.run('ORDERS_SYNC'); self.assertEqual(f.finished[-1][1], False)
        f.values['u_berserk_rickert_bolts_pending'] = 1; f.run('ORDERS_SYNC')
        f.values['u_berserk_rickert_bolts_pending'] = 0; f.run('ORDERS_SYNC'); self.assertFalse(f.missions)
        f.run('ORDERS_SYNC'); self.assertFalse(f.missions)

    def test_victory_followup_targets_real_lair_until_source_is_studied(self):
        f = Book(); pos = (480, 240, 0)
        f.values.update(u_berserk_first_hunt_done=1, u_berserk_first_hunt_location=pos)
        f.terrain[pos] = 'berserk_first_hunt_lair'; f.run('TRACE_SYNC')
        self.assertEqual(f.missions['MISSION_BERSERK_FIRST_TRACE'], pos)
        f.om = 'berserk_first_hunt_lair'; f.run('EOC_BERSERK_HUNT_REVEALED_TRAIL')
        self.assertNotIn('MISSION_BERSERK_FIRST_TRACE', f.missions)
        self.assertIn('MISSION_BERSERK_BREACH', f.missions); self.assertFalse(f.inventory['berserk_apostle_burned_clue'])

    def test_older_knowledge_migrates_once_without_reading_unread_letters(self):
        f = Book(old=True); f.values.update(u_berserk_journal_knows_count=1, u_berserk_godo_sword_iron_given=16)
        f.inventory['berserk_flora_rescued_manuscript'] = 1; f.run('MIGRATE'); f.sync()
        self.assertIn('Резиденция Графа — Новое', f.titles('places'))
        self.assertNotIn('Спасённая рукопись — Новое', f.titles('past'))
        self.assertEqual(f.values['u_berserk_godo_sword_iron_given'], 16)
        self.assertFalse(f.missions); self.assertFalse(f.traits)

    def test_only_cave_texts_contain_sound_distraction_advice(self):
        for code in ['М02', 'М04', 'М05', 'П08', 'П09', 'П10', 'П13', 'П14', 'П16', 'П27', 'П28']:
            text = ' '.join(MANUSCRIPT[code]['paragraphs'])
            self.assertNotRegex(text.lower(), 'колокол|звон|отвлекал|подвеск')
        self.assertIn('подвеск', ' '.join(MANUSCRIPT['П12']['paragraphs']))

    def test_book_graph_is_read_only_and_no_visible_author_notes(self):
        for id_, obj in TOPICS.items():
            if not id_.startswith(T): continue
            for node in walk(obj):
                self.assertFalse(set(node) & {'u_spawn_item', 'assign_mission', 'u_consume_item', 'reveal_map', 'mapgen_update', 'u_add_trait'})
                if 'run_eocs' in node: self.assertTrue(str(node['run_eocs']).startswith(P))
            text = json.dumps(obj, ensure_ascii=False)
            self.assertNotRegex(text, 'Условие:|Дополнение:|Авторское замечание:|форма пешки|слабая версия')

    def test_monster_death_uses_native_eoc_and_all_reference_targets_exist(self):
        data = json.loads((MOD / 'monsters/apostle_count.json').read_text())
        captive = next(x for x in data if x['id'] == 'mon_berserk_count_witness')
        death = 'EOC_BERSERK_COUNT33_LEGACY_DEATH'
        self.assertEqual(captive['death_function'], {'eoc': death})
        self.assertIn({'run_eocs': P + 'PRISONER_DEATH'}, EOCS[death]['effect'])
        f = Book(); f.run(death)
        self.assertEqual(f.values['berserk_count_prisoner_dead'], 1)
        for obj in EOCS.values():
            if not obj['id'].startswith(P): continue
            for node in walk(obj):
                if isinstance(node.get('run_eocs'), str): self.assertIn(node['run_eocs'], EOCS)
                if 'test_eoc' in node: self.assertIn(node['test_eoc'], EOCS)


if __name__ == '__main__': unittest.main()
