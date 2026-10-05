#!/usr/bin/env python3
"""Flora's organic house around one large tree; keep the existing four OMT IDs."""
import json
import random
from pathlib import Path

MOD=Path(__file__).resolve().parents[1]/'mods/Berserk'
SECTIONS=[('berserk_flora_manor_west',0,0),('berserk_flora_manor_east',1,0),
          ('berserk_flora_garden_west',0,1),('berserk_flora_garden_east',1,1)]
LAYOUT=(14,12)
FLORA=(15,12)
WARD=(16,12)
GUARDS=[(14,4),(42,18)]
MANUSCRIPT=(18,8)
NICHE=(26,30)
COLLAPSED_PASSAGE=(28,6)
LAYOUT_VERSION=2


def build():
    a=[['.']*48 for _ in range(48)]
    footprint=set();props=[]
    def rect(x1,y1,x2,y2,c):
        for y in range(y1,y2+1):
            for x in range(x1,x2+1):a[y][x]=c
    def room(x1,y1,x2,y2):
        footprint.update((x,y) for y in range(y1,y2+1) for x in range(x1,x2+1))
    def prop(k,x,y):
        assert (x,y) not in {(xx,yy) for _,xx,yy in props},(k,x,y)
        props.append((k,x,y))
    # The house has several wings embracing the trunk, not a rectangular mansion.
    for box in [(10,5,20,30),(19,5,31,8),
                (29,5,41,29),(18,21,31,28)]:room(*box)
    for p in [(10,5),(11,5),(10,6),(40,5),(39,5),(40,6),
              (10,30),(11,30),(41,28),(41,29),(40,29)]:footprint.discard(p)
    for x,y in footprint:
        a[y][x]='#' if any((x+dx,y+dy) not in footprint for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]) else '_'
    # A library above the reception room; two small sleeping rooms below it.
    rect(11,11,19,11,'#');a[11][17]='+'
    rect(11,18,17,18,'#');a[18][14]='+'
    rect(18,18,19,18,'#')
    # The foyer serves two enclosed guest rooms, not beds in the passage.
    rect(11,22,19,22,'#');a[22][12]='+';a[22][18]='+'
    rect(15,23,15,29,'#');rect(20,22,20,29,'#');a[25][20]='+'
    # Pantry, kitchen and workshop have distinct enclosed volumes.
    rect(36,6,36,10,'#');rect(36,11,40,11,'#');a[9][36]='+'
    rect(30,18,40,18,'#');a[18][33]='+'
    a[15][20]='+';a[15][29]='+'
    # Large original-coordinate exits survive warning/collapse and both layouts.
    a[14][10]='+';a[28][24]='+'
    a[29][34]='+';a[29][35]='+'
    for x,y in [(10,8),(10,25),(12,30),(18,30),(41,10),(41,22),(34,5),(14,5)]:
        if (x,y) in footprint:a[y][x]='W'
    # Rugged edges and a hidden west approach through the trees.
    rng=random.Random(3012)
    for y in range(48):
        for x in range(48):
            border=(y<4 and x not in range(12,17)) or (y>43 and x not in range(21,28)) or (x<4 and y not in range(11,18)) or (x>43 and y not in range(16,21))
            if border and rng.random()<.48:a[y][x]='T'
    for x,y in [(5,7),(7,9),(5,18),(7,20),(5,40),(8,42),(36,41),(41,39),(39,33),(43,30)]:a[y][x]='T'
    rect(0,13,9,15,'d');rect(4,11,6,17,'d')
    rect(22,29,26,31,'d');rect(23,32,25,47,'d')
    rect(13,0,15,4,'d');rect(41,17,47,19,'d')
    # The many-cell trunk straddles the two northern OMTs. Root tongues reach the
    # house foundations and gardens; doors/escape paths are never painted over.
    for y in range(8,21):
        for x in range(21,28):
            if ((x-24)/3)**2+((y-14)/7)**2<1:a[y][x]='G'
    # The ring is continuous: never put roots immediately behind a doorway.
    for y in range(8,22):
        for x in (21,27,28):
            if a[y][x]=='.':a[y][x]='_'
    for x in range(21,29):
        if a[21][x]=='.':a[21][x]='_'
    for points in [[(23,20),(23,21)],[(26,20),(27,21)],
                   [(19,29),(18,30),(18,31),(17,32),(16,33)],
                   [(30,28),(31,29),(32,30),(33,31),(34,31)]]:
        for x,y in points:
            if a[y][x] not in '#W+_':a[y][x]='R'
    # Actual raid anchors retain free cells; an eastern outer root barrier is
    # breached at the 30-second assault stage, not placed across either exit.
    a[18][43]='R'
    prop('f_berserk_flora_treehouse_threshold_v2',*LAYOUT)
    prop('f_berserk_flora_ward',*WARD)
    prop('f_berserk_flora_scene',12,20)
    # Seven shelves against the walls, a manuscript desk and a reading chair.
    for k,x,y in [('f_berserk_flora_cosmology_shelf',11,7),('f_berserk_flora_cosmology_shelf',11,8),
                  ('f_berserk_flora_ward_shelf',13,6),('f_berserk_flora_ward_shelf',15,6),
                  ('f_berserk_flora_chronicle_shelf',19,9),('f_berserk_flora_chronicle_shelf',19,10),
                  ('f_berserk_flora_botany_shelf',11,10),
                  ('f_berserk_flora_manuscript',*MANUSCRIPT),('f_chair',17,8),
                  ('f_berserk_flora_linen_armchair',13,9),
                  ('f_berserk_flora_reading_lamp',18,9),('f_berserk_flora_gallery_record',25,6)]:prop(k,x,y)
    # Reception room: hearth, rug, tea table, comfortable seats, correspondence.
    rect(12,12,18,16,'r')
    for k,x,y in [('f_berserk_flora_stone_hearth',11,16),('f_berserk_flora_low_table',13,15),
                  ('f_berserk_flora_linen_armchair',12,15),('f_berserk_flora_linen_armchair',14,15),
                  ('f_berserk_flora_house_rules',11,17)]:prop(k,x,y)
    # Guest room and private room, with bedding, wardrobes and small writing desks.
    for k,x,y in [('f_bed',12,26),('f_bed',18,26),
                  ('f_berserk_flora_wooden_cupboard',11,23),('f_berserk_flora_wooden_cupboard',19,23),
                  ('f_berserk_flora_wooden_rack',11,28),('f_berserk_flora_wooden_rack',19,28),
                  ('f_berserk_flora_guest_record',11,20),('f_berserk_flora_reading_lamp',13,28),
                  ('f_berserk_flora_reading_lamp',17,28)]:prop(k,x,y)
    # A lived-in kitchen: oven, counters, drying herbs, stores, a shared table.
    for k,x,y in [('f_clay_oven',35,6),('f_berserk_flora_wooden_worktop',30,6),
                  ('f_berserk_flora_wooden_worktop',31,6),('f_berserk_flora_wooden_worktop',32,6),
                  ('f_berserk_flora_drying_herbs',33,6),('f_berserk_flora_aid_pantry',39,7),
                  ('f_berserk_flora_wooden_rack',37,7),('f_berserk_flora_wooden_rack',40,8),
                  ('f_table',33,13),('f_table',34,13),
                  ('f_chair',32,13),('f_chair',35,13),('f_chair',33,12),('f_chair',34,14),
                  ('f_berserk_flora_reading_lamp',30,10)]:prop(k,x,y)
    # Workshop's armor rack explains the dialogue gift rather than spawning loot.
    for k,x,y in [('f_berserk_flora_wooden_worktop',34,21),('f_berserk_flora_wooden_worktop',35,21),('f_chair',34,22),
                  ('f_berserk_flora_armor_stand',38,20),('f_berserk_flora_aid_workshop',36,23),
                  ('f_berserk_flora_aid_ward',30,25),('f_rack',40,25),('f_rack',40,26),
                  ('f_berserk_flora_ward_shelf',31,19),('f_berserk_flora_botany_shelf',32,19),
                  ('f_berserk_flora_reading_lamp',37,24)]:prop(k,x,y)
    # Front gallery makes the southern escape visible during peaceful exploration.
    for k,x,y in [('f_bench',21,26),
                  ('f_berserk_flora_south_sign',25,27),('f_berserk_flora_root_niche',*NICHE),
                  ('f_berserk_flora_west_sign',6,13),('f_bench',28,32),
                  ('f_bench',20,33),('f_berserk_flora_garden_record',8,32),
                  ('f_berserk_flora_rain_basin',31,34),('f_berserk_flora_garden_arch',24,37)]:prop(k,x,y)
    for x,y in [(6,25),(7,25),(8,25),(6,28),(7,28),(8,28),(6,35),(7,35),(8,35),
                (32,35),(33,35),(34,35),(32,37),(33,37),(34,37)]:prop('f_berserk_flora_herb_bed',x,y)
    for x,y in [(10,35),(11,36),(12,35),(31,33),(34,40),(35,39)]:prop('f_flower_tulip',x,y)
    # No industrial rack, metal bench fittings or modern mattress in this home.
    rustic={'f_chair':'f_berserk_flora_wooden_chair','f_bench':'f_berserk_flora_wooden_bench',
            'f_table':'f_berserk_flora_pegged_table',
            'f_bed':'f_berserk_flora_linen_bed','f_rack':'f_berserk_flora_wooden_rack'}
    props=[(rustic.get(k,k),x,y) for k,x,y in props]
    # Marker, ward and Flora retain exact original local coordinates.
    assert a[FLORA[1]][FLORA[0]]=='r'
    for _,x,y in props:assert a[y][x] not in '#W+GRT',(x,y,a[y][x])
    return a,props,footprint


