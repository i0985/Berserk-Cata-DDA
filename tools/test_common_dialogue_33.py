"""Real JSON transitions for concealment and common prose.

The native LIE roll's result is supplied by a fixture, not reimplemented.
Placement, physical visibility and NPC identities are explicit environment
fixtures. Native probability, animation, fire and AI still need a playtest.
"""
import copy
import json
import re
import unittest
from test_named_apostle_dialogues_33 import Contract, monster, npc, MUTATIONS
from test_reference_journal_33 import MOD, EOCS, TOPICS, walk

P='EOC_BERSERK_COMMON33_';T='TALK_BERSERK_COMMON33_'

class Common(Contract):
    def __init__(self,k='GODO'):
        super().__init__();self.person=k;self.om='berserk_godo_workshop';self.external=[]
        if k=='RICKERT':self.beta=npc();self.beta['class']='NC_BERSERK_RICKERT'
        else:self.beta=monster({'GODO':'mon_berserk_godo','FLORA':'mon_berserk_flora','KNIGHT':'mon_skull_knight_rescuer'}[k])
        self.monsters=[self.beta] if self.beta['kind']=='monster' else []
        self.values.update(berserk_eclipse_era=1,berserk_flora_stage=1,u_berserk_eclipse_rescue_state=2)
        for stem in ['count','wyald','rosine']:self.values['berserk_hunt_'+stem+'_state']=4
        self.overrides['EOC_BERSERK_FLORA_AT_REGISTERED_MANOR']=True
        if k=='FLORA':self.om='berserk_flora_manor'
    def value(self,s):
        s=re.sub(r"n_monsters_nearby\('([^']+)'[^)]*\)",lambda m:str(int(bool(self.beta and self.beta.get('id')==m[1]))),s)
        s=s.replace('n_npc_trust()',str(self.values.get('trust',0)))
        return super().value(s)
    def condition(self,c):
        if c=='npc_is_npc':return self.beta is not None and self.beta['kind']=='npc'
        if isinstance(c,dict) and 'npc_has_class' in c:return self.beta is not None and self.beta.get('class')==c['npc_has_class']
        return super().condition(c)
    def run(self,id_):
        if id_ in ['EOC_BERSERK_REF_SYNC','EOC_BERSERK_GODO_ORDER_SYNC','EOC_BERSERK_FLORA_REGISTER_HERE',
                   'EOC_BERSERK_FLORA_SYNC_MANOR_CENTER','EOC_BERSERK_FLORA33_QUEUE']:
            self.external.append(id_);return
        return super().run(id_)
    def effect(self,x):
        if isinstance(x,dict) and 'npc_first_topic' in x:
            self.beta['first_topic']=x['npc_first_topic'];return
        if isinstance(x,dict) and 'u_spawn_item' in x and isinstance(x.get('count'),dict):
            self.inventory[x['u_spawn_item']]+=self.getvar(x['count']);return
        if x in ['leave','assign_guard']:
            if x=='leave':self.beta['following']=False;self.beta['friend']=False
            else:self.beta['guard']=True
            return
        return super().effect(x)
    def demon(self,line='SLAN',path=1,visible=False):
        self.values.update(u_berserk_apostol_path=path,u_berserk_apostol_lineage=2,u_berserk_apostol_stage=1)
        self.traits.add('BERSERK_'+line+'_SEED')
        if visible:self.traits.add('BERSERK_'+line+'_FORM')
    def allowed(self):return self.condition({'test_eoc':P+self.person+'_ALLOWED'})
    def lie(self,success=True):
        rows=self.available(T+self.person+'_SUSPICION');row=next(r for r in rows if 'trial' in r)
        outcome=row['success' if success else 'failure'];self.effect(outcome['effect']);return outcome['topic']

