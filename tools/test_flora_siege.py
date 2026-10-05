"""Data-level siege regression checks; no native game loader, AI or saves."""

import copy
import gettext
import json
import re
import unittest

from test_flora import FloraGraph, ARMOR
from test_apostle_hunts import connected, stitched
from test_behelit_rewards import MOD, objects


class SiegeGraph(FloraGraph):
    def __init__(self, flags=None):
        super().__init__(flags)
        self.eocs.update({e['id']: e for e in objects(MOD/'effects_on_condition.json')})
        self.clock = 0
        self.confirm = True
        self.avatar = (-81,60,0)
        self.omt = 'berserk_flora_manor_west'
        self.blocked = set()
        self.attempts = []
        self.spawn_targets = []
        self.existing_zodd = False
        self.siege_updates = []
        self.messages = []
        self.popups = []

    def evaluate(self, expr):
        if 'u_monsters_nearby(' in expr:
            # Substitute the count, then evaluate the comparison as the engine does.
            # Returning the count directly incorrectly makes a zero-count guard false.
            def count(match):
                return str(int(self.existing_zodd and 'zodd' in match[0]))
            expr=re.sub(r'u_monsters_nearby\([^)]*\)',count,expr)
        return super().evaluate(expr.replace("time('now')", str(self.clock)))

    def condition(self, value):
        if isinstance(value,str) and value=='u_is_avatar':
            return self.alpha=='avatar'
        if isinstance(value,dict) and 'u_query' in value:
            return self.confirm
        return super().condition(value)

    def effect(self, value):
        if isinstance(value,dict):
            if 'set_string_var' in value:
                target = value['target_var']
                scope = self.flags if 'global_val' in target else self.context
                key = target.get('global_val', target.get('context_val'))
                scope[key] = value['set_string_var']
                return
            if 'location_variable_adjust' in value:
                target=value['location_variable_adjust']
                scope=self.flags if 'global_val' in target else self.context
                key=target.get('global_val',target.get('context_val'))
                pos=scope[key]
                if value.get('overmap_tile'):
                    scale=24
                else:scale=1
                scope[key]=tuple(pos[i]+value.get(axis+'_adjust',0)*scale
                                 for i,axis in enumerate(('x','y','z')))
                return
            if 'u_spawn_monster' in value:
                id=value['u_spawn_monster']
                self.attempts.append(id)
                if id not in self.blocked:
                    self.spawns.append(id)
                    self.spawn_targets.append((id,self.resolve(value['target_var'])))
                    for e in value.get('true_eocs',[]):self.run(e)
                else:
                    for e in value.get('false_eocs',[]):self.run(e)
                return
            if 'mapgen_update' in value:
                self.siege_updates.append((value['mapgen_update'],self.resolve(value['target_var'])))
                return
            if 'u_make_sound' in value:return
            if 'u_message' in value:
                message=re.sub(r'<context_val:([^>]+)>',
                               lambda match:str(self.context.get(match[1],'')),value['u_message'])
                self.messages.append(message)
                if value.get('popup',False):self.popups.append(message)
                return
        return super().effect(value)


def ready(full=False):
    g=SiegeGraph({'berserk_eclipse_era':1,'u_berserk_eclipse_rescue_state':2,
                  'berserk_flora_stage':1,'berserk_flora_location':(-96,48,0),
                  'berserk_flora_center':(-72,72,0)})
    if full:g.worn=set(ARMOR)
    return g


