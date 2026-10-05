#!/usr/bin/env python3
"""Static geometry/content audit. Does not launch CDDA or simulate its AI."""
import argparse
import json
from collections import Counter, deque
from pathlib import Path
from build_eclipse_expanded import ACTORS, EVENT_ZONES, MARKERS, SCENE_SPAWNS, ROOT, build_field, build_scene, line, side_details

BLOCKED = set('#%&@PCBp')
START, FINAL = (12, 12), (63, 89)
DETAIL_DEFS = {o['id']:o for o in json.loads((ROOT/'furniture/eclipse_sidepath_details.json').read_text())}

def reachable(field, start=START, excluded=None, allowed=None, furniture=None):
    if furniture is None:furniture = {(o['x'],o['y']):o['furn'] for o in side_details(field)[0]}
    dist = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for xx, yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            pos = xx, yy
            if pos in dist or not (0 <= xx < 72 and 0 <= yy < 96):
                continue
            if field[yy][xx] in BLOCKED or (excluded and excluded(xx,yy)):
                continue
            if DETAIL_DEFS.get(furniture.get(pos),{}).get('move_cost_mod',0)<0:
                continue
            if allowed is not None and field[yy][xx] not in allowed:
                continue
            dist[pos] = dist[x,y]+1
            queue.append(pos)
    return dist

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vanilla-data',type=Path)
    parser.add_argument('--render',type=Path)
    parser.add_argument('--legacy-maps',type=Path,help='An earlier eclipse_expanded.json for partial-map seam checks')
    args=parser.parse_args()
    field = build_field()
    maps = json.loads((ROOT/'mapgen/eclipse_expanded.json').read_text())
    assert maps == [build_scene(x,y,field) for y in range(4) for x in range(3)], 'regenerate field JSON'
    palette = json.loads((ROOT/'mapgen/eclipse_palettes.json').read_text())[-1]
    for entry in maps:
        rows = entry['object']['rows']
        assert len(rows)==24 and all(len(row)==24 for row in rows)
        assert set(''.join(rows)) <= set(palette['terrain'])
    dist = reachable(field)
    for glyph, points in MARKERS.items():
        if glyph != 'B':
            assert all(pos in dist for pos in points), (glyph,points)
    assert all((x,y) in dist for _,x,y in ACTORS)
    assert all(pos in dist for pos in SCENE_SPAWNS+[FINAL])
    assert FINAL in reachable(field, allowed=set('avqstSJW!Rt')), 'ash trail is interrupted'
    zones = EVENT_ZONES
    assert FINAL in reachable(field, excluded=lambda x,y:any(max(abs(x-a),abs(y-b))<=3 for a,b in zones))
    # Both east/west side routes reach the threshold even when the central spine is removed.
    for direction, boundary in [('west', 24),('east', 48)]:
        start = (11,41) if direction=='west' else (68,40)
        target = (11,84) if direction=='west' else (59,80)
        cut = (lambda x,y:x>=boundary) if direction=='west' else (lambda x,y:x<boundary)
        assert target in reachable(field,start,excluded=cut), direction
    for token, spawn in zip(zones,SCENE_SPAWNS):
        assert any(field[y][x]=='#' for x,y in list(line(token,spawn))[1:-1]), (token,spawn)
    assert not any(all(field[y][x] not in '#%&@B' for x,y in list(line(START,(ax,ay)))[1:-1])
                   for _,ax,ay in ACTORS), 'arrival has an unobstructed actor ray'
    closed = reachable(field,(39,61)).get((41,61))
    opened = [row[:] for row in field]; opened[61][40]='.'
    assert reachable(opened,(39,61))[(41,61)] < closed
    events = json.loads((ROOT/'effects/eclipse_field_events.json').read_text())
    events = {o['id']:o for o in events}
    spawns=[]
    for name in ('FEAST_ONE','FEAST_TWO','FEAST_THREE','SIDE_HUNTER','CACHE_ONE','CACHE_TWO'):
        start=events['EOC_BERSERK_ECLIPSE_'+name+'_START']
        spawn=start['effect'][-1]['then']
        assert spawn['real_count']==1 and spawn['min_radius']==spawn['max_radius']==0
        assert spawn['target_var']=={'context_val':'berserk_field_spawn'}
        assert start['effect'][-1]['if']=={'not':{'u_can_see_location':{'context_val':'berserk_field_spawn'}}}
        assert 'u_transform_radius' in events[spawn['true_eocs'][0]]['effect'][0]
        spawns.append(spawn['u_spawn_monster'])
    counts=Counter(kind for kind,_,_ in ACTORS)
    counts.update({'WRETCH':4,'HALF':1,'HUNTER':1})
    assert counts=={'WRETCH':18,'HALF':9,'HUNTER':7,'BUTCHER':4,'ELITE':2}
    assert not any('griffith' in a.get('monster','') or 'griffith' in a.get('group','')
                   for o in maps for a in o['object'].get('place_monster',[]))
    furniture,blood,loot=side_details(field)
    for f in furniture:
        pos=f['x'],f['y']
        assert pos in dist or any(q in dist for q in ((pos[0]-1,pos[1]),(pos[0]+1,pos[1]),(pos[0],pos[1]-1),(pos[0],pos[1]+1))),('inaccessible detail',f)
        assert field[pos[1]][pos[0]] not in BLOCKED | set('a'),('detail blocks route/floor',f)
    for p in loot:
        assert (p['x'],p['y']) in dist,('inaccessible loot',p)
        assert not set(p).intersection({'amount','damage','charges'}),p
    assert len(furniture)>100,'side branches were not filled'
    # The clefts are visible, impassable geometry, without an invisible falling trap.
    terrains={o['id']:o for o in json.loads((ROOT/'mapgen/eclipse_palettes.json').read_text()) if o['type']=='terrain'}
    cleft=terrains['t_berserk_eclipse_open_chasm']
    assert cleft['move_cost']==0 and 'trap' not in cleft and 'NO_FLOOR' not in cleft['flags']
    if args.vanilla_data:
        from audit_behelit_adventures import catalog,merged
        cat=catalog(args.vanilla_data);cat.update(catalog(ROOT))
        for f in furniture:
            obj=merged(cat,'furniture',f['furn'])
            assert obj,('unknown furniture',f)
            assert any((kind,obj['looks_like']) in cat for kind in ('terrain','furniture','ITEM')),obj
            for p in obj.get('bash',{}).get('items',[]):assert ('ITEM',p['item']) in cat,p
        for obj in maps:
            obj=obj['object']
            for p in obj.get('place_loot',[]):
                kind='item_group' if 'group' in p else 'ITEM'
                assert (kind,p.get('group',p.get('item'))) in cat,p
            for p in obj.get('place_item',[]):assert ('ITEM',p['item']) in cat,p
            for p in obj.get('place_fields',[]):assert ('field_type',p['field']) in cat,p
    if args.legacy_maps:
        old={o['om_terrain'][0]:o for o in json.loads(args.legacy_maps.read_text())}
        masks=[{i} for i in range(12)]+[set(range(y*3,y*3+3)) for y in range(4)]+[{y*3+x for y in range(4)} for x in (0,2)]
        for new_tiles in masks:
            mixed=[['.']*72 for _ in range(96)];fs={};actors=[];targets=[]
            for i,current in enumerate(maps):
                obj=(current if i in new_tiles else old[current['om_terrain'][0]])['object']
                ox,oy=(i%3)*24,(i//3)*24
                for y,row in enumerate(obj['rows']):
                    for x,c in enumerate(row):
                        mixed[oy+y][ox+x]=c
                        if c in 'SIJKGXHFOR!':targets.append((ox+x,oy+y))
                fs.update({(ox+f['x'],oy+f['y']):f['furn'] for f in obj.get('place_furniture',[])})
                actors.extend((ox+a['x'],oy+a['y']) for a in obj.get('place_monster',[]))
            seen=reachable(mixed,furniture=fs)
            assert FINAL in seen and all(p in seen for p in targets+actors),('partial-map seam failed',new_tiles)
        print(f'OK: {len(masks)} partial-map combinations keep the finale, story targets and actor pockets reachable')
    if args.render:
        from PIL import Image,ImageDraw
        args.render.mkdir(parents=True,exist_ok=True)
        s=10;im=Image.new('RGB',(72*s,96*s),(30,20,25));draw=ImageDraw.Draw(im)
        colors={'#':(70,45,51),'a':(199,176,141),'r':(116,95,86),'p':(13,12,19),'l':(171,144,140),'%':(54,36,43),'&':(54,36,43),'@':(20,18,23)}
        for y,row in enumerate(field):
            for x,c in enumerate(row):draw.rectangle((x*s,y*s,(x+1)*s-1,(y+1)*s-1),fill=colors.get(c,(96,62,65)))
        for f in furniture:
            x,y=f['x'],f['y'];blocked=DETAIL_DEFS[f['furn']].get('move_cost_mod',0)<0
            draw.rectangle((x*s+2,y*s+2,(x+1)*s-3,(y+1)*s-3),fill=(39,29,35) if blocked else (144,94,87))
        for glyph,points in MARKERS.items():
            for x,y in points:
                if glyph in 'SIJKGXHFO':draw.ellipse((x*s+1,y*s+1,(x+1)*s-2,(y+1)*s-2),fill=(100,208,181))
        for x,y in EVENT_ZONES:draw.rectangle((x*s+2,y*s+2,(x+1)*s-3,(y+1)*s-3),outline=(249,192,65),width=2)
        im.save(args.render/'eclipse_sidepaths.png')
        for name,box in [('cache',(48,0,72,24)),('feast',(48,24,72,48)),('hunt',(0,48,24,72)),('ravine',(24,48,48,72)),('laststand',(0,72,24,96))]:
            im.crop(tuple(v*s for v in box)).resize((480,480),Image.Resampling.NEAREST).save(args.render/(name+'.png'))
    print(f'OK: {len(furniture)} details, continuous ash trail, two flank routes, optional scenes, all targets and pockets')
    print('OK: arrival screening, shortcut, fixed finite spawns, composition 34 + 6, no preplaced Griffith')
    print('Geometry only: light, engine vision, pursuit and save/load require game testing.')

if __name__=='__main__':
    main()