def maps():
    a,props,_=build();result=[]
    for omt,ox,oy in SECTIONS:
        x0,y0=ox*24,oy*24
        actors=[dict(monster='mon_berserk_flora',x=FLORA[0],y=FLORA[1],chance=100,one_or_none=True,friendly=True)] if (ox,oy)==(0,0) else []
        actors += [dict(monster='mon_berserk_flora_root_guard',x=x-x0,y=y-y0,chance=100,one_or_none=True,friendly=True)
                   for x,y in GUARDS if x0<=x<x0+24 and y0<=y<y0+24]
        obj={'fill_ter':'t_grass','rows':[''.join(row[x0:x0+24]) for row in a[y0:y0+24]],
             'palettes':['berserk_flora_treehouse_palette'],'place_monster':actors,
             'place_furniture':[dict(furn=k,x=x-x0,y=y-y0) for k,x,y in props if x0<=x<x0+24 and y0<=y<y0+24]}
        result.append({'type':'mapgen','om_terrain':[omt],'object':obj})
    return result


def updates():
    """Only v2 patches; saved v0/v1 map updates remain in their existing files."""
    result=[]
    seeds={
        'warning':[('fd_smoke',14,3,30,1),('fd_smoke',44,18,30,1)],
        'assault':[('fd_fire',x,y,-300,2) for x,y in [(17,5),(23,11),(41,12),(25,13)]],
        'collapse':[('fd_fire',x,y,-300,2) for x,y in [(18,7),(13,24),(32,6),(38,20),(14,26),(35,26)]],
        'ruins':[]}
    patches={'warning':[],'assault':[],
             'collapse':[('f_berserk_flora_fallen_bough',*COLLAPSED_PASSAGE)],
             'ruins':[('f_berserk_flora_ruined_ward',*WARD),('f_berserk_flora_ruin_keepsake',*NICHE)]}
    for stage in seeds:
        for _,ox,oy in SECTIONS:
            suffix=['west','east','garden_west','garden_east'][oy*2+ox]
            inside=lambda x,y:ox*24<=x<ox*24+24 and oy*24<=y<oy*24+24
            obj={'flags':['ALLOW_TERRAIN_UNDER_OTHER_DATA']}
            fields=[dict(field=k,x=x-ox*24,y=y-oy*24,intensity=i,age=t)
                    for k,x,y,t,i in seeds[stage] if inside(x,y)]
            changes=[dict(point='furniture',id=k,x=x-ox*24,y=y-oy*24)
                     for k,x,y in patches[stage] if inside(x,y)]
            if fields:obj['place_fields']=fields
            if changes:obj['set']=changes
            result.append({'type':'mapgen','update_mapgen_id':f'berserk_flora_treehouse_v2_{stage}_{suffix}','object':obj})
    return result


def main():
    for name,data in [('mapgen/flora_manor.json',maps()),('mapgen/flora_treehouse_v2_updates.json',updates())]:
        (MOD/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
