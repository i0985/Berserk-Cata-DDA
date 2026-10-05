#!/usr/bin/env python3
"""Build block C's encounter maps, retaining OMT IDs and relic coordinates.

This edits new-map definitions only. It does not update generated save maps,
special placement, quests, rewards, or guardian balance.
"""
import json
import random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'mods/Berserk/mapgen/behelit_sites.json'


class Layout:
    def __init__(self,width,height,fill):
        self.grid=[[fill]*width for _ in range(height)]
        self.width=width;self.height=height
        self.furniture=[];self.loot=[];self.monsters=[];self.fields=[];self.groups=[]

    def put(self,x,y,c):
        assert 0<=x<self.width and 0<=y<self.height,(x,y)
        self.grid[y][x]=c

    def rect(self,x1,y1,x2,y2,c):
        for y in range(y1,y2+1):
            for x in range(x1,x2+1):self.put(x,y,c)

    def room(self,x1,y1,x2,y2,floor='_'):
        self.rect(x1,y1,x2,y2,'#');self.rect(x1+1,y1+1,x2-1,y2-1,floor)

    def ellipse(self,cx,cy,rx,ry,c):
        for y in range(max(0,cy-ry),min(self.height,cy+ry+1)):
            for x in range(max(0,cx-rx),min(self.width,cx+rx+1)):
                if ((x-cx)/rx)**2+((y-cy)/ry)**2<=1:self.put(x,y,c)

    def trail(self,points,radius,c):
        for a,b in zip(points,points[1:]):
            steps=max(abs(a[0]-b[0]),abs(a[1]-b[1]))
            for i in range(steps+1):
                x=round(a[0]+(b[0]-a[0])*i/max(1,steps))
                y=round(a[1]+(b[1]-a[1])*i/max(1,steps))
                for yy in range(y-radius,y+radius+1):
                    for xx in range(x-radius,x+radius+1):
                        if 0<=xx<self.width and 0<=yy<self.height:self.put(xx,yy,c)

    def furnish(self,x,y,id):
        assert self.grid[y][x] not in '#TG',(id,x,y,self.grid[y][x])
        assert not any(f['x']==x and f['y']==y for f in self.furniture),(id,x,y)
        self.furniture.append({'furn':id,'x':x,'y':y})

    def item(self,x,y,id,**extra):
        # place_loot has neither amount nor damage in 0.I-1. Repeated ordinary
        # spawns and named item groups handle counts and actual damage.
        count=extra.pop('amount',1)
        if 'damage' in extra:
            assert (id,extra.pop('damage')) in [('hatchet',3),('crowbar',1)]
            spec={'group':'berserk_behelit_worn_'+id}
        else:spec={'item':id}
        assert not extra,extra
        for _ in range(count):self.loot.append({**spec,'x':x,'y':y,'chance':100})

    def monster(self,x,y,id):
        self.monsters.append({'monster':id,'x':x,'y':y,'one_or_none':True})

    def field(self,x,y,id,intensity=1):
        self.fields.append({'field':id,'x':x,'y':y,'intensity':intensity,'age':0})

    def tile(self,xoff,yoff,palette):
        obj={'rows':[''.join(row[xoff:xoff+24]) for row in self.grid[yoff:yoff+24]],
             'palettes':[palette]}
        for key,entries in [('place_furniture',self.furniture),('place_loot',self.loot),
                            ('place_monster',self.monsters),('place_fields',self.fields),
                            ('place_items',self.groups)]:
            selected=[]
            for entry in entries:
                if xoff<=entry['x']<xoff+24 and yoff<=entry['y']<yoff+24:
                    selected.append({**entry,'x':entry['x']-xoff,'y':entry['y']-yoff})
            if selected:obj[key]=selected
        return obj


