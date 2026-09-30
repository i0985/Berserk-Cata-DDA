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
        self.assertEqual(drops["items"], [])
        for projection_id, original_id in expected.items():
            monster = projections[projection_id]
            self.assertEqual(monster["copy-from"], original_id)
            self.assertEqual(monster["death_drops"], drops["id"])
            self.assertEqual(monster["death_function"]["corpse_type"], "NO_CORPSE")
            self.assertEqual(monster["death_function"]["eoc"], "EOC_BERSERK_BEHELIT_BOSS_DIES")
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
        expanded = next(obj for obj in objects(MOD / "overmap" / "eclipse_expanded.json")
                        if obj.get("id") == "berserk_eclipse_expanded_special")
        room_ids.update(tile["overmap"] for tile in expanded["overmaps"])
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
        self.assertEqual({part["u_at_om_location"] for part in effects[1]["if"]["or"]},
                         {"berserk_eclipse_dungeon_entry", "berserk_eclipse_expanded_arrival"})
        self.assertIn({"u_consume_item": "berserk_behelit", "count": 1}, effects[1]["then"])
        self.assertIn("u_berserk_eclipse_behelit_spent = 1", str(effects[1]["then"]))
        self.assertIn("u_berserk_eclipse_behelit_spent == 1", str(self.eocs["EOC_BERSERK_ECLIPSE_TRIAL_EXIT"]))
        self.assertIn("f_berserk_eclipse_arrival_scar", str(enter))
        self.assertIn("berserk_eclipse_expanded_special", str(enter))
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
        ward_search = hunt["effect"]
        self.assertEqual(ward_search["furniture"], "f_berserk_shelter_ward")
        self.assertEqual(ward_search["target_max_radius"], 8)
        self.assertNotIn("true_eocs", ward_search)
        self.assertEqual(ward_search["false_eocs"], ["EOC_BERSERK_BRAND_NIGHT_HUNT_UNSHELTERED"])
        unsheltered = self.eocs["EOC_BERSERK_BRAND_NIGHT_HUNT_UNSHELTERED"]
        self.assertIn("berserk_local_breach", str(unsheltered))
        self.assertIn("x_in_y_chance", str(unsheltered))
        spawn = self.eocs["EOC_BERSERK_BRAND_NIGHT_HUNT_SPAWN"]["effect"][1]["then"]
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

    def test_arrival_visual_trial_screens_sight_and_keeps_two_safe_routes(self) -> None:
        entry = next(room["object"] for room in objects(MOD / "mapgen" / "eclipse_mapgen.json")
                     if room["om_terrain"] == ["berserk_eclipse_dungeon_entry"])
        rows = entry["rows"]
        palette = next(obj for obj in objects(MOD / "mapgen" / "eclipse_palettes.json")
                       if obj["type"] == "palette")
        self.assertEqual(rows[12][11], "S")
        self.assertEqual(rows[12][20], "#")  # No direct line of sight to the eastern edge.
        self.assertEqual({"a", "r", "v"}, set("".join(rows)) & {"a", "r", "v"})
        self.assertEqual(palette["terrain"]["#"], "t_berserk_eclipse_ridge")
        self.assertEqual(palette["terrain"]["v"], "t_berserk_eclipse_dim_vein")

        def can_reach_east(via_north: bool) -> bool:
            start = (11, 12)
            destination = (23, 12)
            queue = deque([start])
            visited = {start}
            while queue:
                x, y = queue.popleft()
                if (x, y) == destination:
                    return True
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if not 0 <= nx < 24 or not 0 <= ny < 24 or (nx, ny) in visited:
                        continue
                    if rows[ny][nx] in "#PC":
                        continue
                    if 18 <= nx <= 20 and (ny >= 11 if via_north else ny <= 14):
                        continue
                    visited.add((nx, ny))
                    queue.append((nx, ny))
            return False

        self.assertTrue(can_reach_east(via_north=True))
        self.assertTrue(can_reach_east(via_north=False))

    def test_expanded_eclipse_has_a_walkable_story_route_and_old_special_remains(self) -> None:
        from build_eclipse_expanded import build_scene, scene_id

        specials = objects(MOD / "overmap" / "eclipse_expanded.json")
        special = next(entry for entry in specials if entry["type"] == "overmap_special")
        positions = {tile["overmap"]: tuple(tile["point"][:2]) for tile in special["overmaps"]}
        self.assertEqual(len(positions), 12)
        self.assertEqual(set(positions.values()), {(x, y) for x in range(3) for y in range(4)})
        self.assertEqual(special["id"], "berserk_eclipse_expanded_special")
        self.assertIn("berserk_eclipse_dungeon_special_fixed",
                      {entry["id"] for entry in objects(MOD / "overmap" / "eclipse_dungeon.json")})

        rooms = objects(MOD / "mapgen" / "eclipse_expanded.json")
        self.assertEqual(rooms, [build_scene(x, y) for y in range(4) for x in range(3)])
        safe: set[tuple[int, int]] = set()
        markers = {}
        enemies = 0
        for room in rooms:
            ox, oy = positions[room["om_terrain"][0]]
            rows = room["object"]["rows"]
            self.assertEqual(len(rows), 24)
            self.assertTrue(all(len(row) == 24 for row in rows))
            for y, row in enumerate(rows):
                for x, symbol in enumerate(row):
                    point = (ox * 24 + x, oy * 24 + y)
                    if symbol not in "#PC":
                        safe.add(point)
                    if symbol in "SIJKGWFRXH":
                        self.assertNotIn(symbol, markers)
                        markers[symbol] = point
            for enemy in room["object"].get("place_monster", []):
                point = (ox * 24 + enemy["x"], oy * 24 + enemy["y"])
                self.assertIn(point, safe, room["om_terrain"][0])
                enemies += 1
        self.assertEqual(set(markers), set("SIJKGWFRXH"))
        self.assertEqual(enemies, 40)
        self.assertGreater(markers["R"][0] + markers["R"][1], 100)
        self.assertEqual(markers["S"], (11, 12))
        reached = {markers["S"]}
        pending = deque(reached)
        while pending:
            x, y = pending.popleft()
            for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if neighbor in safe and neighbor not in reached:
                    reached.add(neighbor)
                    pending.append(neighbor)
        self.assertEqual(reached, safe)
        self.assertLessEqual(set(markers.values()), reached)

        boss = objects(MOD / "monsters" / "griffith_eclipse_active.json")[0]
        self.assertNotIn("IMMOBILE", boss["flags"])
        self.assertEqual(boss["death_function"]["eoc"], "EOC_BERSERK_ECLIPSE_GRIFFITH_DIES")
        self.assertIn("mon_berserk_eclipse_griffith_active",
                      str(objects(MOD / "mod_tileset_griffith.json")))
        for rescue_id in ("EOC_BERSERK_ECLIPSE_RESCUE_THRESHOLD",
                          "EOC_BERSERK_ECLIPSE_RESCUE_PREVENT_DEATH"):
            condition = self.eocs[rescue_id]["condition"]
            self.assertIn("berserk_eclipse_expanded_ceremony", str(condition))
            self.assertIn("u_berserk_eclipse_final_started == 1", str(condition))
            self.assertTrue(set(positions) <= {part["u_at_om_location"]
                             for part in condition["and"][0]["or"][1]["and"][1]["or"]})
        finale = self.eocs["EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_START"]
        self.assertEqual(finale["required_event"], "avatar_enters_omt")
        self.assertIn("u_berserk_eclipse_final_started != 1", str(finale["condition"]))
        self.assertEqual(finale["effect"]["monster"], boss["id"])
        self.assertEqual(finale["effect"]["false_eocs"],
                         ["EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_SPAWN"])
        spawn = self.eocs["EOC_BERSERK_ECLIPSE_EXPANDED_FINAL_SPAWN"]
        self.assertIn("berserk_eclipse_griffith_on_entry", str(spawn))
        update = objects(MOD / "mapgen" / "eclipse_griffith_on_entry.json")[0]
        self.assertEqual(update["object"]["place_monster"][0]["monster"], boss["id"])
        self.assertEqual((update["object"]["place_monster"][0]["x"],
                          update["object"]["place_monster"][0]["y"]), (15, 17))

    def test_first_hunt_is_reachable_and_unique_without_pre_event_spawn(self) -> None:
        special = next(obj for obj in objects(MOD / "overmap" / "first_hunt.json")
                       if obj["type"] == "overmap_special")
        self.assertEqual(special["occurrences"], [0, 0])
        hunt = self.eocs["EOC_BERSERK_FIRST_HUNT_FIND"]
        self.assertIn("berserk_eclipse_era == 1", str(hunt["condition"]))
        self.assertIn("u_berserk_first_hunt_marked != 1", str(hunt["condition"]))
        self.assertEqual(hunt["effect"]["target_params"]["om_special"], special["id"])
        self.assertEqual(hunt["effect"]["true_eocs"], ["EOC_BERSERK_FIRST_HUNT_FOUND"])
        self.assertIn("u_berserk_first_hunt_marked = 1",
                      str(self.eocs["EOC_BERSERK_FIRST_HUNT_FOUND"]))
        room = objects(MOD / "mapgen" / "first_hunt.json")[0]["object"]
        self.assertEqual(len(room["rows"]), 24)
        self.assertTrue(all(len(row) == 24 for row in room["rows"]))
        boss = objects(MOD / "monsters" / "first_hunt_apostle.json")[0]
        self.assertEqual(sum(mon["monster"] == boss["id"] for mon in
                             room["place_monster"]), 1)
        self.assertEqual(boss["hp"], 290)
        self.assertIn("EOC_BERSERK_FIRST_HUNT_COMPLETE",
                      references(self.eocs[boss["death_function"]["eoc"]]))
        self.assertIn("u_berserk_first_hunt_done != 1",
                      str(self.eocs["EOC_BERSERK_FIRST_HUNT_COMPLETE"]["condition"]))

    def test_breach_requires_first_hunt_and_closes_only_after_guardian_dies(self) -> None:
        clue = objects(MOD / "items" / "first_hunt_clue.json")[0]
        self.assertEqual(clue["use_action"]["effect_on_conditions"],
                         ["EOC_BERSERK_BREACH_READ_CLUE"])
        loot = objects(MOD / "monsterdrops" / "first_hunt.json")[0]
        self.assertIn({"item": clue["id"], "prob": 100}, loot["items"])
        hunt = self.eocs["EOC_BERSERK_BREACH_READ_CLUE"]
        self.assertIn("u_berserk_first_hunt_done == 1", str(hunt["condition"]))
        special = next(o for o in objects(MOD / "overmap" / "local_breach.json")
                       if o["type"] == "overmap_special")
        self.assertEqual(special["occurrences"], [0, 0])
        finder = self.eocs["EOC_BERSERK_BREACH_FIND"]
        self.assertEqual(finder["effect"]["target_params"]["om_special"], special["id"])
        self.assertEqual(finder["effect"]["true_eocs"], ["EOC_BERSERK_BREACH_FOUND"])

        mapgen = objects(MOD / "mapgen" / "local_breach.json")
        room = next(o["object"] for o in mapgen if "om_terrain" in o)
        self.assertEqual(len(room["rows"]), 24)
        self.assertTrue(all(len(row) == 24 for row in room["rows"]))
        self.assertEqual(room["rows"][11][11], "A")
        self.assertEqual(room["furniture"]["A"], "f_berserk_open_breach")
        visited = {(2, 0)}
        queue = deque(visited)
        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < 24 and 0 <= ny < 24 and room["rows"][ny][nx] != "T" and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        self.assertIn((11, 10), visited)
        self.assertIn((11, 11), visited)
        warden = objects(MOD / "monsters" / "breach_warden.json")[0]
        self.assertEqual(sum(x["monster"] == warden["id"] for x in room["place_monster"]), 1)
        for monster in room["place_monster"]:
            self.assertEqual(room["rows"][monster["y"]][monster["x"]], ".")
        self.assertEqual(warden["regenerates"], 0)
        death = self.eocs[warden["death_function"]["eoc"]]
        self.assertIn("EOC_BERSERK_BREACH_WARDEN_DEFEATED", references(death))
        close = self.eocs["EOC_BERSERK_BREACH_CLOSE"]
        self.assertIn("u_berserk_breach_guardian_defeated == 1", str(close["condition"]))
        self.assertIn("u_berserk_breach_sealed != 1", str(close["condition"]))
        update = next(o for o in mapgen if o.get("update_mapgen_id") == "berserk_local_breach_seal")
        self.assertEqual(update["object"]["set"], [
            {"point": "furniture", "id": "f_berserk_sealed_breach", "x": 11, "y": 11}])
        self.assertIn("berserk_post_eclipse_journal", str(close["effect"]))

        era = self.eocs["EOC_BERSERK_ECLIPSE_ERA_ENTER_OMT"]
        self.assertIn("u_berserk_breach_sealed == 1", str(era["condition"]))
        self.assertIn("u_near_om_location", str(era["condition"]))
        brand = self.eocs["EOC_BERSERK_BRAND_NIGHT_HUNT_UNSHELTERED"]
        self.assertEqual(brand["effect"]["then"]["if"]["x_in_y_chance"],
                         {"x": 1, "y": 3})
        journal = objects(MOD / "items" / "post_eclipse_journal.json")[0]
        choice = self.eocs[journal["use_action"]["effect_on_conditions"][0]]
        self.assertIn("u_berserk_breach_sealed == 1", str(choice["condition"]))
        self.assertIn("u_berserk_path_choice = 1", str(choice["effect"]))
        self.assertIn("u_berserk_path_choice = 2", str(choice["effect"]))

        texts: set[str] = set()
        for section, filename in (("overmap", "local_breach.json"),
                                  ("furniture", "local_breach.json"),
                                  ("monsters", "breach_warden.json"),
                                  ("items", "post_eclipse_journal.json"),
                                  ("effects", "local_breach_eocs.json"),
                                  ("items", "first_hunt_clue.json")):
            def collect(value: object) -> None:
                if isinstance(value, list):
                    for child in value:
                        collect(child)
                elif isinstance(value, dict):
                    for key, child in value.items():
                        if key in ("name", "description", "u_message", "menu_text", "u_query"):
                            if isinstance(child, str):
                                texts.add(child)
                            elif isinstance(child, dict) and "str" in child:
                                texts.add(child["str"])
                        collect(child)
            collect(objects(MOD / section / filename))
        for locale in ("ru", "zh_CN"):
            catalog_path = MOD / "lang" / "mo" / locale / "LC_MESSAGES" / "Berserk.mo"
            with catalog_path.open("rb") as catalog_file:
                catalog = gettext.GNUTranslations(catalog_file)
            self.assertFalse({entry for entry in texts if catalog.gettext(entry) == entry}, locale)

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
            MOD / "monsters" / "griffith_eclipse_active.json",
            MOD / "overmap" / "eclipse_dungeon.json",
            MOD / "overmap" / "eclipse_expanded.json",
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
