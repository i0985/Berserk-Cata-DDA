"""Check projection isolation and reward semantics; no native AI simulation."""
import json
import unittest
from test_recovery_33 import MOD, load, walk
from test_behelit_rewards import RewardGraph
from test_apostle_relics import RelicGraph


class ProjectionRecovery(unittest.TestCase):
    def setUp(self):
        self.monsters = {x['id']:x for x in load('monsters/apostle_projections.json')}
        self.new = [m for id_,m in self.monsters.items() if id_.split('_')[-1] not in ('zodd','griffith','void')]

    def test_ten_projections_share_the_previous_total_rarity(self):
        self.assertEqual(len(self.monsters), 10)
        group = load('monstergroups/monster_groups.json')[0]
        entries = [x for x in group['monsters'] if x['monster'] in self.monsters]
        self.assertEqual(sum(x['weight'] for x in entries), 16)
        self.assertEqual(sum(x['weight'] for x in group['monsters']), 186)

    def test_new_projections_do_not_inherit_original_rewards_or_pawn_contracts(self):
        self.assertEqual(len(self.new), 7)
        for mon in self.new:
            self.assertNotIn('copy-from', mon)
            self.assertEqual(mon['species'], ['NETHER'])
            self.assertNotIn('chat_topics', mon)
            self.assertNotIn('CONVERSATION', mon['flags'])
            self.assertEqual(mon['regenerates'], 0)
            self.assertEqual(mon['looks_like'], '')
            self.assertEqual(mon['death_function']['eoc'], 'EOC_BERSERK_BEHELIT_BOSS_DIES')
            self.assertEqual(mon['death_function']['corpse_type'], 'NO_CORPSE')
        self.assertEqual(load('monsterdrops/projection_drops.json')['items'], [])

    def test_attack_actors_are_complete_and_spells_resolve(self):
        spells = {x['id']:x for x in load('spells/apostle_projections.json')}
        for mon in self.new:
            for attack in mon['special_attacks']:
                self.assertGreater(attack['cooldown'], 0)
                if attack['type'] == 'leap':
                    self.assertGreater(attack['max_range'], 0)
                    self.assertFalse(attack['allow_no_target'])
                else:
                    spell = spells[attack['spell_data']['id']]
                    self.assertIn('message', spell)
                    self.assertIn('monster_message', attack)
        heat = spells['berserk_projection_grunbeld_heat']
        self.assertNotIn('field_id', heat)

    def test_new_projections_join_brand_budget_and_damage_whitelists(self):
        for name in ['effects/eclipse_brand_eocs.json','effects/eclipse_era_eocs.json','effects/apostle_relic_eocs.json']:
            serialized = json.dumps(load(name))
            for mon in self.new: self.assertIn(mon['id'], serialized)

    def test_no_projection_added_to_night_or_world_spawn_groups(self):
        for name in ['monstergroups/brand_night_groups.json','monstergroups/eclipse_era_groups.json']:
            self.assertNotIn('mon_berserk_projection_', json.dumps(load(name)))

    def test_ordinary_monster_kill_drops_at_victim_not_avatar(self):
        for killer in [None, 'npc', 'monster', 'avatar']:
            graph = RewardGraph(); graph.alpha = killer; graph.victim = (120,-12,-2)
            graph.avatar = (400,400,0); graph.run('EOC_BERSERK_BEHELIT_BOSS_DIES')
            self.assertEqual(graph.ground, [('berserk_behelit', graph.victim)])
            self.assertFalse(graph.inventory)

    def test_after_eclipse_no_new_behelit_is_awarded(self):
        for state in [{'berserk_eclipse_era':1}, {'u_berserk_eclipse_behelit_spent':1},
                      {'u_berserk_eclipse_trial_active':1}, {'u_berserk_eclipse_rescue_state':2}]:
            graph = RewardGraph(state); graph.alpha = None; graph.victim = (1,1,-1)
            graph.run('EOC_BERSERK_BEHELIT_BOSS_DIES'); self.assertFalse(graph.ground)

    def test_relic_bonus_applies_to_projection_without_qualifying_ordinary_zombies(self):
        for mon in self.new:
            g = RelicGraph(); g.alpha = 'monster'; g.beta = 'avatar'; g.target_id = mon['id']
            g.attacker_worn.add('berserk_count_iron_seal'); g.damage = 10
            g.run('EOC_BERSERK_COUNT_RELIC_DAMAGE')
            self.assertEqual(g.target_hp, 98)
        g = RelicGraph(); g.alpha='monster';g.beta='avatar';g.target_id='mon_zombie'
        g.attacker_worn.add('berserk_count_iron_seal');g.damage=10
        g.neighbors=[(self.new[0]['id'],1,False)];g.run('EOC_BERSERK_COUNT_RELIC_DAMAGE')
        self.assertEqual(g.target_hp,100)

    def test_names_and_abilities_have_russian_translations(self):
        import gettext
        for locale in ['ru', 'zh_CN']:
            with (MOD / f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo').open('rb') as f:
                catalog = gettext.GNUTranslations(f)
            for mon in self.new:
                self.assertNotEqual(catalog.gettext(mon['name']['str']), mon['name']['str'])
                self.assertNotEqual(catalog.gettext(mon['description']), mon['description'])
                for count in [1,2,5]:
                    value = catalog.ngettext(mon['name']['str'], mon['name']['str_pl'], count)
                    self.assertNotIn(value, (mon['name']['str'], mon['name']['str_pl']))


if __name__ == '__main__': unittest.main()
