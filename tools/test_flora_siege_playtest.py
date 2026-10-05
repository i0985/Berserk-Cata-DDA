"""Regressions from the Flora playtest: data flow only, no CDDA process.

The interpreter checks conditions, clocks and registered coordinates. Field
definitions are inspected as data; native fire spread, AI and rendering are
deliberately outside these checks.
"""

import copy
import json
import unittest

from test_behelit_rewards import MOD, objects
from test_flora_siege import ready


class FloraSiegePlaytest(unittest.TestCase):
    def started(self, **flags):
        graph=ready()
        graph.flags.update(flags)
        graph.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        graph.run('EOC_BERSERK_FLORA_START_SIEGE')
        return graph

    def test_departing_before_assault_does_not_cancel_fire_or_repeat_escort(self):
        g=self.started(berserk_flora_treehouse_layout=1)
        g.avatar=(-105,62,0);g.clock=10
        g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_state'],5)
        self.assertEqual(g.flags['berserk_flora_fire_phase'],1)
        self.assertFalse(any('_ruins_' in update for update,_ in g.siege_updates))
        g.clock=30;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_fire_phase'],2)
        escort=[id for id in g.spawns if id in
                ('mon_berserk_flora_raider','mon_berserk_flora_reaver')]
        self.assertEqual(len(escort),10)
        self.assertEqual(escort.count('mon_berserk_flora_reaver'),3)
        g=copy.deepcopy(g)  # abstract persistence, not a native save
        g.clock=90;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_fire_phase'],3)
        g.clock=600;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_fire_phase'],4)
        spawns=list(g.spawns);patches=list(g.siege_updates)
        g.clock=1200;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.spawns,spawns)
        self.assertEqual(g.siege_updates,patches)

    def test_registered_fortress_does_not_suppress_grove_boss(self):
        g=self.started(berserk_hunt_grunbeld_site_registered=1)
        g.clock=30;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertIn('mon_berserk_flora_grunbeld',g.spawns)

    def test_living_fortress_original_is_not_duplicated(self):
        g=self.started(berserk_hunt_grunbeld_site_registered=1,
                       berserk_hunt_grunbeld_spawned=1)
        g.clock=30;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertNotIn('mon_berserk_flora_grunbeld',g.spawns)
        self.assertEqual(g.spawns.count('mon_berserk_flora_raider'),7)

    def test_offscreen_recall_waits_until_aftermath_and_distance(self):
        g=self.started(berserk_hunt_grunbeld_site_registered=1)
        g.flags.update(berserk_flora_stage=3,berserk_flora_siege_state=5)
        for eoc in ('EOC_BERSERK_GRUNBELD_RECALL_GROVE',
                    'EOC_BERSERK_GRUNBELD_RECALL_OLD_SCENE'):
            condition=g.eocs[eoc]['condition']
            g.flags['berserk_flora_fire_phase']=3;g.avatar=(-200,72,0)
            self.assertFalse(g.condition(condition))
            g.flags['berserk_flora_fire_phase']=4;g.avatar=(-90,72,0)
            self.assertFalse(g.condition(condition))
            g.avatar=(-200,72,0)
            self.assertTrue(g.condition(condition))

    def test_completed_legacy_scene_does_not_restart_fire(self):
        g=ready();g.flags.update(berserk_flora_stage=3,berserk_flora_siege_state=5)
        g.clock=1000;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertFalse(g.siege_updates);self.assertFalse(g.spawns)
        self.assertNotIn('berserk_flora_siege_v2',g.flags)

    def test_active_legacy_scene_upgrades_without_resetting_original_fates(self):
        g=ready();g.flags.update(berserk_flora_stage=2,berserk_flora_siege_state=3,
                               berserk_flora_siege_started=0,
                               berserk_apostle_grunbeld_dead=1,
                               berserk_flora_zodd_spawned=1)
        g.clock=40;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(g.flags['berserk_flora_siege_v2'],1)
        self.assertEqual(g.flags['berserk_flora_fire_phase'],2)
        self.assertEqual(g.flags['berserk_flora_siege_started'],0)
        self.assertNotIn('mon_berserk_flora_zodd',g.spawns)
        self.assertNotIn('mon_berserk_flora_grunbeld',g.spawns)

    def test_seed_fields_are_real_fire_and_updates_never_replace_terrain(self):
        for file in ('flora_treehouse_updates.json','flora_siege_updates.json'):
            seeds=[]
            for patch in objects(MOD/'mapgen'/file):
                obj=patch['object']
                self.assertFalse([p for p in obj.get('set',[]) if p.get('point')=='terrain'])
                self.assertNotIn('f_berserk_flora_held_embers',json.dumps(obj))
                fire=[f for f in obj.get('place_fields',[]) if f['field']=='fd_fire']
                if '_warning_' in patch['update_mapgen_id'] or '_ruins_' in patch['update_mapgen_id']:
                    self.assertFalse(fire)
                seeds.extend(fire)
            self.assertEqual(len(seeds),10)
            self.assertTrue(all(f['intensity']==2 and f['age']==-300 for f in seeds))
        ruins=next(e for e in objects(MOD/'effects/flora_siege_eocs.json')
                   if e['id']=='EOC_BERSERK_FLORA_UPDATE_RUINS')
        self.assertNotIn('u_transform_radius',json.dumps(ruins))

    def test_escort_uses_existing_art_and_has_no_summon_timer(self):
        monsters={m['id']:m for m in objects(MOD/'monsters/flora_siege.json')}
        spawn=next(e for e in objects(MOD/'effects/flora_siege_eocs.json')
                   if e['id']=='EOC_BERSERK_FLORA_SPAWN_ESCORT')
        for mtype in ('mon_berserk_flora_raider','mon_berserk_flora_reaver'):
            actor=monsters[mtype]
            self.assertEqual(actor['looks_like'],actor['copy-from'])
            self.assertEqual(actor['default_faction'],'berserk_flora_attackers')
        specs=[s for s in spawn['effect'] if 'u_spawn_monster' in s]
        self.assertEqual(len(specs),10)
        self.assertTrue(all(s['real_count']==1 and 'lifespan' not in s for s in specs))

    def test_escape_has_one_summary_and_no_future_unknown_bosses(self):
        g=self.started();initial=len(g.popups)
        g.avatar=(-105,62,0);g.clock=10;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
        self.assertEqual(len(g.popups)-initial,1)
        summary=g.popups[-1]
        self.assertIn('Darkness is taking deeper root',summary)
        self.assertNotIn('Grunbeld',summary)
        self.assertNotIn('Count',summary)
        self.assertNotIn('Black Dogs',summary)
        g.run('EOC_BERSERK_CAMPAIGN_POST_FIRE')
        self.assertEqual(len(g.popups)-initial,1)

    def test_escape_summary_uses_known_unfinished_target(self):
        g=self.started(berserk_hunt_grunbeld_state=1)
        g.run('EOC_BERSERK_FLORA_ESCAPED')
        self.assertIn("road to Grunbeld's stronghold remains",g.popups[-1])
        self.assertNotIn("Count's unfinished",g.popups[-1])

    def test_known_route_reuse_and_gift_do_not_announce_campaign(self):
        g=ready();g.flags['u_berserk_first_hunt_done']=1
        g.run('EOC_BERSERK_FLORA_SEEK');g.run('EOC_BERSERK_FLORA_SEEK')
        self.assertFalse(g.popups)
        self.assertEqual(len(g.messages),1)  # one legitimate mission assignment
        self.assertIn('A new objective',g.messages[0])
        messages=list(g.messages)
        g.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
        self.assertFalse(g.popups);self.assertEqual(g.messages,messages)


if __name__=='__main__':unittest.main()
