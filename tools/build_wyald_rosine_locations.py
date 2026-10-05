#!/usr/bin/env python3
"""Compose two continuous 48x48 hunt sites without moving their legacy OMT IDs."""
import json
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'
SECTIONS = {
    'wyald': ['berserk_wyald_approach', 'berserk_wyald_camp',
              'berserk_wyald_quarry', 'berserk_wyald_ring'],
    'rosine': ['berserk_rosine_trail', 'berserk_rosine_cocoons',
               'berserk_rosine_gully', 'berserk_rosine_nest'],
}


class Field:
    def __init__(self):
        self.rows = [['.'] * 48 for _ in range(48)]
        self.props = []
        self.actors = []

    def box(self, x1, y1, x2, y2, char):
        for y in range(y1, y2+1):
            for x in range(x1, x2+1):
                self.rows[y][x] = char

    def path(self, points, width=1, char='d'):
        # Orthogonal segments, with irregular outlines introduced by the waypoints.
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            assert x1 == x2 or y1 == y2
            for y in range(min(y1, y2), max(y1, y2)+1):
                for x in range(min(x1, x2), max(x1, x2)+1):
                    self.box(max(0,x-width), max(0,y-width), min(47,x+width), min(47,y+width), char)

    def prop(self, kind, x, y):
        assert not any((px,py)==(x,y) for _,px,py in self.props), (kind,x,y)
        self.props.append((kind, x, y))

    def woodland_edge(self, north_gap, south_gap, west_gap, east_gap):
        # Shifting bands of trunks form an uneven woodland edge rather than a
        # straight four-sided arena wall. Paths are drawn through it afterward.
        for x in range(3,46):
            if x not in north_gap:
                self.rows[2+(x//7)%2][x] = 'T'
            if x not in south_gap:
                self.rows[45-(x//9)%2][x] = 'T'
        for y in range(4,44):
            if y not in west_gap:
                self.rows[y][2+(y//8)%2] = 'T'
            if y not in east_gap:
                self.rows[y][45-(y//6)%2] = 'T'

    def tent(self, x1, y1, x2, y2, door):
        self.box(x1,y1,x2,y2,'m')
        for y in range(y1,y2+1):
            for x in range(x1,x2+1):
                if x in (x1,x2) or y in (y1,y2): self.rows[y][x] = 'c'
        self.rows[door[1]][door[0]] = 'v'

    def recesses(self, kind, ground='d'):
        # Preserve all four arrival candidates used by hunt_arena_eocs.json.
        # These curved screens are sight breaks, not an invisible boss tether.
        for x,y in ((30,30),(41,30),(30,41),(41,41)):
            self.box(x-1,y-1,x+1,y+1,ground)
            for dx,dy in ((-1,-1),(0,-1),(1,-1),(-1,0)):
                self.rows[y+dy][x+dx] = kind
        self.rows[36][36] = ground
        self.prop('f_berserk_hunt_arena_tracks',36,36)


def wyald():
    f = Field()
    # Broken woodland edge, not a square fort enclosing four identical fields.
    f.woodland_edge(range(8,14),range(35,40),range(29,35),range(25,32))
    f.path([(10,0),(10,14),(18,14),(18,23),(27,23),(27,28),(36,28),(36,47)])
    f.path([(10,14),(6,14),(6,30),(1,30)])
    f.path([(6,30),(22,30),(22,37),(28,37),(28,43),(36,43)])
    f.path([(18,14),(29,14),(29,22),(42,22),(42,29),(47,29)])
    # Irregular campaign tents: sleeping quarters, mess, stores and command.
    for args in ((13,4,20,10,(17,10)), (24,5,30,11,(27,11)),
                 (34,9,43,16,(34,13)), (7,18,14,25,(14,22)),
                 (16,17,22,21,(18,21))): f.tent(*args)
    f.rows[6][24] = 'v'  # torn second entrance, distinct damaged tent
    f.prop('f_berserk_location_wyald_baggage',6,8)
    f.prop('f_berserk_wyald_wagon_chime',7,7)
    f.prop('f_berserk_wyald_wagon_wreck',5,9)
    f.prop('f_berserk_wyald_wagon_wreck',7,10)
    f.prop('f_berserk_wyald_record',9,16)  # legacy inscription ID
    f.prop('f_berserk_location_wyald_kitchen',9,20)
    f.prop('f_clay_oven',9,23)
    f.prop('f_table',11,21)
    f.prop('f_bench',11,23)
    f.prop('f_berserk_location_wyald_repair',20,18)
    f.prop('f_berserk_location_wyald_command',40,11)
    f.prop('f_table',38,13)
    f.prop('f_bench',40,14)
    f.prop('f_berserk_wyald_scene',27,18)
    f.prop('f_berserk_wyald_punishment_post',24,20)
    f.prop('f_berserk_wyald_punishment_post',25,20)
    for p in ((14,7),(16,7),(26,8),(28,8)): f.prop('f_berserk_campaign_bedding',*p)
    for p in ((12,12),(23,13),(33,18)): f.prop('f_firering',*p)
    # Wooden cage wall divides two routes. Opening it is optional, not a quest key.
    f.box(16,25,19,31,'d')
    f.box(16,25,16,31,'p')
    f.box(19,25,19,31,'p')
    f.box(16,25,19,25,'p')
    f.box(16,31,19,31,'p')
    f.rows[28][16] = f.rows[28][19] = 'd'
    f.prop('f_berserk_wyald_cage_gate',16,28)
    f.prop('f_berserk_wyald_cage_gate',19,28)
    f.prop('f_berserk_location_wyald_prisoners',17,26)
    f.prop('f_berserk_wyald_prisoner_trace',18,30)
    # Quarry ledges and a side approach into a broad trampled fighting ground.
    for x1,y1,x2,y2 in ((5,36,12,38),(8,40,15,42),(17,39,20,42)):
        f.box(x1,y1,x2,y2,'#')
    f.box(27,26,43,43,'d')
    f.recesses('p')
    for x,y in ((33,33),(39,36),(33,40)):
        f.prop('f_berserk_wyald_charge_obstacle',x,y)
        f.prop('f_berserk_wyald_charge_obstacle',x+1,y)
    f.prop('f_berserk_wyald_breach',36,31)  # original local (12,7)
    f.prop('f_berserk_wyald_ring_warning',26,28)
    f.actors = [('mon_berserk_black_dog_thrall',26,12),
                ('mon_berserk_black_dog_thrall',29,19),
                ('mon_berserk_black_dog_thrall',39,22),
                ('mon_berserk_black_dog_thrall',20,33),
                ('mon_berserk_black_dog_thrall',32,35),
                ('mon_berserk_black_dog_thrall',42,39)]
    return f


def rosine():
    f = Field()
    f.woodland_edge(range(8,13),range(33,39),range(25,30),range(21,27))
    # A sweeping gully crosses OMT seams; these are shallow slopes, not z-level pits.
    for y in range(13,42):
        x = 6 + (y-13)//5
        f.box(x,y,x+3,y,'s')
        if y % 5 == 1: f.rows[y][x-1] = '#'
    f.path([(10,0),(10,9),(17,9),(17,16),(26,16),(26,22),(37,22),(37,47)],char='l')
    f.path([(10,9),(6,9),(6,13),(8,13)],char='l')
    f.path([(8,13),(8,22),(10,22),(10,31),(13,31),(13,40),(26,40),(26,37),(31,37)],char='s')
    f.path([(17,16),(17,24),(24,24),(24,32),(30,32)],char='l')
    f.path([(37,22),(46,22)],char='l')
    # False paradise: an irregular petal clearing and a grove crossing both seams.
    for y in range(7,25):
        for x in range(14,35):
            if (x-24)**2/110+(y-16)**2/64 < 1 and f.rows[y][x]=='.': f.rows[y][x]='l'
    for x,y in ((15,11),(20,10),(27,9),(32,14),(22,20),(31,20),
                (16,22),(30,25),(26,28),(22,31),(20,35),(40,24)):
        f.prop('f_flower_tulip',x,y)
    for x,y in ((19,13),(28,13),(29,18),(19,21),(24,27),(21,30),(25,35),(42,27)):
        f.rows[y][x] = 'T'
    f.prop('f_berserk_rosine_record',9,11)
    f.prop('f_berserk_location_rosine_travelers',6,7)
    f.prop('f_berserk_rosine_missing_trace',14,8)
    f.prop('f_berserk_rosine_scene',24,17)
    f.prop('f_berserk_location_rosine_keepsake',29,16)
    f.prop('f_berserk_rosine_story_cocoon',22,25)
    for x,y in ((33,17),(27,26),(23,34),(40,28)):
        f.prop('f_berserk_rosine_cocoon_watchful',x,y)
    for x,y in ((31,12),(20,24),(27,30),(39,42)):
        f.prop('f_berserk_rosine_cocoon_sealed',x,y)
    for x,y in ((16,15),(25,22),(18,33)):
        f.prop('f_berserk_rosine_shell_material',x,y)
    f.prop('f_berserk_rosine_cocoon_destroyed',21,37)
    f.prop('f_berserk_location_rosine_waycamp',15,38)
    # The old roost OMT remains, but its roots connect to the whole grove.
    for y in range(24,44):
        for x in range(26,45):
            if (x-36)**2/100+(y-34)**2/121 < 1:
                f.rows[y][x]='l'
    for x,y in ((32,25),(33,25),(34,25),(35,25),(36,25),
                (34,26),(35,26),(36,26),(35,27)):
        f.rows[y][x]='G'
    f.recesses('R',ground='l')
    for x,y in ((33,34),(34,34),(39,37),(40,37),(33,40),(34,40)):
        f.rows[y][x] = 'R'  # genuine opaque tree-root screens against diving
    f.prop('f_berserk_rosine_breach',36,31)  # legacy local (12,7)
    f.prop('f_berserk_rosine_nest_warning',28,24)
    # Two initial sentries; four finite cocoons replace the other two preplaced
    # creatures and the former pair of manual cocoons. Maximum support stays six.
    f.actors = [('mon_berserk_cocoon_ravager',17,28),
                ('mon_berserk_cocoon_ravager',27,39)]
    return f


def split(kind, field):
    result = []
    for index,omt in enumerate(SECTIONS[kind]):
        x0,y0 = (index%2)*24,(index//2)*24
        obj = {'fill_ter':'t_grass',
               'rows':[''.join(row[x0:x0+24]) for row in field.rows[y0:y0+24]],
               'palettes':['berserk_hunt_location_detail_palette'],
               'place_furniture':[dict(furn=k,x=x-x0,y=y-y0) for k,x,y in field.props
                                  if x0<=x<x0+24 and y0<=y<y0+24],
               'place_monster':[dict(monster=k,x=x-x0,y=y-y0,chance=100,one_or_none=True)
                                for k,x,y in field.actors if x0<=x<x0+24 and y0<=y<y0+24]}
        result.append({'type':'mapgen','om_terrain':[omt],'object':obj})
    return result


def main():
    for kind,build in (('wyald',wyald),('rosine',rosine)):
        field=build()
        # Validate placements before writing any of the generated maps.
        for actor,x,y in field.actors:
            assert field.rows[y][x] not in 'T#GpRc', (actor,x,y)
            assert not any((x,y)==(px,py) for _,px,py in field.props)
        for kind_,x,y in field.props:
            assert field.rows[y][x] not in 'T#GpRc', (kind_,x,y)
        (MOD/f'mapgen/apostle_{kind}.json').write_text(
            json.dumps(split(kind,field),ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__': main()
