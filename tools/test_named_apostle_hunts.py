"""Independent named hunt data checks, not native combat/mapgen/save tests."""
import copy
import gettext
import json
import unittest

from test_apostle_hunts import HuntGraph, connected, stitched
from test_behelit_rewards import MOD, objects


class NamedHuntGraph(HuntGraph):
    def __init__(self, flags=None):
        super().__init__({'berserk_eclipse_era':1,'u_berserk_eclipse_rescue_state':2,
                          'u_berserk_first_hunt_done':1,**(flags or {})})
        self.updates.update({m['update_mapgen_id']:m['object']['set']
                             for m in objects(MOD/'mapgen/wyald_rosine_updates.json')})
        self.locator_calls=[]
        self.can_locate=True
        self.blocked=False
        self.spawn_attempts=[]
        self.spawned=[]
        self.origins={'wyald':(-72,24,0),'rosine':(432,-240,0)}

    def run(self, id):
        obj=self.eocs[id]
        if 'condition' not in obj or self.condition(obj['condition']):
            self.effect(obj['effect'])
        elif 'false_effect' in obj:
            self.effect(obj['false_effect'])

    def effect(self, value):
        if isinstance(value,dict):
            if 'target_params' in value:
                kind='wyald' if 'wyald' in value['target_params']['om_terrain'] else 'rosine'
                self.locator_calls.append(kind)
                if self.can_locate:
                    origin=self.origins[kind]
                    self.flags[value['u_location_variable']['global_val']]=(origin[0]+12,origin[1]+7,0)
                    for id in value['true_eocs']:self.run(id)
                else:
                    for id in value['false_eocs']:self.run(id)
                return
            if 'location_variable_adjust' in value:
                target=value['location_variable_adjust']
                scope=self.flags if 'global_val' in target else self.context
                key=target.get('global_val',target.get('context_val'));pos=scope[key]
                scale=24 if value.get('overmap_tile') else 1
                if scale==24:pos=(pos[0]//24*24,pos[1]//24*24,pos[2])
                scope[key]=tuple(pos[i]+value.get(axis+'_adjust',0)*scale
                                 for i,axis in enumerate(('x','y','z')))
                return
            if 'u_spawn_monster' in value:
                id=value['u_spawn_monster'];self.spawn_attempts.append(id)
                if not self.blocked:
                    self.spawned.append((id,self.resolve(value['target_var'])))
                    for e in value['true_eocs']:self.run(e)
                else:
                    for e in value['false_eocs']:self.run(e)
                return
        return super().effect(value)

    def arena(self,kind):
        origin=self.origins[kind]
        self.omt='berserk_'+kind+('_ring' if kind=='wyald' else '_nest')
        self.avatar=(origin[0]+12,origin[1]+12,0)
        self.context['pos']=(origin[0]+12,origin[1]+7,0)
        self.furniture[self.context['pos']]='f_berserk_'+kind+'_breach'


class NamedApostleHunts(unittest.TestCase):
    def test_discovery_is_post_eclipse_and_locator_is_reused_without_resetting_progress(self):
        for kind in ('wyald','rosine'):
            K=kind.upper();g=NamedHuntGraph({'berserk_eclipse_era':0})
            g.run('EOC_BERSERK_'+K+'_SEEK');self.assertFalse(g.locator_calls)
            g.flags['berserk_eclipse_era']=1;g.can_locate=False
            g.run('EOC_BERSERK_'+K+'_SEEK')
            self.assertFalse(g.flags.get('berserk_hunt_'+kind+'_state'))
            g.can_locate=True;g.run('EOC_BERSERK_'+K+'_SEEK')
            self.assertEqual(g.flags['berserk_hunt_'+kind+'_location'],g.origins[kind])
            self.assertEqual(g.flags['berserk_hunt_'+kind+'_state'],1)
            for state in (2,3,4,5):
                g.flags['berserk_hunt_'+kind+'_state']=state
                g.run('EOC_BERSERK_'+K+'_SEEK')
                self.assertEqual(g.flags['berserk_hunt_'+kind+'_state'],state)
            self.assertEqual(g.locator_calls,[kind,kind])

    def test_only_final_omt_starts_boss_once_and_failed_spawn_can_be_retried(self):
        for kind in ('wyald','rosine'):
            K=kind.upper();g=NamedHuntGraph();g.run('EOC_BERSERK_'+K+'_SEEK')
            g.omt='field';g.run('EOC_BERSERK_'+K+'_ENTER');self.assertFalse(g.spawned)
            g.arena(kind);g.blocked=True
            for _ in range(10):g.run('EOC_BERSERK_'+K+'_RETRY')
            self.assertEqual(len(g.spawn_attempts),6)
            self.assertFalse(g.flags.get('berserk_hunt_'+kind+'_spawned'))
            g.blocked=False;g.run('EOC_BERSERK_'+K+'_SEAL') # explicit retry, not early seal
            self.assertEqual(len(g.spawned),1)
            self.assertEqual(g.flags['berserk_hunt_'+kind+'_state'],2)
            saved=copy.deepcopy(g)
            for _ in range(10):saved.run('EOC_BERSERK_'+K+'_ENTER')
            self.assertEqual(saved.spawned,g.spawned)
            self.assertFalse(g.inventory)

    def test_all_five_states_and_unique_reward_for_both_hunts(self):
        for kind,relic in (('wyald','berserk_wyald_beast_knot'),('rosine','berserk_rosine_mistvale_veil')):
            K=kind.upper();key='berserk_hunt_'+kind+'_state';g=NamedHuntGraph()
            g.run('EOC_BERSERK_'+K+'_SEEK');self.assertEqual(g.flags[key],1)
            g.arena(kind);g.run('EOC_BERSERK_'+K+'_ENTER');self.assertEqual(g.flags[key],2)
            g.run('EOC_BERSERK_'+K+'_SEAL');self.assertEqual(g.flags[key],2)
            g.victim=(999,999,0);g.run('EOC_BERSERK_'+K+'_DIES');self.assertEqual(g.flags[key],3)
            self.assertEqual(g.flags['berserk_hunt_'+kind+'_location'],g.origins[kind])
            self.assertNotIn(relic,g.inventory)
            g.fail_updates=True;g.run('EOC_BERSERK_'+K+'_SEAL');self.assertEqual(g.flags[key],3)
            g.fail_updates=False;g.run('EOC_BERSERK_'+K+'_SEAL');self.assertEqual(g.flags[key],4)
            self.assertNotIn(relic,g.inventory)
            g.run('EOC_BERSERK_'+K+'_CLAIM');self.assertEqual(g.flags[key],5)
            self.assertEqual(g.inventory.count(relic),1)
            self.assertEqual(g.inventory.count('berserk_apostle_hunt_journal'),1)
            saved=copy.deepcopy(g);saved.inventory.remove(relic)
            saved.run('EOC_BERSERK_'+K+'_CLAIM');saved.run('EOC_BERSERK_'+K+'_ENTER')
            self.assertNotIn(relic,saved.inventory)
            self.assertEqual(saved.spawned,g.spawned)

    def test_reward_from_wrong_place_and_existing_prototype_do_not_duplicate(self):
        for kind,relic in (('wyald','berserk_wyald_beast_knot'),('rosine','berserk_rosine_mistvale_veil')):
            K=kind.upper();g=NamedHuntGraph({'berserk_hunt_'+kind+'_state':4})
            g.arena(kind);g.furniture[g.context['pos']]='f_berserk_'+kind+'_breach_sealed'
            g.omt='field';g.run('EOC_BERSERK_'+K+'_CLAIM');self.assertFalse(g.inventory)
            g.arena(kind);g.inventory.append(relic);g.furniture[g.context['pos']]='f_berserk_'+kind+'_breach_sealed'
            g.run('EOC_BERSERK_'+K+'_CLAIM');self.assertEqual(g.inventory.count(relic),1)
            self.assertEqual(g.flags['berserk_hunt_'+kind+'_state'],5)

    def test_death_registry_has_no_killer_dependency_and_preserves_other_site(self):
        for kind,other in (('wyald','rosine'),('rosine','wyald')):
            for killer in ('avatar','npc','zombie',None):
                g=NamedHuntGraph({'berserk_hunt_'+other+'_state':4,'berserk_hunt_'+other+'_location':(960,960,0)})
                g.alpha=killer;g.victim=(-17,71,0)
                g.run('EOC_BERSERK_'+kind.upper()+'_DIES')
                self.assertEqual(g.flags['berserk_hunt_'+kind+'_state'],3)
                self.assertEqual(g.flags['berserk_apostle_'+kind+'_dead'],1)
                self.assertEqual(g.flags['berserk_hunt_'+other+'_state'],4)
                self.assertEqual(g.flags['berserk_hunt_'+other+'_location'],(960,960,0))
                g.alpha='avatar';g.arena(kind);g.run('EOC_BERSERK_'+kind.upper()+'_ENTER')
                self.assertFalse(g.spawned)

    def test_independent_local_quiet_persists_after_reward_and_never_clears_creatures(self):
        g=NamedHuntGraph({'berserk_hunt_count_state':5,'berserk_hunt_count_location':(0,0,0),
                         'berserk_hunt_wyald_state':4,'berserk_hunt_wyald_location':(480,0,0),
                         'berserk_hunt_rosine_state':3,'berserk_hunt_rosine_location':(960,0,0)})
        query=g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']
        for loc,expected in (((0,24,0),True),((480,24,0),True),((960,24,0),False),((240,24,0),False)):
            g.context['berserk_quiet_target']=loc;self.assertEqual(g.condition(query),expected)
        g.flags['berserk_hunt_rosine_state']=5;g.context['berserk_quiet_target']=(960,24,0)
        self.assertTrue(g.condition(query))
        eocs=(MOD/'effects/wyald_rosine_hunt_eocs.json').read_text()
        for operation in ('u_die','npc_die','u_lose_bionic','u_lose_effect'):
            # Only special-attack readiness is removed; no demons/Brand/rage cleanup.
            if operation=='u_lose_effect':continue
            self.assertNotIn(operation,eocs)

    def test_count_old_reward_migrates_without_a_second_item_and_keeps_quiet_region(self):
        g=NamedHuntGraph({'berserk_hunt_count_state':4,'berserk_hunt_count_location':(0,0,0)})
        g.run('EOC_BERSERK_COUNT_REWARD_WATCH');self.assertEqual(g.flags['berserk_hunt_count_state'],4)
        g.inventory=['berserk_count_iron_seal'];g.run('EOC_BERSERK_COUNT_REWARD_WATCH')
        self.assertEqual(g.flags['berserk_hunt_count_state'],5)
        self.assertEqual(g.inventory,['berserk_count_iron_seal'])
        g.context['berserk_quiet_target']=(0,0,0)
        self.assertTrue(g.condition(g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']))

    def test_maps_two_paths_splices_cover_and_no_early_or_random_boss_placement(self):
        for kind,parts in [('wyald',['approach','camp','quarry','ring']),('rosine',['trail','cocoons','gully','nest'])]:
            maps,rows=stitched('apostle_'+kind+'.json',[
                ['berserk_'+kind+'_'+parts[0],'berserk_'+kind+'_'+parts[1]],
                ['berserk_'+kind+'_'+parts[2],'berserk_'+kind+'_'+parts[3]]])
            for start in ((11,47),(0,21)):
                seen=connected(rows,start,blocked='#TbI?')
                self.assertIn((36,38),seen);self.assertIn((36,32),seen)
                # Two middle routes and an optional supplies position.
                self.assertIn((11,30),seen);self.assertIn((37,21),seen)
                self.assertIn((8,31),seen)
            spawns=[]
            for obj in maps.values():
                self.assertEqual(len(obj['rows']),24);self.assertTrue(all(len(r)==24 for r in obj['rows']))
                for actor in obj.get('place_monster',[]):
                    self.assertNotIn(obj['rows'][actor['y']][actor['x']],'#TbI?')
                    spawns.append(actor['monster'])
                for loot in obj.get('place_loot',[]):self.assertNotIn('container',loot)
            self.assertEqual(len(spawns),6)
            self.assertNotIn('mon_berserk_apostle_'+kind,spawns)
            for path in (MOD/'monstergroups').glob('*.json'):
                self.assertNotIn('mon_berserk_apostle_'+kind,path.read_text())
        specials=[s for s in objects(MOD/'overmap/wyald_rosine_hunts.json') if s['type']=='overmap_special']
        self.assertTrue(all(s['occurrences']==[0,100] and s['flags']==['GLOBALLY_UNIQUE'] and not s['rotate'] for s in specials))

    def test_telegraph_actors_consume_moves_have_visible_effect_and_ordered_payload(self):
        attacks={a['id']:a for a in objects(MOD/'monster_special_attacks/wyald_rosine_attacks.json')}
        for kind,payload in [('wyald','crush'),('rosine','dive')]:
            prepare=attacks['berserk_'+kind+'_b_prepare'];strike=attacks['berserk_'+kind+'_a_'+payload]
            self.assertGreaterEqual(prepare['move_cost'],220)
            self.assertEqual(prepare['damage_max_instance'][0]['amount'],0)
            self.assertLess(strike['id'],prepare['id'])
            self.assertEqual(strike['condition']['u_has_effect'],prepare['self_effects_always'][0]['id'])
            self.assertEqual(strike['eoc'],['EOC_BERSERK_'+kind.upper()+'_CLEAR_READY'])
            self.assertEqual(prepare['self_effects_always'][0]['duration'],5)
        wyald=objects(MOD/'monsters/apostle_wyald.json')[0];rosine=objects(MOD/'monsters/apostle_rosine.json')[0]
        self.assertEqual(wyald['regenerates'],0);self.assertEqual(rosine['regenerates'],0)
        self.assertEqual(rosine['hp'],420);self.assertIn('FLIES',rosine['flags'])
        self.assertEqual(wyald['death_drops'],'EMPTY_GROUP');self.assertEqual(rosine['death_drops'],'EMPTY_GROUP')

    def test_closed_hunt_gives_next_mark_and_journal_works_without_actor(self):
        g=NamedHuntGraph({'berserk_hunt_wyald_state':3});g.arena('wyald')
        g.run('EOC_BERSERK_WYALD_SEAL')
        self.assertEqual(g.flags['berserk_hunt_rosine_state'],1)
        self.assertEqual(g.flags['berserk_hunt_rosine_location'],g.origins['rosine'])
        self.assertIn('berserk_apostle_hunt_journal',g.inventory)
        g.flags['berserk_hunt_wyald_state']=5;g.flags['berserk_hunt_count_state']=5
        g.flags['berserk_hunt_first_breach_location']=(120,120,0)
        g.run('EOC_BERSERK_ROSINE_NEXT') # concrete return site after all available hunts
        self.assertFalse(g.flags.get('berserk_hunt_grunbeld_state'))
        g.flags['berserk_hunt_rosine_state']=5
        before=list(g.locator_calls)
        g.run('EOC_BERSERK_WYALD_NEXT')
        self.assertEqual(g.locator_calls,before)

    def test_user_strings_are_compiled_in_both_languages(self):
        keys={'name','description','str','str_sp','text','dynamic_line','u_message','u_query','menu_text','desc',
              'hit_dmg_u','hit_dmg_npc','miss_msg_u','miss_msg_npc','no_dmg_msg_u','no_dmg_msg_npc'}
        texts=set();plurals=[]
        def walk(v):
            if isinstance(v,list):
                for child in v:walk(child)
            elif isinstance(v,dict):
                if 'str' in v and 'str_pl' in v:plurals.append((v['str'],v['str_pl']))
                for key,child in v.items():
                    if key in keys:
                        if isinstance(child,str):texts.add(child)
                        elif isinstance(child,list):texts.update(s for s in child if isinstance(s,str))
                    walk(child)
        for path in ['effects/wyald_rosine_hunt_eocs.json','effects/wyald_rosine_combat_effects.json',
                     'furniture/wyald_rosine_hunts.json','overmap/wyald_rosine_hunts.json','mapgen/named_hunt_palettes.json',
                     'monsters/apostle_wyald.json','monsters/apostle_rosine.json','items/apostle_hunt_journal.json',
                     'monster_special_attacks/wyald_rosine_attacks.json']:
            walk(objects(MOD/path))
        # Proper names have identical Latin/Chinese/Russian forms only in English.
        for locale in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{locale}/LC_MESSAGES/Berserk.mo').open('rb') as f:cat=gettext.GNUTranslations(f)
            self.assertFalse([s for s in texts if cat.gettext(s)==s],locale)
            for singular,plural in plurals:
                for count in (1,2,5):
                    self.assertNotIn(cat.ngettext(singular,plural,count),(singular,plural))


if __name__=='__main__':unittest.main()
