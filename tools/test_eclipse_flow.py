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
            if key in ("run_eocs", "true_eocs", "false_eocs", "effect_on_conditions", "u_run_monster_eocs"):
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

    def test_pre_eclipse_nether_encounters_are_lootable_projections(self) -> None:
        projections = {
            monster["id"]: monster
            for monster in objects(MOD / "monsters" / "apostle_projections.json")
        }
        expected = {
            "mon_berserk_projection_zodd": "mon_nosferatu_zodd",
            "mon_berserk_projection_griffith": "mon_griffith_reborn",
            "mon_berserk_projection_void": "mon_void_apostle",
        }
        self.assertEqual(set(projections), set(expected))
        group = objects(MOD / "monstergroups" / "monster_groups.json")[0]
        members = {entry["monster"] for entry in group["monsters"]}
        self.assertTrue(set(expected) <= members)
        self.assertTrue(set(expected.values()).isdisjoint(members))
        drops = objects(MOD / "monsterdrops" / "projection_drops.json")[0]
        self.assertIn(
            {"item": "berserk_behelit", "prob": 100}, drops["items"]
        )
        for projection_id, original_id in expected.items():
            monster = projections[projection_id]
            self.assertEqual(monster["copy-from"], original_id)
            self.assertEqual(monster["death_drops"], drops["id"])
            self.assertEqual(monster["death_function"]["corpse_type"], "NO_CORPSE")
            self.assertEqual(monster["regenerates"], 0)
            self.assertTrue((MOD / "monsters" / {
                "mon_nosferatu_zodd": "nosferatu_zodd.json",
                "mon_griffith_reborn": "griffith_reborn.json",
                "mon_void_apostle": "mon_void_apostle.json",
            }[original_id]).exists())

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

    def test_knight_waits_for_deliberate_farewell(self) -> None:
        knight = objects(MOD / "monsters" / "skull_knight_rescuer.json")[0]
        self.assertTrue({"CONVERSATION", "IMMOBILE", "PACIFIST"} <= set(knight["flags"]))
        self.assertEqual(knight["chat_topics"], ["TALK_BERSERK_SKULL_KNIGHT_AFTER"])

        aftermath = self.eocs["EOC_BERSERK_ECLIPSE_AFTERMATH"]
        spawn = next(effect for effect in aftermath["effect"] if "u_spawn_monster" in effect)
        self.assertEqual(spawn["u_spawn_monster"], knight["id"])
        self.assertNotIn("lifespan", spawn)
        self.assertIn("EOC_BERSERK_ECLIPSE_KNIGHT_ARRIVED", references(spawn))
        retry = self.eocs["EOC_BERSERK_ECLIPSE_KNIGHT_RETRY"]
        self.assertEqual(retry["recurrence"], "1 minute")
        self.assertIn("berserk_knight_waiting", str(retry["condition"]))
        self.assertNotIn("lifespan", retry["effect"])

        topics = {topic["id"]: topic for topic in objects(MOD / "dialogue" / "skull_knight.json")}
        after = topics["TALK_BERSERK_SKULL_KNIGHT_AFTER"]
        self.assertEqual(after["speaker_effect"]["effect"]["u_add_var"], "berserk_knight_spoken")
        self.assertTrue(all(response["topic"] in topics or response["topic"] == "TALK_DONE"
                            for topic in topics.values() for response in topic["responses"]))
        answers = {response["text"]: response for response in after["responses"]}
        self.assertEqual(answers["I need to go."]["topic"], "TALK_DONE")
        self.assertNotIn("effect", answers["I need to go."])
        farewell = answers["I have my answers. Farewell, Skull Knight."]
        self.assertIn("berserk_knight_spoken", str(farewell["condition"]))
        self.assertEqual(farewell["effect"][-1], {"npc_die": {"remove_from_creature_tracker": True}})

    def test_victory_releases_player_even_if_griffith_crossed_an_omt_boundary(self) -> None:
        griffith = objects(MOD / "monsters" / "griffith_eclipse.json")[0]
        self.assertIn("IMMOBILE", griffith["flags"])
        victory = self.eocs[griffith["death_function"]["eoc"]]
        self.assertIn("EOC_BERSERK_ECLIPSE_VICTORY", references(victory))
        victory = self.eocs["EOC_BERSERK_ECLIPSE_VICTORY"]
        self.assertNotIn("u_at_om_location", str(victory["condition"]))

        special = next(obj for obj in objects(MOD / "overmap" / "eclipse_dungeon.json")
                       if obj.get("id") == "berserk_eclipse_dungeon_special_fixed")
        room_ids = {tile["overmap"] for tile in special["overmaps"]}
        returned = self.eocs["EOC_BERSERK_ECLIPSE_RESCUE_RETURN"]
        for attempt in returned["effect"][1:]:
            self.assertEqual({part["u_at_om_location"] for part in
                              (attempt["if"].get("or") or attempt["if"]["and"][0]["or"])}, room_ids)
        commit = self.eocs["EOC_BERSERK_ECLIPSE_RESCUE_COMMIT_IF_RETURNED"]
        self.assertEqual({part["u_at_om_location"] for part in
                          commit["condition"]["and"][1]["not"]["or"]}, room_ids)

        for scene in ("EOC_BERSERK_ECLIPSE_VICTORY", "EOC_BERSERK_ECLIPSE_RESCUE_SCENE"):
            spawn = next(part for part in self.eocs[scene]["effect"] if "u_spawn_monster" in part)
            self.assertNotIn("indoor_only", spawn)

    def test_eclipse_marks_are_standalone_bionics(self) -> None:
        marks = objects(MOD / "bionics" / "eclipse_marks.json")
        self.assertEqual({mark["id"] for mark in marks},
                         {"bio_berserk_brand_of_sacrifice", "bio_berserk_lost_eye"})
        self.assertTrue(all(not mark.get("included", False) for mark in marks))

    def test_behelit_consumed_only_after_arrival_and_new_entrance_is_sealed(self) -> None:
        enter = self.eocs["EOC_BERSERK_ECLIPSE_TRIAL_ENTER"]
        arrive = self.eocs["EOC_BERSERK_ECLIPSE_TRIAL_ARRIVE"]
        self.assertNotIn("u_consume_item", str(enter))
        effects = arrive["effect"]
        self.assertIn("u_teleport", effects[0])
        self.assertEqual(effects[1]["if"], {"u_at_om_location": "berserk_eclipse_dungeon_entry"})
        self.assertEqual(effects[1]["then"][-1], {"u_consume_item": "berserk_behelit", "count": 1})
        self.assertIn("u_berserk_eclipse_behelit_spent = 1", str(effects[1]["then"]))
        self.assertIn("u_berserk_eclipse_behelit_spent == 1", str(self.eocs["EOC_BERSERK_ECLIPSE_TRIAL_EXIT"]))
        self.assertIn("f_berserk_eclipse_arrival_scar", str(enter))
        self.assertNotIn("f_berserk_eclipse_return_seal", str(objects(MOD / "mapgen" / "eclipse_mapgen.json")))
        self.assertIn("f_berserk_eclipse_escape_rift", str(objects(MOD / "mapgen" / "eclipse_palettes.json")))

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

    def test_eclipse_marks_and_night_hunt(self) -> None:
        bionics = {obj["id"]: obj for obj in objects(MOD / "bionics" / "eclipse_marks.json")}
        brand_id = "bio_berserk_brand_of_sacrifice"
        eye_id = "bio_berserk_lost_eye"
        self.assertEqual(set(bionics), {brand_id, eye_id})
        self.assertEqual(
            bionics[eye_id]["enchantments"][0]["values"],
            [{"value": "PERCEPTION", "multiply": -0.5}],
        )
        self.assertIn("EOC_BERSERK_ECLIPSE_INSTALL_MARKS", references(self.eocs["EOC_BERSERK_ECLIPSE_AFTERMATH"]))
        install = self.eocs["EOC_BERSERK_ECLIPSE_INSTALL_MARKS"]
        self.assertIn(brand_id, str(install))
        self.assertIn(eye_id, str(install))
        migration = self.eocs["EOC_BERSERK_ECLIPSE_RESTORE_OLD_SAVE_MARKS"]
        self.assertEqual(migration["recurrence"], "1 minute")
        self.assertIn("u_berserk_eclipse_rescue_state == 2", str(migration["condition"]))
        self.assertIn("EOC_BERSERK_ECLIPSE_INSTALL_MARKS", references(migration))

        hunt = self.eocs["EOC_BERSERK_BRAND_NIGHT_HUNT"]
        self.assertEqual(hunt["recurrence"], "1 hour")
        self.assertIn({"not": "is_day"}, hunt["condition"]["and"])
        spawn = hunt["effect"][1]["then"]
        self.assertEqual(spawn["real_count"], 1)
        self.assertEqual((spawn["min_radius"], spawn["max_radius"]), (20, 30))
        self.assertTrue(spawn["outdoor_only"])
        self.assertIn("EOC_BERSERK_BRAND_DEMON_ARRIVAL", references(spawn))
        for eoc_id in ("EOC_BERSERK_BRAND_DEMON_SCAN", "EOC_BERSERK_BRAND_POWERFUL_SCAN"):
            for ref in references(self.eocs[eoc_id]):
                self.assertIn(ref, self.eocs)
        self.assertEqual(self.eocs["EOC_BERSERK_BRAND_POWERFUL_SCAN"]["effect"]["monster_range"], 40)
        for eoc_id in ("EOC_BERSERK_BRAND_ORDINARY_WARNING", "EOC_BERSERK_BRAND_POWERFUL_WARNING"):
            self.assertIn("u_pain()", str(self.eocs[eoc_id]))

    def test_arm_cannon_item_installs_only_on_missing_hand(self) -> None:
        items = {obj["id"]: obj for obj in objects(MOD / "items" / "bionics" / "arm_cannon_cbms.json")}
        action = items["bio_berserk_arm_cannon"]["use_action"]
        self.assertEqual(action["type"], "effect_on_conditions")
        self.assertEqual(action["effect_on_conditions"], ["EOC_BERSERK_ARM_CANNON_SELF_INSTALL"])
        install = self.eocs[action["effect_on_conditions"][0]]
        self.assertIn({"u_has_bionics": "bio_berserk_hand_stump"}, install["condition"]["and"])
        self.assertIn({"not": {"u_has_bionics": "bio_berserk_arm_cannon"}}, install["condition"]["and"])
        self.assertIn({"u_has_items": {"item": "bio_berserk_arm_cannon", "count": 1}}, install["condition"]["and"])
        self.assertEqual(install["effect"][:2], [
            {"u_consume_item": "bio_berserk_arm_cannon", "count": 1},
            {"u_add_bionic": "bio_berserk_arm_cannon"},
        ])
        self.assertNotIn("use_action", items["bio_berserk_hand_stump"])

    def test_all_six_rooms_and_story_targets_are_reachable(self) -> None:
        specials = objects(MOD / "overmap" / "eclipse_dungeon.json")
        special = next(obj for obj in specials if obj.get("id") == "berserk_eclipse_dungeon_special_fixed")
        positions = {tile["overmap"]: tuple(tile["point"][:2]) for tile in special["overmaps"]}
        self.assertEqual(len(positions), 6)
        self.assertEqual(set(positions.values()), {(x, y) for x in range(2) for y in range(3)})

        traversable: set[tuple[int, int]] = set()
        safe: set[tuple[int, int]] = set()
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
                    if symbol not in ("#", "P"):
                        safe.add((24 * x_omt + x, 24 * y_omt + y))
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

        # Both columns offer safe middle routes, even if one column is closed.
        finale = (24 + 13, 48 + 12)
        for blocked_column in (0, 1):
            permitted = {
                p for p in safe
                if not (24 <= p[1] < 48 and p[0] // 24 == blocked_column)
            }
            visited = {start}
            pending = deque([start])
            while pending:
                x, y = pending.popleft()
                for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if nxt in permitted and nxt not in visited:
                        visited.add(nxt)
                        pending.append(nxt)
            self.assertIn(finale, visited, f"blocked middle column {blocked_column}")

        placed = {
            item["item"]
            for room in objects(MOD / "mapgen" / "eclipse_mapgen.json")
            for item in room["object"].get("place_item", [])
        }
        self.assertTrue({"berserk_judeau_knife_hilt", "berserk_pippin_broken_clasp"} <= placed)

    def test_eclipse_text_is_present_in_both_compiled_catalogs(self) -> None:
        paths = [
            *sorted((MOD / "effects").glob("eclipse_*.json")),
            MOD / "effects" / "arm_cannon_install_eocs.json",
            MOD / "effects" / "arm_cannon_recipe_eoc.json",
            MOD / "effects" / "brand_cooldowns.json",
            MOD / "bionics" / "arm_cannon.json",
            MOD / "bionics" / "eclipse_marks.json",
            MOD / "items" / "bionics" / "arm_cannon_cbms.json",
            MOD / "items" / "behelit.json",
            *sorted((MOD / "items").glob("eclipse_*.json")),
            MOD / "furniture" / "eclipse_trial.json",
            MOD / "mapgen" / "eclipse_palettes.json",
            MOD / "dialogue" / "skull_knight.json",
            *sorted((MOD / "monsters").glob("eclipse_*.json")),
            MOD / "monsters" / "griffith_eclipse.json",
            MOD / "overmap" / "eclipse_dungeon.json",
        ]
        fields = {"u_message", "u_query", "success_message", "fail_message",
                  "name", "description", "desc", "cant_remove_reason",
                  "dynamic_line", "text", "menu_text"}
        messages: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, list):
                for part in value:
                    collect(part)
            elif isinstance(value, dict):
                for key, part in value.items():
                    if key in fields:
                        sources = [part] if isinstance(part, str) else (
                            [part.get("str")] if isinstance(part, dict) else part if isinstance(part, list) else []
                        )
                        messages.update(source for source in sources if isinstance(source, str))
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