def expedition():
    m=Layout(24,24,'.')
    for x,y,c in [(0,5,'T'),(0,16,'T'),(23,3,'T'),(23,20,'T'),(3,23,'T'),
                  (21,23,'T'),(0,4,'h'),(23,7,'h'),(1,18,'u'),(22,22,'u')]:m.put(x,y,c)
    m.rect(2,1,21,1,'P');m.rect(2,22,21,22,'P')
    m.rect(1,2,1,21,'P');m.rect(22,2,22,21,'P')
    m.rect(11,0,12,23,',');m.rect(2,11,23,12,',')
    m.rect(22,11,23,12,',')  # second break, in the eastern cordon
    for box in [(3,3,9,9),(15,3,21,9),(3,14,9,21),(14,14,21,21)]:m.room(*box)
    for x,y,c in [(9,6,'+'),(15,6,'D'),(9,17,'+'),(14,18,'+'),(5,6,'?'),
                  (18,6,'A'),(2,20,'N')]:m.put(x,y,c)
    # Damage belongs to the tents: one torn corner, one ripped roof/wall line.
    for x,y in [(3,14),(3,15),(19,14),(20,14),(21,14)]:
        m.put(x,y,'_');m.furnish(x,y,'f_berserk_expedition_torn_canvas')
    for x,y,id in [(7,5,'f_berserk_expedition_scene'),(6,6,'f_chair_folding'),
                   (8,7,'f_crate_o'),(7,4,'f_table'),
                   (8,17,'f_berserk_location_expedition_medical'),(7,16,'f_table'),
                   (7,18,'f_chair_folding'),(19,18,'f_berserk_location_expedition_tools'),
                   (16,18,'f_crate_o'),(18,20,'f_crate_o'),(16,16,'f_table'),
                   (16,5,'f_berserk_expedition_sample_diagram'),
                   (10,21,'f_berserk_expedition_approach_note')]:m.furnish(x,y,id)
    for x,y in [(4,5),(4,7),(4,16),(4,19)]:m.item(x,y,'sleeping_bag_roll')
    m.item(7,5,'berserk_expedition_transfer_note')
    m.item(10,21,'berserk_expedition_alarm_note')
    m.item(8,7,'bottle_plastic');m.item(7,16,'scrap_cotton',amount=2)
    m.groups.append({'item':'cannedfood','x':16,'y':18,'chance':65})
    m.monster(20,8,'mon_berserk_expedition_guardian')
    m.monster(18,17,'mon_berserk_eclipse_wretch')
    m.monster(18,2,'mon_berserk_eclipse_wretch')
    for x,y in [(20,10),(20,12),(18,17),(4,15)]:m.field(x,y,'fd_blood')
    return m


def chapel():
    m=Layout(24,48,'.')
    for x,y,c in [(1,8,'T'),(22,5,'h'),(22,13,'T'),(1,29,'h'),(22,34,'T'),
                  (2,46,'T'),(20,46,'u'),(1,21,'u')]:m.put(x,y,c)
    m.room(3,3,20,42)
    # A small apse, long nave and service aisles cross the OMT seam.
    for x,y in [(3,3),(4,3),(19,3),(20,3),(3,4),(20,4)]:m.put(x,y,'.')
    for x,y in [(5,3),(18,3),(4,4),(19,4)]:m.put(x,y,'#')
    m.rect(8,14,8,35,'#');m.rect(15,14,15,35,'#')
    m.rect(8,4,8,13,'#');m.put(8,11,'+')
    for x,y in [(8,17),(8,27),(15,17),(15,29)]:m.put(x,y,'+')
    m.rect(15,12,19,12,'#');m.put(17,12,'+')
    m.rect(15,22,19,22,'#');m.put(17,22,'+')
    m.rect(15,31,19,31,'#');m.put(17,31,'+')
    m.rect(4,35,8,35,'#');m.put(6,35,'+')
    m.rect(9,36,9,40,'#');m.put(9,38,'+')
    m.rect(10,38,14,38,'#');m.put(11,38,'+');m.put(12,38,'+')
    m.put(11,42,'+');m.put(12,42,'+')
    m.rect(11,43,12,47,',')
    m.put(3,37,'/');m.put(3,38,'/')  # broken side wall, behind the bell room
    for x,y in [(20,18),(20,26),(3,23),(3,30)]:m.put(x,y,'w')
    for x,y in [(1,37),(1,39),(1,41),(5,45),(7,46)]:m.put(x,y,'G')
    m.put(12,6,'A');m.put(6,39,'N');m.put(12,40,'?')
    for x,y in [(9,25),(10,25),(13,25),(14,25),(9,29),(10,29),(13,29),
                (14,29),(10,33),(13,33)]:m.furnish(x,y,'f_bench_wooden')
    for x,y in [(10,9),(11,9),(12,9),(13,9),(14,9)]:m.furnish(x,y,'f_berserk_chapel_altar')
    for x,y,id in [(13,7,'f_berserk_chapel_scene'),(18,14,'f_bookcase'),(18,15,'f_bookcase'),
                   (17,16,'f_table'),(17,25,'f_rack_wood'),(18,25,'f_rack_wood'),
                   (18,27,'f_berserk_location_chapel_pantry'),(16,36,'f_table'),
                   (17,36,'f_chair'),(18,38,'f_makeshift_bed'),(18,39,'f_makeshift_bed'),
                   (17,37,'f_berserk_location_chapel_aid'),(5,40,'f_crate_o'),
                   (5,38,'f_rubble'),(10,34,'f_rubble'),(16,8,'f_berserk_chapel_vigil'),
                   (5,6,'f_rack_wood'),(6,8,'f_table'),(5,9,'f_chair')]:m.furnish(x,y,id)
    for x,y in [(9,16),(14,16),(9,21),(14,21)]:m.furnish(x,y,'f_berserk_chapel_stone_pillar')
    m.item(17,16,'berserk_chapel_ritual_note')
    m.item(16,8,'berserk_chapel_last_vigil')
    for x,y in [(18,38),(18,39)]:m.item(x,y,'blanket')
    m.item(16,36,'scrap_cotton',amount=2)
    m.loot.append({'group':'berserk_location_chapel_candles','x':5,'y':40,'chance':100})
    m.groups.append({'item':'religious_books','x':18,'y':14,'chance':60})
    m.monster(12,12,'mon_berserk_chapel_guardian')
    m.monster(13,31,'mon_berserk_eclipse_wretch')
    m.monster(6,25,'mon_berserk_eclipse_wretch')
    for x,y in [(12,10),(11,32),(4,38)]:m.field(x,y,'fd_blood')
    return m


