"""Known route/mission data, with native placement represented by a fixture."""
import copy
import json
import unittest
from test_apostle_hunts import HuntGraph
from test_recovery_33 import MOD


class Routes(HuntGraph):
    def __init__(self):
        super().__init__({'berserk_eclipse_era':1,'u_berserk_first_hunt_done':1,'u_berserk_road_journal_issued':1})
        self.calls=[];self.now=100
    def evaluate(self,s):
        return super().evaluate(s.replace("time('now')",str(self.now)))
    def condition(self,c):
        if c=='u_is_avatar':return True
        return super().condition(c)
    def run(self,name):
        self.calls.append(name)
        if name in ['EOC_BERSERK_NEXT_STRONGHOLD_GUIDE','EOC_BERSERK_JOURNAL_REFRESH']:return
        super().run(name)
    def locate(self,key,pos):
        terrain={'COUNT':'berserk_count_hall','WYALD':'berserk_wyald_ring','ROSINE':'berserk_rosine_nest'}[key]
        self.flags.update({'u_berserk_journal_knows_'+key.lower():1,'berserk_hunt_'+key.lower()+'_state':1,'berserk_hunt_'+key.lower()+'_location':pos})
        self.terrain_locations[pos]=terrain


class DirectMissions(unittest.TestCase):
    def test_existing_known_routes_assign_real_targets_without_a_book(self):
        f=Routes();pos=(1200,2400,0);f.locate('COUNT',pos)
        f.run('EOC_BERSERK_KNOWN_ROUTES_NOW')
        self.assertEqual(f.active_missions['MISSION_BERSERK_COUNT'],pos)
        self.assertNotIn('berserk_campaign_journal',f.inventory)
        self.assertNotIn('EOC_BERSERK_COUNT_FIND',f.calls)

    def test_closed_breach_hook_learns_then_assigns_all_three_known_directions(self):
        f=Routes()
        for i,key in enumerate(['COUNT','WYALD','ROSINE']):f.locate(key,(2400+i*240,1200,0))
        commit=f.eocs['EOC_BERSERK_BREACH_CLOSE_COMMIT']['effect']
        start=next(i for i,x in enumerate(commit) if x.get('run_eocs')=='EOC_BERSERK_JOURNAL_LEARN_NAMED')
        f.effect(commit[start:])
        self.assertEqual(set(f.active_missions),{'MISSION_BERSERK_COUNT','MISSION_BERSERK_WYALD','MISSION_BERSERK_ROSINE'})

    def test_unknown_future_routes_are_not_queried(self):
        f=Routes();f.run('EOC_BERSERK_KNOWN_ROUTES_NOW')
        self.assertFalse(f.active_missions)
        self.assertFalse(any('LOCATE' in s or s.endswith('_FIND') for s in f.calls))

    def test_reload_keeps_target_and_never_awards_second_mission(self):
        f=Routes();f.locate('COUNT',(1800,2400,0));f.run('EOC_BERSERK_KNOWN_ROUTES_NOW')
        f=copy.deepcopy(f);before=copy.deepcopy(f.active_missions);f.calls=[]
        f.run('EOC_BERSERK_KNOWN_ROUTES_NOW')
        self.assertEqual(f.active_missions,before);self.assertNotIn('EOC_BERSERK_JOURNAL_LOCATE_COUNT',f.calls)

    def test_hourly_retry_is_not_a_per_second_locator(self):
        f=Routes();f.run('EOC_BERSERK_KNOWN_ROUTES_RETRY');self.assertEqual(f.flags['u_berserk_known_routes_retry_at'],3700)
        f.calls=[];f.now=3699;f.run('EOC_BERSERK_KNOWN_ROUTES_RETRY')
        self.assertNotIn('EOC_BERSERK_KNOWN_ROUTES_NOW',f.calls)
        f.now=3700;f.run('EOC_BERSERK_KNOWN_ROUTES_RETRY');self.assertEqual(f.flags['u_berserk_known_routes_retry_at'],7300)

    def test_source_reading_and_alternative_return_have_no_book_menu_gate(self):
        f=Routes();clue=f.eocs['EOC_BERSERK_BREACH_READ_CLUE']
        self.assertNotIn('open_dialogue',json.dumps(clue))
        self.assertIn('EOC_BERSERK_JOURNAL_BREACH_LOCATE',json.dumps(clue))
        self.assertEqual(f.eocs['EOC_BERSERK_APOSTOL_CONTINUATION_BEGIN']['effect'][-1]['run_eocs'],'EOC_BERSERK_KNOWN_ROUTES_NOW')

    def test_first_hunt_stays_automatic_and_nothing_erases_known_coordinates(self):
        f=Routes();self.assertIn({'run_eocs':'EOC_BERSERK_FIRST_HUNT_REQUEST'},f.eocs['EOC_BERSERK_ECLIPSE_AFTERMATH']['effect'])
        p=MOD/'effects/direct_hunt_missions_33_eocs.json'
        data=p.read_text();self.assertNotIn('u_has_item',data);self.assertNotIn('open_dialogue',data)
        self.assertNotIn('u_spawn_item',data);self.assertNotIn('location_variable_adjust',data)


if __name__=='__main__':unittest.main()
