"""Execute published ceremony choices, scar draws and combat outcomes.

Teleport collision/forge placement are environmental fixtures. These tests do
not claim to simulate native monster AI, field visibility, or actual combat.
"""
import copy
import json
import random
import re
import unittest
from test_named_apostle_dialogues_33 import Contract, monster, MONSTERS, MUTATIONS
from test_reference_journal_33 import EOCS, TOPICS, MOD, walk

P='EOC_BERSERK_HAND33_';OLD='EOC_BERSERK_APOSTOL_';T='TALK_BERSERK_APOSTOL_'
KINDS=['VOID','SLAN','UBIK','CONRAD','FEMTO']

class Ceremony(Contract):
    def __init__(self,seed=0):
        super().__init__();self.om='berserk_eclipse_apostol_ceremony'
        self.monsters=[monster('mon_berserk_godhand_'+k.lower()) for k in KINDS]
        self.beta=self.monsters[0];self.rng=random.Random(seed);self.external=[]
        self.values.update(u_berserk_eclipse_route=2,u_berserk_eclipse_trial_active=1,
            u_berserk_apostol_origin=(10,10,0),u_berserk_apostol_origin_z=0)
        for n in range(1,9):self.values['u_berserk_apostol_fallback_'+str(n)]=(10+n,10,0)
        self.teleport_succeeds=True
        self.overrides[OLD+'LANDING_SAFE']=True
    def value(self,s):
        s=re.sub(r"n_monsters_nearby\('([^']+)'[^)]*\)",
            lambda m:str(int(bool(self.beta and self.beta.get('id')==m[1]))),s)
        s=re.sub(r'rand\(([^()]+)\)',lambda m:str(self.rng.randint(0,int(super(Ceremony,self).value(m[1])))),s)
        return super().value(s)
    def effect(self,x):
        if isinstance(x,dict):
            if 'switch' in x:
                n=self.value(x['switch']['math'][0])
                for case in x['cases']:
                    if case['case']==n or case['case']=='default':self.effect(case['effect']);break
                return
            if 'math' in x:
                m=re.fullmatch(r'([_\w]+) ([+-])= (.*)',x['math'][0])
                if m:
                    self.values[m[1]]=self.values.get(m[1],0)+(1 if m[2]=='+' else -1)*self.value(m[3]);return
            if 'u_teleport' in x:
                if self.teleport_succeeds:
                    self.pos=self.getvar(x['u_teleport']);self.om='field'
                return
        return super().effect(x)
    def run(self,id_):
        # External subsystems have independent suites; the new dispatch is real.
        if id_ in ['EOC_BERSERK_REF_SYNC','EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL',OLD+'GIFT_BEGIN',
                   OLD+'CONTINUATION_BEGIN','EOC_BERSERK_ECLIPSE_RESCUE_STABILIZE',
                   'EOC_BERSERK_ECLIPSE_RESCUE_RETURN']:
            self.external.append(id_);return
        return super().run(id_)
    def pick_hand(self,k,s,to):
        id_=T+k if s=='ROOT' else T+k+'_'+s
        target=to if to.startswith('TALK_') else T+k+'_'+to
        r=next(r for r in self.available(id_) if r['topic']==target)
        if 'effect' in r:self.effect(r['effect'])
        if target in TOPICS:return self.enter(target)
    def attacked(self):self.run(OLD+'HAND_RAGE')
    def kill(self,k):
        # monster::die: alpha=killer (possibly absent), beta=dying monster.
        b=self.beta
        self.beta=next(m for m in self.monsters if m['id']=='mon_berserk_godhand_'+k.lower())
        self.terrain[self.beta_pos]=self.om
        self.run(OLD+'HAND_'+k+'_DIED')
        self.beta=b
    def start(self):self.om='berserk_eclipse_apostol_arrival';self.run(P+'START_USE')

