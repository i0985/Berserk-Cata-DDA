#!/usr/bin/env python3
"""Audit block C against vanilla definitions; optionally draw exact tile plans.

This is an offline geometry/reference audit. Doors are assumed openable;
monsters, sound, fire, lighting and native save loading are not simulated.
"""
import argparse
import json
from collections import deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'mods/Berserk'


def objects(path):
    data=json.loads(path.read_text())
    return data if isinstance(data,list) else [data]


def catalog(root):
    result={}
    for file in root.rglob('*.json'):
        for obj in objects(file):
            ids=obj.get('id',obj.get('abstract',[]))
            for id in [ids] if isinstance(ids,str) else ids:
                result[(obj.get('type'),id)]=obj
    return result


def merged(cat,kind,id):
    obj=cat.get((kind,id),{})
    parent=obj.get('copy-from')
    result={**(merged(cat,kind,parent) if parent else {}),**obj}
    if 'flags' in obj.get('extend',{}):
        result['flags']=list(set(result.get('flags',[])) | set(obj['extend']['flags']))
    if 'flags' in obj.get('delete',{}):
        result['flags']=list(set(result.get('flags',[]))-set(obj['delete']['flags']))
    return result


def build_scenes():
    maps={m['om_terrain'][0]:m['object'] for m in objects(MOD/'mapgen/behelit_sites.json') if 'om_terrain' in m}
    palettes={p['id']:p for p in objects(MOD/'mapgen/behelit_site_palettes.json')}
    arrangements={
        'Expedition':[['berserk_lost_expedition']],
        'Chapel':[['berserk_desecrated_chapel_reliquary'],['berserk_desecrated_chapel_nave']],
        'Oak':[['berserk_cursed_oak']],
        'Cave':[['berserk_echo_cave_depth','berserk_echo_cave_gallery'],
                ['berserk_echo_cave_passage','berserk_echo_cave_relic_chamber']]}
    scenes={}
    for name,parts in arrangements.items():
        terrain={};furniture={};loot=[];monsters=[]
        for yy,row in enumerate(parts):
            for xx,id in enumerate(row):
                obj=maps[id];p=palettes[obj['palettes'][0]]
                assert len(obj['rows'])==24 and all(len(r)==24 for r in obj['rows']),id
                for y,line in enumerate(obj['rows']):
                    for x,c in enumerate(line):
                        pos=(xx*24+x,yy*24+y)
                        terrain[pos]=p['terrain'][c]
                        if c in p.get('furniture',{}):furniture[pos]=p['furniture'][c]
                for f in obj.get('place_furniture',[]):furniture[(xx*24+f['x'],yy*24+f['y'])]=f['furn']
                for key,out in [('place_loot',loot),('place_items',loot),('place_monster',monsters)]:
                    out.extend({**e,'x':xx*24+e['x'],'y':yy*24+e['y']} for e in obj.get(key,[]))
        scenes[name]={'terrain':terrain,'furniture':furniture,'loot':loot,'monsters':monsters,
                      'width':len(parts[0])*24,'height':len(parts)*24}
    return scenes


def neighbors(pos):
    x,y=pos
    return [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]


def walkable(cat,scene,pos):
    if pos not in scene['terrain']:return False
    tid=scene['terrain'][pos];fid=scene['furniture'].get(pos,'f_null')
    ter=merged(cat,'terrain',tid);furn=merged(cat,'furniture',fid)
    # A normal closed door can be opened; an opaque root or slab cannot.
    door=furn.get('open')
    furniture_passable=(furn.get('move_cost_mod',0)>=0
                       or bool(door) and merged(cat,'furniture',door).get('move_cost_mod',-1)>=0)
    return (ter.get('move_cost',0)>0 or tid=='t_door_c') and furniture_passable


def distances(cat,scene,start):
    assert walkable(cat,scene,start),start
    queue=deque([start]);seen={start:0}
    while queue:
        p=queue.popleft()
        for q in neighbors(p):
            if q not in seen and walkable(cat,scene,q):seen[q]=seen[p]+1;queue.append(q)
    return seen


def line(a,b):
    x,y=a;tx,ty=b;dx=abs(tx-x);dy=-abs(ty-y)
    sx=1 if x<tx else -1;sy=1 if y<ty else -1;error=dx+dy
    while (x,y)!=(tx,ty):
        yield (x,y)
        twice=error*2
        if twice>=dy:error+=dy;x+=sx
        if twice<=dx:error+=dx;y+=sy


def opaque(cat,scene,pos):
    ter=merged(cat,'terrain',scene['terrain'][pos])
    furn=merged(cat,'furniture',scene['furniture'].get(pos,'f_null'))
    return ('TRANSPARENT' not in ter.get('flags',[])
            or bool(furn) and 'TRANSPARENT' not in furn.get('flags',[]))


