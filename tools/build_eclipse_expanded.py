#!/usr/bin/env python3
"""Build one continuous 72x96 Eclipse field, then split it into twelve OMTs.
Existing OMT IDs and legacy maps are retained. Saved maps are never rebuilt.
"""
import json
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'mods' / 'Berserk'
PREFIX = 'berserk_eclipse_expanded_'
SCENES = [('arrival', 'Eclipse: arrival'), ('traces', 'Eclipse: fallen band'),
 ('cache', 'Eclipse: abandoned supplies'), ('torn', 'Eclipse: torn field'),
 ('crossroads', 'Eclipse: crossroads'), ('feast', 'Eclipse: feast'),
 ('hunt', 'Eclipse: hunting ground'), ('ravine', 'Eclipse: scarred ravine'),
 ('approach', 'Eclipse: final approach'), ('laststand', 'Eclipse: last stand'),
 ('threshold', 'Eclipse: ceremony threshold'), ('ceremony', 'Eclipse: ceremony')]
WIDTH, HEIGHT = 72, 96
MARKERS = {'S': [(11,12)], 'J': [(33,7)], 'I': [(10,41)], 'K': [(61,41)],
 'G': [(65,56)], 'X': [(65,10)], 'H': [(14,57)], 'F': [(59,35)],
 'W': [(34,80)], 'R': [(60,92)], '1': [(60,37)], '2': [(61,37)],
 '3': [(62,37)], '4': [(14,58)], 'B': [(40,61)], 'O': [(39,61)],
 '!': [(59,80)], 'q': [(36,18)], 's': [(55,45)], 't': [(60,88)],
 '5': [(64,11)], '6': [(65,11)]}
ACTORS = [('WRETCH',38,10), ('WRETCH',30,18), ('HUNTER',57,58),
 ('WRETCH',7,32), ('HALF',16,43), ('WRETCH',9,45), ('HALF',31,37), ('WRETCH',43,28),
 ('BUTCHER',67,45), ('WRETCH',56,43), ('HALF',12,67), ('WRETCH',5,53),
 ('HALF',41,67), ('BUTCHER',31,58), ('HALF',60,67), ('HUNTER',67,59),
 ('WRETCH',9,82), ('BUTCHER',17,86), ('HALF',34,89), ('ELITE',53,88),
 ('WRETCH',28,5), ('WRETCH',5,44), ('WRETCH',43,31),
 ('WRETCH',54,38), ('WRETCH',16,69), ('WRETCH',13,89),
 ('HALF',45,45), ('HALF',56,61), ('HUNTER',55,69), ('HUNTER',6,40),
 ('HUNTER',41,54), ('HUNTER',31,84), ('BUTCHER',6,78), ('ELITE',67,88)]
SCENE_SPAWNS = [(62,32), (63,32), (64,32), (19,54), (61,7), (62,7)]
EVENT_ZONES = [(60,37), (61,37), (62,37), (14,58), (64,11), (65,11)]
def scene_id(x,y): return PREFIX + SCENES[3*y+x][0]
def line(a,b):
 length=max(abs(b[0]-a[0]),abs(b[1]-a[1]))
 for n in range(length+1):
  t=n/max(1,length); yield round(a[0]+(b[0]-a[0])*t),round(a[1]+(b[1]-a[1])*t)