class GodHand(unittest.TestCase):
    def test_five_distinct_greetings_then_short_replies(self):
        f=Ceremony()
        for k in KINDS:
            first=f.enter(T+k);again=f.enter(T+k)
            self.assertNotEqual(first,again)
            self.assertLess(len(again),len(first))
        self.assertEqual(f.values.get('u_berserk_apostol_outcome',0),0)
    def test_all_topics_and_followups_have_valid_targets(self):
        for id_,obj in TOPICS.items():
            if not id_.startswith(T) or '_PAWN_' in id_:continue
            for r in obj['responses']:
                self.assertTrue(r['topic'] in TOPICS or r['topic'] in ['TALK_DONE','TALK_NONE'],(id_,r))
    def test_every_ceremony_page_has_an_exit_after_attack_or_outcome(self):
        f=Ceremony();f.values['u_berserk_apostol_godhand_attacked']=1
        for id_,obj in TOPICS.items():
            if id_ in json.loads((MOD.parents[1]/'docs/dialogue_sources/godhand-bindings-33.json').read_text())['topics']:
                self.assertTrue(any(r['topic']=='TALK_DONE' for r in f.available(id_)),id_)
    def test_asking_pausing_and_others_do_not_choose(self):
        f=Ceremony()
        for k in KINDS:
            for s in ['ROOT','QUESTION','FORM_CHOICE','GROWTH','END_GROWTH','SACRIFICE','PRICE','OTHERS','PAUSE','CONFIRM']:
                f.enter(T+k+('_'+s if s!='ROOT' else ''))
        self.assertEqual(f.values.get('u_berserk_apostol_outcome',0),0)
        self.assertEqual(f.values.get('u_berserk_apostol_gift_roll',0),0)
        self.assertEqual(f.traits,set())
    def test_confirmation_is_required_even_for_legacy_accept(self):
        f=Ceremony();f.run(OLD+'CHOOSE_GIFT');f.run(OLD+'CHOOSE_SLAN')
        self.assertEqual(f.values.get('u_berserk_apostol_gift_roll',0),0)
        f.pick_hand('SLAN','CONFIRM','TALK_DONE')
        self.assertEqual(f.values['u_berserk_apostol_return_state'],2)
        self.assertEqual(f.values['u_berserk_apostol_outcome'],1)
        self.assertEqual(f.values['berserk_eclipse_era'],1)
        self.assertNotIn('EOC_BERSERK_ECLIPSE_RESCUE_RETURN',f.external)
    def test_speaker_order_does_not_change_the_five_way_roll(self):
        results=[]
        for k in KINDS:
            f=Ceremony(seed=57)
            for other in reversed(KINDS):f.enter(T+other)
            f.pick_hand(k,'CONFIRM','TALK_DONE');results.append(f.values['u_berserk_apostol_gift_roll'])
        self.assertEqual(len(set(results)),1)
        obj=EOCS[OLD+'CHOOSE_GIFT']
        self.assertIn('1 + rand(4)',json.dumps(obj))
    def test_accepted_roll_is_saved_across_retry_and_reload(self):
        f=Ceremony(seed=4);f.teleport_succeeds=False;f.overrides[OLD+'LANDING_SAFE']=False
        f.pick_hand('FEMTO','CONFIRM','TALK_DONE')
        self.assertEqual(f.values['u_berserk_apostol_return_state'],1)
        roll=f.values['u_berserk_apostol_gift_roll'];saved=copy.deepcopy(f.values)
        f.values=saved;f.teleport_succeeds=True;f.overrides[OLD+'LANDING_SAFE']=True
        f.run(OLD+'RETURN');f.run(OLD+'CHOOSE_GIFT')
        self.assertEqual(f.values['u_berserk_apostol_gift_roll'],roll)
        self.assertEqual(f.values['u_berserk_apostol_return_state'],2)
    def test_guts_cannot_open_or_accept_ceremony(self):
        f=Ceremony();f.guts=True
        self.assertFalse(f.condition({'test_eoc':OLD+'CEREMONY_OPEN'}))
        f.values['u_berserk_hand33_choice_confirmed']=1;f.run(OLD+'CHOOSE_GIFT')
        self.assertEqual(f.values.get('u_berserk_apostol_outcome',0),0)
    def test_memory_once_across_all_five(self):
        f=Ceremony();first=f.enter(T+'VOID_REFUSE')
        self.assertIn('Обрывки прежней жизни',first)
        for k in KINDS:
            again=f.enter(T+k+'_REFUSE')
            self.assertNotIn('Обрывки прежней жизни',again)
            self.assertIn('подтверждаешь',again)
        self.assertEqual(f.values.get('u_berserk_apostol_outcome',0),0)
    def test_refusal_has_two_distinct_scars_and_optional_third(self):
        counts=set()
        for seed in range(50):
            f=Ceremony(seed=seed);f.enter(T+'CONRAD_REFUSE');f.run(OLD+'CHOOSE_HUMAN')
            scars=[f.values['u_berserk_apostol_scar_'+str(i)] for i in range(1,f.values['u_berserk_apostol_scar_count']+1)]
            counts.add(len(scars));self.assertEqual(len(scars),len(set(scars)))
            self.assertTrue(all(1<=x<=5 for x in scars));self.assertTrue(2<=len(scars)<=3)
            self.assertNotIn('BLIND',f.traits);self.assertNotIn('DEAF',f.traits)
            self.assertEqual(len(f.traits),len(scars))
        self.assertEqual(counts,{2,3})
    def test_refusal_does_not_redraw_or_become_a_demonic_path(self):
        f=Ceremony();f.enter(T+'UBIK_REFUSE');f.run(OLD+'CHOOSE_HUMAN')
        saved=copy.deepcopy(f.values);traits=set(f.traits)
        f.run(OLD+'CHOOSE_HUMAN');f.run(OLD+'APPLY_REFUSAL_SCAR')
        self.assertEqual(f.values,saved);self.assertEqual(f.traits,traits)
        self.assertEqual(f.values.get('u_berserk_apostol_path',0),0)
    def test_portal_requires_attack_and_arrival_not_final_circle(self):
        f=Ceremony();f.start()
        self.assertEqual(f.values.get('u_berserk_apostol_return_state',0),0)
        f.om='berserk_eclipse_apostol_ceremony';f.attacked();f.run(P+'START_USE')
        self.assertEqual(f.values.get('u_berserk_apostol_return_state',0),0)
        f.run(OLD+'CIRCLE_USE');self.assertFalse(f.opened)
        f.start();self.assertEqual(f.values['u_berserk_apostol_outcome'],3)
    def test_escape_joins_normal_rescue_without_gift_or_refusal_scars(self):
        f=Ceremony();f.attacked();f.start()
        self.assertEqual(f.values['u_berserk_eclipse_route'],1)
        self.assertEqual(f.values['u_berserk_eclipse_rescue_state'],1)
        self.assertIn('EOC_BERSERK_ECLIPSE_RESCUE_RETURN',f.external)
        self.assertNotIn(OLD+'GIFT_BEGIN',f.external);self.assertNotIn(OLD+'CONTINUATION_BEGIN',f.external)
        self.assertEqual(f.traits,set());self.assertEqual(f.values.get('u_berserk_apostol_path',0),0)
    def test_failed_combat_escape_can_retry_at_start_only(self):
        f=Ceremony();f.attacked();f.teleport_succeeds=False;f.overrides[OLD+'LANDING_SAFE']=False;f.start()
        self.assertEqual(f.values['u_berserk_apostol_return_state'],1)
        self.assertEqual(f.values['u_berserk_eclipse_route'],2)
        self.assertNotIn('EOC_BERSERK_ECLIPSE_RESCUE_RETURN',f.external)
        f.teleport_succeeds=True;f.overrides[OLD+'LANDING_SAFE']=True;f.start()
        self.assertEqual(f.values['u_berserk_eclipse_route'],1)
    def test_missing_or_only_four_dead_is_not_victory(self):
        f=Ceremony();f.attacked()
        f.monsters=[];f.run(P+'CHECK_VICTORY')
        self.assertEqual(f.values.get('berserk_godhand_defeated',0),0)
        f=Ceremony();f.attacked()
        for k in KINDS[:4]:f.kill(k)
        f.run(P+'CHECK_VICTORY');self.assertNotIn('BERSERK_THREADBREAKER',f.traits)
        f.start();self.assertEqual(f.values['u_berserk_apostol_outcome'],3)
    def test_five_real_deaths_reward_once_immediately_and_end_invasion(self):
        f=Ceremony();f.attacked()
        for k in KINDS:f.kill(k)
        self.assertEqual(f.values['berserk_godhand_defeated'],1)
        self.assertEqual(f.values['berserk_eclipse_era'],0)
        self.assertIn('BERSERK_THREADBREAKER',f.traits)
        saved=copy.deepcopy(f.values);f.kill('VOID');self.assertEqual(f.values,saved)
        f.start();self.assertEqual(f.values['u_berserk_apostol_outcome'],4)
        self.assertEqual(f.values['berserk_eclipse_era'],0)
        self.assertNotIn('EOC_BERSERK_ECLIPSE_RESCUE_RETURN',f.external)
        self.assertEqual(f.traits,{'BERSERK_THREADBREAKER'})
        self.assertNotIn(OLD+'CONTINUATION_BEGIN',f.external)
    def test_native_null_npc_and_monster_killers_keep_the_dying_beta(self):
        for killer in [None,'npc','monster']:
            f=Ceremony();f.attacked();f.actor=killer
            f.actor_ref=None if killer is None else {'kind':killer,'traits':set(),'effects':set()}
            for k in KINDS:f.kill(k)
            self.assertEqual(f.values['berserk_godhand_defeated'],1,killer)
            self.assertIn('BERSERK_THREADBREAKER',f.traits)
    def test_no_reward_for_outside_or_non_godhand_victims(self):
        f=Ceremony();f.attacked();f.om='field'
        for k in KINDS:f.kill(k)
        self.assertNotIn('BERSERK_THREADBREAKER',f.traits)
        f.om='berserk_eclipse_apostol_ceremony'
        f.beta=monster('mon_berserk_projection_griffith')
        for k in KINDS:f.run(OLD+'HAND_'+k+'_DIED')
        self.assertNotIn('BERSERK_THREADBREAKER',f.traits)
    def test_world_migration_cannot_reenable_after_victory(self):
        f=Ceremony();f.values.update(berserk_godhand_defeated=1,berserk_eclipse_era=0,
            u_berserk_apostol_return_state=2,u_berserk_apostol_outcome=1)
        f.run(OLD+'RESTORE_WORLD_ERA');self.assertEqual(f.values['berserk_eclipse_era'],0)
        self.assertFalse(f.condition(EOCS['EOC_BERSERK_ECLIPSE_ERA_ENTER_OMT']['condition']))
    def test_only_verified_projection_unlocks_femto_question(self):
        f=Ceremony()
        def has():return any(r['topic']==T+'FEMTO_PROJECTION' for r in f.available(T+'FEMTO'))
        self.assertFalse(has());f.values['u_berserk_hand33_femto_projection_seen']=1;self.assertTrue(has())
        self.assertFalse(any(r['topic']==T+'FEMTO_PROJECTION_KILLED' for r in f.available(T+'FEMTO_PROJECTION')))
        f.values['u_berserk_griffith_projection_defeated']=1
        self.assertTrue(any(r['topic']==T+'FEMTO_PROJECTION_KILLED' for r in f.available(T+'FEMTO_PROJECTION')))
    def test_all_actual_death_callbacks_and_start_furniture_exist(self):
        for k in KINDS:
            obj=MONSTERS['mon_berserk_godhand_'+k.lower()]
            self.assertIn(OLD+'HAND_'+k+'_DIED',json.dumps(obj['death_function']))
        furniture=json.loads((MOD/'furniture/eclipse_trial.json').read_text())
        scar=next(o for o in furniture if o['id']=='f_berserk_eclipse_arrival_scar')
        self.assertEqual(scar['examine_action']['effect_on_conditions'],[P+'START_USE'])
    def test_victory_is_human_and_permanent_with_documented_stats(self):
        m=MUTATIONS['BERSERK_THREADBREAKER']
        self.assertFalse(m['purifiable']);self.assertFalse(m['valid'])
        self.assertNotIn('category',m);self.assertNotIn('transform',m)
        vals={v['value']:v for v in m['enchantments'][0]['values']}
        self.assertEqual(vals['STRENGTH']['add'],8);self.assertEqual(vals['SPEED']['add'],25)
        self.assertEqual(vals['MAX_HP']['multiply'],0.5)
        self.assertEqual(vals['MAX_STAMINA']['multiply'],0.5)
    def test_no_automatic_instant_kill_effects(self):
        for file in ['apostol_godhand_eocs.json','godhand_dialogue_33_eocs.json']:
            for node in walk(json.loads((MOD/'effects'/file).read_text())):
                self.assertNotIn('u_die',node);self.assertNotIn('npc_die',node)

if __name__=='__main__':unittest.main()
