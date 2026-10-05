"""Timer, placement and localization contracts; NOT a native monster AI test."""
import copy
import gettext
import heapq
import json
from collections import deque
from pathlib import Path
import unittest

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'


def load(path):
    return json.loads((MOD / path).read_text())


EOCS = {o['id']: o for p in ('effects/behelit_site_eocs.json', 'effects/behelit_distraction_eocs.json') for o in load(p)}
SITES = ('oak', 'cave', 'chapel', 'expedition')


def schedule(site):
    effects = EOCS[f'EOC_BERSERK_{site.upper()}_DISTRACTION']['effect']['then']
    return [(int(e['time_in_future'].split()[0]), e['run_eocs']) if 'run_eocs' in e
            else (int(e['time_in_future'].split()[0])+1, 'WORLD_RESET')
            for e in effects if 'time_in_future' in e]


class QueueModel:
    """Independent lifecycle model using the actual configured queue times.

    Models the native source's copied queue context, furniture gate, and reset.
    Does not implement game movement, pathfinding, hearing, or sound clustering.
    """
    def __init__(self):
        self.time = 0
        self.cells = {}
        self.events = []
        self.sounds = []
        self.serial = 0

    def arm(self, site, pos):
        key = str(pos)
        if self.cells.get(key) != site:
            return False
        self.cells[key] = site + '_armed'
        ctx = {'pos': list(pos), 'berserk_noise_z': pos[2]}
        for delay, event in schedule(site):
            self.serial += 1
            heapq.heappush(self.events, (self.time + delay, self.serial, site, event, copy.deepcopy(ctx)))
        return True

    def advance(self, end, player):
        while self.events and self.events[0][0] <= end:
            when, serial, site, event, ctx = heapq.heappop(self.events)
            pos = tuple(ctx['pos'])
            key = str(pos)
            if self.cells.get(key) == site + '_armed':
                if event.endswith('_RESET'):
                    self.cells[key] = site
                elif player[2] == ctx['berserk_noise_z'] and max(abs(a-b) for a,b in zip(player,pos)) <= 48:
                    self.sounds.append((when, pos))
        self.time = end

    def reload(self):
        payload = json.loads(json.dumps({'time': self.time, 'cells': self.cells, 'events': self.events, 'serial': self.serial}))
        self.time, self.cells, self.serial = payload['time'], payload['cells'], payload['serial']
        self.events = [tuple(event) for event in payload['events']]
        heapq.heapify(self.events)


def path(rows, start, goal):
    q = deque([start])
    seen = {start}
    width, height = len(rows[0]), len(rows)
    while q:
        x,y = q.popleft()
        if (x,y) == goal:
            return True
        for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
            nxt = x+dx,y+dy
            if 0 <= nxt[0] < width and 0 <= nxt[1] < height and nxt not in seen and rows[nxt[1]][nxt[0]] not in '#TKRB':
                seen.add(nxt)
                q.append(nxt)
    return False


def line(start,end):
    """Geometric screen check only; does not reproduce native vision."""
    x,y = start
    tx,ty = end
    dx,dy = abs(tx-x),-abs(ty-y)
    sx,sy = (1 if x<tx else -1),(1 if y<ty else -1)
    error = dx+dy
    while (x,y) != (tx,ty):
        yield x,y
        twice = 2*error
        if twice >= dy:
            error += dy
            x += sx
        if twice <= dx:
            error += dx
            y += sy


