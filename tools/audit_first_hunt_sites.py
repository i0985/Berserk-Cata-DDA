#!/usr/bin/env python3
"""Conservative, static audit of the two introductory hunt maps. No CDDA run."""
import json
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/Berserk'
POCKETS = ((6, 6), (17, 6), (6, 17), (17, 17))


def load(path):
    return json.loads((MOD / path).read_text())


def walk(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def reachable(rows, start, blocked):
    dist = {start: 0}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for pos in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if pos in dist or pos in blocked or not (0 <= pos[0] < 24 and 0 <= pos[1] < 24):
                continue
            dist[pos] = dist[x, y] + 1
            queue.append(pos)
    return dist


def ray(a, b):
    x, y = a
    xx, yy = b
    dx, dy = abs(xx - x), -abs(yy - y)
    sx, sy = (1 if x < xx else -1), (1 if y < yy else -1)
    error = dx + dy
    while True:
        yield x, y
        if (x, y) == b:
            break
        twice = 2 * error
        if twice >= dy:
            error += dy
            x += sx
        if twice <= dx:
            error += dx
            y += sy


def audit_map(name, start):
    obj = load('mapgen/' + name + '.json')[0]['object']
    rows = obj['rows']
    assert len(rows) == 24 and all(len(row) == 24 for row in rows)
    assert set(''.join(rows)) <= obj['terrain'].keys()
    # Treat fissures and even the bench as unavailable: safe routes must not rely on them.
    blocked = {(x, y) for y, row in enumerate(rows) for x, char in enumerate(row) if char in '#Tw'}
    blocked.update((f['x'], f['y']) for f in obj['place_furniture']
                   if f['furn'] in ('f_berserk_breach_fallen_beam', 'f_bench'))
    dist = reachable(rows, start, blocked)
    assert all(p in dist for p in POCKETS + ((12, 12), (11, 11)))
    for f in obj['place_furniture']:
        p = f['x'], f['y']
        assert rows[p[1]][p[0]] not in '#Tw', (name, f, 'prop on unsuitable terrain')
        assert p in dist or any((p[0] + dx, p[1] + dy) in dist
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))), f
    for actor in obj['place_monster']:
        assert (actor['x'], actor['y']) in dist
    assert not any(a['monster'] in ('mon_berserk_hollow_apostle', 'mon_berserk_breach_warden')
                   for a in obj['place_monster']), 'boss preplaced'
    assert any(f['furn'] == 'f_berserk_hunt_arena_tracks' and (f['x'], f['y']) == (12, 12)
               for f in obj['place_furniture']), 'legacy arena token moved'
    # Approximate rays only, not the engine's vision algorithm: each accessible trigger cell
    # must have at least one pocket screened by opaque stone/tree along the ray.
    for y in range(8, 16):
        for x in range(8, 16):
            if (x, y) in blocked:
                continue
            assert any(any(rows[b][a] in '#T' for a, b in list(ray((x, y), p))[1:-1])
                       for p in POCKETS), (name, x, y, 'no screened pocket')
    return obj, blocked, dist


def main():
    hunt, hunt_blocked, _ = audit_map('first_hunt', (6, 23))
    breach, breach_blocked, _ = audit_map('local_breach', (9, 23))
    # Preparation and sheltered supplies can be visited without crossing the trigger square.
    arena = {(x, y) for y in range(8, 16) for x in range(8, 16)}
    outside = reachable(hunt['rows'], (6, 23), hunt_blocked | arena)
    assert all(p in outside for p in ((4, 20), (6, 10), (4, 13)))
    before = reachable(breach['rows'], (3, 11), breach_blocked)[11, 11]
    after = reachable(breach['rows'], (3, 11), breach_blocked - {(4, 11)})[11, 11]
    assert after < before
    wounds = [(x, y) for y, row in enumerate(breach['rows']) for x, c in enumerate(row) if c == 'w']
    assert wounds and all(max(abs(x - 11), abs(y - 11)) <= 7 for x, y in wounds)
    assert any(f['furn'] == 'f_berserk_open_breach' and (f['x'], f['y']) == (11, 11)
               for f in breach['place_furniture'])
    details = {o['id']: o for o in load('effects/hunt_site_detail_eocs.json')}
    for key in ('HUNT_SHELTER', 'HUNT_REWARD', 'BREACH_DEFENDERS'):
        effect = details['EOC_BERSERK_LOCATION_' + key]['effect']
        assert effect['run_eocs'] == 'EOC_BERSERK_LOCATION_CLAIM'
        variables = effect['variables']
        transform = details[variables['berserk_location_transform']]['furniture'][0]
        assert transform['valid_furniture'] == [variables['berserk_location_full']]
        assert transform['result'] == variables['berserk_location_empty']
    closed = {o['id']: o for o in load('effects/local_breach_eocs.json')}
    gate = str(closed['EOC_BERSERK_BREACH_CLOSE']['condition'])
    assert all(s in gate for s in ('u_berserk_breach_guardian_defeated == 1',
                                  'u_berserk_breach_sealed != 1',
                                  'u_berserk_local_breach_location.x', 'f_berserk_open_breach'))
    commit = closed['EOC_BERSERK_BREACH_CLOSE_COMMIT']
    assert 'f_berserk_sealed_breach' in str(commit['condition'])
    assert sum(isinstance(v, dict) and v.get('u_spawn_item') == 'berserk_post_eclipse_journal'
               for v in walk(commit)) == 1
    # Closure must neither edit a named hunt state nor remove live creatures.
    assert not any(any(key in v for key in ('u_kill_monsters', 'kill_npcs', 'u_remove_effect'))
                   for v in walk(commit) if isinstance(v, dict))
    assert not any(name in str(commit) for name in ('berserk_hunt_count_state',
                   'berserk_hunt_wyald_state', 'berserk_hunt_rosine_state', 'berserk_hunt_grunbeld_state'))
    assert details['berserk_first_breach_ground_cooled']['terrain'] == [{
        'valid_terrain': ['t_berserk_breach_wound'], 'result': 't_berserk_breach_scar'}]
    assert 'f_berserk_open_breach' in str(details['EOC_BERSERK_FIRST_BREACH_SOUND']['effect'])
    for v in walk(details):
        if isinstance(v, dict) and 'u_query' in v:
            assert 'default' in v
    groups = {o['id']: o for o in load('itemgroups/location_supplies.json')}
    for key in ('hunt_shelter', 'hunt_reward', 'breach_defenders'):
        group = groups['berserk_location_' + key]
        assert group['subtype'] == 'collection'
        assert not any('gun' in e.get('item', '') or 'aspirin' in e.get('item', '')
                       for e in group['entries'])
    assert any(e.get('item') == 'flint_steel' for e in groups['berserk_location_breach_defenders']['entries'])
    print('OK: two 24x24 maps; preparation without entering arena; all caches, exits and four boss pockets reachable')
    print(f'OK: optional beam shortens covered approach {before} -> {after}; all fissures lie inside closure radius')
    print('OK: finite per-cell caches; sealed-state reward guard; separate first-breach registry; native flint_steel ID')
    print('Static geometry/data only. AI, actual vision, difficulty, noise and save/load require user game testing.')


if __name__ == '__main__':
    main()
