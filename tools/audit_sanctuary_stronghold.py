#!/usr/bin/env python3
"""Audit block E geometry using vanilla inheritance; never starts the game.

Doors are assumed openable. Field seeds are treated as avoided cells; native
fire spread, AI, lighting and saved-map loading remain player checks.
"""
import argparse
import copy
import itertools
import json
from collections import deque
from pathlib import Path

from audit_behelit_adventures import catalog, merged, objects, neighbors, walkable, distances
from build_flora_treehouse import maps as flora_maps, updates, SECTIONS as F_SECTIONS, FLORA
from build_grunbeld_stronghold import maps as fort_maps, SECTIONS as G_SECTIONS, SPAWNS, SEAL, TRACKS

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'mods/Berserk'


def scene(data,sections):
    out={'terrain':{},'furniture':{},'actors':[]}
    for entry,(_,ox,oy) in zip(data,sections):
        obj=entry['object']
        pal=objects(MOD/('mapgen/flora_treehouse_palette.json' if sections==F_SECTIONS else 'mapgen/grunbeld_detail_palette.json'))[0]
        assert len(obj['rows'])==24 and all(len(row)==24 for row in obj['rows'])
        for y,row in enumerate(obj['rows']):
            for x,c in enumerate(row):out['terrain'][(x+ox*24,y+oy*24)]=pal['terrain'][c]
        for p in obj['place_furniture']:out['furniture'][(p['x']+ox*24,p['y']+oy*24)]=p['furn']
        for p in obj['place_monster']:out['actors'].append((p['monster'],p['x']+ox*24,p['y']+oy*24))
    return out


def blocked_reach(cat,s,start,extra):
    todo=deque([start]);seen={start}
    while todo:
        for q in neighbors(todo.popleft()):
            if q not in seen and q not in extra and walkable(cat,s,q):seen.add(q);todo.append(q)
    return seen


def geometry(cat,s,start):
    seen=distances(cat,s,start)
    for pos,tid in s['terrain'].items():assert ('terrain',tid) in cat,tid
    for pos,fid in s['furniture'].items():
        assert ('furniture',fid) in cat,fid
        assert merged(cat,'terrain',s['terrain'][pos]).get('move_cost',0)>0,('furniture on wall',fid,pos)
        assert pos in seen or any(q in seen for q in neighbors(pos)),('furniture inaccessible',fid,pos)
    for actor,x,y in s['actors']:
        assert ('MONSTER',actor) in cat,actor
        assert (x,y) in seen,('actor inaccessible',actor,x,y)
    return seen


def flora(cat,s):
    seen=geometry(cat,s,FLORA)
    assert (0,14) in seen and (24,47) in seen
    library=[p for p,f in s['furniture'].items() if f.endswith('_shelf') and p[0]<24 and p[1]<11]
    assert len(library)==7
    for p in library:
        assert any(merged(cat,'terrain',s['terrain'].get(q,'t_null')).get('move_cost',0)==0 for q in neighbors(p)),('shelf away from wall',p)
    # A closed bedroom door isolates its own room, not an open corridor.
    for bed,box,doors in [((12,26),(11,23,14,29),[(12,22)]),
                          ((18,26),(16,23,19,29),[(18,22),(20,25)])]:
        room=blocked_reach(cat,s,bed,set(doors))
        x1,y1,x2,y2=box
        assert all(x1<=x<=x2 and y1<=y<=y2 for x,y in room),('bedroom not enclosed',bed)
    assert s['terrain'][(20,15)]=='t_door_c' and walkable(cat,s,(21,15))
    assert s['terrain'][(29,15)]=='t_door_c' and walkable(cat,s,(28,15))
    assert s['furniture'][(39,7)]=='f_berserk_flora_aid_pantry'
    assert s['terrain'][(39,7)]=='t_berserk_flora_wood_floor'
    # New map updates seed native fields and alter only three exact furniture cells.
    patches=updates()
    assert patches==objects(MOD/'mapgen/flora_treehouse_v2_updates.json')
    starts=[FLORA,(12,26),(18,26),(38,9),(34,15),(34,22),(25,6),(24,26)]
    staged=copy.deepcopy(s);hot=set()
    for stage in ('warning','assault','collapse','ruins'):
        for patch,(_,ox,oy) in zip([p for p in patches if '_'+stage+'_' in p['update_mapgen_id']],F_SECTIONS):
            obj=patch['object']
            for e in obj.get('set',[]):
                assert e['point']=='furniture'
                staged['furniture'][(e['x']+ox*24,e['y']+oy*24)]=e['id']
            for f in obj.get('place_fields',[]):
                assert ('field_type',f['field']) in cat
                if f['field']=='fd_fire':
                    p=(f['x']+ox*24,f['y']+oy*24);hot.add(p)
                    ter=merged(cat,'terrain',staged['terrain'][p]);fid=staged['furniture'].get(p)
                    flags=ter.get('flags',[])+(merged(cat,'furniture',fid).get('flags',[]) if fid else [])
                    assert any(flag.startswith('FLAMMABLE') for flag in flags),('fire on nonfuel cell',p)
        for start in starts:
            assert start not in hot
            reached=blocked_reach(cat,staged,start,hot)
            assert (0,14) in reached and (24,47) in reached,(stage,start,'escape blocked by seeds or furniture')
    print('Flora: seven wall shelves, two enclosed guest rooms, pantry, tree ring and both exits; ten fire seeds avoided in all stages.')


