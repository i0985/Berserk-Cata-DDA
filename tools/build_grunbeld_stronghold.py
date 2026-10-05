#!/usr/bin/env python3
"""One continuous 48x72 occupied siege stronghold, divided into six legacy OMTs."""
import json
import random
from pathlib import Path
MOD=Path(__file__).resolve().parents[1]/'mods/Berserk'
SECTIONS=[('berserk_grunbeld_approach',0,0),('berserk_grunbeld_ramparts',1,0),
          ('berserk_grunbeld_quarry',0,1),('berserk_grunbeld_barracks',1,1),
          ('berserk_grunbeld_ruins',0,2),('berserk_grunbeld_crucible',1,2)]
SPAWNS=[(30,54),(41,54),(30,65),(41,65)]
SEAL=(36,55);TRACKS=(36,60)

def build():
    a=[['.']*48 for _ in range(72)];props=[]
    def rect(x1,y1,x2,y2,c):
        for y in range(y1,y2+1):
            for x in range(x1,x2+1):a[y][x]=c
    def room(x1,y1,x2,y2):
        rect(x1,y1,x2,y2,'_')
        for x in range(x1,x2+1):a[y1][x]=a[y2][x]='#'
        for y in range(y1,y2+1):a[y][x1]=a[y][x2]='#'
    def prop(fid,x,y):
        assert (x,y) not in {(xx,yy) for _,xx,yy in props},(fid,x,y)
        props.append((fid,x,y))
    rng=random.Random(3013)
    for y in range(72):
        for x in range(48):
            if (x<3 or x>45) and rng.random()<.3:a[y][x]='T'
    # Broken siege lines outside the gate: cover, wrecked mantlets, two approaches.
    rect(10,0,14,26,'d');rect(9,20,30,24,'d')
    for box in [(5,7,9,8),(18,10,23,10),(31,6,36,7),(35,12,40,12)]:rect(*box,'s')
    for p in [(8,8),(20,10),(35,7)]:a[p[1]][p[0]]='d'
    for x,y in [(6,10),(7,10),(24,8),(25,8),(33,10),(36,14),(17,14)]:prop('f_rubble',x,y)
    prop('f_berserk_grunbeld_scene',5,18)
    prop('f_berserk_grunbeld_siege_orders',18,6)
    prop('f_berserk_grunbeld_evacuated_cart',6,12)
    for x,y in [(19,12),(34,9)]:prop('f_berserk_grunbeld_wagon_wreck',x,y)
    for x,y in [(7,6),(21,14),(38,10)]:prop('f_berserk_grunbeld_broken_mantlet',x,y)
    for x,y in [(9,10),(26,7),(18,13)]:prop('f_berserk_grunbeld_split_spears',x,y)
    prop('f_firering',16,9)
    # Castle perimeter spans OMT seams; the north gate and quarry break are open.
    for x in range(4,45):a[16][x]='#';a[68][x]='#'
    for y in range(16,69):a[y][4]=a[y][44]='#'
    rect(10,15,14,18,'d');rect(1,26,12,28,'d');rect(4,45,8,49,'q')
    rect(25,23,29,53,'d');rect(8,25,12,47,'q')
    rect(8,45,18,50,'q');rect(15,48,27,52,'q')
    # Arsenal and gate service room in the northeast.
    room(31,17,42,27)
    for y in range(18,27):a[y][36]='#'
    a[23][31]='+';a[23][36]='+';a[27][39]='+'
    prop('f_berserk_grunbeld_record',9,20)
    prop('f_berserk_grunbeld_garrison_roll',19,21)
    prop('f_berserk_grunbeld_armory',39,20)
    prop('f_berserk_flora_wooden_rack',38,18);prop('f_berserk_flora_wooden_rack',40,18)
    prop('f_table',33,20);prop('f_berserk_flora_wooden_chair',34,20)
    prop('f_berserk_grunbeld_ration_store',33,25)
    for x,y in [(16,19),(21,26),(42,29)]:prop('f_rubble',x,y)
    # Quarry is a long bend, with raw faces and a connecting breach rather than a box.
    for box in [(6,31,7,36),(14,29,17,32),(17,36,20,40),(6,40,7,43),(12,43,15,45)]:rect(*box,'R')
    rect(8,32,11,44,'q');rect(8,40,16,42,'q');rect(15,39,16,48,'q')
    prop('f_berserk_grunbeld_quarry_note',11,30)
    prop('f_berserk_grunbeld_quarry_rope',15,35)
    prop('f_berserk_grunbeld_quarry_hoist',15,34)
    prop('f_berserk_flora_wooden_crate',9,38);prop('f_rubble',19,43)
    # Barracks: sleeping squad, dressing room, kitchen and repair stores.
    room(27,30,42,44)
    for y in range(31,44):a[y][35]='#'
    for x in range(36,42):a[37][x]='#'
    for x,y in [(30,30),(35,34),(35,40),(38,37),(30,44),(27,39),(42,40)]:a[y][x]='+'
    # Eight straw pallets in two rows with a clear two-cell central aisle.
    for x in (29,32):
        for y in (32,35,38,41):prop('f_straw_bed',x,y)
    for x,y in [(28,33),(33,33)]:prop('f_berserk_flora_wooden_bench',x,y)
    for x,y in [(28,43),(33,43)]:prop('f_berserk_flora_wooden_rack',x,y)
    prop('f_berserk_grunbeld_soldier_letter',33,31)
    # A separate infirmary has actual beds and a dressing table.
    prop('f_straw_bed',37,32);prop('f_straw_bed',40,32)
    prop('f_table',38,34);prop('f_berserk_grunbeld_dressing_store',40,34)
    prop('f_berserk_grunbeld_dresser_note',37,35)
    prop('f_clay_oven',40,38);prop('f_table',37,40)
    prop('f_berserk_flora_wooden_chair',38,40)
    prop('f_berserk_grunbeld_barrack_pantry',40,42)
    # Repair stores are by the working court, not in a sleeping-room corner.
    prop('f_berserk_flora_wooden_worktop',23,37)
    prop('f_berserk_grunbeld_repair_store',23,40)
    prop('f_berserk_flora_wooden_crate',21,40)
    prop('f_berserk_grunbeld_split_spears',22,35)
    # The inner defense is broken at two well-separated routes.
    for x in range(17,44):a[47][x]='#'
    rect(17,46,20,48,'q');rect(26,46,30,49,'d');rect(38,46,40,49,'d')
    prop('f_berserk_grunbeld_inner_warning',27,49)
    for x,y in [(23,46),(24,46),(36,47),(37,47)]:
        a[y][x]='d';prop('f_rubble',x,y)
    # Burned repair court, smith's room and the former ceremonial hall.
    room(6,53,19,65);a[58][19]='+';a[53][12]='+';a[65][12]='+'
    rect(7,54,18,64,'i')
    prop('f_berserk_grunbeld_smith_hearth',8,56)
    prop('f_berserk_grunbeld_anvil_stump',10,56)
    prop('f_workbench',12,58)
    prop('f_berserk_flora_wooden_crate',17,57)
    prop('f_berserk_flora_wooden_rack',7,60)
    prop('f_berserk_grunbeld_split_spears',14,60)
    prop('f_berserk_grunbeld_smith_note',16,55)
    prop('f_berserk_grunbeld_forge_store',17,59)
    prop('f_berserk_grunbeld_heat_clothing',8,62)
    prop('f_berserk_grunbeld_standard_keepsake',16,63)
    rect(20,55,29,61,'d');rect(10,66,35,67,'d');rect(34,65,37,71,'d')
    rect(28,50,43,67,'a')
    # Burned silhouette north of the arena; it shelters the northern spawn cells.
    for box in [(28,50,31,51),(37,50,42,51)]:rect(*box,'s')
    # Four separated broken pillars preserve legacy hidden candidate cells.
    for box in [(31,53,31,55),(40,53,40,55),(31,64,32,66),(40,64,40,66),
                (28,57,29,58),(42,60,43,61)]:rect(*box,'s')
    # Boss trigger and original seal coordinates stay in the southeast OMT.
    prop('f_berserk_grunbeld_breach',*SEAL);prop('f_berserk_hunt_arena_tracks',*TRACKS)
    prop('f_berserk_grunbeld_last_warning',36,52)
    prop('f_berserk_grunbeld_fallen_garrison',25,64)
    # Two independent arena approaches and a southern exit cross chunk seams.
    rect(24,58,30,60,'d');rect(34,48,36,54,'d');rect(34,67,37,71,'d')
    for p in SPAWNS:assert a[p[1]][p[0]] in 'ad_',p
    actors=[('mon_berserk_eclipse_halfbreed',21,23),('mon_berserk_eclipse_halfbreed',28,25),
            ('mon_berserk_eclipse_butcher',18,34),('mon_berserk_eclipse_elite',31,39),
            ('mon_berserk_eclipse_halfbreed',23,54),('mon_berserk_eclipse_butcher',38,61)]
    rustic={'f_table':'f_berserk_flora_pegged_table','f_workbench':'f_berserk_flora_wooden_worktop'}
    props=[(rustic.get(k,k),x,y) for k,x,y in props]
    for _,x,y in props:assert a[y][x] not in '#sRT+',('prop on obstacle',x,y,a[y][x])
    for _,x,y in actors:assert a[y][x] not in '#sRT+',('actor on obstacle',x,y)
    return a,props,actors

def maps():
    a,props,actors=build();out=[]
    for omt,ox,oy in SECTIONS:
        x0,y0=24*ox,24*oy
        obj={'fill_ter':'t_grass','rows':[''.join(row[x0:x0+24]) for row in a[y0:y0+24]],'palettes':['berserk_grunbeld_detail_palette'],
             'place_furniture':[{'furn':k,'x':x-x0,'y':y-y0} for k,x,y in props if x0<=x<x0+24 and y0<=y<y0+24],
             'place_monster':[{'monster':k,'x':x-x0,'y':y-y0,'chance':100,'one_or_none':True} for k,x,y in actors if x0<=x<x0+24 and y0<=y<y0+24]}
        out.append({'type':'mapgen','om_terrain':[omt],'object':obj})
    return out

def main():
    p=MOD/'mapgen/apostle_grunbeld.json';old=json.loads(p.read_text());palettes=[o for o in old if o['type']=='palette']
    p.write_text(json.dumps(palettes+maps(),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
