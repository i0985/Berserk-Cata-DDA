"""Static regression checks for the Eclipse story and release catalogs.

These checks do not replace a playthrough with CDDA 0.I-1.  In particular,
they cannot determine combat behavior, teleport success, or saved-game loading.
"""

from __future__ import annotations

from collections import deque
import gettext
import json
from pathlib import Path
import unittest

from validate_mod_assets import ValidationError, validate_mapgen_update_effects


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods" / "Berserk"
STORY_EOC_PREFIX = "EOC_BERSERK_ECLIPSE_"


def objects(path: Path) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, list) else [value]


def references(value: object) -> set[str]:
    result: set[str] = set()
    if isinstance(value, list):
        for part in value:
            result.update(references(part))
    elif isinstance(value, dict):
        for key, part in value.items():
            if key in ("run_eocs", "true_eocs", "false_eocs", "effect_on_conditions"):
                if isinstance(part, str):
                    result.add(part)
                elif isinstance(part, list):
                    result.update(x for x in part if isinstance(x, str))
            result.update(references(part))
    return result


class EclipseFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.eocs = {}
        for path in (MOD / "effects").glob("*.json"):
            for obj in objects(path):
                if obj.get("type") == "effect_on_condition":
                    cls.eocs[obj["id"]] = obj

    def reachable(self, starting_id: str) -> set[str]:
        visited: set[str] = set()
        pending = [starting_id]
        while pending:
            current = pending.pop()
            if current in visited:
                continue
            self.assertIn(current, self.eocs)
            visited.add(current)
            pending.extend(references(self.eocs[current]) - visited)
        return visited

    def test_behelit_exit_and_both_endings_reach_world_era(self) -> None:
        behelit = objects(MOD / "items" / "behelit.json")[0]
        self.assertIn(
            "EOC_BERSERK_ECLIPSE_TRIAL_USE",
            behelit["use_action"]["effect_on_conditions"],
        )
        entry = self.reachable("EOC_BERSERK_ECLIPSE_TRIAL_USE")
        self.assertIn("EOC_BERSERK_ECLIPSE_TRIAL_ARRIVE", entry)
        self.assertIn("EOC_BERSERK_ECLIPSE_TRIAL_RETURN", entry)

        boss = objects(MOD / "monsters" / "griffith_eclipse.json")[0]
        victory = self.reachable(boss["death_function"]["eoc"])
        rescue = self.reachable("EOC_BERSERK_ECLIPSE_RESCUE_PREVENT_DEATH")
        for route in (victory, rescue):
            self.assertIn("EOC_BERSERK_ECLIPSE_RESCUE_RETURN", route)
            self.assertIn("EOC_BERSERK_ECLIPSE_AFTERMATH", route)
        aftermath = self.eocs["EOC_BERSERK_ECLIPSE_AFTERMATH"]
        self.assertIn("berserk_eclipse_era = 1", str(aftermath))

        # A completed trial must not reopen an altar whose rescue is one-shot.
        self.assertIn("u_berserk_eclipse_rescue_state == 2", str(self.eocs["EOC_BERSERK_ECLIPSE_TRIAL_USE"]))
        one_shot = self.eocs["EOC_BERSERK_ECLIPSE_RESCUE"]
        self.assertIn("u_berserk_eclipse_rescue_state == 0", str(one_shot["condition"]))
        prevent_death = self.eocs["EOC_BERSERK_ECLIPSE_RESCUE_PREVENT_DEATH"]
        self.assertIn("EOC_BERSERK_ECLIPSE_RESCUE_STABILIZE", references(prevent_death))

    def test_eclipse_eoc_links_and_post_event_spawns(self) -> None:
        for eoc_id, obj in self.eocs.items():
            if eoc_id.startswith(STORY_EOC_PREFIX):
                for ref in references(obj):
                    self.assertIn(ref, self.eocs, f"{eoc_id} references missing {ref}")
        era = self.eocs["EOC_BERSERK_ECLIPSE_ERA_ENTER_OMT"]
        self.assertEqual(era["required_event"], "avatar_enters_omt")
        self.assertIn("berserk_eclipse_era == 1", str(era["condition"]))
        self.assertIn("u_val('pos_z') == 0", str(era["condition"]))
        self.assertIn('"var_val": "berserk_era_omt_key"', json.dumps(era))

        # An object-valued mapgen_update silently passed the old asset checks,
        # then prevented this EOC from loading in CDDA 0.I-1.
        era_file = MOD / "effects" / "eclipse_era_eocs.json"
        validate_mapgen_update_effects(era_file, objects(era_file))
        with self.assertRaises(ValidationError):
            validate_mapgen_update_effects(era_file, [{
                "type": "effect_on_condition",
                "effect": {"mapgen_update": {"context_val": "unsupported"}},
            }])
        updates = {obj["update_mapgen_id"] for obj in objects(MOD / "mapgen" / "eclipse_era_spawns.json")}
        for direction in ("EAST", "WEST", "SOUTH", "NORTH"):
            helper = self.eocs[f"EOC_BERSERK_ECLIPSE_ERA_SEED_{direction}"]
            self.assertIn(helper["effect"]["mapgen_update"], updates)
            self.assertIn(helper["false_effect"]["then"]["mapgen_update"], updates)

        groups = {entry["id"]: entry for entry in objects(MOD / "monstergroups" / "eclipse_era_groups.json")}
        for group in groups.values():
            for choice in group["monsters"]:
                self.assertNotIn(choice["monster"], {
                    "mon_berserk_eclipse_elite", "mon_berserk_eclipse_griffith",
                    "mon_void_apostle", "mon_griffith_reborn", "mon_nosferatu_zodd",
                })

    def test_all_six_rooms_and_story_targets_are_reachable(self) -> None:
        specials = objects(MOD / "overmap" / "eclipse_dungeon.json")
        special = next(obj for obj in specials if obj.get("id") == "berserk_eclipse_dungeon_special_fixed")
        positions = {tile["overmap"]: tuple(tile["point"][:2]) for tile in special["overmaps"]}
        self.assertEqual(len(positions), 6)
        self.assertEqual(set(positions.values()), {(x, y) for x in range(2) for y in range(3)})

        traversable: set[tuple[int, int]] = set()
        story_targets: set[tuple[int, int]] = set()
        bodies: set[str] = set()
        for room in objects(MOD / "mapgen" / "eclipse_mapgen.json"):
            room_id = room["om_terrain"][0]
            x_omt, y_omt = positions[room_id]
            mapping = room["object"]
            rows = mapping["rows"]
            self.assertEqual(len(rows), 24)
            self.assertTrue(all(len(row) == 24 for row in rows))
            for y, row in enumerate(rows):
                for x, symbol in enumerate(row):
                    if symbol != "#":
                        traversable.add((24 * x_omt + x, 24 * y_omt + y))
            for item in mapping.get("place_item", []):
                if item["item"].startswith("berserk_eclipse_") and item["item"].endswith("_body"):
                    bodies.add(item["item"])
                    story_targets.add((24 * x_omt + item["x"], 24 * y_omt + item["y"]))
            for monster in mapping.get("place_monster", []):
                if monster.get("monster") == "mon_berserk_eclipse_griffith":
                    story_targets.add((24 * x_omt + monster["x"], 24 * y_omt + monster["y"]))
        self.assertEqual(len(bodies), 4)
        self.assertEqual(len(story_targets), 5)

        start = (11, 12)  # The entrance return seal.
        self.assertIn(start, traversable)
        reached = {start}
        pending = deque([start])
        while pending:
            x, y = pending.popleft()
            for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if nxt in traversable and nxt not in reached:
                    reached.add(nxt)
                    pending.append(nxt)
        self.assertEqual(reached, traversable)
        self.assertLessEqual(story_targets, reached)

    def test_eclipse_text_is_present_in_both_compiled_catalogs(self) -> None:
        paths = [
            *sorted((MOD / "effects").glob("eclipse_*.json")),
            MOD / "items" / "behelit.json",
            *sorted((MOD / "items").glob("eclipse_*.json")),
            MOD / "dialogue" / "skull_knight.json",
            *sorted((MOD / "monsters").glob("eclipse_*.json")),
            MOD / "monsters" / "griffith_eclipse.json",
            MOD / "overmap" / "eclipse_dungeon.json",
        ]
        fields = {"u_message", "u_query", "success_message", "fail_message",
                  "name", "description", "dynamic_line", "text", "menu_text"}
        messages: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, list):
                for part in value:
                    collect(part)
            elif isinstance(value, dict):
                for key, part in value.items():
                    if key in fields:
                        source = part if isinstance(part, str) else part.get("str") if isinstance(part, dict) else None
                        if isinstance(source, str):
                            messages.add(source)
                    collect(part)

        for path in paths:
            for obj in objects(path):
                collect(obj)
        self.assertGreaterEqual(len(messages), 45)
        for locale in ("ru", "zh_CN"):
            catalog = MOD / "lang" / "mo" / locale / "LC_MESSAGES" / "Berserk.mo"
            with catalog.open("rb") as stream:
                translation = gettext.GNUTranslations(stream)
            missing = [source for source in messages if translation.gettext(source) == source]
            self.assertFalse(missing, f"{locale} missing: {missing}")


if __name__ == "__main__":
    unittest.main()