class FloraSiege(unittest.TestCase):
    def test_preparation_waits_for_activation_and_does_not_duplicate_armor(self):
        for full in (False,True):
            g=ready(full);g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
            self.assertEqual(set(g.inventory), {'berserk_flora_escape_charm'} | (set() if full else ARMOR))
            self.assertEqual(g.flags['berserk_flora_siege_state'],1)
            for clock in (0,30,90,86400):
                g.clock=clock;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)
            self.assertEqual(g.flags['berserk_flora_stage'],1)
            saved=copy.deepcopy(g)  # abstract state, not native save/load
            saved.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
            self.assertEqual(saved.inventory,g.inventory)

    def test_fake_speaker_pre_eclipse_and_repeated_claim_cannot_prepare(self):
        for configure in (lambda g:setattr(g,'beta',None),
                          lambda g:setattr(g,'beta','mon_skull_knight_rescuer'),
                          lambda g:g.flags.update(berserk_eclipse_era=0),
                          lambda g:g.flags.update(berserk_flora_stage=3),
                          lambda g:g.flags.update(berserk_flora_siege_state=5)):
            g=ready();configure(g);g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
            self.assertFalse(g.inventory);self.assertFalse(g.siege_updates)

    def test_charm_replacement_only_before_attack_and_activation_needs_no_second_query(self):
        g=ready();g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        g.inventory.remove('berserk_flora_escape_charm')
        g.run('EOC_BERSERK_FLORA_REPLACE_CHARM');g.run('EOC_BERSERK_FLORA_REPLACE_CHARM')
        self.assertEqual(g.inventory.count('berserk_flora_escape_charm'),1)
        g.omt='field';g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertEqual(g.flags['berserk_flora_siege_state'],1)
        self.assertFalse(g.spawns);self.assertFalse(g.siege_updates)
        g.confirm=False;g.omt='berserk_flora_manor_west'
        g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertEqual(g.flags['berserk_flora_siege_state'],2)

    def test_phase_clock_spawns_once_at_fixed_approaches_and_survives_state_copy(self):
        g=ready();g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE');g.clock=700
        g.run('EOC_BERSERK_FLORA_START_SIEGE');g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertEqual(g.spawns,['mon_berserk_flora_root_guard']*2)
        g.clock=729;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_state'],2)
        g=copy.deepcopy(g);g.clock=730;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_state'],3)
        self.assertIn(('mon_berserk_flora_zodd',(-82,50,0)),g.spawn_targets)
        self.assertIn(('mon_berserk_flora_grunbeld',(-52,66,0)),g.spawn_targets)
        g.clock=790;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_state'],4)
        g.clock=1000;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.spawns.count('mon_berserk_flora_zodd'),1)
        self.assertEqual(g.spawns.count('mon_berserk_flora_grunbeld'),1)
        self.assertEqual(len(g.siege_updates),12)

    def test_blocked_approach_has_bounded_retries_and_never_blocks_escape(self):
        g=ready();g.blocked={'mon_berserk_flora_zodd','mon_berserk_flora_grunbeld'}
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE');g.run('EOC_BERSERK_FLORA_START_SIEGE')
        for t in range(0,200):
            g.clock=t;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        for name in ('zodd','grunbeld'):
            self.assertEqual(g.attempts.count('mon_berserk_flora_'+name),6)
        g.avatar=(-106,62,0);g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_state'],5)
        self.assertEqual(g.flags['berserk_flora_stage'],3)

    def test_escape_preserves_house_then_fire_clock_updates_registered_manor_once(self):
        for escape in ((-105,62,0),(-72,105,0),(10000,10000,0)):
            g=ready();g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE');g.run('EOC_BERSERK_FLORA_START_SIEGE')
            g.avatar=escape;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            self.assertEqual(g.flags['u_berserk_flora_escaped'],1)
            ruins=[(id,pos) for id,pos in g.siege_updates if '_ruins_' in id]
            self.assertFalse(ruins)
            saved=copy.deepcopy(g);saved.avatar=(-81,60,0)
            saved.run('EOC_BERSERK_FLORA_START_SIEGE');saved.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            self.assertEqual(saved.siege_updates,g.siege_updates)
            self.assertEqual(saved.spawns,g.spawns)
            saved.clock=600;saved.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            ruins=[(id,pos) for id,pos in saved.siege_updates if '_ruins_' in id]
            self.assertEqual({pos for id,pos in ruins},{(-96,48,0),(-72,48,0),(-96,72,0),(-72,72,0)})
            updates=list(saved.siege_updates)
            saved.clock=1200;saved.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            self.assertEqual(saved.siege_updates,updates)

    def test_dead_originals_are_not_spawned_and_projections_do_not_set_death_registry(self):
        for killer in ('avatar','npc','zombie',None):
            g=ready();g.alpha=killer;g.victim=(-52,66,0)
            g.run('EOC_BERSERK_FLORA_GRUNBELD_DIES');g.run('EOC_BERSERK_FLORA_ZODD_DIES')
            self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],3)
            self.assertEqual(g.flags['berserk_hunt_grunbeld_location'],(-72,48,0))
            g.alpha='avatar';g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE');g.run('EOC_BERSERK_FLORA_START_SIEGE')
            g.clock=30;g.run('EOC_BERSERK_FLORA_SIEGE_TICK');g.run('EOC_BERSERK_ZODD_PURSUER')
            self.assertNotIn('mon_berserk_flora_zodd',g.spawns)
            self.assertNotIn('mon_berserk_flora_grunbeld',g.spawns)
            self.assertEqual(sum(id in ('mon_berserk_flora_raider','mon_berserk_flora_reaver')
                                 for id in g.spawns),10)
        projections=objects(MOD/'monsters/apostle_projections.json')
        self.assertTrue(all(m['death_function']['eoc']==('EOC_BERSERK_GRIFFITH_PROJECTION_DIES' if m['id']=='mon_berserk_projection_griffith' else 'EOC_BERSERK_BEHELIT_BOSS_DIES') for m in projections))
        g=ready();g.existing_zodd=True;g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE');g.run('EOC_BERSERK_FLORA_START_SIEGE')
        g.clock=30;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertNotIn('mon_berserk_flora_zodd',g.spawns)
        self.assertEqual(g.flags['berserk_flora_zodd_spawned'],1)

    def test_legacy_zodd_keeps_behelit_reward_and_records_death_for_any_killer(self):
        for killer in ('avatar','npc','zombie',None):
            g=SiegeGraph();g.alpha=killer;g.victim=(71,-15,0)
            g.run('EOC_BERSERK_FLORA_LEGACY_ZODD_DIES')
            self.assertEqual(g.flags['berserk_apostle_zodd_dead'],1)
            self.assertEqual(g.ground,[('berserk_behelit',(71,-15,0))])

    def test_siege_patches_preserve_paths_without_forced_doors_or_floor_repainting(self):
        maps,rows=stitched('flora_manor.json',[
            ['berserk_flora_manor_west','berserk_flora_manor_east'],
            ['berserk_flora_garden_west','berserk_flora_garden_east']])
        offsets={'west':(0,0),'east':(24,0),'garden_west':(0,24),'garden_east':(24,24)}
        updates=objects(MOD/'mapgen/flora_siege_updates.json')
        for phase in ('warning','assault','collapse','ruins'):
            grid=[list(r) for r in rows]
            for update in updates:
                id=update['update_mapgen_id']
                if '_'+phase+'_' not in id:continue
                suffix=id.removeprefix('berserk_flora_'+phase+'_');dx,dy=offsets[suffix]
                obj=update['object']
                self.assertEqual(obj['flags'],['ALLOW_TERRAIN_UNDER_OTHER_DATA'])
                for change in obj.get('set',[]):
                    if change.get('point')=='furniture':continue
                    self.assertFalse(change['id'].startswith('t_door'))
                    self.assertNotIn(change['id'],('t_berserk_flora_ash_floor','t_berserk_flora_charred_wall'))
                    x,y=change['x'],change['y'];x2,y2=change.get('x2',x),change.get('y2',y)
                    for yy in range(y,y2+1):
                        for xx in range(x,x2+1):
                            grid[yy+dy][xx+dx]='#' if change['id']=='t_berserk_flora_charred_wall' else '.'
                for field in obj.get('place_fields',[]):
                    self.assertIn(field['field'],('fd_smoke','fd_fire'))
                    self.assertIsInstance(field['age'],int)
            seen=connected(grid,(15,12),blocked='#TWG')
            self.assertIn((0,14),seen,phase);self.assertIn((24,47),seen,phase)
            self.assertNotIn('remove_all',json.dumps(updates))
            self.assertNotIn('item_remove',json.dumps(updates))
        self.assertIn('fd_fire',json.dumps(updates))
        cleanup=json.dumps(next(e for e in objects(MOD/'effects/flora_siege_eocs.json') if e['id']=='EOC_BERSERK_FLORA_RUINS_CLEANUP'))
        self.assertNotIn('mon_berserk_flora_zodd',cleanup)
        self.assertNotIn('mon_berserk_flora_grunbeld',cleanup)

    def test_faction_hostility_and_original_sprite_fallbacks(self):
        factions={e['name']:e for e in objects(MOD/'monster_factions.json')}
        self.assertIn('berserk_flora_attackers',factions['berserk_flora_guardians']['hate'])
        self.assertIn('berserk_flora_guardians',factions['berserk_flora_attackers']['hate'])
        actors={e['id']:e for e in objects(MOD/'monsters/flora_siege.json')}
        self.assertNotIn('PACIFIST',actors['mon_berserk_flora_root_guard']['flags'])
        self.assertEqual(actors['mon_berserk_flora_zodd']['looks_like'],'mon_nosferatu_zodd')
        self.assertNotIn('IMMOBILE',actors['mon_berserk_flora_grunbeld']['flags'])
        self.assertEqual(actors['mon_berserk_flora_grunbeld']['regenerates'],0)
        effects=json.dumps(objects(MOD/'effects/flora_siege_eocs.json'))
        self.assertNotIn('u_teleport',effects);self.assertNotIn('u_prevent_death',effects)

    def test_new_user_messages_are_compiled_in_both_languages(self):
        texts=set()
        plural_pairs=[]
        keys={'name','str_sp','str','description','text','dynamic_line','yes','no',
              'u_message','u_query','u_make_sound','menu_text'}
        def collect(value):
            if isinstance(value,list):
                for v in value:collect(v)
            elif isinstance(value,dict):
                if 'str' in value and 'str_pl' in value:
                    plural_pairs.append((value['str'],value['str_pl']))
                for key,child in value.items():
                    if key in keys and isinstance(child,str):texts.add(child)
                    collect(child)
        for path in ('effects/flora_siege_eocs.json','dialogue/flora.json','items/flora_escape_charm.json',
                     'monsters/flora_siege.json','mapgen/flora_siege_terrain.json'):
            collect(objects(MOD/path))
        for locale in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo').open('rb') as f:cat=gettext.GNUTranslations(f)
            self.assertFalse([s for s in texts if cat.gettext(s)==s],locale)
            self.assertFalse([s for s,p in plural_pairs if cat.ngettext(s,p,2)==p],locale)


if __name__=='__main__':unittest.main()
