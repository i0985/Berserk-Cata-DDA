"""Data-level regressions for independent hunt state and connected layouts.

The small EOC interpreter exercises the definitions; it is not CDDA's loader,
AI, combat, mapgen or savegame implementation. No game binary is launched.
"""

import copy
import gettext
import json
import math
import re
from collections import deque
import unittest

from test_behelit_rewards import MOD, RewardGraph, objects


class HuntGraph(RewardGraph):
    def __init__(self, flags=None):
        super().__init__(flags)
        self.eocs = {e['id']: e for p in (MOD/'effects').glob('*.json')
                     for e in objects(p) if e['type'] == 'effect_on_condition'}
        self.updates.update({m['update_mapgen_id']: m['object']['set']
                             for m in objects(MOD/'mapgen/apostle_count.json')
                             if 'update_mapgen_id' in m})
        self.updates.update({m['update_mapgen_id']: m['object']['set']
                             for m in objects(MOD/'mapgen/local_breach.json')
                             if 'update_mapgen_id' in m})
        self.omt = 'berserk_count_dungeon'
        self.update_calls = []
        self.in_city = True
        self.active_missions = {}
        self.completed_missions = []
        self.terrain_locations = {}

    def variable(self, name):
        if name.startswith("_"):return self.context.get(name[1:],0)
        return super().variable(name)

    def resolve(self, value):
        if isinstance(value, dict):
            if 'global_val' in value:
                return self.flags[value['global_val']]
            if 'u_val' in value:
                return self.flags['u_'+value['u_val']]
        return super().resolve(value)

    def evaluate(self, expr):
        expr = re.sub(r'(\w+)\.([xyz])', lambda m: str(self.variable(m[1])[{'x':0,'y':1,'z':2}[m[2]]]), expr)
        names = {name: self.variable(name) for name in re.findall(r'\b\w+\b', expr)
                 if not name.startswith('_')}
        names.update({'_'+key: value for key, value in self.context.items()})
        expr = re.sub(r'has_var\((\w+)\)',
                      lambda m: str(m[1] in self.flags or m[1].lstrip('_') in self.context), expr)
        names.update(floor=math.floor, max=max, min=min, abs=abs,
                     u_val=lambda axis: self.avatar[{'pos_x': 0, 'pos_y': 1, 'pos_z': 2}[axis]],
                     n_val=lambda axis: self.victim[{'pos_x': 0, 'pos_y': 1, 'pos_z': 2}[axis]],
                     distance=lambda a, b: max(abs((self.avatar if a=='u' else self.victim if a=='npc' else a)[i]-b[i]) for i in range(3)))
        return eval(expr, {'__builtins__': {}}, names)

    def condition(self, value):
        if value=='has_beta':return self.victim is not None
        if value=='npc_is_monster':
            assert self.victim is not None, 'invalid beta talker'
            return True  # This fixture's explicit victim is a monster.
        if 'overmap_at_point' in value:
            p=self.resolve(value['point'])
            return any((q[0]//24,q[1]//24,q[2])==(p[0]//24,p[1]//24,p[2]) and t==value['overmap_at_point']
                       for q,t in self.terrain_locations.items())
        if 'u_has_mission' in value:
            return value['u_has_mission'] in self.active_missions
        if 'u_has_item' in value:
            return value['u_has_item'] in self.inventory
        if 'math' in value:
            return bool(self.evaluate(value['math'][0]))
        if 'not' in value:
            return not self.condition(value['not'])
        if 'or' in value:
            return any(self.condition(child) for child in value['or'])
        if 'u_at_om_location' in value:
            return self.omt == value['u_at_om_location']
        if 'map_in_city' in value:
            return self.in_city
        if 'x_in_y_chance' in value:
            return True  # deterministic: exercise the successful wilderness branch
        return super().condition(value)

    def effect(self, value):
        if isinstance(value, dict):
            if 'assign_mission' in value:
                definitions={m['id']:m for p in (MOD/'missions').glob('*.json') for m in objects(p)}
                m=definitions[value['assign_mission']]
                self.active_missions[m['id']]=self.resolve(m['start']['assign_mission_target']['var'])
                return
            if 'finish_mission' in value:
                m=value['finish_mission']
                if m in self.active_missions:self.completed_missions.append(m);del self.active_missions[m]
                return
            if 'location_variable_adjust' in value:
                target=value['location_variable_adjust'];scope,key=next(iter(target.items()))
                d=self.context if scope=='context_val' else self.flags
                key=('u_' if scope=='u_val' else '')+key;p=d[key]
                scale=24 if value.get('overmap_tile') else 1
                d[key]=tuple(p[i]+value.get(a+'_adjust',0)*scale for i,a in enumerate(('x','y','z')))
                return
            if 'target_params' in value:
                # Existing Count tests do not simulate generating the next site.
                # Exercise the supported failure/retry path; new hunt tests model success.
                for id in value.get('false_eocs', []):
                    self.run(id)
                return
            if 'math' in value:
                name, rhs = value['math'][0].split(' = ')
                if '.' in name:
                    key,axis=name.split('.');d=self.context if key.startswith('_') else self.flags;key=key.lstrip('_');pos=list(d[key]);pos[{'x':0,'y':1,'z':2}[axis]]=self.evaluate(rhs);d[key]=tuple(pos)
                else:self.flags[name] = self.evaluate(rhs)
                return
            for field, pos in (('u_location_variable', self.avatar),
                               ('npc_location_variable', self.victim)):
                if field in value:
                    def adjustment(axis):
                        a=value.get(axis+'_adjust',0)
                        return self.evaluate(a['math'][0]) if isinstance(a,dict) else a
                    point = tuple(pos[i]+adjustment(axis)
                                  for i, axis in enumerate(('x','y','z')))
                    if value.get('z_override'):
                        point = (*point[:2], value['z_adjust'])
                    target = value[field]
                    if 'global_val' in target:
                        self.flags[target['global_val']] = point
                    elif 'u_val' in target:
                        self.flags['u_'+target['u_val']] = point
                    else:
                        self.context[target['context_val']] = point
                    return
            if 'copy_var' in value:
                target = value['target_var']
                result = self.resolve(value['copy_var'])
                if 'global_val' in target:
                    self.flags[target['global_val']] = result
                elif 'u_val' in target:
                    self.flags['u_'+target['u_val']] = result
                else:
                    self.context[target['context_val']] = result
                return
            if 'reveal_map' in value:
                return
            if 'mapgen_update' in value:
                self.update_calls.append(value['mapgen_update'])
                # Era updates spawn creatures, not furniture; record the selection.
                if value['mapgen_update'].startswith('berserk_eclipse_era_'):
                    return
        return super().effect(value)


def connected(rows, start, blocked='#TAb?rN'):
    seen={start}; todo=deque([start])
    while todo:
        x,y=todo.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            p=(x+dx,y+dy)
            if 0 <= p[0] < len(rows[0]) and 0 <= p[1] < len(rows) and p not in seen:
                if rows[p[1]][p[0]] not in blocked:
                    seen.add(p); todo.append(p)
    return seen


def stitched(filename, arrangement):
    maps={m['om_terrain'][0]:m['object'] for m in objects(MOD/'mapgen'/filename)
          if 'om_terrain' in m}
    grid=[]
    for parts in arrangement:
        for y in range(24):
            grid.append(''.join(maps[id]['rows'][y] for id in parts))
    return maps,grid


class ApostleHunts(unittest.TestCase):
    def test_count_death_registers_for_any_killer_and_preserves_other_hunts(self):
        for killer in ('avatar','npc','zombie',None):
            g=HuntGraph({'berserk_eclipse_era':1,'berserk_hunt_count_state':2,
                         'berserk_hunt_first_breach_state':4})
            g.alpha=killer; g.victim=(-17,71,-1)
            g.run('EOC_BERSERK_COUNT_DIES')
            self.assertEqual(g.flags['berserk_hunt_count_state'],3)
            self.assertEqual(g.flags['berserk_hunt_count_location'],(-24,48,0))
            self.assertEqual(g.flags['berserk_hunt_first_breach_state'],4)

        # Count trophy still comes only from the unique boss's loot.

    def test_two_sealed_regions_do_not_suppress_unrelated_area(self):
        g=HuntGraph({'berserk_hunt_first_breach_state':4,
                     'berserk_hunt_first_breach_location':(0,0,0),
                     'berserk_hunt_count_state':4,
                     'berserk_hunt_count_location':(240,240,0)})
        predicate=g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']
        for pos,expected in (((48,0,0),True),((288,240,0),True),((96,96,0),False)):
            g.context['berserk_quiet_target']=pos
            self.assertEqual(g.condition(predicate),expected)
        g.flags['berserk_hunt_count_state']=3
        g.context['berserk_quiet_target']=(240,240,0)
        self.assertFalse(g.condition(predicate))


    def test_old_sealed_breach_can_register_without_resetting_count(self):
        g=HuntGraph({'u_berserk_breach_sealed':1,
                     'u_berserk_local_breach_location':(48,-24,0),
                     'berserk_hunt_count_state':3})
        g.run('EOC_BERSERK_APOSTLE_MIGRATE_FIRST_BREACH')
        self.assertEqual(g.flags['berserk_hunt_first_breach_location'],(48,-24,0))
        self.assertEqual(g.flags['berserk_hunt_first_breach_state'],4)
        self.assertEqual(g.flags['berserk_hunt_count_state'],3)
        g.flags['u_berserk_local_breach_location']=(999,999,0)
        g.run('EOC_BERSERK_APOSTLE_MIGRATE_FIRST_BREACH')
        self.assertEqual(g.flags['berserk_hunt_first_breach_location'],(48,-24,0))






if __name__=='__main__':unittest.main()
