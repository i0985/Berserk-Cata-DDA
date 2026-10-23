"""Run contract JSON transitions; native AI attitudes are checked separately."""
import copy
import json
import re
import unittest
from test_reference_journal_33 import Book, EOCS, TOPICS, MOD, walk

E='EOC_BERSERK_CONTRACT33_';OLD='EOC_BERSERK_APOSTOL_'
STEMS=['COUNT','WYALD','ROSINE','GRUNBELD']
SITES=['berserk_count_dungeon','berserk_wyald_ring','berserk_rosine_nest','berserk_grunbeld_crucible']
BODIES=['mon_berserk_apostle_count','mon_berserk_apostle_wyald','mon_berserk_apostle_rosine','mon_berserk_grunbeld_knight']
MONSTERS={o['id']:o for p in (MOD/'monsters').glob('*.json')
    for o in (lambda d:d if isinstance(d,list) else [d])(json.loads(p.read_text())) if o.get('type')=='MONSTER'}
MUTATIONS={o['id']:o for p in (MOD/'mutations').glob('*.json') for o in json.loads(p.read_text()) if o.get('type')=='mutation'}

def species(id_):
    o=MONSTERS[id_];base=species(o['copy-from']) if o.get('copy-from') in MONSTERS else set()
    if 'species' in o:base=set(o['species'] if isinstance(o['species'],list) else [o['species']])
    return (base|set(o.get('extend',{}).get('species',[])))-set(o.get('delete',{}).get('species',[]))

def npc(friend=True):return {'kind':'npc','friend':friend,'following':friend,'traits':set(),'effects':set(),'hp':100,'friendly':0}
def monster(id_):return {'kind':'monster','id':id_,'traits':set(),'effects':set(),'hp':100,'friendly':0,'visible':True}