class CommonDialogue(unittest.TestCase):
    def test_human_and_refusal_scars_do_not_raise_suspicion(self):
        for k in ['GODO','RICKERT','FLORA']:
            f=Common(k);f.traits.update(['BERSERK_ECLIPSE_SCAR_HEARING','BERSERK_ECLIPSE_SCAR_DREAD'])
            f.values.update(u_berserk_apostol_outcome=2,u_berserk_apostol_return_state=2)
            self.assertTrue(f.allowed());self.assertFalse(f.condition({'test_eoc':P+k+'_PENDING'}))
    def test_behelit_possession_and_showing_it_do_not_accept_a_path(self):
        for k in ['GODO','RICKERT','FLORA','KNIGHT']:
            f=Common(k);f.inventory['berserk_behelit_distorted']=1
            f.enter(T+k+'_STONE');f.enter(T+k+'_STONE_MORE')
            self.assertTrue(f.allowed());self.assertEqual(f.values.get('u_berserk_apostol_path',0),0)
    def test_each_hidden_trial_is_native_lie_with_two_real_branches(self):
        for k in ['GODO','RICKERT','FLORA']:
            f=Common(k);f.demon();self.assertFalse(f.allowed())
            r=next(r for r in f.available(T+k+'_SUSPICION') if 'trial' in r)
            self.assertEqual(r['trial']['type'],'LIE')
            self.assertEqual(set(r['trial']),{'type','difficulty'})
            self.assertIn('success',r);self.assertIn('failure',r)
            f.lie(True);self.assertTrue(f.allowed())
            self.assertFalse(f.condition({'test_eoc':'EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED'}))
    def test_failed_lie_reveals_permanently_without_free_retries(self):
        for k in ['GODO','RICKERT','FLORA']:
            f=Common(k);f.demon();f.lie(False)
            self.assertFalse(f.allowed());self.assertTrue(f.condition({'test_eoc':P+k+'_KNOWS'}))
            self.assertFalse(any('trial' in r for r in f.available(T+k+'_SUSPICION')))
            self.assertEqual(f.values['u_berserk_apostol_path'],1)
    def test_admission_closes_a_previously_successful_concealment(self):
        for k in ['GODO','RICKERT','FLORA']:
            f=Common(k);f.demon();f.lie(True);f.run(P+k+'_TELL')
            self.assertFalse(f.allowed())
    def test_godo_flora_and_rickert_results_do_not_leak_between_people(self):
        f=Common();f.demon();f.lie(True)
        self.assertTrue(f.allowed())
        self.assertFalse(f.condition({'test_eoc':P+'FLORA_ALLOWED'}))
        self.assertFalse(f.condition({'test_eoc':P+'RICKERT_ALLOWED'}))
    def test_visible_body_overrides_a_saved_success_for_all_thirteen_forms(self):
        bodies=[id_ for id_ in MUTATIONS if id_.endswith('_FORM') and id_.startswith('BERSERK_')]
        self.assertEqual(len(bodies),13)
        for trait in bodies:
            f=Common();f.demon();f.lie(True);f.traits.add(trait)
            self.assertFalse(f.allowed(),trait)
            self.assertFalse(any('trial' in r for r in f.available(T+'GODO_SUSPICION')),trait)
    def test_visible_change_stays_known_after_actor_observes_it(self):
        f=Common();f.demon(visible=True);f.run(P+'GODO_NOTICE')
        f.traits.discard('BERSERK_SLAN_FORM')
        self.assertFalse(f.allowed());self.assertTrue(f.condition({'test_eoc':P+'GODO_KNOWS'}))
    def test_concealment_survives_reload_without_clearing_the_demonic_path(self):
        f=Common();f.demon();f.lie(True)
        other=Common();other.values=copy.deepcopy(f.values);other.traits=set(f.traits);other.self_ref['traits']=other.traits
        self.assertTrue(other.allowed());self.assertEqual(other.values['u_berserk_apostol_path'],1)
    def test_old_confirmed_conversations_are_not_forgotten_for_a_new_lie(self):
        for k,proof in [('GODO','u_berserk_godo_demon_refused'),('RICKERT','u_berserk_apostol_rickert_counsel'),('FLORA','u_berserk_flora33_demon_noticed')]:
            f=Common(k);f.demon();f.values[proof]=1
            self.assertFalse(f.condition({'test_eoc':P+k+'_PENDING'}));self.assertFalse(f.allowed())
    def test_unseen_scene_does_not_announce_a_spawn_or_a_combat_line(self):
        f=Common();f.can_see=False;f.values.update(berserk_flora_siege_state=2)
        f.values['_common33_actor_pos']=(1,1,0);f.values['_common33_combat_pos']=(1,1,0)
        f.run(P+'ZODD_OBSERVED');f.run(P+'ZODD_COMBAT')
        self.assertFalse(f.messages)
    def test_visible_scene_and_hit_are_each_reported_once(self):
        f=Common();f.can_see=True;f.values.update(berserk_flora_siege_state=2)
        f.values['_common33_actor_pos']=(1,1,0);f.values['_common33_combat_pos']=(1,1,0)
        for _ in range(2):f.run(P+'ZODD_OBSERVED');f.run(P+'ZODD_COMBAT')
        self.assertEqual(len(f.messages),2)
    def test_finished_dragonslayer_requires_a_successful_lie_and_claims_once(self):
        f=Common();f.demon();f.values.update(u_berserk_godo_sword_state=3,u_berserk_godo_sword_ready_at=0)
        f.run('EOC_BERSERK_GODO_SWORD_CLAIM');self.assertFalse(f.inventory)
        f.lie(True);f.run('EOC_BERSERK_GODO_SWORD_CLAIM');f.run('EOC_BERSERK_GODO_SWORD_CLAIM')
        self.assertEqual(f.inventory['true_guts_sword'],1)
        self.assertEqual(f.values['u_berserk_apostol_path'],1)
    def test_early_blade_can_be_collected_while_hidden(self):
        f=Common();f.demon();f.values.update(u_berserk_godo_early_state=2,u_berserk_godo_early_ready_at=0)
        f.lie(True);f.run('EOC_BERSERK_GODO_EARLY_CLAIM')
        self.assertEqual(f.inventory['true_guts_early_sword'],1)
    def test_failure_refunds_the_actual_materials_once(self):
        f=Common();f.demon();f.values.update(u_berserk_godo_sword_state=3,u_berserk_godo_sword_iron_given=32)
        f.lie(False);f.run('EOC_BERSERK_GODO_SWORD_REFUND');f.run('EOC_BERSERK_GODO_SWORD_REFUND')
        self.assertEqual(f.inventory['steel_lump'],32);self.assertEqual(f.inventory['hc_steel_lump'],8)
        self.assertEqual(f.inventory['true_guts_sword'],0)
    def test_flora_can_really_grant_missing_armor_after_success(self):
        f=Common('FLORA');f.demon();f.inventory['berserk_helmet']=1
        f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertEqual(len(f.inventory),1)
        f.lie(True);f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');f.run('EOC_BERSERK_FLORA_GIVE_ARMOR')
        self.assertEqual(f.inventory['berserk_helmet'],1)
        for item in ['berserk_chestplate','berserk_gloves','berserk_armguards','berserk_legguards','berserk_boots']:self.assertEqual(f.inventory[item],1)
    def test_form_growing_after_receipt_never_confiscates_rewards(self):
        f=Common();f.demon();f.lie(True);f.inventory.update(true_guts_sword=1,berserk_chestplate=1)
        f.traits.add('BERSERK_SLAN_FORM');before=f.inventory.copy();f.run(P+'GODO_NOTICE')
        self.assertEqual(f.inventory,before);self.assertFalse(f.allowed())
    def test_rickert_lie_does_not_create_a_missing_hand(self):
        f=Common('RICKERT');f.demon();f.lie(True);f.values.update(u_berserk_godo_arm_state=3,u_berserk_godo_arm_ready_at=0)
        f.run('EOC_BERSERK_GODO_ARM_CLAIM');self.assertEqual(f.inventory['bio_berserk_arm_cannon'],0)
    def test_rickert_command_rejects_service_and_stops_following(self):
        f=Common('RICKERT');f.demon(path=3);f.beta['following']=True
        f.enter(T+'RICKERT_PACT_COMMAND')
        self.assertFalse(f.beta['following']);self.assertEqual(f.values['n_berserk_rickert_recruit_refused'],1)
    def test_guts_remembers_and_ordinary_avatar_does_not_inherit_his_life(self):
        for stem in ['JUDEAU','PIPPIN','CORKUS','GASTON']:
            f=Common();f.guts=False;f.run('EOC_BERSERK_ECLIPSE_SCENE_'+stem)
            text=f.messages[-1]['u_message']
            self.assertNotIn('Вы помните',text);self.assertNotIn('Вы вспоминаете',text)
            count=len(f.messages);f.run('EOC_BERSERK_ECLIPSE_SCENE_'+stem)
            self.assertEqual(len(f.messages),count+1);self.assertFalse(f.messages[-1].get('popup'))
            self.assertFalse(f.inventory)
    def test_old_read_body_does_not_replay_full_emotional_scene(self):
        f=Common();f.values['u_berserk_godo_witness_judeau']=1
        f.run('EOC_BERSERK_ECLIPSE_SCENE_JUDEAU');self.assertFalse(f.messages[-1].get('popup'))
    def test_rickert_discusses_found_keepsake_without_demanding_it_as_payment(self):
        f=Common('RICKERT');f.values['u_berserk_godo_witness_gaston']=1
        before=f.inventory.copy();f.enter(T+'RICKERT_FIND_GASTON')
        self.assertEqual(before,f.inventory);self.assertEqual(f.values['u_berserk_rickert_knows_death_gaston'],1)
    def test_important_reaction_is_short_on_repetition(self):
        f=Common();f.demon();first=f.enter(T+'GODO_EARLY');again=f.enter(T+'GODO_EARLY')
        self.assertNotEqual(first,again);self.assertIn('помню',again)
    def test_new_topics_including_both_trial_outcomes_have_valid_destinations(self):
        for id_,obj in TOPICS.items():
            if not id_.startswith(T):continue
            for r in obj['responses']:
                for x in [r,r.get('success',{}),r.get('failure',{})]:
                    if 'topic' in x:self.assertTrue(x['topic'] in TOPICS or x['topic'] in ['TALK_DONE','TALK_NONE'],(id_,x))
            for n in walk(obj):
                if 'test_eoc' in n:self.assertIn(n['test_eoc'],EOCS)
    def test_original_short_manifestation_and_existing_story_wounds_remain_separate(self):
        obj=EOCS['EOC_BERSERK_ECLIPSE_GRASP_BEGIN']
        msgs=[n['u_message'] for n in walk(obj) if 'u_message' in n]
        self.assertTrue(all('Alien limbs' in m for m in msgs))
        self.assertNotIn('human with a Behelit',json.dumps(obj,ensure_ascii=False))
        self.assertIn('EOC_BERSERK_ECLIPSE_APPLY_STORY_WOUNDS',json.dumps(EOCS['EOC_BERSERK_ECLIPSE_GRASP_RESOLVE']))
    def test_projections_keep_reward_callbacks_and_have_no_contract_topics(self):
        data=json.loads((MOD/'monsters/apostle_projections.json').read_text());self.assertEqual(len(data),10)
        for mon in data:
            self.assertNotIn('chat_topics',mon)
            self.assertEqual(mon['death_function']['eoc'],'EOC_BERSERK_GRIFFITH_PROJECTION_DIES' if mon['id'].endswith('griffith') else 'EOC_BERSERK_BEHELIT_BOSS_DIES')
    def test_no_unimplemented_ritual_evacuations_or_knight_resurrection(self):
        text=json.dumps([o for id_,o in EOCS.items() if id_.startswith(P)])
        self.assertNotIn('u_spawn_monster',text);self.assertNotIn('u_add_bionic',text)

if __name__=='__main__':unittest.main()
