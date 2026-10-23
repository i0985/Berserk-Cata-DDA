"""Run the captive JSON in a data model. Native NPC AI is an environment fixture."""
import copy
import json
import re
import unittest

from test_reference_journal_33 import Book, EOCS, TOPICS, MOD, walk

E='EOC_BERSERK_COUNT33_';P='TALK_BERSERK_COUNT_'
CLASS='NC_BERSERK_COUNT_PRISONER';UID='BERSERK_COUNT_PRISONER'
CLOSED='t_berserk_count_cell_gate_c';OPEN='t_berserk_count_cell_gate_o'


class Captive(Book):
    def __init__(self):
        super().__init__();self.npc_exists=True;self.following=False;self.fleeing=False
        self.legacy=None;self.spawn_success=True;self.spawns=[];self.confirm=True;self.turns=[]
        self.pos=(9,11,0);self.beta_pos=(7,11,0);self.om='berserk_count_prison'
        self.terrain[(8,11,0)]=CLOSED
        self.furniture[(27,16,0)]='f_berserk_count_service_grate'
    def value(self,s):
        if self.actor=='npc':s=re.sub(r'\bu_berserk_count33_', 'n_berserk_count33_',s)
        s=re.sub(r"u_monsters_nearby\([^)]*\)",str(int(self.legacy is not None)),s)
        s=re.sub(r'_count33_actor_pos\.([xyz])',lambda m:repr(self.values.get('_count33_actor_pos',(0,0,0))['xyz'.index(m[1])]),s)
        return super().value(s)
    def condition(self,c):
        if isinstance(c,str):
            if c=='npc_is_npc':return self.npc_exists
            if c=='u_is_npc':return self.actor=='npc'
            if c=='npc_following':return self.following
        if isinstance(c,dict):
            if 'npc_has_class' in c:return self.npc_exists and c['npc_has_class']==CLASS
            if 'u_has_class' in c:return self.actor=='npc' and c['u_has_class']==CLASS
            if 'npc_at_om_location' in c or ('u_at_om_location' in c and self.actor=='npc'):
                x,y,z=self.beta_pos
                return 0<=x<24 and 0<=y<24 and z==0
            if 'u_query' in c:return self.confirm
        return super().condition(c)
    def effect(self,x):
        if isinstance(x,str):
            if x=='follow':self.following=True;self.fleeing=False;return
            if x=='flee':self.fleeing=True;self.following=False;return
            raise AssertionError(x)
        if isinstance(x,dict):
            if 'math' in x and self.actor=='npc':
                x=copy.deepcopy(x);x['math']=[re.sub(r'\bu_berserk_count33_', 'n_berserk_count33_',s) for s in x['math']]
            if 'u_location_variable' in x and self.actor in ['npc','monster']:
                old=self.pos;self.pos=self.beta_pos if self.actor=='npc' else self.legacy
                super().effect(x);self.pos=old;return
            if 'u_run_npc_eocs' in x:
                if self.npc_exists:
                    old=self.actor;self.actor='npc'
                    for id_ in x['u_run_npc_eocs']:self.run(id_)
                    self.actor=old
                return
            if 'u_run_monster_eocs' in x:
                if self.legacy is not None:
                    old=self.actor;self.actor='monster'
                    for id_ in x['u_run_monster_eocs']:self.run(id_)
                    self.actor=old
                return
            if 'u_spawn_npc' in x:
                if self.spawn_success:
                    self.npc_exists=True;self.spawns.append((x['u_spawn_npc'],x['unique_id']))
                    at=self.getvar(x['target_var']);self.beta_pos=(at[0]+1,at[1],at[2])
                    for id_ in x.get('true_eocs',[]):self.run(id_)
                return
            if 'u_die' in x:
                assert x['u_die']=={'remove_from_creature_tracker':True};self.legacy=None;return
            if 'location_variable_adjust' in x:
                k,v=next(iter(x['location_variable_adjust'].items()));key={'global_val':'','context_val':'_','u_val':'u_'}[k]+v
                old=self.values[key];self.values[key]=tuple(old[i]+x.get(axis+'_adjust',0) for i,axis in enumerate('xyz'));return
            if 'u_transform_radius' in x:
                at=self.getvar(x['target_var'])
                if self.terrain.get(at)==CLOSED:self.terrain[at]=OPEN
                return
            if 'turn_cost' in x:self.turns.append(x['turn_cost']);return
        return super().effect(x)
    def pick(self,from_,to):
        rs=[r for r in self.available(P+from_) if r['topic']==(to if to.startswith('TALK_') else P+to)]
        assert len(rs)==1,(from_,to,rs)
        r=rs[0]
        if 'effect' in r:self.effect(r['effect'])
        if r['topic'] in TOPICS:self.enter(r['topic'])
    def targets(self,s):return [r['topic'] for r in self.available(P+s)]
    def meet(self):self.enter(P+'WITNESS');self.pick('WITNESS','QUESTIONS')
    def npc_scan(self):
        old=self.actor;self.actor='npc';self.run(E+'NPC_SCAN');self.actor=old