def oak():
    m=Layout(24,24,'.');rng=random.Random(30405)
    for y in range(24):
        for x in range(24):
            if (x<3 or x>21 or y<3 or y>21) and rng.random()<0.46:m.put(x,y,'T')
            elif rng.random()<0.035:m.put(x,y,'T')
    m.ellipse(12,12,6,5,'d')
    m.trail([(4,23),(5,20),(5,17),(8,15),(10,14),(12,13)],0,'d')
    m.trail([(5,20),(15,21),(20,18),(20,7),(21,5)],0,'d')
    m.trail([(12,13),(16,14),(18,11),(20,7),(21,5)],0,'d')
    m.trail([(8,15),(5,10),(4,5),(0,5)],0,'d')
    roots=[(8,7),(9,7),(8,8),(7,9),(7,10),(8,11),(8,12),(7,14),
           (16,7),(16,8),(17,8),(17,9),(17,10),(16,11),
           (9,15),(9,16),(10,16),(11,17),(15,15),(15,16),(14,16),(14,17)]
    for x,y in roots:m.put(x,y,'R')
    m.rect(11,10,13,12,'K');m.put(12,12,'A')
    fragments=[(11,10,'nw'),(12,10,'n'),(13,10,'ne'),(11,11,'w'),
               (13,11,'e'),(11,12,'sw'),(13,12,'se')]
    # Explicit trunk furniture is assigned after splitting: K provides its base.
    for x,y,suffix in fragments:
        m.furniture.append({'furn':'f_berserk_oak_trunk_'+suffix,'x':x,'y':y})
    for x,y in [(18,5),(19,5),(18,6),(18,7),(19,9),(19,10)]:m.put(x,y,'T')
    m.put(21,5,'N');m.put(5,20,'C');m.put(16,20,'F');m.put(8,17,'W')
    for x,y,id in [(4,21,'f_berserk_oak_cart_tracks'),(6,21,'f_crate_o'),
                   (16,19,'f_firering'),(6,16,'f_berserk_oak_visitor_remains'),
                   (10,8,'f_berserk_oak_low_roots'),(15,13,'f_berserk_oak_low_roots')]:
        m.put(x,y,'d');m.furnish(x,y,id)
    m.item(6,21,'hatchet',damage=3)
    m.item(6,16,'scrap_cotton',amount=2)
    m.monster(12,9,'mon_berserk_cursed_oak_guardian')
    m.monster(5,8,'mon_berserk_eclipse_wretch')
    m.monster(20,14,'mon_berserk_eclipse_wretch')
    m.field(7,16,'fd_blood');m.field(10,14,'fd_blood')
    return m