def audit(cat,scenes):
    starts={'Expedition':(11,23),'Chapel':(12,47),'Oak':(4,23),'Cave':(12,12)}
    for name,scene in scenes.items():
        for tid in scene['terrain'].values():assert ('terrain',tid) in cat,(name,tid)
        for fid in scene['furniture'].values():assert ('furniture',fid) in cat,(name,fid)
        seen=distances(cat,scene,starts[name])
        for pos,fid in scene['furniture'].items():
            assert pos in seen or any(q in seen for q in neighbors(pos)),(name,'inaccessible furniture',pos,fid)
        for item in scene['loot']:
            pos=(item['x'],item['y'])
            assert pos in seen or any(q in seen for q in neighbors(pos)),(name,'inaccessible item',item)
            if 'group' in item:assert ('item_group',item['group']) in cat,item
            elif 'item' in item:
                assert any((kind,item['item']) in cat for kind in ('ITEM','item_group')),item
            assert not set(item).intersection({'damage','amount','charges'}),item
        for actor in scene['monsters']:
            assert ('MONSTER',actor['monster']) in cat,actor
            assert (actor['x'],actor['y']) in seen,(name,actor)
        guardian=next(a for a in scene['monsters'] if 'guardian' in a['monster'])
        gp=(guardian['x'],guardian['y'])
        source=next(p for p,f in scene['furniture'].items() if f.endswith('_noisemaker'))
        relic=next(p for p,f in scene['furniture'].items() if f.endswith('_relic'))
        assert max(abs(a-b) for a,b in zip(source,relic))>8,(name,'lure is too close')
        assert any(opaque(cat,scene,p) for p in list(line(gp,source))[1:]),(name,'lure exposed to guardian')
        assert any(opaque(cat,scene,p) for p in list(line(gp,starts[name]))[1:]),(name,'guardian sees arrival')
        print(f'{name}: {len(seen)} reachable cells, {len(scene["furniture"])} furnishings; relic, lure, loot and actors accessible')
    cave=scenes['Cave'];release=next(p for p,f in cave['furniture'].items() if f=='f_berserk_cave_return_release')
    closed=distances(cat,cave,starts['Cave'])[release]
    brace=next(p for p,f in cave['furniture'].items() if f=='f_berserk_cave_return_brace')
    assert max(abs(a-b) for a,b in zip(brace,release))<=2
    opened={**cave,'furniture':{p:f for p,f in cave['furniture'].items() if p!=brace}}
    shortcut=distances(cat,opened,starts['Cave'])[release]
    assert shortcut<closed,(closed,shortcut)
    print(f'Cave return: {closed} steps before release, {shortcut} after (doors assumed openable).')
    for scene in [scenes['Expedition']]:
        for item in scene['loot']:
            pos=(item['x'],item['y'])
            if scene['furniture'].get(pos)=='f_berserk_expedition_approach_note':continue
            assert scene['terrain'][pos]=='t_berserk_expedition_groundsheet',item


def render(cat,scenes,out):
    from PIL import Image,ImageDraw,ImageFont
    out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    for name,scene in scenes.items():
        size=16;im=Image.new('RGB',(scene['width']*size+30,scene['height']*size+70),'#17191c')
        d=ImageDraw.Draw(im);d.text((12,8),name+' — data layout',font=font,fill='white')
        for p,tid in scene['terrain'].items():
            x,y=p;box=(15+x*size,35+y*size,15+(x+1)*size-1,35+(y+1)*size-1)
            color=('#37363a' if not walkable(cat,scene,p) else
                   '#a18c65' if 'groundsheet' in tid else
                   '#766957' if tid in ['t_floor','t_door_o','t_door_c'] else
                   '#697279' if 'rock_floor' in tid or 'scree' in tid or 'cave_glow' in tid else '#4c6546')
            d.rectangle(box,fill=color)
            if tid.startswith('t_stairs'):d.text((box[0]+2,box[1]-1),'^',font=font,fill='white')
        for p,fid in scene['furniture'].items():
            x,y=p;box=(18+x*size,38+y*size,26+x*size,46+y*size)
            color='#d6bc86'
            if fid.endswith('_noisemaker'):color='#66ccdf'
            elif fid.endswith('_relic'):color='#fa5555'
            elif 'root' in fid or 'trunk' in fid:color='#34251e'
            elif 'note' in fid or 'record' in fid or 'marks' in fid:color='#f1dfbd'
            d.rectangle(box,fill=color)
        for actor in scene['monsters']:
            x,y=actor['x'],actor['y']
            d.ellipse((16+x*size,36+y*size,29+x*size,49+y*size),fill='#ed6f27')
        d.text((12,im.height-24),'Red: relic   Cyan: lure   Orange: monsters',font=font,fill='white')
        im.save(out/(name.lower()+'.png'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vanilla-data',required=True,type=Path)
    parser.add_argument('--render',type=Path)
    args=parser.parse_args()
    cat={**catalog(args.vanilla_data),**catalog(MOD)}
    scenes=build_scenes();audit(cat,scenes)
    if args.render:render(cat,scenes,args.render)


if __name__=='__main__':main()
