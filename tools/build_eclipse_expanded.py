#!/usr/bin/env python3
"""Generate the versioned 3x4 Eclipse field for CDDA 0.I-1.

Run from anywhere. Keep existing six-OMT files for saves already in the trial.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "mods" / "Berserk"
PREFIX = "berserk_eclipse_expanded_"
SCENES = [
    ("arrival", "Eclipse: arrival"),
    ("traces", "Eclipse: fallen band"),
    ("cache", "Eclipse: abandoned supplies"),
    ("torn", "Eclipse: torn field"),
    ("crossroads", "Eclipse: crossroads"),
    ("feast", "Eclipse: feast"),
    ("hunt", "Eclipse: hunting ground"),
    ("ravine", "Eclipse: scarred ravine"),
    ("approach", "Eclipse: final approach"),
    ("laststand", "Eclipse: last stand"),
    ("threshold", "Eclipse: ceremony threshold"),
    ("ceremony", "Eclipse: ceremony"),
]
HORIZONTAL_GATES = ((14, 9), (9, 17), (16, 10), (15, 11))
VERTICAL_GATES = ((12, 15, 13), (13, 10, 8), (11, 14, 17))
MAIN = {(0, 0): "E", (1, 0): "WS", (1, 1): "NS", (1, 2): "NS",
        (1, 3): "NE", (2, 3): "W"}


def scene_id(x, y):
    return PREFIX + SCENES[3 * y + x][0]


def build_scene(x, y):
    name = SCENES[3 * y + x][0]
    rows = [["." for _ in range(24)] for _ in range(24)]

    def put(px, py, value, replace=".ar"):
        if 0 <= px < 24 and 0 <= py < 24 and rows[py][px] in replace:
            rows[py][px] = value

    # Two colors of ground, with ridges screening diagonal sightlines.
    for py in range(1, 23):
        for px in range(1, 23):
            if (px * 5 + py * 3 + x * 7 + y * 11) % 17 < 2:
                put(px, py, "a")
    for ox, oy, radius in ((5 + (y % 2), 6 + (x % 2), 2 + (x % 2)),
                           (18 - (y % 2), 17 - (x % 2), 2 + (y % 2))):
        for py in range(oy - radius, oy + radius + 1):
            for px in range(ox - radius, ox + radius + 1):
                if abs(px - ox) + abs(py - oy) <= radius + 1:
                    put(px, py, "#")
    # The broad crossing points line up exactly between adjoining OMTs.
    gates = {}
    if x:
        gates["W"] = (0, HORIZONTAL_GATES[y][x - 1])
    if x < 2:
        gates["E"] = (23, HORIZONTAL_GATES[y][x])
    if y:
        gates["N"] = (VERTICAL_GATES[y - 1][x], 0)
    if y < 3:
        gates["S"] = (VERTICAL_GATES[y][x], 23)

    for py in range(24):
        for px in range(24):
            if px in (0, 23) or py in (0, 23):
                rows[py][px] = "#"
    for direction, (gx, gy) in gates.items():
        for delta in range(-4, 5):
            if direction in "WE":
                rows[gy + delta][gx] = "."
            else:
                rows[gy][gx + delta] = "."

    # A deliberate bend in the main path prevents one straight sightline
    # across several OMTs. Secondary branches use subtle trampled flesh.
    center = (12, 12)
    for direction, (gx, gy) in gates.items():
        primary = direction in MAIN.get((x, y), "")
        glyph = "a" if primary else "r"
        bend = (12 + (y % 2) * 2, 12 + (x % 2) * 2)
        segments = ((center, bend), (bend, (gx, bend[1])), ((gx, bend[1]), (gx, gy))) if direction in "WE" else (
            (center, bend), (bend, (bend[0], gy)), ((bend[0], gy), (gx, gy))
        )
        for (x1, y1), (x2, y2) in segments:
            for py in range(min(y1, y2), max(y1, y2) + 1):
                for px in range(min(x1, x2), max(x1, x2) + 1):
                    for offset in (-1, 0, 1):
                        tx, ty = (px, py + offset) if y1 == y2 else (px + offset, py)
                        put(tx, ty, glyph, replace=".ar#" if 1 < tx < 22 and 1 < ty < 22 else ".ar")
        if primary:
            lx, ly = (min(20, max(3, gx - 5 if direction == "E" else gx + 5)), gy) if direction in "WE" else (
                gx, min(20, max(3, gy - 5 if direction == "S" else gy + 5))
            )
            put(lx, ly, "v", replace=".ar")
    put(12, 12, "v")

    hazards = {
        "torn": ((16, 5), (17, 5), (18, 5), (16, 6), (17, 6), (18, 6)),
        "ravine": ((5, 16), (6, 16), (7, 16), (5, 17), (6, 17), (7, 17)),
        "hunt": ((17, 5), (18, 5), (17, 6)),
        "threshold": ((18, 6), (19, 6), (18, 7)),
    }
    for hx, hy in hazards.get(name, ()):
        put(hx, hy, "P", replace=".r")
    if name == "feast":
        for hx, hy in ((15, 17), (16, 18), (17, 19), (18, 19)):
            put(hx, hy, "C", replace=".r")

    # Scene pieces and encounters sit off the main ash trail. No monster is
    # placed on the arrival pad or immediately beside a map seam.
    markers = {
        "arrival": ("S", 11, 12), "traces": ("J", 9, 7),
        "cache": ("X", 17, 10), "torn": ("I", 10, 17),
        "crossroads": ("H", 17, 8), "feast": ("F", 11, 8),
        "approach": ("G", 17, 8), "threshold": ("W", 10, 8),
        "ceremony": ("R", 12, 20),
    }
    if name in markers:
        mark, mx, my = markers[name]
        rows[my][mx] = mark
    if name == "feast":
        rows[17][13] = "K"

    groups = {
        "traces": ["WRETCH", "WRETCH", "WRETCH"],
        "cache": ["HUNTER", "WRETCH", "WRETCH"],
        "torn": ["WRETCH", "HALF", "WRETCH", "WRETCH"],
        "crossroads": ["HALF", "HUNTER", "WRETCH", "HALF"],
        "feast": ["WRETCH", "WRETCH", "HALF", "BUTCHER", "WRETCH", "WRETCH"],
        "hunt": ["HUNTER", "HUNTER", "HALF", "WRETCH"],
        "ravine": ["HALF", "HUNTER", "BUTCHER", "WRETCH"],
        "approach": ["HALF", "BUTCHER", "HUNTER", "WRETCH"],
        "laststand": ["WRETCH", "HALF", "BUTCHER", "WRETCH"],
        "threshold": ["HUNTER", "ELITE", "HALF"],
        "ceremony": ["ELITE"],
    }
    slots = ((18, 5), (6, 19), (17, 18), (5, 12), (19, 7), (10, 20))
    monsters = []
    occupied = set()
    for index, group in enumerate(groups.get(name, [])):
        mx, my = slots[index]
        if rows[my][mx] not in ".r" or (mx, my) in occupied:
            mx, my = min(((px, py) for py in range(3, 21) for px in range(3, 21)
                          if rows[py][px] in ".r" and (px, py) not in occupied),
                         key=lambda pos: abs(pos[0] - mx) + abs(pos[1] - my))
        occupied.add((mx, my))
        monsters.append({"group": "GROUP_BERSERK_ECLIPSE_" + group, "x": mx, "y": my})
    if name == "ceremony":
        for by in range(16, 19):
            for bx in range(14, 17):
                rows[by][bx] = "."
        assert rows[17][15] != "#"
        monsters.append({"monster": "mon_berserk_eclipse_griffith_active", "x": 15, "y": 17,
                         "one_or_none": True})

    obj = {"rows": ["".join(row) for row in rows],
           "palettes": ["berserk_eclipse_flesh_palette"]}
    if monsters:
        obj["place_monster"] = monsters
    if name in ("traces", "torn", "approach"):
        person, bx, by = {"traces": ("judeau", 9, 7), "torn": ("pippin", 10, 17),
                          "approach": ("gaston", 17, 8)}[name]
        obj["place_item"] = [{"item": f"berserk_eclipse_{person}_body", "x": bx, "y": by, "amount": 1}]
        if person != "gaston":
            memory = "berserk_judeau_knife_hilt" if person == "judeau" else "berserk_pippin_broken_clasp"
            obj["place_item"].append({"item": memory, "x": bx, "y": by, "amount": 1})
        obj["place_loot"] = [{"group": f"berserk_eclipse_{person}_gear", "x": bx, "y": by, "chance": 100}]
    elif name == "feast":
        obj["place_item"] = [{"item": "berserk_eclipse_corkus_body", "x": 13, "y": 17, "amount": 1}]
        obj["place_loot"] = [{"group": "berserk_eclipse_corkus_gear", "x": 13, "y": 17, "chance": 100}]
    elif name == "cache":
        obj["place_loot"] = [{"group": "berserk_eclipse_supply_cache", "x": 17, "y": 10, "chance": 100}]
    return {"type": "mapgen", "om_terrain": [scene_id(x, y)], "object": obj}


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    overmap = []
    for y in range(4):
        for x in range(3):
            overmap.append({"type": "overmap_terrain", "id": scene_id(x, y),
                            "name": SCENES[3 * y + x][1], "sym": "%", "color": "dark_gray",
                            "see_cost": "high", "travel_cost_type": "impassable",
                            "flags": ["NO_ROTATE", "SHOULD_NOT_SPAWN"]})
    overmap.append({"type": "overmap_special", "id": "berserk_eclipse_expanded_special",
                    "overmaps": [{"point": [x, y, -7], "overmap": scene_id(x, y)}
                                 for y in range(4) for x in range(3)],
                    "locations": ["subterranean_empty"], "occurrences": [0, 0], "rotate": False})
    write(ROOT / "overmap" / "eclipse_expanded.json", overmap)
    write(ROOT / "mapgen" / "eclipse_expanded.json",
          [build_scene(x, y) for y in range(4) for x in range(3)])


if __name__ == "__main__":
    main()