def build_field():
 field=[['.' for _ in range(WIDTH)] for _ in range(HEIGHT)]
 def paint(cx,cy,glyph,radius=0):
  for y in range(max(2,cy-radius),min(HEIGHT-2,cy+radius+1)):
   for x in range(max(2,cx-radius),min(WIDTH-2,cx+radius+1)):
    if (x-cx)**2+(y-cy)**2<=radius**2:
     if glyph == 'r' and field[y][x] == 'a':continue
     if glyph == '.' and field[y][x] not in '#PCp':continue
     field[y][x]=glyph
 def stroke(points,glyph,radius):
  for a,b in zip(points,points[1:]):
   for x,y in line(a,b):paint(x,y,glyph,radius)
 for y in range(2,94):
  for x in range(2,70):
   if math.sin(x/5+math.sin(y/9))+math.cos(y/6)>1.2:field[y][x]=','
   elif math.sin((x+y)/11)<-.6:field[y][x]=';'
 # Large flesh folds cross OMT seams: there are no local 24x24 border walls.
 for points,radius in [([(20,4),(21,19),(18,29),(23,43),(21,62),(24,79)],2),
  ([(47,5),(43,20),(48,33),(47,50),(50,66),(48,79)],2),
  ([(3,23),(12,21),(25,24),(35,21)],2), ([(38,27),(51,26),(59,29),(69,27)],2),
  ([(3,48),(15,47),(22,51),(34,48)],2), ([(39,51),(48,48),(58,51),(69,50)],2),
  ([(6,73),(20,72),(27,75),(36,73)],2), ([(44,73),(55,71),(66,74)],2)]:stroke(points,'#',radius)
 for cx,cy,rx,ry in [(39,42,5,5),(29,63,4,6),(9,62,3,4),(54,21,3,3)]:
  for y in range(cy-ry,cy+ry+1):
   for x in range(cx-rx,cx+rx+1):
    if ((x-cx)/rx)**2+((y-cy)/ry)**2<1:field[y][x]='p'
 # A ragged visible cleft separates the ravine's branches. No hidden fall trap.
 for y in range(57,66):
  for x in range(41,48):
   if abs(x-(44+round(math.sin(y/2)))) <= (1 if y in (57,65) else 2):
    field[y][x]='p'
 for x,y in [(64,42),(65,43),(62,44),(63,45)]:field[y][x]='C'
 main=[(11,12),(17,15),(27,13),(35,13),(37,19),(33,27),(36,34),(31,44),(35,52),
       (38,59),(36,68),(35,77),(34,84),(43,86),(51,82),(59,80),(59,86),(63,89)]
 stroke(main,'a',1)
 for n,(x,y) in enumerate(p for a,b in zip(main,main[1:]) for p in line(a,b)):
  if n%7==0:paint(x,y,'a',2)
 branches=[[(17,15),(11,24),(10,34),(10,41),(15,47),(12,56),(14,64),(11,74),(11,84),(24,86),(34,84)],
  [(35,13),(45,12),(59,13),(65,10),(65,20),(65,26),(68,33),(68,43),(60,51),(65,56),(61,65),(58,74),(59,80)],
  [(10,34),(20,33),(36,34),(46,35),(58,35)], [(14,64),(24,55),(35,52)],
  [(38,59),(45,65),(53,61),(65,56)], [(34,84),(34,80)],[(35,13),(33,7)],[(58,35),(61,41)]]
 for points in branches:stroke(points,'r',1)
 # The diaphragm blocks only a shortcut. The main and flank routes stay open.
 stroke([(38,59),(40,61),(44,61),(48,61),(53,61)],'r',1)
 for y in range(56,65):field[y][40]='#'
 field[61][40]='.'
 stroke([(59,33),(64,34),(66,36)],'#',1)
 stroke([(14,25),(15,29)],'#',1)
 stroke([(16,51),(17,55),(20,57)],'#',1)
 stroke([(19,54),(20,52),(23,53),(24,55)],'r',1)
 # The supply pocket is screened to the west/north; its broad east exit remains.
 stroke([(60,8),(61,9),(64,9)],'#',0)
 # The cache creatures have a route around this fold, never onto its solid cells.
 stroke([(61,7),(59,7),(59,12),(62,13)],'r',0)
 stroke([(52,92),(50,88),(53,84)],'#',1)
 stroke([(68,80),(68,86),(67,92)],'#',1)
 for points in MARKERS.values():
  for x,y in points:
   if (x,y)!=(40,61):paint(x,y,'.',1)
 for x,y in SCENE_SPAWNS+[(63,89)]:paint(x,y,'.',1)
 # Connect static actor pockets, without broad corridor carving.
 for _,x,y in ACTORS:
  near=[(xx,yy) for yy in range(max(2,y-8),min(94,y+9))
        for xx in range(max(2,x-8),min(70,x+9)) if field[yy][xx] in 'ar']
  stroke([min(near,key=lambda p:abs(p[0]-x)+abs(p[1]-y)),(x,y)],'r',0)
 for cx,cy in [(36,18),(55,45),(60,88)]:
  for dx,dy in [(-2,0),(-1,0),(0,0),(1,1),(2,1),(0,-1)]:
   if field[cy+dy][cx+dx]!='#':field[cy+dy][cx+dx]='v'
 # A visible, passable lip makes each cleft readable before a step into it.
 for y in range(3,93):
  for x in range(3,69):
   if field[y][x] in '.,;' and any(field[yy][xx]=='p'
       for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):field[y][x]='l'
 for y in range(HEIGHT):
  for x in range(WIDTH):
   if x<2 or x>69 or y<2 or y>93:field[y][x]='%' if (x+y)//5%2 else '&'
 for x,y in [(70,79),(70,85),(70,90),(69,94)]:field[y][x]='@'
 for glyph,points in MARKERS.items():
  for x,y in points:field[y][x]=glyph
 return field

