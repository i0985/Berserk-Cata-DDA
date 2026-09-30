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

    def resolve(self, value):
        if isinstance(value, dict):
            if 'global_val' in value:
                return self.flags[value['global_val']]
            if 'u_val' in value:
                return self.flags['u_'+value['u_val']]
        return super().resolve(value)

    def evaluate(self, expr):
        names = {name: self.variable(name) for name in re.findall(r'\b\w+\b', expr)
                 if not name.startswith('_')}
        names.update({'_'+key: value for key, value in self.context.items()})
        expr = re.sub(r'has_var\((\w+)\)',
                      lambda m: str(m[1] in self.flags or m[1].lstrip('_') in self.context), expr)
        names.update(floor=math.floor, max=max, min=min,
                     u_val=lambda axis: self.avatar[{'pos_x': 0, 'pos_y': 1, 'pos_z': 2}[axis]],
                     n_val=lambda axis: self.victim[{'pos_x': 0, 'pos_y': 1, 'pos_z': 2}[axis]],
                     distance=lambda a, b: max(abs(a[i]-b[i]) for i in range(3)))
        return eval(expr, {'__builtins__': {}}, names)

    def condition(self, value):
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
            if 'target_params' in value:
                # Existing Count tests do not simulate generating the next site.
                # Exercise the supported failure/retry path; new hunt tests model success.
                for id in value.get('false_eocs', []):
                    self.run(id)
                return
            if 'math' in value:
                name, rhs = value['math'][0].split(' = ')
                self.flags[name] = self.evaluate(rhs)
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
                    else:
                        self.context[target['context_val']] = point
                    return
            if 'copy_var' in value:
                target = value['target_var']
                result = self.resolve(value['copy_var'])
                if 'global_val' in target:
                    self.flags[target['global_val']] = result
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

    def test_guardian_alive_and_failed_update_cannot_complete_hunt(self):
        g=HuntGraph({'berserk_eclipse_era':1,'berserk_hunt_count_state':2})
        g.avatar=(35,6,-1); g.context={'pos':(36,5,-1)}
        g.furniture[g.context['pos']]='f_berserk_count_breach'
        g.run('EOC_BERSERK_COUNT_SEAL')
        self.assertFalse(g.update_calls)
        g.flags['berserk_hunt_count_state']=3; g.fail_updates=True
        g.run('EOC_BERSERK_COUNT_SEAL')
        self.assertEqual(g.flags['berserk_hunt_count_state'],3)
        g.fail_updates=False; g.run('EOC_BERSERK_COUNT_SEAL')
        self.assertEqual(g.flags['berserk_hunt_count_state'],4)
        self.assertEqual(g.flags['berserk_hunt_count_location'],(24,0,0))
        g=copy.deepcopy(g)  # data persistence, not an actual game save/load
        calls=len(g.update_calls);g.run('EOC_BERSERK_COUNT_SEAL')
        self.assertEqual(len(g.update_calls),calls)
        self.assertEqual(g.inventory, ['berserk_apostle_hunt_journal'])
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

    def test_all_era_seed_branches_guard_target_not_just_entry_tile(self):
        for direction in ('EAST','WEST','NORTH','SOUTH'):
            for city in (True,False):
                g=HuntGraph({'berserk_hunt_count_state':4,
                             'berserk_hunt_count_location':(240,240,0)})
                g.avatar=(168,240,0)  # outside quiet region, target is inside
                g.context={'berserk_quiet_target':(216,240,0),
                           'berserk_era_neighbor':(216,240,0)}
                g.in_city=city
                e=g.eocs[f'EOC_BERSERK_ECLIPSE_ERA_SEED_{direction}']
                if g.condition(e['condition']):g.effect(e['effect'])
                else:g.effect(e['false_effect'])
                self.assertFalse(g.update_calls)
                g.context['berserk_quiet_target']=(168,240,0)
                if g.condition(e['condition']):g.effect(e['effect'])
                else:g.effect(e['false_effect'])
                self.assertEqual(len(g.update_calls),1)

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

    def test_first_breach_update_failure_and_repeated_examine_preserve_rewards(self):
        g=HuntGraph({'u_berserk_first_hunt_done':1,'u_berserk_breach_guardian_defeated':1})
        g.omt='berserk_local_breach';g.avatar=(10,11,0);g.context={'pos':(11,11,0)}
        g.furniture[(11,11,0)]='f_berserk_open_breach';g.fail_updates=True
        g.run('EOC_BERSERK_BREACH_CLOSE')
        self.assertFalse(g.flags.get('u_berserk_breach_sealed'))
        self.assertFalse(g.flags.get('berserk_hunt_first_breach_state'))
        self.assertFalse(g.inventory)
        g.fail_updates=False;g.run('EOC_BERSERK_BREACH_CLOSE')
        self.assertEqual(g.flags['berserk_hunt_first_breach_state'],4)
        self.assertEqual(g.inventory,['berserk_post_eclipse_journal'])
        g.run('EOC_BERSERK_BREACH_CLOSE')
        self.assertEqual(g.inventory,['berserk_post_eclipse_journal'])

    def test_residence_and_dungeon_have_two_approaches_and_matching_stairs(self):
        maps,rows=stitched('apostle_count.json',[
            ['berserk_count_prison','berserk_count_hall'],
            ['berserk_count_west_yard','berserk_count_east_yard']])
        for entry in ((23,47),(0,30)):
            route=connected(rows,entry)
            self.assertIn((36,20),route)
            self.assertIn((8,32),route)  # adjacent to optional supply rack
            self.assertIn((7,17),route)  # adjacent to witness
        self.assertEqual(rows[20][36],'V')
        self.assertEqual(maps['berserk_count_prison']['rows'][17][10],'+')
        dungeon=maps['berserk_count_dungeon']['rows']
        self.assertEqual(dungeon[20][12],'U')
        seen=connected(dungeon,(12,20))
        self.assertIn((12,8),seen)
        self.assertIn((12,6),seen)  # adjacent to sealing furniture
        self.assertIn((5,17),seen);self.assertIn((18,17),seen)
        for obj in maps.values():
            self.assertEqual(len(obj['rows']),24)
            self.assertTrue(all(len(r)==24 for r in obj['rows']))
            for m in obj.get('place_monster',[]):
                self.assertNotIn(obj['rows'][m['y']][m['x']],'#rAb?')
        placed=[p['monster'] for m in maps.values() for p in m.get('place_monster',[])]
        self.assertEqual(placed.count('mon_berserk_apostle_count'),1)
        self.assertEqual(placed.count('mon_berserk_count_servant'),8)
        for path in (MOD/'monstergroups').glob('*.json'):
            self.assertNotIn('mon_berserk_apostle_count',path.read_text())

    def test_cave_loops_and_guardian_are_separated_from_arrival(self):
        maps,rows=stitched('behelit_sites.json',[
            ['berserk_echo_cave_depth','berserk_echo_cave_gallery'],
            ['berserk_echo_cave_passage','berserk_echo_cave_relic_chamber']])
        seen=connected(rows,(12,12))
        self.assertEqual(rows[12][12],'U');self.assertEqual(rows[29][36],'A')
        for p in ((36,28),(9,32),(12,36),(24,8),(8,24),(36,24),(24,36)):
            self.assertTrue(p in seen, f'unreachable cave point: {p}')
        guardian=next(p for p in maps['berserk_echo_cave_relic_chamber']['place_monster']
                      if p['monster']=='mon_berserk_echo_cave_guardian')
        self.assertGreater(max(abs(guardian['x']+24-12),abs(guardian['y']+24-12)),20)
        cave_eocs={e['id']:e for e in objects(MOD/'effects/behelit_site_eocs.json')}
        noise=cave_eocs['EOC_BERSERK_CAVE_DISTRACTION']['effect']
        self.assertEqual(noise[0]['target_var'],{'context_val':'pos'})
        self.assertEqual(noise[-1],{'turn_cost':'1 sec'})

    def test_new_text_and_monster_plurals_are_localized(self):
        messages=set(); plurals=[]
        def collect(v):
            if isinstance(v,list):
                for p in v:collect(p)
            elif isinstance(v,dict):
                for key,child in v.items():
                    if key in {'name','desc','description','u_message','dynamic_line','text','menu_text',
                               'hit_dmg_u','hit_dmg_npc','miss_msg_u','miss_msg_npc','no_dmg_msg_u','no_dmg_msg_npc'}:
                        if isinstance(child,str):messages.add(child)
                        elif isinstance(child,list):messages.update(s for s in child if isinstance(s,str))
                        elif isinstance(child,dict) and 'str' in child:
                            messages.add(child['str'])
                            if 'str_pl' in child:plurals.append((child['str'],child['str_pl']))
                    collect(child)
        for folder in ('effects','monsters','furniture','dialogue','items','monster_special_attacks','overmap'):
            for path in (MOD/folder).glob('apostle_*.json'):collect(objects(path))
        for locale in ('ru','zh_CN'):
            with (MOD/'lang/mo'/locale/'LC_MESSAGES/Berserk.mo').open('rb') as f:
                catalog=gettext.GNUTranslations(f)
            self.assertFalse({s for s in messages if catalog.gettext(s)==s},locale)
            for singular,plural in plurals:
                for count in (1,2,5):
                    self.assertNotIn(catalog.ngettext(singular,plural,count),(singular,plural))


if __name__=='__main__':unittest.main()
