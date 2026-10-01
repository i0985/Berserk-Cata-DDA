"""Exercise the reward graph with a small data interpreter, without CDDA.

This covers state, talker changes, cache coordinates and duplicate rewards.
It does not validate CDDA's JSON loader, AI, map persistence or rendering.
"""

import copy
import json
from pathlib import Path
import re
import unittest


MOD = Path(__file__).resolve().parents[1] / "mods" / "Berserk"


def objects(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, list) else [value]


class RewardGraph:
    def __init__(self, flags=None):
        self.eocs = {obj["id"]: obj for path in (MOD / "effects").glob("behelit_*eocs.json")
                     for obj in objects(path)}
        self.updates = {obj["update_mapgen_id"]: obj["object"]["set"]
                        for obj in objects(MOD / "mapgen" / "behelit_sites.json")
                        if "update_mapgen_id" in obj}
        self.flags = dict(flags or {})
        self.context = {}
        self.furniture = {}
        self.monsters = []
        self.inventory = []
        self.ground = []
        self.avatar = (0, 0, 0)
        self.victim = None
        self.alpha = "avatar"
        self.fail_updates = False

    def variable(self, name):
        if name.startswith("u_") and self.alpha != "avatar":
            raise AssertionError("player state read from the wrong death talker")
        return self.flags.get(name, 0)

    def resolve(self, value):
        return self.context[value["context_val"]] if isinstance(value, dict) else value

    def condition(self, value):
        if "and" in value:
            return all(self.condition(v) for v in value["and"])
        if "test_eoc" in value:
            return self.condition(self.eocs[value["test_eoc"]]["condition"])
        if "math" in value:
            name, expected = value["math"][0].split(" == ")
            return self.variable(name) == int(expected)
        if "map_furniture_id" in value:
            return self.furniture.get(self.resolve(value["loc"])) == self.resolve(value["map_furniture_id"])
        raise AssertionError(f"Unsupported condition: {value}")

    def run(self, id):
        obj = self.eocs[id]
        if "condition" not in obj or self.condition(obj["condition"]):
            self.effect(obj["effect"])

    def effect(self, value):
        if isinstance(value, list):
            for child in value:
                self.effect(child)
        elif "if" in value:
            branch = "then" if self.condition(value["if"]) else "else"
            if branch in value:
                self.effect(value[branch])
        elif "run_eocs" in value:
            context, alpha = self.context, self.alpha
            self.context = dict(context, **value.get("variables", {}))
            self.alpha = value.get("alpha_talker", alpha)
            self.run(self.resolve(value["run_eocs"]))
            self.context, self.alpha = context, alpha
        elif "npc_location_variable" in value:
            self.context[value["npc_location_variable"]["context_val"]] = self.victim
        elif "math" in value:
            name, op, number = re.fullmatch(r"(\w+) (=|\+=) (\d+)", value["math"][0]).groups()
            self.flags[name] = int(number) + (self.variable(name) if op == "+=" else 0)
        elif "u_run_monster_eocs" in value:
            ids = [self.resolve(id) for id in value["mtype_ids"]]
            for id, pos in self.monsters:
                if id in ids and pos[2] == self.avatar[2] and max(abs(pos[i] - self.avatar[i]) for i in (0, 1)) <= value["monster_range"]:
                    for eoc in value["u_run_monster_eocs"]:
                        self.run(eoc)
        elif "mapgen_update" in value:
            if not self.fail_updates:
                pos = self.resolve(value["target_var"])
                for change in self.updates[value["mapgen_update"]]:
                    location = (pos[0] // 24 * 24 + change["x"],
                                pos[1] // 24 * 24 + change["y"], pos[2])
                    self.furniture[location] = change["id"]
        elif "map_spawn_item" in value:
            self.ground.append((value["map_spawn_item"], self.resolve(value["loc"])))
        elif "u_spawn_item" in value:
            self.inventory.append(value["u_spawn_item"])
        elif "u_message" not in value:
            raise AssertionError(f"Unsupported effect: {value}")

    def cache(self, name, origin=(0, 0, 0)):
        update = self.updates[f"berserk_{name}_relic_taken"][0]
        pos = (origin[0] + update["x"], origin[1] + update["y"], origin[2])
        self.furniture[pos] = f"f_berserk_{name}_relic"
        self.context = {"pos": pos}
        self.avatar = (pos[0] - 1, pos[1], pos[2])
        return pos


class BehelitRewards(unittest.TestCase):
    def test_absent_old_save_variables_allow_all_sources(self):
        for name in ("oak", "cave", "chapel", "expedition"):
            graph = RewardGraph()
            pos = graph.cache(name)
            graph.run(f"EOC_BERSERK_CLAIM_{name.upper()}_BEHELIT")
            self.assertEqual(graph.inventory, ["berserk_behelit"])
            self.assertEqual(graph.furniture[pos], f"f_berserk_{name}_relic_empty")

    def test_every_eclipse_state_blocks_bosses_and_unopened_caches(self):
        for flags in ({"berserk_eclipse_era": 1},
                      {"u_berserk_eclipse_behelit_spent": 1},
                      {"u_berserk_eclipse_trial_active": 1},
                      {"u_berserk_eclipse_rescue_state": 1},
                      {"u_berserk_eclipse_rescue_state": 2}):
            for name in ("oak", "cave", "chapel", "expedition"):
                with self.subTest(flags=flags, site=name):
                    graph = RewardGraph(flags)
                    graph.inventory = ["berserk_behelit"]  # old loot is preserved
                    pos = graph.cache(name)
                    graph.run(f"EOC_BERSERK_CLAIM_{name.upper()}_BEHELIT")
                    graph.run(f"EOC_BERSERK_CLAIM_{name.upper()}_BEHELIT")
                    self.assertEqual(graph.inventory, ["berserk_behelit"])
                    self.assertEqual(graph.furniture[pos], f"f_berserk_{name}_relic_empty")
            graph = RewardGraph(flags)
            graph.victim = (71, -15, 0)
            graph.alpha = None
            graph.run("EOC_BERSERK_BEHELIT_BOSS_DIES")
            self.assertFalse(graph.ground)

    def test_guard_at_eight_tiles_blocks_but_nine_tiles_allows(self):
        for name in ("oak", "cave", "chapel", "expedition"):
            graph = RewardGraph()
            graph.cache(name)
            wrapper = graph.eocs[f"EOC_BERSERK_CLAIM_{name.upper()}_BEHELIT"]
            guardian = wrapper["effect"]["variables"]["berserk_site_guardian"]
            x, y, z = graph.avatar
            graph.monsters = [(guardian, (x + 8, y, z))]
            graph.run(wrapper["id"])
            self.assertFalse(graph.inventory)
            graph.monsters = [(guardian, (x + 9, y, z))]
            graph.run(wrapper["id"])
            self.assertEqual(graph.inventory, ["berserk_behelit"])

    def test_failed_update_cannot_award_item_and_retry_works(self):
        graph = RewardGraph()
        pos = graph.cache("cave")
        graph.fail_updates = True
        graph.run("EOC_BERSERK_CLAIM_CAVE_BEHELIT")
        self.assertFalse(graph.inventory)
        self.assertEqual(graph.furniture[pos], "f_berserk_cave_relic")
        graph.fail_updates = False
        graph.run("EOC_BERSERK_CLAIM_CAVE_BEHELIT")
        self.assertEqual(graph.inventory, ["berserk_behelit"])

    def test_old_chapel_and_camp_guardians_still_block_claim(self):
        for name in ('chapel', 'expedition'):
            graph = RewardGraph()
            graph.cache(name)
            wrapper = graph.eocs[f'EOC_BERSERK_CLAIM_{name.upper()}_BEHELIT']
            legacy = wrapper['effect']['variables']['berserk_site_legacy_guardian']
            self.assertNotEqual(legacy,wrapper['effect']['variables']['berserk_site_guardian'])
            x,y,z = graph.avatar
            graph.monsters = [(legacy,(x+8,y,z))]
            graph.run(wrapper['id'])
            self.assertFalse(graph.inventory)
            graph.monsters = [(legacy,(x+9,y,z))]
            graph.run(wrapper['id'])
            self.assertEqual(graph.inventory,['berserk_behelit'])

    def test_local_cache_state_survives_reload_and_does_not_block_other_sites(self):
        graph = RewardGraph()
        graph.cache("oak")
        graph.run("EOC_BERSERK_CLAIM_OAK_BEHELIT")
        graph = copy.deepcopy(graph)  # persisted furniture and player state
        graph.run("EOC_BERSERK_CLAIM_OAK_BEHELIT")
        self.assertEqual(graph.inventory, ["berserk_behelit"])
        graph.cache("chapel", (24, 24, 0))
        graph.run("EOC_BERSERK_CLAIM_CHAPEL_BEHELIT")
        self.assertEqual(graph.inventory, ["berserk_behelit", "berserk_behelit"])

    def test_update_targets_cache_even_if_avatar_is_in_neighboring_omt(self):
        graph = RewardGraph()
        pos = graph.cache("oak", (24, 0, 0))
        graph.avatar = (23, pos[1], 0)
        graph.run("EOC_BERSERK_CLAIM_OAK_BEHELIT")
        self.assertEqual(graph.furniture[pos], "f_berserk_oak_relic_empty")
        self.assertNotIn((12, 12, 0), graph.furniture)

    def test_boss_drop_is_on_victim_for_any_killer(self):
        for killer in ("avatar", "zombie", "npc", None):
            graph = RewardGraph()
            graph.victim = (71, -15, 0)
            graph.alpha = killer
            graph.run("EOC_BERSERK_BEHELIT_BOSS_DIES")
            self.assertEqual(graph.ground, [("berserk_behelit", graph.victim)])
            self.assertFalse(graph.inventory)

    def test_no_unconditional_behelit_loot_remains(self):
        for path in MOD.rglob("*.json"):
            for obj in objects(path):
                if obj["type"] in ("item_group", "mapgen"):
                    self.assertNotIn('"berserk_behelit"', json.dumps(obj), str(path))
        for filename in ("nosferatu_zodd.json", "griffith_reborn.json", "mon_void_apostle.json", "apostle_projections.json"):
            for monster in objects(MOD / "monsters" / filename):
                expected = "EOC_BERSERK_FLORA_LEGACY_ZODD_DIES" if monster["id"] == "mon_nosferatu_zodd" else "EOC_BERSERK_BEHELIT_BOSS_DIES"
                self.assertEqual(monster["death_function"]["eoc"], expected)
        for filename in ("griffith_eclipse.json", "griffith_eclipse_active.json"):
            self.assertEqual(objects(MOD / "monsters" / filename)[0]["death_function"]["eoc"],
                             "EOC_BERSERK_ECLIPSE_GRIFFITH_DIES")


if __name__ == "__main__":
    unittest.main()