def cave():
    m=Layout(48,48,'#')
    m.ellipse(12,12,5,5,'.')
    m.trail([(15,12),(18,12),(18,9),(24,9),(29,12)],1,'.')
    m.ellipse(31,13,10,7,'.')
    m.trail([(36,15),(41,18),(42,24),(42,28),(39,31)],2,'.')
    m.ellipse(37,33,8,7,'.')
    # Quiet, winding outer route, with two usable connections to the gallery.
    m.trail([(11,15),(10,19),(8,23),(10,27),(14,31),(20,35),(28,35),(31,33)],1,'.')
    m.ellipse(9,34,6,5,'.')
    m.trail([(9,31),(10,27)],1,'.')
    m.trail([(14,23),(19,25),(25,24),(29,21),(31,18)],1,'.')
    m.trail([(22,35),(25,30),(29,26),(31,23)],1,'.')
    # Small camp in a side pocket, reached from the quiet route.
    m.ellipse(15,28,4,3,'.')
    m.trail([(12,28),(15,28)],1,'.')
    # One-cell return chute. Both sides are solid, so the brace is meaningful.
    m.trail([(15,13),(18,13),(21,13),(21,22),(19,25)],0,'.')
    m.rect(20,14,20,19,'#');m.rect(22,14,22,19,'#')
    m.put(21,16,'B');m.put(21,18,'H')
    # Pillars and bends screen the entrance and break up the broad chambers.
    for box in [(28,9,29,11),(34,14,35,16),(38,28,39,30),
                (32,35,33,36),(40,36,41,37)]:m.rect(*box,'#')
    for y in range(7,21):
        for x in range(22,42):
            if m.grid[y][x]=='.' and (x+2*y)%5 in (0,1):m.put(x,y,'s')
    m.put(12,12,'U');m.put(36,29,'A');m.put(6,34,'N')
    for x,y in [(32,8),(42,22),(34,38)]:m.put(x,y,'L')
    for x,y,id in [(9,12,'f_berserk_location_cave_scout'),(31,11,'f_berserk_cave_claw_marks'),
                   (23,32,'f_berserk_cave_return_marks'),(12,27,'f_berserk_location_cave_lamp'),
                   (13,28,'f_crate_o'),(14,28,'f_firering'),
                   (17,29,'f_berserk_cave_broken_support'),(8,35,'f_rubble'),
                   (27,12,'f_rubble'),(43,32,'f_rubble')]:m.furnish(x,y,id)
    m.item(17,30,'crowbar',damage=1);m.item(17,30,'rope_6')
    m.item(17,29,'berserk_cave_last_scrap')
    m.monster(39,35,'mon_berserk_echo_cave_guardian')
    m.monster(37,16,'mon_berserk_eclipse_wretch')
    m.monster(18,33,'mon_berserk_eclipse_wretch')
    for x,y in [(30,12),(18,30),(35,32)]:m.field(x,y,'fd_blood')
    return m


def cave_surface():
    # Keep the ladder at the same coordinate while giving the approach a camp.
    m=Layout(24,24,'g')
    m.ellipse(12,9,8,7,'#');m.ellipse(12,11,4,5,'d')
    m.trail([(12,23),(12,15),(12,12)],0,'d');m.put(12,12,'V')
    for x,y,c in [(3,3,'T'),(20,5,'T'),(4,19,'T'),(20,21,'T'),
                  (6,17,'u'),(18,18,'h')]:m.put(x,y,c)
    m.furnish(10,15,'f_rubble');m.item(10,15,'stick',amount=2)
    m.field(12,17,'fd_blood')
    return m


def build():
    chapel_map=chapel();cave_map=cave()
    replacements={
      'berserk_cursed_oak':oak().tile(0,0,'berserk_oak_site_palette'),
      'berserk_echo_cave_entrance':cave_surface().tile(0,0,'berserk_cave_entrance_palette'),
      'berserk_lost_expedition':expedition().tile(0,0,'berserk_expedition_site_palette'),
      'berserk_desecrated_chapel_reliquary':chapel_map.tile(0,0,'berserk_chapel_site_palette'),
      'berserk_desecrated_chapel_nave':chapel_map.tile(0,24,'berserk_chapel_site_palette'),
      'berserk_echo_cave_depth':cave_map.tile(0,0,'berserk_cave_depth_palette'),
      'berserk_echo_cave_gallery':cave_map.tile(24,0,'berserk_cave_depth_palette'),
      'berserk_echo_cave_passage':cave_map.tile(0,24,'berserk_cave_depth_palette'),
      'berserk_echo_cave_relic_chamber':cave_map.tile(24,24,'berserk_cave_depth_palette')}
    data=json.loads(TARGET.read_text())
    found=set()
    for obj in data:
        if 'om_terrain' not in obj:continue
        name=obj['om_terrain'][0]
        if name in replacements:obj['object']=replacements[name];found.add(name)
    assert found==set(replacements),(found,set(replacements))
    TARGET.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('Built 9 new-map definitions; existing relic updates retained.')


if __name__=='__main__':build()
