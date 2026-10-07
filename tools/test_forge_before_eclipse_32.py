"""Exercise dialogue branches and actual JSON order transactions; no native gameplay."""
import json
import unittest

from test_godo_32 import Forge, MOD


class BeforeEclipseForge(unittest.TestCase):
    def survivor(self, profession='unemployed', after=False, actor='godo'):
        f = Forge(); f.profession = profession; f.actor = actor
        f.vars['berserk_eclipse_era'] = int(after); f.bionics.clear()
        return f

    def line(self, f, id):
        def resolve(value):
            if isinstance(value, str): return value
            condition = {k: v for k, v in value.items() if k not in {'yes', 'no'}}
            return resolve(value['yes'] if f.condition(condition) else value['no'])
        return resolve(f.topics[id]['dynamic_line'])

    def early(self, f):
        f.items.update({'steel_lump': 4, 'hc_steel_lump': 1, 'charcoal': 200, 'leather': 2})
        f.run('EOC_BERSERK_GODO_START_EARLY_SWORD'); f.run('EOC_BERSERK_GODO_EARLY_MATERIALS')

    def bolts(self, f):
        f.items.update({'steel_chunk': 1, 'stick': 1, 'thread': 20, 'feather': 10, 'charcoal': 50})
        f.run('EOC_BERSERK_RICKERT_ORDER_BOLTS')

    def test_only_two_professions_receive_invisible_start_marker(self):
        professions = json.loads((MOD/'professions/professions.json').read_text())
        marked = {p['id'] for p in professions if 'EOC_BERSERK_FORGE_GUTS_IDENTITY' in p.get('effect_on_conditions', [])}
        self.assertEqual(marked, {'berserk', 'berserk_before_eclipse'})
        self.assertTrue(all('eoc' not in p for p in professions))
        post=next(p for p in professions if p['id']=='berserk')
        self.assertIn('EOC_BERSERK_POST_ECLIPSE_START',post['effect_on_conditions'])
        for profession in ['berserk', 'berserk_before_eclipse', 'berserk_fan', 'berserk_prosthesis', 'unemployed']:
            f = self.survivor(profession); f.run('EOC_BERSERK_FORGE_GUTS_IDENTITY')
            self.assertEqual(f.vars['u_berserk_is_guts'], int(profession in marked))

    def test_first_old_save_greeting_does_not_need_speaker_effect_first(self):
        guts = self.survivor('berserk_before_eclipse', actor='rickert')
        stranger = self.survivor(actor='rickert')
        self.assertIn('Guts!', self.line(guts, 'TALK_BERSERK_RICKERT'))
        self.assertNotIn('Guts', self.line(stranger, 'TALK_BERSERK_RICKERT'))
        self.assertEqual(guts.vars['u_berserk_is_guts'], 0)

    def test_godot_introduction_is_personal_and_has_followups(self):
        f = self.survivor('berserk_before_eclipse')
        choices = f.available('TALK_BERSERK_GODO_ENTER')
        self.assertIn('TALK_BERSERK_GODO_RECOGNIZE', [r['topic'] for r in choices])
        self.assertNotIn('TALK_BERSERK_GODO_STRANGER', [r['topic'] for r in choices])
        self.assertIn('Guts', self.line(f, 'TALK_BERSERK_GODO_RECOGNIZE'))
        self.assertGreaterEqual(len(f.available('TALK_BERSERK_GODO_CRAFT')), 5)

    def test_world_era_and_personal_rescue_both_select_after_dialogues(self):
        for world, rescued in [(1, 0), (0, 2), (1, 2)]:
            f = self.survivor(actor='rickert'); f.vars['berserk_eclipse_era'] = world
            f.vars['u_berserk_eclipse_rescue_state'] = rescued
            self.assertTrue(f.condition({'test_eoc':'EOC_BERSERK_FORGE_AFTER_ECLIPSE'}))
            self.assertNotIn('TALK_BERSERK_RICKERT_HAWKS', [r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])
        f = self.survivor(actor='rickert')
        self.assertIn('TALK_BERSERK_RICKERT_HAWKS', [r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])
        self.assertNotIn('TALK_BERSERK_RICKERT_ECLIPSE', [r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])

    def test_world_event_does_not_fabricate_personal_reunion(self):
        f = self.survivor(after=True, actor='rickert')
        self.assertNotIn('brought you', self.line(f, 'TALK_BERSERK_RICKERT'))
        f.profession='berserk'; f.vars.update({'u_berserk_eclipse_rescue_state':2, 'u_berserk_godo_rescue_relocated':1})
        self.assertIn('Guts!', self.line(f, 'TALK_BERSERK_RICKERT'))
        self.assertIn('barely alive', self.line(f, 'TALK_BERSERK_RICKERT'))

    def test_pre_eclipse_topics_do_not_assume_missing_hand_or_brand(self):
        f = self.survivor(actor='rickert')
        for id in ['TALK_BERSERK_RICKERT', 'TALK_BERSERK_RICKERT_CRAFT', 'TALK_BERSERK_RICKERT_HOME', 'TALK_BERSERK_GODO_HOME']:
            text = self.line(f, id)
            self.assertNotIn('Brand', text); self.assertNotIn('arm cannon', text)
        self.assertNotIn('TALK_BERSERK_GODO_ARM', [r['topic'] for r in f.available('TALK_BERSERK_RICKERT')])

    def test_early_order_waits_and_awards_only_one_correct_sword(self):
        f = self.survivor(); self.early(f)
        self.assertIn('MISSION_BERSERK_GODO_EARLY_COLLECT', f.missions)
        f.run('EOC_BERSERK_GODO_EARLY_CLAIM'); self.assertEqual(f.items['true_guts_early_sword'],0)
        f.now += 43200
        for _ in range(3): f.run('EOC_BERSERK_GODO_EARLY_CLAIM')
        self.assertEqual(f.items['true_guts_early_sword'],1); self.assertEqual(f.items['true_guts_sword'],0)
        self.assertEqual(f.vars['u_berserk_godo_early_state'],3)
        self.assertFalse(any(id.startswith('MISSION_BERSERK_GODO_EARLY_') for id in f.missions))
        f.items['true_guts_early_sword']=0; f.run('EOC_BERSERK_GODO_START_EARLY_SWORD')
        self.assertEqual(f.vars['u_berserk_godo_early_state'],3)

    def test_missing_component_leaves_the_entire_delivery_intact(self):
        f = self.survivor(); f.items.update({'steel_lump':4, 'hc_steel_lump':1, 'charcoal':200})
        f.run('EOC_BERSERK_GODO_START_EARLY_SWORD'); before=f.items.copy()
        f.run('EOC_BERSERK_GODO_EARLY_MATERIALS')
        self.assertEqual(f.items,before); self.assertEqual(f.vars['u_berserk_godo_early_state'],1)

    def test_existing_profession_sword_is_repaired_instead_of_duplicated(self):
        f = self.survivor('berserk_before_eclipse'); f.items['true_guts_early_sword']=1
        f.run('EOC_BERSERK_GODO_START_EARLY_SWORD'); self.assertEqual(f.vars['u_berserk_godo_early_state'],0)
        self.assertIn('TALK_BERSERK_GODO_REPAIR',[r['topic'] for r in f.available('TALK_BERSERK_GODO_EARLY_SWORD')])
        f.items.update({'steel_lump':1, 'charcoal':50}); f.repair_item='true_guts_early_sword'
        f.run('EOC_BERSERK_GODO_REPAIR_PICK'); self.assertEqual(f.item_hp,f.item_max)
        self.assertEqual(f.items['true_guts_early_sword'],1)

    def test_prepaid_early_order_survives_eclipse_and_reload(self):
        f=self.survivor(); self.early(f); f.vars['berserk_eclipse_era']=1
        loaded=self.survivor(after=True); loaded.vars.update(json.loads(json.dumps(f.vars))); loaded.now=f.now+43200
        loaded.run('EOC_BERSERK_GODO_EARLY_CLAIM')
        self.assertEqual(loaded.items['true_guts_early_sword'],1)
        self.assertIn('TALK_BERSERK_GODO_EARLY_SWORD',[r['topic'] for r in loaded.available('TALK_BERSERK_GODO')])

    def test_early_deposit_refund_exactly_once_if_blade_acquired_elsewhere(self):
        f=self.survivor(); self.early(f); f.items['true_guts_early_sword']=1
        for _ in range(3): f.run('EOC_BERSERK_GODO_EARLY_REFUND')
        self.assertEqual(dict(f.items), {'steel_lump':4,'hc_steel_lump':1,'charcoal':200,'leather':2,'true_guts_early_sword':1})
        self.assertEqual(f.vars['u_berserk_godo_early_state'],3)

    def test_orders_are_owned_services_not_remote_note_rewards(self):
        f=self.survivor(); self.early(f); f.now+=43200; f.actor='book'
        f.run('EOC_BERSERK_GODO_EARLY_CLAIM'); self.assertEqual(f.items['true_guts_early_sword'],0)
        r=self.survivor(actor='rickert'); self.bolts(r); r.now+=1800; r.at_forge=False
        r.run('EOC_BERSERK_RICKERT_COLLECT_BOLTS'); self.assertEqual(r.items['bolt_wood_bodkin'],0)

    def test_dragonslayer_new_order_after_only_but_existing_orders_preserved(self):
        f=self.survivor(); f.run('EOC_BERSERK_GODO_START_SWORD')
        self.assertEqual(f.vars['u_berserk_godo_sword_state'],0)
        f.vars['berserk_eclipse_era']=1; f.run('EOC_BERSERK_GODO_START_SWORD')
        self.assertEqual(f.vars['u_berserk_godo_sword_state'],1)
        f.vars['berserk_eclipse_era']=0; f.items['steel_lump']=8; f.run('EOC_BERSERK_GODO_SWORD_IRON')
        self.assertEqual(f.vars['u_berserk_godo_sword_iron_given'],8)

    def test_bolts_wait_claim_once_and_allow_next_paid_batch(self):
        f=self.survivor(actor='rickert'); self.bolts(f)
        before=f.items.copy(); f.run('EOC_BERSERK_RICKERT_ORDER_BOLTS'); self.assertEqual(f.items,before)
        f.run('EOC_BERSERK_RICKERT_COLLECT_BOLTS'); self.assertEqual(f.items['bolt_wood_bodkin'],0)
        f.now+=1800
        for _ in range(2): f.run('EOC_BERSERK_RICKERT_COLLECT_BOLTS')
        self.assertEqual(f.items['bolt_wood_bodkin'],10)
        self.bolts(f); f.now+=1800; f.run('EOC_BERSERK_RICKERT_COLLECT_BOLTS')
        self.assertEqual(f.items['bolt_wood_bodkin'],20)

    def test_bolt_delivery_is_all_or_nothing_and_owned_by_rickert(self):
        f=self.survivor(actor='rickert'); f.items.update({'steel_chunk':1,'stick':1,'thread':20,'feather':9,'charcoal':50})
        before=f.items.copy(); f.run('EOC_BERSERK_RICKERT_ORDER_BOLTS'); self.assertEqual(f.items,before)
        f.items['feather']=10; before=f.items.copy(); f.actor='godo'
        f.run('EOC_BERSERK_RICKERT_ORDER_BOLTS'); self.assertEqual(f.items,before)

    def test_extra_topics_do_not_bypass_permanent_recruitment_refusal(self):
        f=self.survivor(actor='rickert'); f.vars['n_berserk_rickert_recruit_refused']=1
        self.assertNotIn('TALK_BERSERK_RICKERT_ROAD',[r['topic'] for r in f.available('TALK_BERSERK_RICKERT_TACTICS')])
        f.run('EOC_BERSERK_RICKERT_JOIN'); self.assertFalse(f.following)

    def test_notes_have_no_order_mutations_and_hide_future_sword_before_eclipse(self):
        f=self.survivor(); rows=json.loads((MOD/'dialogue/road_journal.json').read_text())
        f.topics.update({row['id']:row for row in rows})
        self.assertNotIn('TALK_BERSERK_JOURNAL_SWORD',[r['topic'] for r in f.available('TALK_BERSERK_JOURNAL_ORDERS')])
        for id in ['TALK_BERSERK_JOURNAL_EARLY','TALK_BERSERK_JOURNAL_BOLTS']:
            self.assertFalse(any('effect' in r for r in f.topics[id]['responses']))


if __name__ == '__main__': unittest.main()