class DistractionTests(unittest.TestCase):
    def test_source_snapshot_is_saved_and_not_changed_by_player_movement(self):
        m = QueueModel()
        source = (1000,2000,-1)
        m.cells[str(source)] = 'cave'
        self.assertTrue(m.arm('cave',source))
        m.advance(19,(1008,2008,-1))
        self.assertFalse(m.sounds)
        m.reload()
        m.advance(89,(1020,2000,-1))
        self.assertEqual(m.sounds,[(t,source) for t in (20,35,50,65)])
        m.advance(90,(1020,2000,-1))
        self.assertEqual(m.cells[str(source)],'cave')
        self.assertFalse(m.events)

    def test_repeat_activation_does_not_stack_but_separate_devices_are_independent(self):
        m = QueueModel()
        a,b = (0,0,0),(20,0,0)
        for pos in (a,b): m.cells[str(pos)] = 'cave'
        self.assertTrue(m.arm('cave',a))
        self.assertFalse(m.arm('cave',a))
        self.assertTrue(m.arm('cave',b))
        self.assertEqual(len(m.events),10)
        m.advance(90,(10,0,0))
        self.assertEqual(len(m.sounds),8)
        self.assertTrue(m.arm('cave',a))
        self.assertEqual(len(m.events),5)

    def test_destroyed_device_stops_and_is_not_recreated(self):
        m = QueueModel()
        pos = (0,0,0)
        m.cells[str(pos)] = 'oak'
        m.arm('oak',pos)
        m.advance(21,pos)
        m.cells[str(pos)] = 'rubble'
        m.advance(100,pos)
        self.assertEqual(len(m.sounds),1)
        self.assertEqual(m.cells[str(pos)],'rubble')

    def test_remote_and_other_floor_pulses_are_skipped_not_replayed(self):
        for player in ((200,0,0),(0,0,-1)):
            m = QueueModel()
            pos = (0,0,0)
            m.cells[str(pos)] = 'chapel'
            m.arm('chapel',pos)
            m.advance(89,player)
            m.reload()
            m.advance(100,pos)
            self.assertEqual(m.sounds,[])
            self.assertEqual(m.cells[str(pos)],'chapel')
            self.assertEqual(m.events,[])

    def test_json_uses_supported_queue_and_exact_cell_transform_contract(self):
        defs = {o['id']:o for file in ('furniture/behelit_sites.json','furniture/behelit_distractions.json') for o in load(file)}
        reset = defs['berserk_noisemakers_reset']['furniture']
        self.assertEqual(len(reset),4)
        for site in SITES:
            idle = f'f_berserk_{site}_noisemaker'
            armed = idle+'_armed'
            start = EOCS[f'EOC_BERSERK_{site.upper()}_DISTRACTION']['effect']
            self.assertEqual(start['if'],{'map_furniture_id':idle,'loc':{'context_val':'pos'}})
            calls = start['then']
            self.assertEqual(calls[0],{'u_transform_radius':0,'ter_furn_transform':f'berserk_{site}_noisemaker_arm','target_var':{'context_val':'pos'}})
            self.assertFalse(any('u_make_sound' in e for e in calls))
            self.assertEqual([t for t,e in schedule(site)],[20,35,50,65,90])
            pulse = EOCS[schedule(site)[0][1]]
            self.assertEqual(pulse['eoc_type'],'ACTIVATION')
            self.assertEqual(pulse['effect']['if']['and'],[{'math':["u_val('pos_z') == _berserk_noise_z"]},{'math':["distance('u', _pos) <= 48"]}])
            local = pulse['effect']['then']
            self.assertEqual(local['if'],{'map_furniture_id':armed,'loc':{'context_val':'pos'}})
            sound = local['then']
            self.assertEqual(sound['target_var'],{'context_val':'pos'})
            self.assertEqual(sound['type'],'alarm')
            self.assertFalse(sound['ambient'])
            self.assertGreaterEqual(sound['volume'],45)
            self.assertNotIn('copy-from',defs[armed])
            self.assertEqual(defs[armed]['required_str'],defs[idle]['required_str'])
            self.assertEqual(defs[armed]['move_cost_mod'],defs[idle]['move_cost_mod'])
            self.assertEqual(defs[armed]['examine_action']['effect_on_conditions'],['EOC_BERSERK_DISTRACTION_BUSY'])
            for rule in defs[f'berserk_{site}_noisemaker_arm']['furniture']:
                self.assertEqual(rule,{'result':armed,'valid_furniture':[idle],'valid_flags':[]})
            self.assertIn({'result':idle,'valid_furniture':[armed],'valid_flags':[]},reset)
            delayed_reset = next(e for e in calls if e.get('ter_furn_transform') == 'berserk_noisemakers_reset')
            self.assertEqual(delayed_reset,{'//':'0.I-1 adds one second to delayed transform_radius; 89 + 1 resets at 90 seconds. This world timer survives loss of the activating character.', 'u_transform_radius':0,'ter_furn_transform':'berserk_noisemakers_reset','target_var':{'context_val':'pos'},'time_in_future':'89 seconds'})

    def test_world_reset_is_independent_of_lost_character_queue(self):
        m = QueueModel()
        pos = (0,0,0)
        m.cells[str(pos)] = 'oak'
        m.arm('oak',pos)
        m.events = [e for e in m.events if e[3]=='WORLD_RESET']
        heapq.heapify(m.events)
        m.advance(90,(1000,0,0))
        self.assertEqual(m.cells[str(pos)],'oak')
        self.assertFalse(m.sounds)

    def test_every_guardian_can_hear_without_forced_target_or_timed_ai(self):
        monsters = {m['id']:m for p in ('monsters/behelit_site_guardians.json','monsters/eclipse_demons.json') for m in load(p)}
        for id in ('mon_berserk_cursed_oak_guardian','mon_berserk_echo_cave_guardian','mon_berserk_chapel_guardian','mon_berserk_expedition_guardian'):
            guardian = monsters[id]
            base = monsters[guardian['copy-from']] if 'copy-from' in guardian else guardian
            self.assertIn('HEARS',base['flags'])
            self.assertEqual(guardian['path_settings'],{'max_dist':64,'max_length':320,'avoid_traps':True})
            if base is not guardian:
                self.assertEqual(guardian['looks_like'],base['id'])
                self.assertNotIn('hp',guardian)
                self.assertNotIn('speed',guardian)
                self.assertNotIn('melee_damage',guardian)
                self.assertNotIn('path_settings',base)
        text = (MOD/'effects/behelit_distraction_eocs.json').read_text()
        self.assertNotIn('mon_berserk_',text)
        self.assertNotIn('npc_location',text)
        self.assertNotIn('recurrence',text)

    def test_lure_and_relic_routes_do_not_block_each_other(self):
        maps = {o['om_terrain'][0]:o['object']['rows'] for o in load('mapgen/behelit_sites.json') if 'om_terrain' in o}
        cave = []
        for left,right in [('berserk_echo_cave_depth','berserk_echo_cave_gallery'),('berserk_echo_cave_passage','berserk_echo_cave_relic_chamber')]:
            cave.extend([a+b for a,b in zip(maps[left],maps[right])])
        chapel = maps['berserk_desecrated_chapel_reliquary'] + maps['berserk_desecrated_chapel_nave']
        for rows,guard,approach in ((maps['berserk_cursed_oak'],(12,9),(12,13)),(cave,(39,35),(36,28)),(chapel,(12,12),(12,5)),(maps['berserk_lost_expedition'],(20,8),(18,7))):
            sources = [(x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c=='N']
            relic = next((x,y) for y,row in enumerate(rows) for x,c in enumerate(row) if c=='A')
            self.assertTrue(sources)
            for x,y in sources:
                self.assertGreater(max(abs(x-relic[0]),abs(y-relic[1])),8)
                self.assertTrue(path(rows,guard,(x,y)))
                self.assertTrue(any(rows[ly][lx] in '#TRK' for lx,ly in line(guard,(x,y))),
                                f'missing opaque screen on initial guardian-to-device line: {(x,y)}')
                neighbours = [(x+dx,y+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) if 0<=x+dx<len(rows[0]) and 0<=y+dy<len(rows) and rows[y+dy][x+dx] not in '#TN']
                self.assertTrue(any(path(rows,guard,n) for n in neighbours))
                self.assertTrue(any(path(rows,n,approach) for n in neighbours))

    def test_sound_cells_are_reachable_native_pathfinding_goals(self):
        furniture = {o['id']:o for o in load('furniture/behelit_sites.json')}
        for site in SITES:
            self.assertEqual(furniture[f'f_berserk_{site}_noisemaker']['move_cost_mod'],0)

    def test_camp_uses_canvas_terrain_under_furniture_and_tent_flaps(self):
        camp = next(o for o in load('mapgen/behelit_site_palettes.json') if o.get('id')=='berserk_expedition_site_palette')
        self.assertEqual(camp['furniture']['#'],'f_canvas_wall')
        self.assertNotIn('_',camp['furniture'])
        for key in ('_', '?', 'A', 'r'):
            self.assertEqual(camp['terrain'][key],'t_berserk_expedition_groundsheet')
        self.assertEqual(camp['furniture']['+'],'f_canvas_door_o')
        self.assertEqual(camp['terrain']['#'],'t_berserk_expedition_groundsheet')
        self.assertEqual(camp['furniture']['D'],'f_canvas_door')
        rows = next(o['object']['rows'] for o in load('mapgen/behelit_sites.json') if o.get('om_terrain')==['berserk_lost_expedition'])
        self.assertEqual(sum(row.count('+') for row in rows),3)
        self.assertEqual(sum(row.count('D') for row in rows),1)


if __name__ == '__main__':
    unittest.main()