def side_details(field):
 """Furniture is a separate layer: it cannot replace the underlying floor.

 Keep the ash spine, scene markers, actors and event pockets clear. Irregular
 clusters describe specific scenes, including compositions across OMT seams.
 """
 furniture=[]; blood=[]; taken=set()
 protected={p for points in MARKERS.values() for p in points}
 protected.update(SCENE_SPAWNS);protected.update((x,y) for _,x,y in ACTORS)
 def put(id,x,y):
  if (x,y) in protected or (x,y) in taken or field[y][x] not in '.,;rl':return
  furniture.append({'furn':'f_berserk_eclipse_'+id,'x':x,'y':y});taken.add((x,y))
 def cluster(cx,cy):
  for dx,dy in [(-2,0),(-1,-1),(0,0),(1,0),(0,1),(2,1)]:
   put('body_heap_low',cx+dx,cy+dy)
  for dx,dy in [(-1,0),(1,-1)]:put('body_heap_high',cx+dx,cy+dy)
  for dx,dy in [(-2,1),(0,-1),(2,0)]:
   x,y=cx+dx,cy+dy
   if field[y][x] not in '#%&@pPB':blood.append({'field':'fd_blood','x':x,'y':y,'intensity':1,'age':0})
 # Supply train and fleeing victims, with evidence outside the feeding pocket.
 for x,y in [(57,15),(64,15),(66,7),(69,19)]:cluster(x,y)
 for x,y in [(62,11),(62,12),(63,12),(66,12)]:put('cart_wreck',x,y)
 for x,y in [(63,14),(67,11),(60,16)]:put('braided_flesh',x,y)
 put('cart_tally',66,10)
 # Each named casualty has an individual surrounding scene, not a loot chest.
 for x,y in [(30,8),(35,5),(8,39),(13,43),(58,39),(63,43),(62,55),(67,54)]:cluster(x,y)
 for x,y in [(31,9),(35,8),(9,40),(12,40),(59,42),(64,41),(64,57),(67,56)]:put('torn_shield',x,y)
 put('held_gap',7,41)
 # The feast extends around the hollow; the eastern flank stays outside its tokens.
 for x,y in [(55,32),(57,37),(60,45),(64,46),(67,37)]:cluster(x,y)
 for x,y in [(57,34),(58,33),(65,39),(66,40)]:put('braided_flesh',x,y)
 # Hunters' flanking ground: low tangles, stone/bone cover, edge clefts.
 for x,y in [(6,50),(17,62),(9,69),(24,54),(26,56),(52,59),(54,64)]:cluster(x,y)
 for x,y in [(7,55),(7,56),(16,60),(17,60),(22,56),(25,57)]:put('bone_spur',x,y)
 for x,y in [(11,53),(12,53),(13,54),(17,65),(18,65),(22,64)]:put('braided_flesh',x,y)
 for x,y in [(12,60),(11,61),(14,62),(26,58),(42,63),(48,63)]:put('congealed_vein',x,y)
 put('broken_crossing',38,62)
 # Ragged shield line and scattered weapons show a final retreat, not an armory.
 for x,y in [(6,79),(14,80),(20,85),(26,83),(25,86)]:cluster(x,y)
 for x,y in [(7,83),(8,83),(9,84),(14,83),(15,83),(17,84)]:put('shield_barricade',x,y)
 for x,y in [(8,81),(11,86),(16,82),(21,82),(23,85),(28,84)]:put('torn_shield',x,y)
 put('last_retreat',12,82)
 # Sparse details at the threshold; the center of the final fight is untouched.
 for x,y in [(38,77),(46,81),(55,77)]:cluster(x,y)
 for x,y in [(57,79),(60,78),(62,82)]:put('congealed_vein',x,y)
 loot=[{'group':'berserk_eclipse_last_retreat_gear','x':21,'y':82,'chance':100}]
 return furniture,blood,loot

