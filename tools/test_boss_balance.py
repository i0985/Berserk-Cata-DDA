"""Guard against inherited boss mechanics making lab projections unbeatable."""

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "mods" / "Berserk"


def load(relative):
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


class BossBalanceTests(unittest.TestCase):
    def test_projections_replace_heavy_attack_lists_and_do_not_regenerate(self):
        originals = {
            "mon_nosferatu_zodd": load("monsters/nosferatu_zodd.json")[0],
            "mon_griffith_reborn": load("monsters/griffith_reborn.json")[0],
            "mon_void_apostle": load("monsters/mon_void_apostle.json")[0],
        }
        for projection in load("monsters/apostle_projections.json"):
            with self.subTest(projection=projection["id"]):
                original = originals[projection["copy-from"]]
                self.assertLess(projection["hp"], original["hp"])
                self.assertLess(projection["melee_skill"], original["melee_skill"])
                self.assertEqual(projection["regenerates"], 0)
                self.assertIn("special_attacks", projection)
                self.assertEqual(len(projection["special_attacks"]), 1)
                self.assertNotEqual(projection["special_attacks"], original["special_attacks"])
                self.assertEqual(projection["death_drops"], "berserk_projection_behelit_drops")

    def test_originals_and_story_griffith_do_not_recover_in_combat(self):
        for relative in ("monsters/nosferatu_zodd.json", "monsters/griffith_reborn.json",
                         "monsters/mon_void_apostle.json", "monsters/griffith_eclipse.json"):
            with self.subTest(file=relative):
                self.assertEqual(load(relative)[0]["regenerates"], 0)

    def test_vanilla_comparable_hp_and_story_victory_hook(self):
        zodd = load("monsters/nosferatu_zodd.json")[0]
        eclipse = load("monsters/griffith_eclipse.json")[0]
        self.assertLessEqual(zodd["hp"], 600)
        self.assertLessEqual(eclipse["hp"], 480)
        self.assertEqual(eclipse["death_function"]["eoc"],
                         "EOC_BERSERK_ECLIPSE_GRIFFITH_DIES")


if __name__ == "__main__":
    unittest.main()
