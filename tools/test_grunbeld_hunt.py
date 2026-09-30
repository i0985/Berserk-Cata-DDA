"""Data/state regression tests, not CDDA combat, loader or native save tests."""
import copy
import gettext
import re
import unittest

from test_behelit_rewards import MOD, objects
from test_named_apostle_hunts import NamedHuntGraph
from test_apostle_hunts import connected, stitched


class DragonGraph(NamedHuntGraph):
    def __init__(self, flags=None):
        super().__init__({'berserk_hunt_count_state':4,'berserk_hunt_wyald_state':4,
                          'berserk_hunt_rosine_state':4,**(flags or {})})
        self.updates.update({m['update_mapgen_id']:m['object']['set']
                             for m in objects(MOD/'mapgen/grunbeld_updates.json')})
        self.boss=None;self.hp=0;self.effects=set();self.cast_succeeds=True
        self.casts=0;self.pause=0;self.grove_actor=False
        self.death_callbacks=0

    def evaluate(self, expr):
        expr=expr.replace("u_hp('ALL')",str(self.hp))
        expr=expr.replace("u_hp_max('torso')",str(950 if self.boss=='dragon' else 720))
        expr=re.sub(r"u_monsters_nearby\('mon_berserk_grunbeld_dragon', 'radius': 0\)",
                    str(int(self.boss=='dragon' and self.hp>0)),expr)
        return super().evaluate(expr)

    def condition(self, value):
        if value=='u_is_monster':return self.boss is not None
        if isinstance(value,dict) and 'u_has_effect' in value:return value['u_has_effect'] in self.effects
        return super().condition(value)

    def effect(self, v):
        if isinstance(v,dict):
            if 'target_params' in v and 'count' in v['target_params']['om_terrain']:
                # Count's own tests cover its site graph; model the retryable search failure here.
                self.locator_calls.append('count')
                for id in v['false_eocs']:self.run(id)
                return
            if 'u_add_effect' in v:self.effects.add(v['u_add_effect']);return
            if 'u_lose_effect' in v:self.effects.discard(v['u_lose_effect']);return
            if 'turn_cost' in v:self.pause+=int(v['turn_cost'].split()[0]);return
            if 'math' in v and v['math'][0].startswith("u_hp('ALL') = "):
                self.hp=self.evaluate(v['math'][0].split(' = ')[1]);return
            if 'u_cast_spell' in v:
                self.casts+=1
                if self.cast_succeeds:self.boss='dragon';self.hp=int(self.hp/720*950)
                # The native true callback means a cast, not confirmed polymorph.
                for id in v['true_eocs']:self.run(id)
                return
            if 'u_run_monster_eocs' in v:
                for type in v['mtype_ids']:
                    active=(type=='mon_berserk_flora_grunbeld' and self.grove_actor or
                            self.boss and type=='mon_berserk_grunbeld_'+self.boss and self.hp>0)
                    if active:
                        for id in v['u_run_monster_eocs']:self.run(id)
                return
            if 'u_die' in v:
                assert v['u_die']['remove_from_creature_tracker']
                self.grove_actor=False # retirement, no death callback/loot
                return
            if 'u_spawn_monster' in v:
                if not self.blocked:
                    self.boss='dragon' if v['u_spawn_monster'].endswith('dragon') else 'knight'
                    self.hp=950 if self.boss=='dragon' else 720
                    self.effects=set()
                return super().effect(v)
        return super().effect(v)

    def begin(self):
        self.run('EOC_BERSERK_GRUNBELD_SEEK');self.arena('grunbeld')
        self.run('EOC_BERSERK_GRUNBELD_ENTER')


