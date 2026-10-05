"""Focused JSON/EOC regressions for the second playtest; no CDDA binary.

Target fixtures follow spell::is_valid_target in tag 0.I-1. They do not simulate
native damage, armor, AI, overmap placement or the dialogue UI.
"""
import json
import math
import unittest
from test_behelit_rewards import MOD, objects
from test_committed_apostle_attacks import Actor, CommittedGraph
import test_flora_dialogue_states as flora_states

class OctoberSecondPlaytest(unittest.TestCase):
    def test_actual_healing_expressions_add_half_max_and_cap_each_part(self):
        e=next(e for e in objects(MOD/'effects/eclipse_aftermath_eocs.json') if e['id']=='EOC_BERSERK_ECLIPSE_RETURN_RECOVER')
        expressions=[v['math'][0] for v in e['effect'] if 'math' in v and v['math'][0].startswith('u_hp(')]
        self.assertEqual(len(expressions),6)
        for expr in expressions:
            rhs=expr.split(' = ')[1]
            for current,maximum,expected in [(1,100,51),(30,100,80),(80,100,100),(100,100,100),(1,99,50)]:
                with self.subTest(expr=expr,current=current,maximum=maximum):
                    result=eval(rhs,{'__builtins__':{}},{'u_hp':lambda _:current,'u_hp_max':lambda _:maximum,'min':min,'floor':math.floor})
                    self.assertEqual(result,expected)

    def test_committed_warnings_and_damage_accept_occupied_hostile_and_ally_cells(self):
        spells=objects(MOD/'spells/apostle_committed_attacks.json')+objects(MOD/'spells/grunbeld_breath.json')
        attacks=[s for s in spells if s['effect']=='attack']
        self.assertEqual(len(attacks),10)
        for s in attacks:
            targets=s['valid_targets']
            # Empty cells use ground; a creature uses hostile/ally instead.
            for occupant in ('ground','hostile','ally'):
                with self.subTest(spell=s['id'],occupant=occupant):
                    self.assertIn(occupant,targets)
            self.assertNotIn('self',targets)
            if s['id'].endswith('_warning'):self.assertEqual(s['max_damage'],0)
            else:self.assertGreater(s['min_damage'],0)

    def test_wyald_can_rearm_after_recovery_on_same_monster(self):
        g=CommittedGraph('wyald');a=Actor((0,0,0));b=Actor((1,0,0))
        g.begin(a,b);g.tick(a,103)
        self.assertEqual(a.values['berserk_committed_wyald_phase'],0)
        first=len(g.shots());self.assertGreater(first,0)
        g.now=105;g.begin(a,b)
        self.assertEqual(a.values['berserk_committed_wyald_phase'],0)
        g.now=113;g.begin(a,b)
        self.assertEqual(a.values['berserk_committed_wyald_phase'],1)
        g.tick(a,116);self.assertGreater(len(g.shots()),first)
        monster=objects(MOD/'monsters/apostle_wyald.json')[0]
        special=next(s for s in monster['special_attacks'] if s['id']=='berserk_wyald_b_prepare')
        attack=next(s for s in objects(MOD/'monster_special_attacks/wyald_rosine_attacks.json') if s['id']==special['id'])
        self.assertEqual((special['cooldown'],attack['cooldown']),(10,10))

    def test_manual_flora_outside_manor_can_give_once_but_cannot_begin_siege(self):
        fixture=flora_states.FloraDialogueStates();g=fixture.post_eclipse();g.beta_omt='field';g.omt='field'
        menu=fixture.open_conversation(g)
        self.assertTrue(any(r['topic']=='TALK_BERSERK_FLORA_OFFER' for r in menu))
        self.assertFalse(any('SIEGE_' in r['topic'] for r in menu))
        g.run('EOC_BERSERK_FLORA_GIVE_ARMOR');items=list(g.inventory)
        self.assertEqual(len(items),6)
        g.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertEqual(g.inventory,items)
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        self.assertNotIn('berserk_flora_location',g.flags)
        self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)

    def test_knight_points_to_flora_after_first_hunt_without_named_boss_requirement(self):
        topic=next(t for t in objects(MOD/'dialogue/skull_knight.json') if t['id']=='TALK_BERSERK_SKULL_KNIGHT_AFTER')
        r=next(r for r in topic['responses'] if r['text']=='Where can I find Flora before the next apostle hunt?')
        self.assertEqual(r['condition'],{'math':['u_berserk_first_hunt_done == 1']})
        self.assertEqual(r['effect'],{'run_eocs':'EOC_BERSERK_FLORA_DIRECTIONS'})
        self.assertNotIn('berserk_hunt_count',json.dumps(r))

    def test_sites_allow_mixed_field_and_forest_without_automatic_manor_creation(self):
        for path in ('local_breach','flora_manor','apostle_count','wyald_rosine_hunts','grunbeld_hunt'):
            for special in objects(MOD/f'overmap/{path}.json'):
                if special['type']!='overmap_special':continue
                for entry in [special]+special.get('overmaps',[]):
                    if 'locations' in entry:
                        self.assertNotEqual(entry['locations'],['forest'])
                self.assertEqual(special['occurrences'][0],0)
                # For GLOBALLY_UNIQUE, native worldgen treats min/max as a
                # probability; zero min suppresses spontaneous placement.

if __name__=='__main__':unittest.main()