class CountPrisoner(unittest.TestCase):
    def test_native_map_places_one_prisoner_inside_cell(self):
        data=json.loads((MOD/'mapgen/apostle_count.json').read_text())
        prison=next(x['object'] for x in data if x.get('om_terrain')==['berserk_count_prison'])
        self.assertEqual(prison['place_npcs'],[{'class':'berserk_count_prisoner','x':7,'y':11,'unique_id':UID}])
        self.assertFalse(any(x['monster']=='mon_berserk_count_witness' for x in prison['place_monster']))
        self.assertEqual(prison['rows'][11][8],'!')
        palette=json.loads((MOD/'mapgen/apostle_count_palettes.json').read_text())[0]
        self.assertEqual(palette['terrain']['!'],CLOSED)

    def test_barred_gate_keeps_native_lockpick_and_unlocked_close_states(self):
        doors={x['id']:x for x in json.loads((MOD/'furniture/count_cell_gate.json').read_text())}
        self.assertEqual(doors[CLOSED]['copy-from'],'t_door_bar_locked')
        self.assertEqual(doors[CLOSED]['lockpick_result'],OPEN)
        shut=doors[OPEN]['close'];self.assertEqual(doors[shut]['copy-from'],'t_door_bar_c')
        self.assertEqual(doors[shut]['open'],OPEN)

    def test_key_can_open_cell_without_being_consumed_and_cancel_is_harmless(self):
        f=Captive();f.values['_pos']=(8,11,0);f.inventory['berserk_count_service_key']=1
        f.confirm=False;f.run(E+'OPEN_CELL');self.assertEqual(f.terrain[(8,11,0)],CLOSED)
        self.assertNotIn('u_berserk_count33_opened_cell',f.values)
        f.confirm=True;f.run(E+'OPEN_CELL');self.assertEqual(f.terrain[(8,11,0)],OPEN)
        self.assertEqual(f.inventory['berserk_count_service_key'],1)
        f.run(E+'OPEN_CELL');self.assertEqual(f.turns,['2 seconds'])

    def test_missing_key_does_not_open_cell_or_grant_a_key_from_dialogue(self):
        f=Captive();f.values['_pos']=(8,11,0);f.run(E+'OPEN_CELL')
        self.assertEqual(f.terrain[(8,11,0)],CLOSED);f.meet();f.enter(P+'KEY_PLACE')
        self.assertFalse(f.inventory);self.assertIn('сундуке',f.line(P+'KEY_PLACE'))

    def test_locked_cell_blocks_follow_but_open_or_cut_gate_allows_it(self):
        f=Captive();f.meet();self.assertNotIn(P+'FOLLOW_READY',f.targets('ESCAPE'))
        for tile in [OPEN,'t_mdoor_frame','t_floor','t_berserk_count_cell_gate_shut']:
            f.terrain[(8,11,0)]=tile
            self.assertIn(P+'FOLLOW_READY',f.targets('ESCAPE'))

    def test_native_follow_and_flee_do_not_forge_a_successful_escape(self):
        f=Captive();f.meet();f.terrain[(8,11,0)]=OPEN
        f.pick('ESCAPE','FOLLOW_READY');f.pick('FOLLOW_READY','TALK_DONE')
        self.assertTrue(f.following);self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)
        f.pick('ESCAPE','OWN_CHOICE');f.pick('OWN_CHOICE','TALK_DONE')
        self.assertTrue(f.fleeing);self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)

    def test_escape_is_observed_only_after_the_actual_npc_leaves_the_perimeter(self):
        f=Captive();f.meet();f.npc_scan()
        self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)
        f.beta_pos=(24,44,0);f.npc_scan();self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)
        f.beta_pos=(24,46,0);f.npc_scan()
        self.assertEqual(f.values['u_berserk_ref_prisoner_freed'],1)
        self.assertEqual(f.values['n_berserk_count33_escaped'],1)
        saved=copy.deepcopy(f);before=len(saved.messages);saved.npc_scan()
        self.assertEqual(len(saved.messages),before)

    def test_unseen_escape_can_be_learned_by_later_conversation(self):
        f=Captive();f.meet();f.can_see=False;f.beta_pos=(24,46,0);f.npc_scan()
        self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)
        f.pos=(23,46,0);f.enter(P+'WITNESS')
        self.assertEqual(f.values['u_berserk_ref_prisoner_freed'],1)

    def test_other_floor_does_not_count_as_exit_through_the_gates(self):
        f=Captive();f.meet();f.beta_pos=(24,46,-1);f.npc_scan()
        self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)

    def test_count_death_is_told_once_without_unlocking_or_rescuing_prisoner(self):
        f=Captive();f.meet();self.assertNotIn(P+'DEATH_REPORT',f.targets('WITNESS'))
        f.values['berserk_hunt_count_state']=3
        f.pick('WITNESS','DEATH_REPORT');f.pick('DEATH_REPORT','AFTER')
        self.assertEqual(f.values['n_berserk_count33_knows_death'],1)
        self.assertNotIn(P+'DEATH_REPORT',f.targets('WITNESS'))
        self.assertEqual(f.terrain[(8,11,0)],CLOSED)
        self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_freed'),1)

    def test_pact_and_boss_absence_do_not_mean_the_count_is_dead(self):
        f=Captive();f.meet();f.values['u_berserk_pact_resolved_count']=1
        self.assertNotIn(P+'DEATH_REPORT',f.targets('WITNESS'))

    def test_first_visible_form_and_later_change_are_distinct_and_not_hostile(self):
        visible=EOCS[E+'VISIBLE_BODY']['condition']['or'][0]['u_has_trait']
        f=Captive();f.traits.add(visible);f.enter(P+'WITNESS')
        self.assertIn(P+'DEMON_PEACE',f.targets('WITNESS'))
        f.pick('WITNESS','DEMON_PEACE');self.assertIn(P+'WHO',f.targets('WITNESS'))
        f=Captive();f.meet();f.traits.add(visible)
        self.assertIn(P+'CHANGE_STORY',f.targets('WITNESS'))
        self.assertNotIn(P+'CHANGE_REMEMBER',f.targets('WITNESS'))
        f.pick('WITNESS','CHANGE_STRONG');self.assertIn(P+'WHO',f.targets('WITNESS'))

    def test_bypass_claim_requires_real_passage_and_information_does_not_open_it(self):
        f=Captive();f.meet();f.enter(P+'ROUTE')
        self.assertEqual(f.furniture[(27,16,0)],'f_berserk_count_service_grate')
        self.assertNotIn(P+'ROUTE_OPEN',f.targets('ROUTE'))
        f.furniture[(27,16,0)]='f_berserk_count_service_grate_open';f.pos=(27,16,0)
        f.run(E+'BYPASS_OBSERVE');self.assertIn(P+'ROUTE_OPEN',f.targets('ROUTE'))

    def test_old_actor_conversion_keeps_actor_on_failure_and_never_duplicates_existing_npc(self):
        f=Captive();f.npc_exists=False;f.legacy=(7,18,0);f.spawn_success=False
        f.run(E+'MIGRATE');self.assertIsNotNone(f.legacy);self.assertFalse(f.npc_exists)
        f.spawn_success=True;f.run(E+'MIGRATE');self.assertIsNone(f.legacy);self.assertTrue(f.npc_exists)
        self.assertEqual(len(f.spawns),1);self.assertNotEqual(f.values.get('berserk_count_prisoner_dead'),1)
        saved=copy.deepcopy(f);saved.legacy=(7,18,0);saved.run(E+'MIGRATE')
        self.assertIsNone(saved.legacy);self.assertEqual(len(saved.spawns),1)

    def test_npc_death_prevents_recreation_even_without_a_witness(self):
        f=Captive();f.can_see=False;f.actor='npc';f.run(E+'NPC_DEATH');f.actor='avatar'
        self.assertEqual(f.values['berserk_count_prisoner_dead'],1)
        self.assertNotEqual(f.values.get('u_berserk_ref_prisoner_dead'),1)
        f.npc_exists=False;f.legacy=(7,18,0);f.run(E+'MIGRATE');self.assertFalse(f.spawns)

    def test_topics_have_no_placeholders_or_stage_labels_and_keep_public_ids(self):
        for id_ in ['WITNESS','ROUTE','SERVANTS','AFTER','FAMILY']:self.assertIn(P+id_,TOPICS)
        for id_,obj in TOPICS.items():
            if not id_.startswith(P):continue
            text=json.dumps(obj,ensure_ascii=False)
            self.assertNotRegex(text,'Пленник:|Игрок:|\\[действ|\\[помещение|Вариант А|\\[→|в руке героя')
            for r in obj['responses']:self.assertIn(r['topic'],set(TOPICS)|{'TALK_DONE','TALK_FRIEND'})


if __name__=='__main__':unittest.main()
