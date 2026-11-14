"""Run the new one-time branches using the dialogue and EOC models."""
import unittest

from test_godo_dialogue_33 import Conversation as Godot
from test_rickert_dialogue_33 import Conversation as Rickert
from test_recovery_33 import StateGraph, walk
from test_reference_journal_33 import Book, EOCS, RUSSIAN

P = 'EOC_BERSERK_'
G = 'TALK_BERSERK_GODO'
R = 'TALK_BERSERK_RICKERT'


class PlayerGuidance(unittest.TestCase):
    def test_each_new_body_hint_fires_on_gain_only(self):
        world = StateGraph()
        traits = set()
        for name, eoc in world.eocs.items():
            if not name.startswith(P + 'APOSTOL_'):
                continue
            for node in walk(eoc):
                branch = node.get('then')
                if not isinstance(branch, list) or not branch:
                    continue
                trait = branch[0].get('u_add_trait', '')
                if not isinstance(trait, str) or not trait.endswith('_FORM'):
                    continue
                if not any('u_message' in action for action in branch):
                    continue
                traits.add(trait)
                world.messages.clear()
                world.effect(node)
                world.effect(node)
                self.assertIn(trait, world.traits)
                self.assertEqual(len(world.messages), 1, trait)
                self.assertNotEqual(RUSSIAN.gettext(world.messages[0]), world.messages[0])
        self.assertEqual(len(traits), 13)

    def test_sealed_marks_distinguish_available_and_spent_finds(self):
        for boss, terrain in (
            ('count', 'berserk_count_dungeon'), ('wyald', 'berserk_wyald_ring'),
            ('rosine', 'berserk_rosine_nest'), ('grunbeld', 'berserk_grunbeld_crucible'),
        ):
            id_ = 'COUNT_REGISTER_SEAL' if boss == 'count' else boss.upper() + '_SEAL_COMMIT'
            hint = next(a for a in EOCS[P + id_]['effect']
                        if isinstance(a.get('then'), dict)
                        and a['then'].get('u_message', '').startswith('The breach is sealed.'))
            for flesh_issued in (0, 1):
                for relic_claimed in (0, 1):
                    with self.subTest(boss=boss, flesh_issued=flesh_issued, relic_claimed=relic_claimed):
                        world = Book()
                        world.om = terrain
                        world.values.update({
                            '_pos': (1, 0, 0),
                            'berserk_eclipse_era': 1,
                            'u_berserk_eclipse_rescue_state': 2,
                            f'berserk_hunt_{boss}_state': 4,
                            f'berserk_apostle_{boss}_dead': 1,
                            f'berserk_apostol_{boss}_flesh_issued': flesh_issued,
                            f'berserk_hunt_{boss}_reward_claimed': relic_claimed,
                        })
                        world.furniture[(1, 0, 0)] = f'f_berserk_{boss}_breach_sealed'
                        world.effect(hint)
                        self.assertEqual(len(world.messages), 1)
                        self.assertEqual(
                            world.messages[0]['u_message'] == RUSSIAN.gettext(hint['then']['u_message']),
                            not flesh_issued or (boss != 'count' and not relic_claimed),
                        )

    def test_forge_acknowledgments_require_the_event_and_the_player_reporting_it(self):
        godot, rickert = Godot(), Rickert()
        godot.overrides[P + 'GODO_AT_SMITH'] = True
        rickert.met()
        for model, topic, label, flag in (
            (godot, G, 'I made it back from the hunt.', 'u_berserk_first_hunt_done'),
            (godot, G, 'Flora’s home burned. I escaped.', 'u_berserk_flora_escaped'),
            (rickert, R, 'Flora’s home burned. I escaped.', 'u_berserk_flora_escaped'),
        ):
            def options():
                return [a for a in model.available(topic) if a['text'] == label]
            model.values[flag] = 0
            self.assertFalse(options())
            model.values[flag] = 1
            model.messages.clear()
            response, = options()
            self.assertEqual(response['topic'], topic)
            model.effect(response['effect'])
            self.assertEqual(len(model.messages), 1)
            self.assertFalse(options())

    def test_rickert_needs_a_fitted_arm_to_acknowledge_practice_once(self):
        f = Rickert()
        speaker = f.topics[R + '_ARM_HOLDS']['speaker_effect']
        branch = {'if': speaker['condition'], 'then': speaker['effect']}
        f.effect(branch)
        self.assertFalse(f.messages)
        f.bionics.add('bio_berserk_arm_cannon')
        f.effect(branch)
        f.effect(branch)
        self.assertEqual(len(f.messages), 1)