def fortress(cat,s):
    seen=geometry(cat,s,(12,18))
    pallets=[p for p,f in s['furniture'].items() if f=='f_straw_bed']
    assert len([p for p in pallets if p[0]<35])==8
    assert len([p for p in pallets if p[0]>35])==2
    assert s['furniture'][(15,34)]=='f_berserk_grunbeld_quarry_hoist'
    assert s['furniture'][(15,35)]=='f_berserk_grunbeld_quarry_rope'
    # Disallow switching to the other route before the inner defense.
    west={(x,y) for y in range(25,54) for x in range(24)}
    east={(x,y) for y in range(29,54) for x in range(24,48)}
    assert (36,58) in blocked_reach(cat,s,(12,18),west),'garrison route'
    assert (36,58) in blocked_reach(cat,s,(10,27),east),'quarry route'
    for start in SPAWNS+[(36,58)]:
        retreat=distances(cat,s,start)
        assert (25,59) in retreat and (35,71) in retreat,(start,'two retreats')
    assert s['furniture'][SEAL]=='f_berserk_grunbeld_breach'
    assert s['furniture'][TRACKS]=='f_berserk_hunt_arena_tracks'
    groups={d['id']:d for d in objects(MOD/'itemgroups/grunbeld_stronghold_supplies.json')}
    rope=groups['berserk_grunbeld_supplies_quarry_rope']['entries']
    assert any(d.get('item')=='rope_30' and d['prob']==100 for d in rope)
    assert len(groups)==10
    print('Stronghold: 8 barrack pallets + 2 infirmary beds, real hoist rope, 10 finite caches, independent garrison/quarry approaches and two arena retreats.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--vanilla-data',type=Path,required=True)
    p.add_argument('--before',type=Path)
    args=p.parse_args();cat={**catalog(args.vanilla_data),**catalog(MOD)}
    fm=objects(MOD/'mapgen/flora_manor.json')
    gm=[d for d in objects(MOD/'mapgen/apostle_grunbeld.json') if d['type']=='mapgen']
    assert fm==flora_maps() and gm==fort_maps()
    flora(cat,scene(fm,F_SECTIONS));fortress(cat,scene(gm,G_SECTIONS))
    # Check native fallbacks, physical medieval breakdown and work surfaces.
    for path in ('00_household_furnishings.json','furniture/grunbeld_siege_scenery.json'):
        for d in objects(MOD/path):
            obj=merged(cat,'furniture',d['id'])
            assert ('furniture',obj['looks_like']) in cat,d
            assert 'required_str' in obj and 'move_cost_mod' in obj
            for action in ('bash','deconstruct'):
                for e in obj.get(action,{}).get('items',[]):
                    if 'item' in e:
                        assert ('ITEM',e['item']) in cat,e
                        assert e['item'] in ('rock','splinter','scrap_cotton'),('modern output',e)
            if obj.get('crafting_pseudo_item'):assert ('ITEM',obj['crafting_pseudo_item']) in cat
    if args.before:
        before=args.before/'mods/Berserk'
        for path in ('mapgen/flora_treehouse_updates.json','mapgen/flora_siege_updates.json',
                     'effects/hunt_arena_eocs.json',
                     'effects/hunt_site_placement_eocs.json','effects/flora_eocs.json'):
            assert objects(MOD/path)==objects(before/path),('unintended route/state change',path)
        old_hunt=objects(before/'effects/grunbeld_hunt_eocs.json')
        new_hunt=objects(MOD/'effects/grunbeld_hunt_eocs.json')
        # The campaign tablet was rewritten as testimony; every mechanical
        # operation and every other event must still match pre-E data.
        for hunt in (old_hunt,new_hunt):
            inscription=next(d for d in hunt if d['id']=='EOC_BERSERK_GRUNBELD_INSCRIPTION')
            inscription['effect'][0].pop('u_message')
        assert old_hunt==new_hunt,'unintended Grunbeld state change'
        old=objects(before/'mapgen/flora_manor.json')
        for pattern in itertools.product((False,True),repeat=4):
            mixed=[fm[i] if new else old[i] for i,new in enumerate(pattern)]
            reachable=distances(cat,scene(mixed,F_SECTIONS),FLORA)
            assert (0,14) in reachable and (24,47) in reachable,('mixed save exits',pattern)
        print('Pre-E v0/v1 updates and route/fate definitions preserved; all 16 mixed old/new Flora sector combinations have both exits.')
    print('Offline only: native fire propagation, AI, saved-map loading and UltiCa are not validated.')


if __name__=='__main__':main()