class Contract(Book):
    def __init__(self,k='COUNT'):
        super().__init__();self.k=k;self.i=STEMS.index(k);self.om=SITES[self.i]
        self.self_ref={'kind':'avatar','traits':self.traits,'effects':set(),'hp':100,'friendly':0}
        self.beta=monster(BODIES[self.i]);self.monsters=[self.beta];self.npcs=[npc(),npc(False)]
        self.actor_ref=self.self_ref;self.dialogue_actions=[];self.dialogue_count=0;self.confirm=True
        self.values.update(u_berserk_apostol_schema=1)
        self.overrides['EOC_BERSERK_APOSTOL_STATE_CONSISTENT']=True
    def value(self,s):
        s=re.sub(r'\b_berserk_\w+',lambda m:repr(self.values.get(m[0],0)),s)
        s=re.sub(r"time\('([0-9]+) hours?'\)",lambda m:str(int(m[1])*3600),s)
        s=re.sub(r"[un]_hp_max\('[^']+'\)",'100',s)
        s=re.sub(r"u_hp\('[^']+'\)",str(self.actor_ref['hp']),s)
        s=re.sub(r"n_hp\('[^']+'\)",str(self.beta['hp'] if self.beta else 0),s)
        s=s.replace("distance('u', 'npc')",'1')
        s=s.replace("n_val('friendly')",str(self.beta.get('friendly',0) if self.beta else 0))
        s=s.replace("u_val('stamina')",'10000')
        return super().value(s)
    def condition(self,c):
        if isinstance(c,str):
            if c=='has_beta':return self.beta is not None
            if c=='u_is_npc':return self.actor_ref['kind']=='npc'
            if c=='u_is_monster':return self.actor_ref['kind']=='monster'
            if c=='npc_is_monster':return self.beta is not None and self.beta['kind']=='monster'
            if c=='npc_is_avatar':return self.beta is self.self_ref
            if c=='u_friend':return self.actor_ref.get('friend',False)
            if c=='u_following':return self.actor_ref.get('following',False)
            if c=='npc_following':return self.beta and self.beta.get('following',False)
            if c=='npc_friend':return self.beta and self.beta.get('friend',False)
        if isinstance(c,dict):
            if 'u_query' in c:return self.confirm
            for key,actor in [('u_has_trait',self.actor_ref),('npc_has_trait',self.beta)]:
                if key in c:return actor is not None and c[key] in actor['traits']
            for key,actor in [('u_has_species',self.actor_ref),('npc_has_species',self.beta)]:
                if key in c:return actor is not None and actor['kind']=='monster' and c[key] in species(actor['id'])
            for key,actor in [('u_has_effect',self.actor_ref),('npc_has_effect',self.beta)]:
                if key in c:return actor is not None and c[key] in actor['effects']
            if 'u_has_flag' in c:return any(c['u_has_flag'] in MUTATIONS.get(t,{}).get('flags',[]) for t in self.actor_ref['traits'])
        return super().condition(c)
    def run(self,id_):
        # Anatomy and mission placement have independent suites; all contract
        # conditions, mutation completion, supplies and party updates run JSON.
        if id_ in ['EOC_BERSERK_APOSTOL_PAWN_BEGIN','EOC_BERSERK_APOSTOL_PAWN_SYNC','EOC_BERSERK_REF_SYNC']:return
        if id_.endswith('_PAWN_SUSPEND_HUNT'):self.values['u_berserk_pact_resolved_'+self.k.lower()]=1;return
        if id_==OLD+'ACCEPT_REQUEST':
            if self.condition({'test_eoc':OLD+'CAN_ACCEPT'}):
                self.values.update(u_berserk_apostol_path=int(self.values['_berserk_apostol_requested_path']),
                    u_berserk_apostol_lineage=int(self.values['_berserk_apostol_requested_lineage']),u_berserk_apostol_stage=1)
            return
        return super().run(id_)
    def effect(self,x):
        if isinstance(x,str):
            assert x=='open_dialogue',x
            self.dialogue_count+=1;self.enter(self.topic('ROOT'))
            if self.dialogue_actions:self.dialogue_actions.pop(0)(self)
            return
        if isinstance(x,dict):
            if 'run_eocs' in x:
                a,b,ar=self.actor,self.beta,self.actor_ref
                alpha=x.get('alpha_talker');beta=x.get('beta_talker')
                if alpha=='avatar':self.actor_ref=self.self_ref;self.actor='avatar'
                if beta=='u':self.beta=ar
                elif beta=='npc':self.beta=b
                for key,value in x.get('variables',{}).items():self.values['_'+key]=int(value)
                loops=x.get('iterations',1)
                for _ in range(loops):
                    if 'condition' in x and not self.condition(x['condition']):break
                    self.run(x['run_eocs'])
                self.actor,self.beta,self.actor_ref=a,b,ar;return
            if 'u_run_npc_eocs' in x or 'u_run_monster_eocs' in x:
                is_npc='u_run_npc_eocs' in x
                actors=self.npcs if is_npc else [m for m in self.monsters if (not x.get('mtype_ids') or m['id'] in x['mtype_ids']) and (not x.get('monster_must_see') or m['visible'])]
                a,b,ar=self.actor,self.beta,self.actor_ref
                for target in actors:
                    self.actor_ref=target;self.actor=target['kind'];self.beta=None
                    for id_ in x['u_run_npc_eocs' if is_npc else 'u_run_monster_eocs']:self.run(id_)
                self.actor,self.beta,self.actor_ref=a,b,ar;return
            for key,actor,add in [('u_add_trait',self.actor_ref,True),('u_lose_trait',self.actor_ref,False),('u_lose_effect',self.actor_ref,False),('npc_add_effect',self.beta,True),('npc_lose_effect',self.beta,False)]:
                if key in x:
                    bag=actor['traits' if 'trait' in key else 'effects']
                    bag.add(x[key]) if add else bag.discard(x[key]);return
            if 'u_consume_item' in x:self.inventory[x['u_consume_item']]-=x.get('count',1);return
        return super().effect(x)
    def topic(self,s):return 'TALK_BERSERK_APOSTOL_'+self.k+'_PAWN_'+s
    def targets(self,s):return [r['topic'] for r in self.available(self.topic(s))]
    def pick(self,s,to):
        rs=[r for r in self.available(self.topic(s)) if r['topic']==(to if to.startswith('TALK_') else self.topic(to))]
        assert rs,(s,to,self.targets(s))
        if 'effect' in rs[0]:self.effect(rs[0]['effect'])
        if rs[0]['topic'] in TOPICS:self.enter(rs[0]['topic'])
    def begin(self):self.values['berserk_apostol_'+self.k.lower()+'_pawn_encounter']=1
    def accept(self):self.begin();self.pick('DECISION','ACCEPTED')
    def died(self):self.values['berserk_hunt_count_state' if self.k=='COUNT' else 'berserk_apostle_'+self.k.lower()+'_dead']=3 if self.k=='COUNT' else 1

