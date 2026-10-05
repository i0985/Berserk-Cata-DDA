#!/usr/bin/env python3
"""Build one coherent 48x48 residence, then split the four existing OMT IDs."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'mods/Berserk'
SECTIONS = [('berserk_count_prison', 0, 0), ('berserk_count_hall', 1, 0),
            ('berserk_count_west_yard', 0, 1), ('berserk_count_east_yard', 1, 1)]
# Existing finite actors and witness; do not change their stats or multiply them.
ACTORS = [('mon_berserk_count_servant', 9, 10), ('mon_berserk_count_servant', 18, 17),
          ('mon_berserk_count_witness', 7, 18), ('mon_berserk_count_servant', 30, 9),
          ('mon_berserk_count_servant', 40, 18), ('mon_berserk_count_servant', 13, 27),
          ('mon_berserk_count_servant', 36, 34)]
PROPS = [
    ('f_berserk_count_notice', 24, 38),
    ('f_berserk_location_count_property', 7, 7),
    ('f_berserk_location_count_clerk', 18, 7),
    ('f_desk', 18, 9), ('f_chair', 18, 10), ('f_bookcase', 20, 7),
    ('f_bed', 9, 18), ('f_bench', 7, 19), ('f_rubble', 6, 13),
    ('f_berserk_location_count_physician', 30, 8),
    ('f_desk', 30, 7), ('f_bookcase', 32, 7), ('f_table', 31, 11),
    ('f_berserk_location_count_family', 40, 9),
    ('f_bed', 40, 7), ('f_desk', 38, 9), ('f_chair', 38, 10), ('f_bookcase', 42, 11),
    ('f_berserk_count_family_door', 38, 12),
    ('f_berserk_count_service_grate', 27, 16),
    ('f_berserk_count_execution_record', 33, 17),
    ('f_table', 38, 15), ('f_chair', 38, 16), ('f_bench', 30, 19), ('f_bench', 42, 19),
    ('f_clay_oven', 7, 30), ('f_table', 8, 34), ('f_chair', 8, 35),
    ('f_rack', 13, 30), ('f_berserk_location_count_pantry', 13, 34),
    ('f_bench', 11, 38), ('f_table', 18, 33), ('f_chair', 18, 34),
    ('f_berserk_location_count_armory', 40, 34),
    ('f_rack', 32, 30), ('f_rack', 33, 30), ('f_rack', 40, 30), ('f_table', 39, 37),
    ('f_bench', 33, 37), ('f_rubble', 3, 30), ('f_rubble', 3, 34), ('f_rubble', 44, 6),
]


def build_field():
    field = [['.'] * 48 for _ in range(48)]

    def room(x1, y1, x2, y2):
        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                field[y][x] = '#' if x in (x1, x2) or y in (y1, y2) else '_'

    # Fortified perimeter, southern arrival and a visibly broken service entrance.
    for x in range(2, 46):
        field[2][x] = field[45][x] = '#'
    for y in range(2, 46):
        field[y][2] = field[y][45] = '#'
    for y in range(22, 48):
        for x in range(23, 27):
            field[y][x] = ','
    for y in (31, 32, 33):
        for x in range(0, 7):
            field[y][x] = ','
    for x in range(3, 45):
        field[24][x] = field[25][x] = ','
    for y in range(4, 44):
        field[y][3] = ','
    room(5, 5, 22, 21)  # prison, clerk's office, witness's hiding place
    for y in range(6, 15):
        field[y][12] = '#'
        field[y][8] = '|'
    field[11][8] = '!'
    for x in range(6, 22):
        field[14][x] = '#'
    field[14][10] = field[14][17] = '+'
    for y in range(16, 21):
        field[y][11] = '#'
    field[18][11] = '+'
    field[17][5] = '+'
    for x in range(22, 28):
        field[16][x] = '_'
    field[21][18] = '+'

    room(27, 5, 43, 21)  # archive/physician, daughter's room, seat of power
    for y in range(6, 14):
        field[y][34] = '#'
    for x in range(28, 43):
        field[13][x] = '#'
    field[13][31] = field[13][39] = '+'
    # The barred western shortcut does not replace the open southern hall entrance.
    field[16][27] = '_'
    field[21][36] = field[21][37] = '+'
    for y in range(22, 29):
        field[y][36] = field[y][37] = ','
    field[20][36] = 'V'  # original local (12,20), aligned with stairs below

    room(5, 28, 21, 40)  # service kitchen, pantry and servant dining area
    for y in range(29, 40):
        field[y][10] = '#'
        field[y][15] = '#'
    field[35][10] = field[35][15] = '+'
    field[32][5] = field[28][18] = field[40][18] = '+'
    room(30, 28, 43, 40)  # armory and repair benches, not loot in an empty yard
    field[28][36] = field[40][36] = field[34][30] = '+'
    # Small barred openings into the courtyards; no modern shop-window furniture.
    for x, y in ((10,5), (18,5), (30,5), (40,5), (8,28), (43,32)):
        field[y][x] = '|'
    for _, x, y in ACTORS:
        assert field[y][x] in '._,', ('actor blocked', x, y)
    return field


def build_scene(omt, ox, oy, field):
    x0, y0 = ox * 24, oy * 24
    obj = {'rows': [''.join(row[x0:x0 + 24]) for row in field[y0:y0 + 24]],
           'palettes': ['berserk_count_palette']}
    obj['place_monster'] = [dict(monster=kind, x=x-x0, y=y-y0, one_or_none=True)
                            for kind, x, y in ACTORS if x0 <= x < x0+24 and y0 <= y < y0+24]
    obj['place_furniture'] = [dict(furn=kind, x=x-x0, y=y-y0)
                             for kind, x, y in PROPS if x0 <= x < x0+24 and y0 <= y < y0+24]
    return {'type': 'mapgen', 'om_terrain': [omt], 'object': obj}


def main():
    path = ROOT / 'mapgen/apostle_count.json'
    existing = json.loads(path.read_text())
    dungeon = next(o for o in existing if o.get('om_terrain') == ['berserk_count_dungeon'])
    rows = [list(row) for row in dungeon['object']['rows']]
    rows[5][12] = '_'  # original seal location remains usable in old generated maps
    for x, y in [(19, 2), (20, 2), (21, 2), (21, 3), (21, 4), (21, 5), (19, 5), (20, 5)]:
        rows[y][x] = '#'
    rows[4][20] = 'A'  # new secluded alcove, separate from the boss at (12,8)
    dungeon['object']['rows'] = [''.join(row) for row in rows]
    # Preserve the legacy update ID; normal sealing now transforms the examined cell.
    updates = [o for o in existing if 'update_mapgen_id' in o]
    field = build_field()
    output = [build_scene(omt, ox, oy, field) for omt, ox, oy in SECTIONS] + [dungeon] + updates
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print('Built coherent 48x48 Count residence and separate 24x24 dungeon; existing IDs/actors/stairs retained')


if __name__ == '__main__':
    main()
