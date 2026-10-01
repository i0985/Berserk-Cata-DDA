"""Mission/location regressions on the JSON EOC graph, without CDDA.

Stored coordinates, progress, retries and generated target definitions only;
this cannot validate native mission UI, overmap generation or save loading.
"""
import copy
import gettext
import json
import unittest
from test_named_apostle_hunts import NamedHuntGraph
from test_apostle_hunts import HuntGraph
from test_behelit_rewards import MOD, objects

class HuntMissionTests(unittest.TestCase):
    def fixture(self):
        flags={'berserk_eclipse_era':1,'u_berserk_eclipse_rescue_state':2,
               'u_berserk_breach_marked':1,'u_berserk_local_breach_location':(240,120,0),
               'berserk_flora_stage':1,'berserk_flora_location':(-480,0,0)}
        for i,k in enumerate(('count','wyald','rosine','grunbeld')):
            flags['berserk_hunt_'+k+'_state']=1;flags['berserk_hunt_'+k+'_location']=(720+i*240,480,0)
        flags['berserk_hunt_grunbeld_site_registered']=1
        return NamedHuntGraph(flags)
    def test_six_registered_sites_assign_exact_existing_target_once(self):
        g=self.fixture();g.run('EOC_BERSERK_MISSIONS_SYNC')
        self.assertEqual(len(g.active_missions),6);self.assertFalse(g.locator_calls)
        definitions=objects(MOD/'missions/named_hunts.json')
        for d in definitions:
            params=d['start']['assign_mission_target'];self.assertEqual(g.active_missions[d['id']],g.resolve(params['var']))
            self.assertNotIn('om_special',params);self.assertNotIn('om_terrain_replace',params)
        before=copy.deepcopy(g.active_missions)
        for _ in range(3):g.run('EOC_BERSERK_MISSIONS_SYNC')
        self.assertEqual(g.active_missions,before);self.assertFalse(g.completed_missions)
    def test_completion_is_independent_and_cannot_reissue_completed_hunt(self):
        g=self.fixture();g.run('EOC_BERSERK_MISSIONS_SYNC');g.flags['berserk_hunt_count_state']=5
        g.run('EOC_BERSERK_MISSIONS_SYNC')
        self.assertNotIn('MISSION_BERSERK_COUNT',g.active_missions);self.assertEqual(len(g.active_missions),5)
        self.assertEqual(g.completed_missions,['MISSION_BERSERK_COUNT'])
        g.run('EOC_BERSERK_MISSIONS_SYNC');self.assertEqual(g.completed_missions,['MISSION_BERSERK_COUNT'])
        self.assertEqual(g.flags['berserk_hunt_wyald_state'],1)
    def test_old_completed_sites_do_not_give_new_jobs_and_serialized_state_recovers(self):
        g=self.fixture();g.flags['berserk_hunt_count_state']=5;g.flags['u_berserk_breach_sealed']=1
        g.run('EOC_BERSERK_MISSIONS_SYNC')
        self.assertEqual(len(g.active_missions),4)
        fresh=NamedHuntGraph(json.loads(json.dumps(g.flags)));fresh.run('EOC_BERSERK_MISSIONS_SYNC')
        self.assertEqual(set(fresh.active_missions),set(g.active_missions))
        self.assertNotIn('MISSION_BERSERK_COUNT',fresh.active_missions)
    def test_known_location_recall_does_not_search_or_move_the_site(self):
        g=self.fixture();p=g.flags['berserk_hunt_wyald_location'];g.avatar=(-2000,2000,0)
        g.run('EOC_BERSERK_WYALD_SEEK');self.assertFalse(g.locator_calls)
        self.assertEqual(g.flags['berserk_hunt_wyald_location'],p)
        self.assertEqual(g.active_missions['MISSION_BERSERK_WYALD'],p)
    def test_search_has_three_attempts_one_noncreating_recovery_and_resets_after_moving(self):
        g=NamedHuntGraph();g.can_locate=False
        for _ in range(9):g.run('EOC_BERSERK_WYALD_SEEK')
        self.assertEqual(g.locator_calls,['wyald']*4)
        self.assertNotIn('berserk_hunt_wyald_location',g.flags)
        g.avatar=(24,0,0);g.run('EOC_BERSERK_WYALD_SEEK');self.assertEqual(len(g.locator_calls),5)
        fallback=next(e for e in objects(MOD/'effects/hunt_site_placement_eocs.json') if e['id']=='EOC_BERSERK_SITE_WYALD_FAILED')['effect']['then']['target_params']
        self.assertFalse(fallback['create_if_necessary']);self.assertEqual(fallback['min_distance'],0)
    def test_spacing_rejects_unregistered_close_candidate_then_keeps_existing_unique_site(self):
        g=NamedHuntGraph();g.origins['wyald']=(24,0,0)
        for _ in range(2):g.run('EOC_BERSERK_WYALD_SEEK')
        self.assertNotIn('berserk_hunt_wyald_location',g.flags)
        g.run('EOC_BERSERK_WYALD_SEEK')
        self.assertEqual(g.flags['berserk_hunt_wyald_location'],(24,0,0))
        self.assertEqual(g.active_missions['MISSION_BERSERK_WYALD'],(24,0,0))
        before=list(g.locator_calls);g.run('EOC_BERSERK_WYALD_SEEK');self.assertEqual(g.locator_calls,before)
    def test_desired_native_rings_and_hunt_separation_are_explicit(self):
        config=[('local_breach_eocs','BREACH',6,12),('flora_eocs','FLORA',15,30),('apostle_hunt_eocs','COUNT',15,35),('wyald_rosine_hunt_eocs','WYALD',15,35),('wyald_rosine_hunt_eocs','ROSINE',15,35),('grunbeld_hunt_eocs','GRUNBELD',25,45)]
        for file,key,minimum,maximum in config:
            finder=next(e for e in objects(MOD/f'effects/{file}.json') if e['id']==f'EOC_BERSERK_{key}_FIND')
            p=finder['effect'][-1]['then'][-1]['target_params'];self.assertEqual((p['min_distance'],p['search_range']),(minimum,maximum))
        validators={e['id']:e for e in objects(MOD/'effects/hunt_site_placement_eocs.json')}
        text=json.dumps(validators['EOC_BERSERK_SITE_WYALD_VALIDATE'])
        self.assertIn('>= 8',text);self.assertIn('floor(_berserk_site_anchor.x / 24)',text)
    def test_count_last_seal_immediately_finds_stronghold_without_minute_tick(self):
        g=NamedHuntGraph({'berserk_hunt_count_state':3,'berserk_hunt_wyald_state':4,'berserk_hunt_rosine_state':4})
        g.run('EOC_BERSERK_COUNT_REGISTER_SEAL')
        self.assertEqual(g.flags['berserk_hunt_count_state'],4)
        self.assertEqual(g.flags['berserk_hunt_grunbeld_site_registered'],1)
        self.assertIn('MISSION_BERSERK_GRUNBELD',g.active_missions)

    def test_new_ui_strings_have_both_compiled_translations(self):
        texts=set()
        def walk(v):
            if isinstance(v,list):
                for x in v:walk(x)
            elif isinstance(v,dict):
                for k,x in v.items():
                    if k in ('name','description','desc','u_message','npc_message','monster_message','u_make_sound'):
                        if isinstance(x,str):texts.add(x)
                        elif isinstance(x,list):texts.update(s for s in x if isinstance(s,str))
                    walk(x)
        for f in ('missions/named_hunts.json','effects/hunt_mission_eocs.json','effects/hunt_site_placement_eocs.json','spells/apostle_committed_attacks.json','fields/apostle_committed_attacks.json','effects/apostle_attack_recovery.json'):
            walk(objects(MOD/f))
        for lang in ('ru','zh_CN'):
            with (MOD/f'lang/mo/{lang}/LC_MESSAGES/Berserk.mo').open('rb') as f:cat=gettext.GNUTranslations(f)
            self.assertFalse([s for s in texts if cat.gettext(s)==s],lang)

if __name__=='__main__':unittest.main()