class NamedApostles(unittest.TestCase):
    def test_all_four_accept_immediately_only_once_and_keep_body_on_reload(self):
        for k in STEMS:
            f=Contract(k);f.accept()
            self.assertEqual(f.values['u_berserk_apostol_stage'],3)
            self.assertEqual(f.values['u_berserk_apostol_growth_running'],0)
            self.assertIn('BERSERK_'+k+'_PAWN_FORM',f.traits)
            self.assertNotIn(f.topic('OFFER'),f.targets('ROOT'))
            saved=copy.deepcopy(f);before=copy.deepcopy(saved.values)
            saved.run(OLD+k+'_PAWN_ACCEPT');self.assertEqual(saved.values,before)
    def test_escape_and_confirmation_cancel_reopen_without_refusal_or_acceptance(self):
        for k in STEMS:
            f=Contract(k)
            def cancel(g):g.confirm=False;g.pick('DECISION','ACCEPTED');self.assertIn(g.topic('DETAILS'),g.targets('ACCEPTED'))
            def refuse(g):g.pick('DECISION','REFUSAL');g.pick('REFUSAL','TALK_DONE')
            f.dialogue_actions=[lambda g:None,cancel,refuse]
            f.run(OLD+k+'_PAWN_OPEN')
            self.assertEqual(f.dialogue_count,3)
            self.assertEqual(f.values['berserk_apostol_'+k.lower()+'_pawn_encounter'],2)
            self.assertFalse(f.traits)
    def test_saved_pending_offer_is_not_converted_into_refusal(self):
        f=Contract();f.begin();f.run(OLD+'COUNT_PAWN_CLOSE')
        self.assertEqual(f.values['berserk_apostol_count_pawn_encounter'],1)
        f.dialogue_actions=[lambda g:g.accept()]
        f.run(OLD+'PAWN_RECOVER_PARLEY');self.assertEqual(f.values['u_berserk_apostol_stage'],3)
    def test_inquiries_and_one_defiant_reply_do_not_accept_or_start_battle(self):
        for k in STEMS:
            f=Contract(k);f.begin();f.enter(f.topic('ROOT'))
            f.pick('ROOT','OFFER');f.pick('OFFER','DETAILS')
            if self.topic_exists(k,'DEFY'):
                f.enter(f.topic('DEFY'))
            for r in f.available(f.topic('DETAILS')):
                if r['topic'].endswith(('DECISION','TALK_DONE')):continue
                f.enter(r['topic'])
            self.assertEqual(f.values['berserk_apostol_'+k.lower()+'_pawn_encounter'],1)
            self.assertFalse(f.traits)
    def test_guts_other_path_projection_and_dragon_do_not_receive_offer(self):
        for k in STEMS:
            f=Contract(k);f.begin();f.guts=True
            self.assertNotIn(f.topic('OFFER'),f.targets('ROOT'))
            f.pick('DECISION','TALK_DONE');self.assertFalse(f.traits)
            f=Contract(k);f.begin();f.values.update(u_berserk_apostol_path=1,u_berserk_apostol_lineage=1)
            self.assertNotIn(f.topic('OFFER'),f.targets('ROOT'))
            f=Contract(k);f.begin();f.beta=monster('mon_berserk_projection_'+k.lower())
            self.assertNotIn(f.topic('OFFER'),f.targets('ROOT'))
        f=Contract('GRUNBELD');f.values['berserk_apostol_grunbeld_pawn_encounter']=2;f.beta=monster('mon_berserk_grunbeld_dragon')
        self.assertNotIn(f.topic('OFFER'),f.targets('ROOT'))
    def test_payment_is_exact_immediate_six_hours_and_not_repeatable_while_active(self):
        for k,(item,count) in zip(STEMS,[('leather',2),('scrap',12),('meat',4),('steel_lump',4)]):
            f=Contract(k);f.accept();f.inventory[item]=count-1
            f.run(OLD+k+'_PAWN_PAY');self.assertNotIn('u_berserk_apostol_pawn_favor_until',f.values)
            f.inventory[item]=count;f.run(OLD+k+'_PAWN_PAY')
            self.assertEqual(f.inventory[item],0);self.assertEqual(f.values['u_berserk_apostol_pawn_favor_until'],f.now+21600)
            f.inventory[item]=count;f.run(OLD+k+'_PAWN_PAY');self.assertEqual(f.inventory[item],count)
            f.now+=21601;f.run(OLD+k+'_PAWN_PAY');self.assertEqual(f.inventory[item],0)
    def test_old_growth_based_favor_is_capped_once_without_extending_short_support(self):
        f=Contract();f.accept();f.values['u_berserk_contract33_count_schema']=0
        f.values['u_berserk_apostol_pawn_favor_until']=f.now+42*3600
        f.run(E+'PARTY_SYNC');self.assertEqual(f.values['u_berserk_apostol_pawn_favor_until'],f.now+21600)
        f.now+=300;until=f.values['u_berserk_apostol_pawn_favor_until'];f.run(E+'PARTY_SYNC')
        self.assertEqual(f.values['u_berserk_apostol_pawn_favor_until'],until)
    def test_companions_have_truce_but_strangers_and_other_households_do_not(self):
        f=Contract('COUNT');f.accept();truce='BERSERK_COUNT_PAWN_COMPANION_TRUCE'
        self.assertIn(truce,f.npcs[0]['traits']);self.assertNotIn(truce,f.npcs[1]['traits'])
        self.assertIn('BERSERK_COUNT_PAWN_HOUSEHOLD',species('mon_berserk_count_servant'))
        self.assertNotIn('BERSERK_COUNT_PAWN_HOUSEHOLD',species('mon_berserk_black_dog_thrall'))
        self.assertNotIn('BERSERK_COUNT_PAWN_HOUSEHOLD',species('mon_berserk_apostle_wyald'))
        self.assertTrue(MUTATIONS[truce]['player_display'] is False)
        self.assertNotIn('enchantments',MUTATIONS[truce])
    def test_new_cocoon_creature_is_covered_without_delayed_monster_conversion(self):
        f=Contract('ROSINE');f.accept();truce='BERSERK_ROSINE_PAWN_COMPANION_TRUCE'
        self.assertTrue(species('mon_berserk_cocoon_ravager') & set(MUTATIONS[truce]['ignored_by']))
        self.assertIn(truce,f.npcs[0]['traits'])
        late=npc();f.npcs.append(late);f.run(E+'PARTY_SYNC');self.assertIn(truce,late['traits'])
        late['friend']=late['following']=False;f.run(E+'PARTY_SYNC');self.assertNotIn(truce,late['traits'])
    def test_player_or_companion_attack_breaks_truce_and_preserves_body(self):
        for k in STEMS:
            for companion in [False,True]:
                f=Contract(k);f.accept();f.values['_berserk_pawn_player_attack']=1
                if companion:f.actor_ref=f.npcs[0];f.actor='npc'
                f.run(OLD+k+'_PAWN_ATTACK_CHARACTER_MELEE_ATTACKS_MONSTER')
                f.actor_ref=f.self_ref;f.actor='avatar'
                self.assertEqual(f.values['u_berserk_apostol_pawn_oath_broken'],1)
                self.assertEqual(f.values['u_berserk_apostol_pawn_favor_until'],0)
                self.assertIn('BERSERK_'+k+'_PAWN_FORM',f.traits)
                self.assertNotIn('BERSERK_'+k+'_PAWN_COMPANION_TRUCE',f.npcs[0]['traits'])
                self.assertNotIn(f.topic('OFFER'),f.targets('ROOT'))
                self.assertNotIn('BERSERK_'+k+'_PAWN_LOYALTY',f.traits)
    def test_zombie_attack_does_not_betray_and_missed_delivery_does_not_betray(self):
        f=Contract();f.accept();f.values['_berserk_pawn_player_attack']=0
        f.run(OLD+'COUNT_PAWN_ATTACKED');self.assertNotEqual(f.values.get('u_berserk_apostol_pawn_oath_broken'),1)
        f.now+=20*86400;f.run(E+'PARTY_SYNC')
        self.assertIn('BERSERK_COUNT_PAWN_COMPANION_TRUCE',f.npcs[0]['traits'])
    def test_confirmed_master_death_removes_help_immediately_not_the_permanent_body(self):
        for k in STEMS:
            f=Contract(k);f.accept();f.values['u_berserk_apostol_pawn_favor_until']=f.now+21600
            f.run(OLD+k+'_PAWN_MASTER_SYNC');self.assertNotEqual(f.values.get('u_berserk_apostol_pawn_master_dead'),1)
            f.died();f.run(OLD+k+'_PAWN_MASTER_SYNC')
            self.assertEqual(f.values['u_berserk_apostol_pawn_favor_until'],0)
            self.assertNotIn('BERSERK_'+k+'_PAWN_COMPANION_TRUCE',f.npcs[0]['traits'])
            self.assertIn('BERSERK_'+k+'_PAWN_FORM',f.traits)
    @staticmethod
    def topic_exists(k,s):return 'TALK_BERSERK_APOSTOL_'+k+'_PAWN_'+s in TOPICS

    def test_spell_damage_to_servant_by_companion_breaks_the_pact(self):
        f=Contract('COUNT');f.accept()
        f.actor_ref=monster('mon_berserk_count_servant');f.actor='monster';f.beta=f.npcs[0]
        f.run(OLD+'COUNT_PAWN_DAMAGED')
        self.assertEqual(f.values['u_berserk_apostol_pawn_oath_broken'],1)
        self.assertNotIn('BERSERK_COUNT_PAWN_COMPANION_TRUCE',f.npcs[0]['traits'])
    def test_observation_topics_need_actual_personal_proof(self):
        f=Contract('COUNT');f.begin();self.assertNotIn(f.topic('PRISONERS'),f.targets('PROTECT'))
        f.values['u_berserk_ref_prisoner_met']=1;self.assertIn(f.topic('PRISONERS'),f.targets('PROTECT'))
        f=Contract('ROSINE');f.begin();self.assertNotIn(f.topic('COCOONS'),f.targets('DETAILS'))
        f.values['u_berserk_ref_cocoon_examined']=1;self.assertIn(f.topic('COCOONS'),f.targets('DETAILS'))
        f=Contract('GRUNBELD');f.begin();f.values['u_berserk_ref_grunbeld_siege_seen']=1
        self.assertNotIn(f.topic('FLORA'),f.targets('DETAILS'))
        f.values['u_berserk_contract33_siege_witness']=1;self.assertIn(f.topic('FLORA'),f.targets('DETAILS'))
    def test_guts_combat_introduction_is_once_and_does_not_pause_for_offer(self):
        f=Contract();f.guts=True
        f.run(E+'COUNT_COMBAT_CHECK');count=len(f.messages)
        self.assertEqual(count,1);self.assertEqual(f.dialogue_count,0)
        f.run(E+'COUNT_COMBAT_CHECK');self.assertEqual(len(f.messages),count)
        self.assertNotIn('Клеймёный',f.messages[-1]['u_message'])
    def test_environment_damage_to_servant_does_not_break_pact(self):
        f=Contract();f.accept();f.actor_ref=monster('mon_berserk_count_servant');f.actor='monster';f.beta=None
        f.run(OLD+'COUNT_PAWN_DAMAGED')
        self.assertNotEqual(f.values.get('u_berserk_apostol_pawn_oath_broken'),1)
    def test_death_removes_active_flutter_or_brace_without_removing_flesh(self):
        for k,fx in [('ROSINE','berserk_apostol_pawn_flutter'),('GRUNBELD','berserk_apostol_pawn_brace')]:
            f=Contract(k);f.accept();f.self_ref['effects'].add(fx);f.died();f.run(OLD+k+'_PAWN_MASTER_SYNC')
            self.assertNotIn(fx,f.self_ref['effects']);self.assertIn('BERSERK_'+k+'_PAWN_FORM',f.traits)
    def test_full_dialogue_graph_and_no_author_placeholders_or_throne(self):
        data=json.loads((MOD/'dialogue/apostol_contracts.json').read_text())
        self.assertEqual(len(data),100)
        for obj in data:
            for r in obj['responses']:self.assertTrue(r['topic']=='TALK_DONE' or r['topic'] in TOPICS,r['topic'])
            text=json.dumps(obj,ensure_ascii=False)
            self.assertNotRegex(text,r'\[предмет|\[реальн|\[действит|\[правдив|\[необходим|\[существующ|трон|слабая версия|линия мутаций|\*\*Игрок')

if __name__=='__main__':unittest.main()