def build_scene(x,y,field=None):
 field=build_field() if field is None else field
 obj={'rows':[''.join(row[24*x:24*x+24]) for row in field[24*y:24*y+24]],
      'palettes':['berserk_eclipse_flesh_palette']}
 monsters=[{'group':'GROUP_BERSERK_ECLIPSE_'+kind,'x':ax%24,'y':ay%24}
           for kind,ax,ay in ACTORS if (ax//24,ay//24)==(x,y)]
 if monsters:obj['place_monster']=monsters
 bodies=[('judeau',33,7,'berserk_judeau_knife_hilt'),('pippin',10,41,'berserk_pippin_broken_clasp'),
         ('corkus',61,41,'berserk_corkus_scabbard_fragment'),('gaston',65,56,'berserk_gaston_sewing_roll')]
 for person,bx,by,memory in bodies:
  if (bx//24,by//24)==(x,y):
   obj.setdefault('place_item',[]).extend([
    {'item':f'berserk_eclipse_{person}_body','x':bx%24,'y':by%24,'amount':1},
    {'item':memory,'x':bx%24,'y':by%24,'amount':1}])
   obj.setdefault('place_loot',[]).append({'group':f'berserk_eclipse_{person}_gear','x':bx%24,'y':by%24,'chance':100})
 if (x,y)==(2,0):obj['place_loot']=[{'group':'berserk_eclipse_supply_cache','x':17,'y':10,'chance':100}]
 if (x,y)==(0,3):
  obj['place_loot']=[{'group':'berserk_location_cloth_dressings','x':11,'y':12,'chance':100}]
  obj['place_item']=[{'item':'berserk_eclipse_last_stand_note','x':11,'y':12,'amount':1}]
 furniture,blood,loot=side_details(field)
 for key,entries in [('place_furniture',furniture),('place_fields',blood),('place_loot',loot)]:
  selected=[{**p,'x':p['x']%24,'y':p['y']%24} for p in entries
            if (p['x']//24,p['y']//24)==(x,y)]
  if selected:obj.setdefault(key,[]).extend(selected)
 # Existing handlers create Griffith only upon final entry, and hold him still.
 return {'type':'mapgen','om_terrain':[scene_id(x,y)],'object':obj}
def main():
 field=build_field()
 (ROOT/'mapgen/eclipse_expanded.json').write_text(json.dumps(
  [build_scene(x,y,field) for y in range(4) for x in range(3)],ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
