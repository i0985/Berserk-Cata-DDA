"""Static integrity checks for the Behelit encounter maps in CDDA 0.I-1.

These checks do not simulate the game's mapgen, monster AI, or furniture EOCs.
"""

import json
from collections import deque
import gettext
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods" / "Berserk"


def objects(path):
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, list) else [value]


def reachable(rows, start, target):
    queue = deque([start])
    visited = {start}
    while queue:
        x, y = queue.popleft()
        if abs(x - target[0]) + abs(y - target[1]) == 1:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < 24 and 0 <= ny < 24 and (nx, ny) not in visited:
                if rows[ny][nx] not in "#T":
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return False


class BehelitSiteTests(unittest.TestCase):
    def test_new_user_facing_text_has_both_translations(self):
        messages = set()
        plurals = set()
        for folder, filename in (("overmap", "behelit_sites.json"),
                                 ("monsters", "behelit_site_guardians.json"),
                                 ("furniture", "behelit_sites.json"),
                                 ("monster_special_attacks", "behelit_site_attacks.json"),
                                 ("effects", "behelit_site_eocs.json")):
            for obj in objects(MOD / folder / filename):
                def collect(value):
                    if isinstance(value, list):
                        for child in value:
                            collect(child)
                    elif isinstance(value, dict):
                        for key, child in value.items():
                            if key in {"name", "description", "u_message", "u_make_sound", "hit_dmg_u", "hit_dmg_npc",
                                       "miss_msg_u", "miss_msg_npc"}:
                                if isinstance(child, str):
                                    messages.add(child)
                                elif isinstance(child, dict) and "str" in child:
                                    messages.add(child["str"])
                                    if "str_pl" in child:
                                        plurals.add((child["str"], child["str_pl"]))
                            collect(child)
                collect(obj)
        for locale in ("ru", "zh_CN"):
            path = MOD / "lang" / "mo" / locale / "LC_MESSAGES" / "Berserk.mo"
            with path.open("rb") as stream:
                catalog = gettext.GNUTranslations(stream)
            self.assertFalse({m for m in messages if catalog.gettext(m) == m}, locale)
            for singular, plural in plurals:
                self.assertNotEqual(catalog.ngettext(singular, plural, 1), singular)

    def test_cave_stairs_and_both_relics_are_reachable(self):
        maps = {m["om_terrain"][0]: m["object"] for m in objects(MOD / "mapgen" / "behelit_sites.json") if "om_terrain" in m}
        for mapgen in maps.values():
            self.assertEqual(len(mapgen["rows"]), 24)
            self.assertTrue(all(len(row) == 24 for row in mapgen["rows"]))
            for monster in mapgen.get("place_monster", []):
                self.assertNotIn(mapgen["rows"][monster["y"]][monster["x"]], "#T")

        oak = maps["berserk_cursed_oak"]["rows"]
        surface = maps["berserk_echo_cave_entrance"]["rows"]
        cave = maps["berserk_echo_cave_depth"]["rows"]
        self.assertEqual(oak[12][12], "A")
        self.assertEqual(surface[12][12], "V")
        self.assertEqual(cave[12][12], "U")
        self.assertEqual(cave[5][12], "A")
        self.assertTrue(reachable(oak, (1, 12), (12, 12)))
        self.assertTrue(reachable(surface, (12, 23), (12, 12)))
        self.assertTrue(reachable(cave, (12, 12), (12, 5)))

    def test_guardians_only_spawn_on_their_encounter_maps(self):
        guardians = {m["id"] for m in objects(MOD / "monsters" / "behelit_site_guardians.json")}
        maps = objects(MOD / "mapgen" / "behelit_sites.json")
        placed = {entry["monster"] for m in maps if "om_terrain" in m for entry in m["object"].get("place_monster", [])}
        self.assertEqual(guardians, placed & guardians)
        for folder in ("monstergroups", "effects"):
            for path in (MOD / folder).glob("*.json"):
                if path.name == "behelit_site_eocs.json":
                    continue
                self.assertTrue(guardians.isdisjoint(path.read_text(encoding="utf-8").split('"')),
                                f"guardian appears in {path}")

    def test_claim_requires_guardian_absence_and_empties_local_relic(self):
        eocs = {e["id"]: e for e in objects(MOD / "effects" / "behelit_site_eocs.json")}
        updates = {m["update_mapgen_id"]: m for m in objects(MOD / "mapgen" / "behelit_sites.json") if "update_mapgen_id" in m}
        furniture = {f["id"]: f for f in objects(MOD / "furniture" / "behelit_sites.json")}
        for name, guardian, x, y in (("oak", "mon_berserk_cursed_oak_guardian", 12, 12),
                                     ("cave", "mon_berserk_echo_cave_guardian", 12, 5)):
            relic = furniture[f"f_berserk_{name}_relic"]
            eoc = eocs[relic["examine_action"]["effect_on_conditions"][0]]
            scan = next(effect for effect in eoc["effect"] if "u_run_monster_eocs" in effect)
            self.assertEqual(scan["mtype_ids"], [guardian])
            result = next(effect["then"] for effect in eoc["effect"] if "if" in effect)
            self.assertEqual(result[0]["mapgen_update"], f"berserk_{name}_relic_taken")
            self.assertEqual(result[1]["u_spawn_item"], "berserk_behelit")
            self.assertEqual(updates[result[0]["mapgen_update"]]["object"]["set"],
                             [{"point": "furniture", "id": f"f_berserk_{name}_relic_empty", "x": x, "y": y}])
            self.assertNotIn("examine_action", furniture[f"f_berserk_{name}_relic_empty"])


if __name__ == "__main__":
    unittest.main()