class GrunbeldHunt(unittest.TestCase):
    def test_three_sealed_hunts_unlock_late_site_and_saved_coordinate_is_reused(self):
        for key in ('count','wyald','rosine'):
            g=DragonGraph({'berserk_hunt_'+key+'_state':3})
            g.run('EOC_BERSERK_GRUNBELD_SEEK');self.assertFalse(g.locator_calls)
        g=DragonGraph({'berserk_flora_stage':2});g.run('EOC_BERSERK_GRUNBELD_SEEK')
        self.assertFalse(g.locator_calls)
        g=DragonGraph();g.begin();self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],2)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_phase'],1)
        self.assertIn('berserk_grunbeld_knight_form',g.effects)
        saved=copy.deepcopy(g);saved.run('EOC_BERSERK_GRUNBELD_SEEK')
        saved.run('EOC_BERSERK_GRUNBELD_ENTER')
        self.assertEqual(len(saved.locator_calls),1);self.assertEqual(len(saved.spawned),1)

    def test_threshold_and_lethal_hit_both_reveal_one_final_form_without_reward(self):
        for hp in (360,100,0,-5000):
            g=DragonGraph();g.begin();g.hp=hp;g.alpha='monster'
            g.run('EOC_BERSERK_GRUNBELD_TRANSFORM_HIT')
            self.assertEqual(g.boss,'dragon');self.assertEqual(g.hp,950)
            self.assertEqual(g.flags['berserk_hunt_grunbeld_phase'],2)
            self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],2)
            self.assertFalse(g.flags.get('berserk_apostle_grunbeld_dead'))
            self.assertNotIn('berserk_grunbeld_knight_form',g.effects)
            self.assertIn('berserk_grunbeld_dragon_form',g.effects)
            self.assertEqual(g.pause,3)
            g.hp=1;g.run('EOC_BERSERK_GRUNBELD_TRANSFORM_HIT')
            self.assertEqual(g.casts,1);self.assertEqual(g.hp,1)
            self.assertNotIn('berserk_grunbeld_carapace_shard',g.inventory)

    def test_hp_above_threshold_and_failed_poly_do_not_commit_dragon(self):
        g=DragonGraph();g.begin();g.hp=361
        g.run('EOC_BERSERK_GRUNBELD_TRANSFORM_HIT');self.assertEqual(g.casts,0)
        g.hp=100;g.cast_succeeds=False;g.run('EOC_BERSERK_GRUNBELD_TRANSFORM_HIT')
        self.assertEqual(g.boss,'knight');self.assertEqual(g.hp,100)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_phase'],1)
        self.assertNotIn('berserk_grunbeld_dragon_form',g.effects)

    def test_source_less_death_uses_pending_form_and_bounded_retry_not_false_victory(self):
        g=DragonGraph();g.begin();g.alpha=None;g.hp=0
        g.victim=(-466,734,0);g.blocked=True
        g.run('EOC_BERSERK_GRUNBELD_KNIGHT_DIES')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_phase_location'],g.victim)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],2)
        self.assertFalse(g.flags.get('berserk_apostle_grunbeld_dead'))
        g.alpha='avatar'
        for _ in range(10):g.run('EOC_BERSERK_GRUNBELD_DRAGON_RETRY')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_dragon_attempts'],6)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_dragon_pending'],1)
        g.blocked=False;g.run('EOC_BERSERK_GRUNBELD_SEAL')
        self.assertEqual(g.boss,'dragon');self.assertEqual(g.flags['berserk_hunt_grunbeld_phase'],2)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_dragon_pending'],0)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],2)
        saved=copy.deepcopy(g);saved.run('EOC_BERSERK_GRUNBELD_DRAGON_RETRY')
        self.assertEqual(saved.spawned,g.spawned)

    def test_final_death_seal_confirmation_reward_and_repeat_are_independent(self):
        for killer in (None,'zombie','npc','avatar'):
            g=DragonGraph({'berserk_hunt_count_location':(0,0,0),'berserk_hunt_count_state':5})
            g.begin();g.hp=300;g.run('EOC_BERSERK_GRUNBELD_TRANSFORM_HIT')
            g.alpha=killer;g.victim=(-465,735,0);g.run('EOC_BERSERK_GRUNBELD_DIES')
            self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],3)
            self.assertEqual(g.flags['berserk_hunt_grunbeld_phase'],3)
            self.assertEqual(g.flags['berserk_apostle_grunbeld_dead'],1)
            g.alpha='avatar';g.run('EOC_BERSERK_GRUNBELD_SEEK')
            self.assertFalse(g.flags.get('berserk_hunt_grunbeld_reward_claimed'))
            g.fail_updates=True;g.run('EOC_BERSERK_GRUNBELD_SEAL')
            self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],3)
            g.fail_updates=False;g.run('EOC_BERSERK_GRUNBELD_SEAL')
            self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],4)
            g.run('EOC_BERSERK_GRUNBELD_CLAIM')
            self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],5)
            self.assertEqual(g.inventory.count('berserk_grunbeld_carapace_shard'),1)
            saved=copy.deepcopy(g);saved.inventory.remove('berserk_grunbeld_carapace_shard')
            saved.run('EOC_BERSERK_GRUNBELD_CLAIM');saved.run('EOC_BERSERK_GRUNBELD_ENTER')
            self.assertNotIn('berserk_grunbeld_carapace_shard',saved.inventory)
            self.assertEqual(saved.spawned,g.spawned)
            self.assertEqual(g.flags['berserk_hunt_count_location'],(0,0,0))
            g.context['berserk_quiet_target']=(-480,744,0)
            self.assertTrue(g.condition(g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']))
            g.context['berserk_quiet_target']=(480,744,0)
            self.assertFalse(g.condition(g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']))

    def test_old_flora_death_does_not_resurrect_or_duplicate_and_lair_replaces_old_coordinates(self):
        g=DragonGraph({'berserk_apostle_grunbeld_dead':1,'berserk_hunt_grunbeld_state':3,
                       'berserk_hunt_grunbeld_location':(120,120,0),
                       'berserk_hunt_count_state':0,'berserk_hunt_wyald_state':0})
        g.inventory=['berserk_grunbeld_carapace_shard'];g.begin()
        self.assertFalse(g.spawned)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_location'],g.origins['grunbeld'])
        self.assertEqual(g.flags['berserk_hunt_grunbeld_reward_claimed'],1)
        g.run('EOC_BERSERK_GRUNBELD_SEAL');g.run('EOC_BERSERK_GRUNBELD_CLAIM')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],5)
        self.assertEqual(g.inventory.count('berserk_grunbeld_carapace_shard'),1)

    def test_surviving_grove_scene_retires_without_death_or_loot_and_siege_cannot_duplicate(self):
        g=DragonGraph({'berserk_flora_stage':3});g.grove_actor=True;g.begin()
        self.assertFalse(g.grove_actor)
        self.assertFalse(g.flags.get('berserk_apostle_grunbeld_dead'))
        self.assertFalse(g.flags.get('berserk_hunt_grunbeld_reward_claimed'))
        g.run('EOC_BERSERK_FLORA_SPAWN_GRUNBELD')
        self.assertNotIn('mon_berserk_flora_grunbeld',[x[0] for x in g.spawned])
        g.grove_actor=True;g.run('EOC_BERSERK_GRUNBELD_RECALL_OLD_SCENE')
        self.assertFalse(g.grove_actor)

    def test_debug_final_entry_registers_dead_original_lair_instead_of_grove(self):
        g=DragonGraph({'berserk_apostle_grunbeld_dead':1,'berserk_hunt_grunbeld_state':3,
                       'berserk_hunt_grunbeld_location':(120,120,0)})
        g.arena('grunbeld');g.run('EOC_BERSERK_GRUNBELD_ENTER')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_location'],g.origins['grunbeld'])
        self.assertEqual(g.flags['berserk_hunt_grunbeld_site_registered'],1)
        self.assertFalse(g.spawned)
        g.run('EOC_BERSERK_GRUNBELD_SEAL')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_state'],5)
        g.context['berserk_quiet_target']=(120,120,0)
        self.assertFalse(g.condition(g.eocs['EOC_BERSERK_APOSTLE_REGION_QUIET']['condition']))

    def test_flora_death_preserves_registered_lair_and_records_body_drop_once(self):
        g=DragonGraph({'berserk_hunt_grunbeld_site_registered':1,
                       'berserk_hunt_grunbeld_location':(-480,720,0)})
        g.victim=(12,12,0);g.alpha=None
        g.run('EOC_BERSERK_FLORA_GRUNBELD_DIES')
        self.assertEqual(g.flags['berserk_hunt_grunbeld_location'],(-480,720,0))
        self.assertEqual(g.flags['berserk_hunt_grunbeld_reward_claimed'],1)

    def test_six_chunk_map_has_two_connected_routes_and_clear_boss_and_breach(self):
        maps,rows=stitched('apostle_grunbeld.json',[
            ['berserk_grunbeld_approach','berserk_grunbeld_ramparts'],
            ['berserk_grunbeld_quarry','berserk_grunbeld_barracks'],
            ['berserk_grunbeld_ruins','berserk_grunbeld_crucible']])
        self.assertEqual((len(rows[0]),len(rows)),(48,72))
        for entry in ((11,0),(11,71),(0,21)):
            seen=connected(rows,entry,blocked='#TbI?')
            for point in ((36,62),(36,56),(11,45),(37,45),(8,55)):
                self.assertIn(point,seen)
        mobs=[]
        for obj in maps.values():
            for monster in obj['place_monster']:
                self.assertNotIn(obj['rows'][monster['y']][monster['x']],'#TbI?')
                mobs.append(monster['monster'])
        self.assertEqual(len(mobs),6)
        self.assertFalse([m for m in mobs if m.startswith('mon_berserk_grunbeld')])
        for path in (MOD/'monstergroups').glob('*.json'):
            self.assertNotIn('mon_berserk_grunbeld_',path.read_text())

    def test_telegraphs_and_reward_are_partial_heat_protection_not_immunity(self):
        actors={m['id']:m for m in objects(MOD/'monster_special_attacks/grunbeld_attacks.json')}
        for tag,reach in (('hammer',3),('flame',6)):
            a=actors['berserk_grunbeld_'+tag+'_a_strike'];b=actors['berserk_grunbeld_'+tag+'_b_prepare']
            self.assertGreaterEqual(b['move_cost'],260)
            self.assertEqual(b['damage_max_instance'][0]['amount'],0)
            self.assertEqual(a['condition']['u_has_effect'],b['self_effects_always'][0]['id'])
            self.assertEqual(a['range'],reach);self.assertLess(a['id'],b['id'])
        self.assertFalse(actors['berserk_grunbeld_flame_a_strike']['blockable'])
        self.assertEqual(actors['berserk_grunbeld_flame_a_strike']['damage_max_instance'][0]['damage_type'],'heat')
        eocs=(MOD/'effects/grunbeld_hunt_eocs.json').read_text()
        self.assertNotIn("hp_max('ALL')",eocs)
        self.assertNotIn('fd_fire',eocs)
        self.assertNotIn('u_lose_bionic',eocs)
        mon=objects(MOD/'monsters/apostle_grunbeld.json')
        self.assertEqual([m['regenerates'] for m in mon],[0,0])
        self.assertEqual(mon[0]['death_function']['corpse_type'],'NO_CORPSE')
        self.assertTrue(all(m['death_drops']=='EMPTY_GROUP' for m in mon))

    def test_all_new_ui_strings_have_russian_and_chinese_catalog_entries(self):
        keys={'name','str','str_sp','description','desc','text','dynamic_line','u_message','u_query','message',
              'hit_dmg_u','hit_dmg_npc','miss_msg_u','miss_msg_npc','no_dmg_msg_u','no_dmg_msg_npc'}
        texts=set()
        def walk(v):
            if isinstance(v,list):
                for x in v:walk(x)
            elif isinstance(v,dict):
                for key,x in v.items():
                    if key in keys:
                        if isinstance(x,str):texts.add(x)
                        elif isinstance(x,list):texts.update(t for t in x if isinstance(t,str))
                    walk(x)
        for p in ('effects/grunbeld_hunt_eocs.json','effects/grunbeld_combat_effects.json',
                  'monsters/apostle_grunbeld.json','monster_special_attacks/grunbeld_attacks.json',
                  'furniture/grunbeld_hunt.json','overmap/grunbeld_hunt.json','spells/grunbeld_forms.json'):
            walk(objects(MOD/p))
        for lang in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{lang}/LC_MESSAGES/Berserk.mo').open('rb') as f:cat=gettext.GNUTranslations(f)
            self.assertFalse([s for s in texts if cat.gettext(s)==s],lang)

    def test_both_forms_are_in_existing_detection_limits_and_damage_whitelist(self):
        for path in ('effects/eclipse_brand_eocs.json','effects/eclipse_era_eocs.json','effects/apostle_relic_eocs.json'):
            data=(MOD/path).read_text()
            for form in ('knight','dragon'):self.assertIn('mon_berserk_grunbeld_'+form,data)
        g=DragonGraph({'berserk_apostle_grunbeld_dead':1,'berserk_hunt_count_state':5,
                       'berserk_hunt_wyald_state':3,'berserk_hunt_rosine_state':4})
        g.run('EOC_BERSERK_GRUNBELD_NEXT')
        self.assertEqual(g.locator_calls,['wyald'])
        self.assertEqual(g.flags['berserk_hunt_wyald_state'],3)


if __name__=='__main__':unittest.main()
