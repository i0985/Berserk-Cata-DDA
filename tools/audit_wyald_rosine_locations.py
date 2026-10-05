#!/usr/bin/env python3
"""Focused static geometry/state checks; does not run CDDA or simulate its AI."""
import json
from collections import deque
from pathlib import Path
from build_wyald_rosine_locations import MOD, SECTIONS, wyald, rosine, split


def load(path): return json.loads((MOD/path).read_text())
def walk(value):
    yield value
    if isinstance(value,dict):
        for v in value.values(): yield from walk(v)
    elif isinstance(value,list):
        for v in value: yield from walk(v)


def reach(start,blocked):
    seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for p in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=p[0]<48 and 0<=p[1]<48 and p not in seen and p not in blocked:
                seen.add(p);queue.append(p)
    return seen


def main():
    definitions={o['id']:o for o in load('00_hunt_location_details.json')}
    effects={o['id']:o for o in load('effects/wyald_rosine_location_detail_eocs.json')}
    groups={o['id']:o for o in load('itemgroups/location_supplies.json')}
    palette=load('mapgen/wyald_rosine_detail_palette.json')[0]
    for kind,build in (('wyald',wyald),('rosine',rosine)):
        field=build()
        assert load(f'mapgen/apostle_{kind}.json')==split(kind,field)
        assert set(''.join(''.join(row) for row in field.rows))<=palette['terrain'].keys()
        blocked={(x,y) for y,row in enumerate(field.rows) for x,c in enumerate(row) if c in 'T#GpRc'}
        # Conservatively treat tables, posts, canvas and other hard props as blocked.
        blocked.update((x,y) for fid,x,y in field.props
                       if definitions.get(fid,{}).get('move_cost_mod',0)<0 or fid in ('f_table','f_clay_oven'))
        gates={(x,y) for fid,x,y in field.props if fid=='f_berserk_wyald_cage_gate'}
        outer=reach((10,0),blocked)
        assert (36,36) in outer and (36,47) in outer,kind
        if kind=='wyald':
            assert (1,30) in outer and (47,29) in outer
            cage_access=reach((10,0),blocked-gates)
            assert (17,26) in cage_access and (18,30) in cage_access
            # Cages never replace the free western quarry route into the arena.
            assert (28,37) in outer and (43,28) in outer
        else:
            assert (8,22) in outer and (13,40) in outer and (46,22) in outer
        usable=reach((10,0),blocked-gates)
        for fid,x,y in field.props:
            if fid.startswith('f_berserk_location_') or fid.endswith(('_record','_warning','_story_cocoon','_scene','_shell_material')):
                assert any((x+dx,y+dy) in usable for dx,dy in ((0,0),(0,1),(1,0),(0,-1),(-1,0))), (kind,fid,x,y)
                assert field.rows[y][x] not in 'T#GpRc',(kind,fid)
            if fid in ('f_berserk_location_wyald_kitchen','f_berserk_location_wyald_repair','f_berserk_location_wyald_command'):
                assert field.rows[y][x]=='m',(fid,'cache lost its tent floor')
        for x,y in ((30,30),(41,30),(30,41),(41,41)):
            assert (x,y) in usable and (x,y) not in blocked, (kind,'boss candidate blocked',x,y)
        assert any(fid==f'f_berserk_{kind}_breach' and (x,y)==(36,31) for fid,x,y in field.props)
        assert any(fid=='f_berserk_hunt_arena_tracks' and (x,y)==(36,36) for fid,x,y in field.props)
        assert not any(actor==f'mon_berserk_apostle_{kind}' for actor,_,_ in field.actors)
        print(f'OK: {kind}: connected 48x48, free bypasses, four boss pockets and legacy seal/token')
    w=wyald();r=rosine()
    assert len(w.actors)==6
    occupied=[p for p in r.props if p[0]=='f_berserk_rosine_cocoon_watchful']
    assert len(r.actors)==2 and len(occupied)==4
    assert sum(p[0]=='f_berserk_wyald_charge_obstacle' for p in w.props)==6
    for fid in ('f_berserk_rosine_cocoon_watchful','f_berserk_rosine_cocoon_waking'):
        assert definitions[fid]['bash']['furn_set']=='f_berserk_rosine_cocoon_destroyed'
    assert effects['berserk_rosine_cocoon_settle']['furniture'][0]['result']=='f_berserk_rosine_cocoon_watchful'
    hatch=effects['EOC_BERSERK_ROSINE_COCOON_HATCH']
    assert 'map_furniture_id' in str(hatch) and 'f_berserk_rosine_cocoon_waking' in str(hatch)
    assert 'distance' in str(hatch) and 'pos_z' in str(hatch)
    opening=next(o for o in load('effects/rosine_cocoon_eocs.json') if o.get('id')=='EOC_BERSERK_COCOON_OPEN')
    assert 'f_berserk_rosine_cocoon_inhabited' in str(opening)  # saved old cells still work
    for node in walk(effects):
        if isinstance(node,dict) and 'u_query' in node: assert node.get('default') is False
        if isinstance(node,dict) and 'u_spawn_monster' in node:
            assert node['u_spawn_monster']=='mon_berserk_cocoon_ravager' and node['real_count']==1
    for o in effects.values():
        if o['type']=='ter_furn_transform':
            assert all(f['valid_furniture'] for f in o['furniture'])
    cache_effects=[o for o in effects.values() if isinstance(o.get('effect'),dict)
                   and o['effect'].get('run_eocs')=='EOC_BERSERK_LOCATION_CLAIM']
    assert len(cache_effects)==9
    for o in cache_effects:
        v=o['effect']['variables'];tr=effects[v['berserk_location_transform']]['furniture'][0]
        assert tr['valid_furniture']==[v['berserk_location_full']] and tr['result']==v['berserk_location_empty']
        assert v['berserk_location_loot'] in groups
    # New supply groups only refer to approved medieval base groups and native items.
    supplied=[g for g in groups.values() if g['id'] in {o['effect']['variables']['berserk_location_loot'] for o in cache_effects}]
    assert not any(item in str(supplied) for item in ('aspirin','battery','rifle','bandages"'))
    for kind in ('wyald','rosine'):
        seal=next(o for o in load('effects/wyald_rosine_hunt_eocs.json') if o.get('id')==f'EOC_BERSERK_{kind.upper()}_SEAL')
        assert seal['effect'][0]['u_transform_radius']==0
        assert seal['effect'][0]['target_var']=={'context_val':'pos'}
        assert 'distance' in str(seal['condition'])
    print('OK: six finite supporters per hunt; nine independent caches; delayed source sound; destroy-before-hatch and exact-cell seals')


if __name__=='__main__': main()
