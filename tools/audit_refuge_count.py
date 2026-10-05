#!/usr/bin/env python3
"""Static data/geometry audit only: never invokes the CDDA binary."""
import json
from collections import deque
from pathlib import Path
from build_count_residence import ACTORS, PROPS, SECTIONS, build_field, build_scene

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'


def load(path):
    return json.loads((MOD / path).read_text())


def objects(path):
    return {o['id']: o for o in load(path)}


def walk(obj):
    yield obj
    if isinstance(obj, dict):
        for child in obj.values():
            yield from walk(child)
    elif isinstance(obj, list):
        for child in obj:
            yield from walk(child)


def reachable(field, start, blocked):
    queue = deque([start])
    dist = {start: 0}
    while queue:
        x, y = queue.popleft()
        for p in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
            if p in blocked or p in dist or not (0 <= p[0] < len(field[0]) and 0 <= p[1] < len(field)):
                continue
            dist[p] = dist[x, y] + 1
            queue.append(p)
    return dist


def main():
    field = build_field()
    maps = load('mapgen/apostle_count.json')
    assert maps[:4] == [build_scene(omt, x, y, field) for omt, x, y in SECTIONS]
    palette = load('mapgen/apostle_count_palettes.json')[0]
    for m in maps:
        if 'om_terrain' in m:
            rows = m['object']['rows']
            assert len(rows) == 24 and all(len(row) == 24 for row in rows)
            assert set(''.join(rows)) <= palette['terrain'].keys()
    blocked = {(x,y) for y,row in enumerate(field) for x,c in enumerate(row) if c in '#|'}
    blocked.update((x,y) for name,x,y in PROPS if not name.startswith('f_berserk_location_')
                   and name not in ('f_berserk_count_notice','f_berserk_count_family_door','f_rubble'))
    starts = ((24,47), (0,32), (3,16))
    for start in starts:
        dist = reachable(field, start, blocked)
        assert (36,20) in dist and (7,18) in dist, start
        assert all(p in dist for p in ((18,7),(7,7),(30,8),(40,9),(13,34),(40,34)))
    for name,x,y in PROPS:
        assert field[y][x] not in '#|', ('prop on wall',name,x,y)
        if name.startswith('f_berserk_location_'):
            assert field[y][x] == '_', ('chest lacks interior floor',name,x,y)
    assert len(ACTORS) == 7 and sum(name == 'mon_berserk_count_servant' for name,_,_ in ACTORS) == 6
    assert all((x,y) in reachable(field,(24,47),blocked) for _,x,y in ACTORS)
    closed = reachable(field,(18,16),blocked)[36,20]
    opened = reachable(field,(18,16),blocked-{(27,16)})[36,20]
    assert opened < closed
    dungeon = maps[4]['object']
    dr = dungeon['rows']
    db = {(x,y) for y,row in enumerate(dr) for x,c in enumerate(row) if c in '#A'}
    assert dr[20][12] == 'U' and dr[4][20] == 'A' and dr[5][12] != 'A'
    dd = reachable(dr,(12,20),db)
    assert (12,8) in dd and (19,4) in dd, 'boss or seal alcove unreachable'
    assert {(a['monster'],a['x'],a['y']) for a in dungeon['place_monster']} == {
        ('mon_berserk_apostle_count',12,8),('mon_berserk_count_servant',4,11),
        ('mon_berserk_count_servant',19,11)}
    detail = objects('effects/count_residence_detail_eocs.json')
    caches = [o for o in load('furniture/count_residence_details.json')
              if o['id'].startswith('f_berserk_location_') and not o['id'].endswith('_empty')]
    assert len(caches) == 6
    for c in caches:
        wrapper = detail['EOC_'+c['id'].upper()]['effect']
        assert wrapper['run_eocs'] == 'EOC_BERSERK_LOCATION_CLAIM'
        var = wrapper['variables']
        assert detail[var['berserk_location_transform']]['furniture'] == [{
            'valid_furniture':[c['id']], 'result':c['id']+'_empty'}]
    seal = objects('effects/apostle_hunt_eocs.json')['EOC_BERSERK_COUNT_SEAL']
    assert seal['effect'][0] == {'u_transform_radius':0,
        'ter_furn_transform':'berserk_count_breach_closed_at_site','target_var':{'context_val':'pos'}}
    assert detail['berserk_count_breach_closed_at_site']['furniture'] == [{
        'valid_furniture':['f_berserk_count_breach'],'result':'f_berserk_count_breach_sealed'}]
    assert 'berserk_hunt_count_state == 3' in str(objects('effects/apostle_hunt_eocs.json')
                                               ['EOC_BERSERK_COUNT_SEAL_COMMIT']['condition'])
    refuge = objects('effects/refuge_eocs.json')
    register = refuge['EOC_BERSERK_REFUGE_REGISTER']
    assert 'u_is_outside' in str(register['condition']) and '_pos' in str(register['condition'])
    assert {'copy_var':{'context_val':'pos'},'target_var':{'u_val':'berserk_refuge_ward_location'}} in register['effect']
    assert 'u_berserk_refuge_journal_issued != 1' in str(register)
    assert 'u_berserk_refuge_dawn_recorded' not in str(refuge['EOC_BERSERK_REFUGE_NEXT_TRAIL']['condition'])
    assert 'u_berserk_refuge_dawn_recorded' not in str(refuge['EOC_BERSERK_REFUGE_WATCH']['condition']), 'destroyed ward must still be checked after dawn'
    assert refuge['EOC_BERSERK_REFUGE_LEAVE']['required_event'] == 'avatar_moves'
    assert not any(isinstance(v,dict) and any(k in v for k in ('u_add_effect','u_kill_monsters','u_add_bionic'))
                   for v in walk(refuge)), 'journal must not grant protection/healing or kill enemies'
    for v in walk([refuge,detail]):
        if isinstance(v,dict) and 'u_query' in v:
            assert 'default' in v
    night = objects('effects/eclipse_brand_eocs.json')['EOC_BERSERK_BRAND_NIGHT_HUNT']
    assert night['effect']['target_max_radius'] == 8 and night['effect']['target_min_radius'] == -1
    construction = load('construction/shelter_ward.json')[1]
    assert construction['components'] == [[['rock',8]],[['bone',4]]]
    groups = objects('itemgroups/location_supplies.json')
    assert groups['berserk_location_refuge_ward_materials']['entries'][:2] == [
        {'item':'rock','count':8,'prob':100},{'item':'bone','count':4,'prob':100}]
    assert any(e.get('group') == 'berserk_location_refuge_ward_materials'
               for e in groups['berserk_location_hunt_reward']['entries'])
    print('OK: connected 48x48 residence, three entrances, six chests with proper floor, stairs/witness/actors reachable')
    print(f'OK: optional grille shortens approach {closed} -> {opened}; separate accessible seal alcove; old seal ID supported')
    print('OK: finite cache states; unchanged finite actors; refuge journal issued once; no night prerequisite or stat bonus')
    print('OK: ward includes player tile and uses radius 8; same-floor registration/watch; one finite material kit')
    print('Static checks only. Actual vision, combat, dialogue, night observation and saves require game testing.')


if __name__ == '__main__':
    main()
