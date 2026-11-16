"""Check recovery transactions and the geometry of fresh Eclipse fields."""

import json
import unittest
from collections import Counter, deque

from test_reference_journal_33 import Book, EOCS, MOD, TOPICS


def load(path):
    return json.loads((MOD / path).read_text(encoding="utf-8"))


class Forge(Book):
    def __init__(self):
        super().__init__()
        self.om = "berserk_godo_workshop"
        self.drops = Counter()
        self.overrides["EOC_BERSERK_GODO_AT_RICKERT_FORGE"] = True

    def effect(self, action):
        if isinstance(action, dict) and "map_spawn_item" in action:
            self.drops[action["map_spawn_item"]] += 1
        else:
            super().effect(action)


class Siege(Book):
    def __init__(self):
        super().__init__()
        self.values["berserk_flora_location"] = (0, 0, 0)
        self.escorts = Counter()

    def effect(self, action):
        if isinstance(action, dict) and "u_spawn_monster" in action:
            self.escorts[action["u_spawn_monster"]] += 1
        elif isinstance(action, dict) and "location_variable_adjust" in action:
            pass  # The authored spawn cells are static offsets from the manor.
        else:
            super().effect(action)


class CampaignBalanceTests(unittest.TestCase):
    def test_recovery_menu_gives_supplies_once_after_rescue(self):
        forge = Forge()
        topic = "TALK_BERSERK_RICKERT_RECOVERY_SUPPLIES"
        response = next(r for r in TOPICS["TALK_BERSERK_RICKERT"]["responses"] if r["topic"] == topic)
        self.assertFalse(forge.condition(response["condition"]))
        forge.values["u_berserk_eclipse_rescue_state"] = 2
        forge.bionics.add("bio_berserk_hand_stump")
        self.assertTrue(forge.condition(response["condition"]))
        forge.enter(topic)
        forge.enter(topic)
        self.assertFalse(forge.condition(response["condition"]))
        self.assertEqual(forge.drops, {"berserk_forge_recovery_supplies": 1, "machete": 1})

        late_start = Forge()
        late_start.values["u_berserk_eclipse_rescue_state"] = 2
        late_start.bionics.update(("bio_berserk_hand_stump", "bio_berserk_arm_cannon"))
        late_start.enter(topic)
        self.assertEqual(late_start.drops, {"berserk_forge_recovery_supplies": 1})

    def test_forge_respite_ends_at_first_hunt_or_alternative_breach(self):
        condition = EOCS["EOC_BERSERK_FORGE_RECOVERY_SHELTER"]["condition"]
        for entry, milestone in (("ordinary", "u_berserk_first_hunt_done"),
                                 ("alternative", "u_berserk_breach_sealed")):
            with self.subTest(entry=entry):
                forge = Forge()
                if entry == "ordinary":
                    forge.values["u_berserk_eclipse_rescue_state"] = 2
                else:
                    forge.values.update(u_berserk_eclipse_route=2, u_berserk_apostol_return_state=2,
                                        u_berserk_apostol_outcome=2)
                    forge.traits.add("BERSERK_ECLIPSE_SCAR_SIGHT")
                    forge.enter("TALK_BERSERK_RICKERT_RECOVERY_SUPPLIES")
                    self.assertEqual(forge.drops["glasses_eye"], 1)
                    self.assertNotIn("machete", forge.drops)
                self.assertTrue(forge.condition(condition))
                forge.outside = True
                self.assertFalse(forge.condition(condition))
                forge.outside = False
                forge.values[milestone] = 1
                self.assertFalse(forge.condition(condition))

    def test_world_seeding_uses_target_not_the_entered_tile(self):
        condition = EOCS["EOC_BERSERK_ECLIPSE_ERA_SCRIPTED_TARGET"]["condition"]
        field = Book()
        target = (24, -48, 0)
        field.values["_berserk_era_neighbor"] = target
        field.om = "forest"
        field.terrain[target] = "berserk_count_dungeon"
        self.assertTrue(field.condition(condition))
        field.om = "berserk_first_hunt_lair"
        field.terrain[target] = "forest"
        self.assertFalse(field.condition(condition))

    def test_siege_escort_does_not_catch_up_after_escape_or_reload(self):
        initial = "EOC_BERSERK_FLORA_SPAWN_ESCORT"
        next_wave = "EOC_BERSERK_FLORA_SPAWN_ESCORT_REINFORCEMENTS"
        for escape in (False, True):
            with self.subTest(escape=escape):
                siege = Siege()
                siege.values["berserk_flora_siege_state"] = 3
                siege.run(initial)
                siege.run(initial)
                siege.now += 19
                siege.run(next_wave)
                self.assertEqual(siege.escorts.total(), 3)
                siege.now += 1
                if escape:
                    siege.values["berserk_flora_siege_state"] = 5
                siege.run(next_wave)
                siege.run(next_wave)
                self.assertEqual(siege.escorts.total(), 3 if escape else 6)
        legacy = Siege()
        legacy.values.update(berserk_flora_siege_state=3, berserk_flora_escort_started=1)
        legacy.run(initial)
        legacy.run(next_wave)
        self.assertFalse(legacy.escorts)

    def test_screen_can_physically_close_both_routes_to_cover(self):
        for filename in ("eclipse_expanded", "apostol_eclipse"):
            maps = {name.split("_")[-1]: o["object"] for o in load(f"mapgen/{filename}.json")
                    for name in o.get("om_terrain", [])}
            for sector, interior in (("traces", (19, 8)), ("threshold", (5, 8))):
                with self.subTest(field=filename, sector=sector):
                    rows = maps[sector]["rows"]
                    for door_open in (False, True):
                        blocked = "#%&@pB" if door_open else "#%&@pBD"
                        reached, queue = {interior}, deque([interior])
                        while queue:
                            x, y = queue.popleft()
                            for ny in range(max(0, y - 1), min(24, y + 2)):
                                for nx in range(max(0, x - 1), min(24, x + 2)):
                                    if (nx, ny) not in reached and rows[ny][nx] not in blocked:
                                        reached.add((nx, ny))
                                        queue.append((nx, ny))
                        # Test diagonals too. A gap beside the screen lets hunters walk around it.
                        reached_trail = any(rows[y][x] in "ar" for x, y in reached)
                        self.assertEqual(reached_trail, door_open)

    def test_committed_attacks_keep_their_preparation_effect_until_release(self):
        states = {e["id"]: e for e in load("effects/wyald_rosine_combat_effects.json")}
        warnings = {s["id"]: s for s in load("spells/apostle_committed_attacks.json")}
        for enemy in ("wyald", "rosine"):
            with self.subTest(enemy=enemy):
                setup = EOCS[f"EOC_BERSERK_{enemy.upper()}_COMMITTED_BEGIN"]["effect"]
                state = f"berserk_{enemy}_ready"
                due = next(e["math"][0] for e in setup if e.get("math", [""])[0].startswith(
                    f"n_berserk_committed_{enemy}_due ="))
                delay = int(due.rsplit("+", 1)[1])
                duration = int(next(e["duration"] for e in setup if e.get("npc_add_effect") == state).split()[0])
                max_duration = int(states[state]["max_duration"].split()[0])
                self.assertGreater(min(duration, max_duration), delay)
                self.assertGreaterEqual(warnings[f"berserk_committed_{enemy}_warning"]["min_duration"], delay * 100)

    def test_eclipse_paths_and_placement_after_density_changes(self):
        for filename, expected in (("eclipse_expanded", 27), ("apostol_eclipse", 25)):
            with self.subTest(field=filename):
                maps = {name: o["object"] for o in load(f"mapgen/{filename}.json")
                        for name in o.get("om_terrain", [])}
                special = next(o for o in load(f"overmap/{filename}.json") if o["type"] == "overmap_special")
                passable, trail, positions = set(), set(), {}
                count = 0
                for tile in special["overmaps"]:
                    name = tile["overmap"]
                    data = maps[name]
                    ox, oy, _ = tile["point"]
                    blocked_furniture = {(f["x"], f["y"]) for f in data.get("place_furniture", [])
                                         if f["furn"].endswith(("heap_high", "cart_wreck", "shield_barricade"))}
                    for y, row in enumerate(data["rows"]):
                        for x, glyph in enumerate(row):
                            key = (24 * ox + x, 24 * oy + y)
                            if glyph not in "#%&@pB" and (x, y) not in blocked_furniture:
                                passable.add(key)
                            if glyph == "a":
                                trail.add(key)
                            if glyph in "S!" and key in passable:
                                positions[(name.split("_")[-1], glyph)] = key
                    for spawn in data.get("place_monster", []):
                        self.assertIn((24 * ox + spawn["x"], 24 * oy + spawn["y"]), passable, (name, spawn))
                        count += 1
                self.assertEqual(count, expected)
                start = positions[("arrival", "S")]
                reached, queue = {start}, deque([start])
                while queue:
                    x, y = queue.popleft()
                    for point in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if point in passable and point not in reached:
                            reached.add(point)
                            queue.append(point)
                self.assertGreater(len(reached & trail), 100)
                self.assertIn(positions[("ceremony", "!")], reached)
