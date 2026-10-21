"""Stateful checks of Rickert's actual data, not a native CDDA playtest.

Positions, loaded NPCs, inventory UI selection and HP are environmental fixtures.
The predicates, branching, paid order timing, memories and refusal effects execute
the generated JSON. NPC scan callbacks use NPC alpha and an empty beta.
"""
import copy
import gettext
import json
import re
import unittest
from collections import Counter

from test_godo_dialogue_33 import Conversation as GodoConversation
from test_recovery_33 import MOD, walk


def tid(s):return s if s.startswith('TALK_') else 'TALK_BERSERK_RICKERT'+('_'+s if s else '')


class Conversation(GodoConversation):
    def __init__(self):
        super().__init__()
        self.npc={'class':'NC_BERSERK_RICKERT','following':False}
        self.hp={s:100 for s in ['head','torso','arm_l','arm_r','leg_l','leg_r']}
        self.npc_items=Counter();self.follow_calls=0;self.leaves=0;self.guarding=False
        self.scanned_npc=None;self.legacy_rickert=False;self.actor_dead=False
        self.overrides['EOC_BERSERK_GODO_AT_SMITH']=False
        self.overrides['EOC_BERSERK_GODO_KNOWN']=False
        self.overrides['EOC_BERSERK_GODO_ORDER_SYNC']=False

    def evaluate(self,s):
        s=re.sub(r"n_hp\('(\w+)'\)",lambda m:str(self.hp[m[1]]),s)
        s=re.sub(r"n_hp_max\('(\w+)'\)",'100',s)
        s=re.sub(r"u_monsters_nearby\([^)]*\)",str(int(self.legacy_rickert)),s)
        return super().evaluate(s)

    def condition(self,c):
        if isinstance(c,str):
            if c=='npc_is_npc':return self.npc is not None and not self.npc_alpha and not self.actor_dead
            if c=='npc_following':return bool(self.npc and self.npc.get('following'))
            if c=='u_is_avatar':return not self.npc_alpha
        if isinstance(c,dict):
            if 'npc_has_class' in c:return not self.npc_alpha and bool(self.npc and self.npc['class']==c['npc_has_class'])
        return super().condition(c)

    def run(self,name):
        if name=='EOC_BERSERK_GODO_ORDER_SYNC':return
        # GodoConversation skips world registration/mission routing, as intended.
        super().run(name)

    def effect(self,x):
        if isinstance(x,str):
            if x=='follow':
                self.npc['following']=True;self.follow_calls+=1;return
            if x=='leave':self.npc['following']=False;self.leaves+=1;return
            if x=='assign_guard':self.guarding=True;return
        if isinstance(x,dict):
            if 'npc_first_topic' in x:self.npc['chat']=x['npc_first_topic'];return
            if 'u_sell_item' in x:
                item=x['u_sell_item'];n=x.get('count',1)
                if self.inventory[item]>=n:
                    self.inventory[item]-=n;self.npc_items[item]+=n
                    for id in x.get('true_eocs',[]):self.run(id)
                return
            if 'u_run_npc_eocs' in x:
                original=self.npc
                self.npc=self.scanned_npc
                if self.npc:
                    self.npc_alpha=True
                    for id in x['u_run_npc_eocs']:self.run(id)
                    self.npc_alpha=False
                self.npc=original;return
        super().effect(x)

    def choose(self,s,target,index=0):
        matches=[r for r in self.available(tid(s)) if r['topic']==tid(target)]
        assert len(matches)>index,(s,target,[r['topic'] for r in self.available(tid(s))])
        r=matches[index]
        if 'effect' in r:self.effect(r['effect'])
        target=r['topic']
        if target in self.topics and 'speaker_effect' in self.topics[target]:self.effect(self.topics[target]['speaker_effect']['effect'])
        return target

    def line(self,s):return super().line(tid(s))
    def available(self,s):return super().available(tid(s))
    def targets(self,s):return [r['topic'] for r in self.available(s)]
    def met(self):self.values['u_berserk_rickert_met']=1
    def normal_return(self):
        self.values.update(berserk_eclipse_era=1,u_berserk_eclipse_rescue_state=2,
                           u_berserk_godo_rescue_relocated=1,u_berserk_eclipse_route=1)


class RickertDialogue(unittest.TestCase):
    def test_marker_and_godot_acquaintance_do_not_introduce_rickert(self):
        for values in [{},{'u_berserk_journal_knows_godo':1},{'u_berserk_godo_personally_met':1,'u_berserk_forge_visited':1}]:
            f=Conversation();f.values.update(values)
            self.assertIn('pin',f.line(''));self.assertNotIn(tid('ROAD'),f.targets(''))
            f.choose('','INTRO_SMITH')
            self.assertEqual(f.values['u_berserk_rickert_met'],1)
            self.assertEqual(f.values.get('u_berserk_godo_personally_met',0),values.get('u_berserk_godo_personally_met',0))
            self.assertNotIn('pin',f.line(''));self.assertIn(tid('ROAD'),f.targets(''))

    def test_guts_known_without_repeated_introduction(self):
        for after in [0,1]:
            f=Conversation();f.overrides['EOC_BERSERK_FORGE_GUTS']=True;f.values['berserk_eclipse_era']=after
            self.assertIn('Guts',f.line(''));self.assertNotIn(tid('INTRO_SMITH'),f.targets(''))
        f=Conversation();f.met();self.assertNotIn(tid('GUTS_CROSSBOW'),f.targets('MECHANISMS'))
        f.overrides['EOC_BERSERK_FORGE_GUTS']=True;self.assertIn(tid('GUTS_CROSSBOW'),f.targets('MECHANISMS'))

    def test_care_snapshot_records_only_actor_who_was_actually_present(self):
        f=Conversation();f.values['u_berserk_godo_rescue_relocated']=1
        f.scanned_npc={'class':'NC_BERSERK_RICKERT'};f.run('EOC_BERSERK_RICKERT_CAPTURE_CARE')
        self.assertEqual(f.values['u_berserk_rickert_care_present'],1)
        f.scanned_npc=None;f.run('EOC_BERSERK_RICKERT_CAPTURE_CARE')
        self.assertEqual(f.values['u_berserk_rickert_care_present'],1)
        f=Conversation();f.values['u_berserk_godo_rescue_relocated']=1;f.scanned_npc={'class':'NC_OTHER'}
        f.run('EOC_BERSERK_RICKERT_CAPTURE_CARE');self.assertEqual(f.values['u_berserk_rickert_care_present'],0)

    def test_wake_for_acquainted_newcomer_guts_and_follower(self):
        for kind in ['known','unknown','building','guts','follower']:
            f=Conversation();f.normal_return();f.values['u_berserk_rickert_care_present']=1
            f.values['u_berserk_forge_wake_context']=3 if kind=='unknown' else 1
            if kind=='known':f.met()
            if kind=='guts':f.overrides['EOC_BERSERK_FORGE_GUTS']=True
            if kind=='follower':f.npc['following']=True;f.met()
            expected={'known':'back at the forge','unknown':'I am Rickert','building':'I am Rickert','guts':'Guts','follower':'frightened'}[kind]
            self.assertIn(expected,f.line(''));self.assertNotIn(tid('ECLIPSE'),f.targets(''))
            f.choose('','WAKE_THANKS');self.assertEqual(f.values['u_berserk_rickert_wake_greeted'],1)
            self.assertNotIn(tid('WAKE_THANKS'),f.targets(''))

    def test_late_absent_follower_does_not_claim_treatment(self):
        f=Conversation();f.normal_return();f.met();f.npc['following']=True
        self.assertNotIn(tid('WAKE_THANKS'),f.targets(''))
        self.assertIn(tid('REUNION_LATER'),f.targets(''))
        f.choose('','REUNION_LATER');self.assertIn('I was not there',f.line('REUNION_LATER'))
        self.assertNotIn(tid('REUNION_LATER'),f.targets(''))

    def test_knight_still_waiting_is_not_described_as_having_departed(self):
        f=Conversation();self.assertNotIn('went on his way',f.line('WAKE_RIDER'))
        f.values['u_berserk_knight_farewell_confirmed']=1
        self.assertIn('went on his way',f.line('WAKE_RIDER'))

    def test_intact_hand_has_no_prosthesis_paths_even_when_eclipse_happened(self):
        f=Conversation();f.met();f.normal_return()
        for s in ['','ORDERS','MECHANISMS']:
            self.assertNotIn('TALK_BERSERK_GODO_ARM',f.targets(s))
        self.assertNotIn('cannon',f.line(''))
        f.run('EOC_BERSERK_GODO_START_ARM');self.assertEqual(f.values.get('u_berserk_godo_arm_state',0),0)
        f.bionics.add('bio_berserk_hand_stump');self.assertIn('TALK_BERSERK_GODO_ARM',f.targets('ORDERS'))

    def test_prosthesis_explanation_does_not_start_or_charge_order(self):
        f=Conversation();f.bionics.add('bio_berserk_hand_stump')
        f.choose('TALK_BERSERK_GODO_ARM','TALK_BERSERK_GODO_ARM_STATUS')
        self.assertEqual(f.values.get('u_berserk_godo_arm_state',0),0)
        f.choose('TALK_BERSERK_GODO_ARM_STATUS','TALK_BERSERK_GODO_ARM_STATUS')
        self.assertEqual(f.values['u_berserk_godo_arm_state'],1);self.assertFalse(f.inventory)

    def test_two_prosthesis_deliveries_six_hours_and_one_real_item(self):
        f=Conversation();f.bionics.add('bio_berserk_hand_stump')
        f.inventory.update(steel_lump=8,pipe=2,spring=2,leather=4,charcoal=200)
        f.choose('TALK_BERSERK_GODO_ARM_STATUS','TALK_BERSERK_GODO_ARM_STATUS')
        f.choose('TALK_BERSERK_GODO_ARM_STATUS','ARM_DELIVERY')
        self.assertEqual(f.values['u_berserk_godo_arm_state'],2);self.assertEqual(f.inventory['steel_lump'],0)
        f.choose('TALK_BERSERK_GODO_ARM_STATUS','ARM_DELIVERY')
        self.assertEqual(f.values['u_berserk_godo_arm_state'],3);self.assertEqual(f.inventory['charcoal'],0)
        self.assertNotIn(tid('ARM_RECEIVED'),f.targets('TALK_BERSERK_GODO_ARM_STATUS'))
        f.now+=21600;f.choose('TALK_BERSERK_GODO_ARM_STATUS','ARM_RECEIVED')
        self.assertEqual(f.inventory['bio_berserk_arm_cannon'],1);self.assertEqual(f.values['u_berserk_rickert_arm_delivered'],1)
        self.assertNotIn('bio_berserk_arm_cannon',f.bionics)
        self.assertNotIn(tid('ARM_RECEIVED'),f.targets('TALK_BERSERK_GODO_ARM_STATUS'))

    def test_existing_device_refund_is_not_a_second_delivery(self):
        f=Conversation();f.bionics.add('bio_berserk_hand_stump');f.values['u_berserk_godo_arm_state']=3
        f.inventory['bio_berserk_arm_cannon']=1;f.now=100000
        self.assertNotIn(tid('ARM_RECEIVED'),f.targets('TALK_BERSERK_GODO_ARM_STATUS'))
        f.choose('TALK_BERSERK_GODO_ARM_STATUS','ARM_REFUNDED')
        self.assertEqual(f.inventory['steel_lump'],8);self.assertEqual(f.values.get('u_berserk_rickert_arm_delivered',0),0)
        self.assertNotIn(tid('ARM_REFUNDED'),f.targets('TALK_BERSERK_GODO_ARM_STATUS'))

    def test_loose_device_is_not_mistaken_for_installed_or_self_made(self):
        f=Conversation();f.bionics.add('bio_berserk_hand_stump');f.inventory['bio_berserk_arm_cannon']=1
        self.assertIn('not fitted',f.line('TALK_BERSERK_GODO_ARM'))
        self.assertIn(tid('ARM_FOUND'),f.targets('TALK_BERSERK_GODO_ARM'))
        self.assertNotIn(tid('PRAISE'),f.targets('TALK_BERSERK_GODO_ARM'))
        f.values['u_berserk_arm_cannon_self_made']=1
        self.assertNotIn('without the hand',f.line('PRAISE'))
        f.values['u_berserk_arm_cannon_self_made_one_hand']=1
        self.assertIn('without the hand',f.line('PRAISE'))
        f.bionics.add('bio_berserk_arm_cannon');self.assertIn(tid('ARM_FITTED'),f.targets('TALK_BERSERK_GODO_ARM'))

    def test_demonic_gift_does_not_block_prosthesis_or_claim_missing_hand(self):
        f=Conversation();f.demon();f.met()
        self.assertNotIn(tid('ARM_CHANGED'),f.targets('TALK_BERSERK_GODO_ARM'))
        f.bionics.add('bio_berserk_hand_stump');self.assertIn(tid('ARM_CHANGED'),f.targets('TALK_BERSERK_GODO_ARM'))
        f.choose('TALK_BERSERK_GODO_ARM_STATUS','TALK_BERSERK_GODO_ARM_STATUS')
        self.assertEqual(f.values['u_berserk_godo_arm_state'],1)

    def test_bolt_order_is_independent_and_repeats_only_after_collection(self):
        f=Conversation();f.inventory.update(steel_chunk=1,stick=1,thread=20,feather=10,charcoal=50)
        f.choose('BOLTS','BOLTS_ACCEPTED');self.assertFalse(f.values.get('u_berserk_rickert_bolts_pending',0))
        f.choose('BOLTS','BOLTS_DELIVERED');self.assertEqual(f.inventory['charcoal'],0)
        self.assertEqual(f.values.get('u_berserk_godo_arm_state',0),0)
        self.assertNotIn(tid('BOLTS_COLLECTED'),f.targets('BOLTS'));f.now+=1800
        f.choose('BOLTS','BOLTS_COLLECTED');self.assertEqual(f.inventory['bolt_wood_bodkin'],10)
        self.assertIn(tid('BOLTS_ACCEPTED'),f.targets('BOLTS'))

    def test_remote_companion_cannot_consume_forge_materials(self):
        f=Conversation();f.at_forge=False;f.npc['following']=True;f.bionics.add('bio_berserk_hand_stump')
        f.inventory.update(steel_chunk=1,stick=1,thread=20,feather=10,charcoal=50)
        self.assertNotIn(tid('BOLTS_DELIVERED'),f.targets('BOLTS'))
        self.assertNotIn('TALK_BERSERK_GODO_ARM_STATUS',f.targets('TALK_BERSERK_GODO_ARM_STATUS'))

    def test_world_eclipse_does_not_make_a_first_person_witness(self):
        f=Conversation();f.met();f.values['berserk_eclipse_era']=1
        self.assertNotIn(tid('ECLIPSE'),f.targets(''))
        f.run('EOC_BERSERK_RICKERT_STORY_TRUTH');self.assertEqual(f.values.get('u_berserk_rickert_eclipse_story',0),0)
        f.values.update(u_berserk_eclipse_route=2,u_berserk_apostol_return_state=2,u_berserk_apostol_outcome=2)
        self.assertIn(tid('CEREMONY_WITNESS'),f.targets(''));self.assertNotIn(tid('ECLIPSE'),f.targets(''))

    def test_truth_does_not_repeat_first_shock_or_allow_rewriting_to_lie(self):
        f=Conversation();f.normal_return();f.met()
        f.choose('ECLIPSE','ECLIPSE_TRUTH');self.assertEqual(f.values['u_berserk_rickert_eclipse_story'],1)
        self.assertIn('piece at a time',f.line('ECLIPSE'));self.assertNotIn(tid('ECLIPSE_TRUTH'),f.targets('ECLIPSE'))
        f.run('EOC_BERSERK_RICKERT_STORY_LIE');self.assertEqual(f.values['u_berserk_rickert_eclipse_story'],1)
        self.assertIn('thought I knew',f.line('COMMANDER'))

    def test_lie_and_late_confession_remember_both_facts(self):
        f=Conversation();f.normal_return();f.met();f.choose('ECLIPSE','ECLIPSE_LIE')
        self.assertNotIn('thought I knew',f.line('COMMANDER'))
        self.assertIn('took Griffith',f.line('ECLIPSE'))
        f.choose('ECLIPSE','CONFESSION');f.choose('CONFESSION','CONFESSION_HURT')
        self.assertEqual(f.values['u_berserk_rickert_eclipse_story'],2)
        f.choose('CONFESSION_HURT','CONFESSION_RESPONSIBLE');f.choose('CONFESSION_RESPONSIBLE','CONFESSION_DONE')
        self.assertEqual(f.values['u_berserk_rickert_eclipse_story'],1);self.assertEqual(f.values['u_berserk_rickert_lied_before'],1)
        self.assertNotIn('not your fault',f.line('CONFESSION_DONE'))
        self.assertEqual(f.values.get('n_berserk_rickert_recruit_refused',0),0)

    def test_silence_does_not_confirm_deaths_or_close_services(self):
        f=Conversation();f.normal_return();f.met();f.choose('ECLIPSE','ECLIPSE_SILENCE')
        self.assertEqual(f.values['u_berserk_rickert_eclipse_story'],3)
        self.assertEqual(f.values.get('u_berserk_rickert_heard_losses',0),0)
        self.assertIn(tid('ROAD'),f.targets(''));self.assertIn(tid('ORDERS'),f.targets(''))
        f.choose('ECLIPSE','ECLIPSE_TRUTH');self.assertEqual(f.values['u_berserk_rickert_eclipse_story'],1)

    def test_individual_death_needs_studied_evidence_and_keeps_memory_after_loss(self):
        f=Conversation();f.normal_return();f.met();f.inventory['berserk_judeau_knife_hilt']=1
        self.assertNotIn(tid('DEATH_JUDEAU'),f.targets('REMEMBER_JUDEAU'))
        f.values['u_berserk_godo_witness_judeau']=1;f.choose('REMEMBER_JUDEAU','DEATH_JUDEAU')
        self.assertEqual(f.values['u_berserk_rickert_knows_death_judeau'],1)
        self.assertEqual(f.values.get('u_berserk_rickert_knows_death_pippin',0),0)
        f.inventory.clear();self.assertIn(tid('DEATH_JUDEAU'),f.targets('REMEMBER_JUDEAU'))

    def test_keepsake_viewing_does_not_take_it_and_gift_is_explicit(self):
        f=Conversation();f.met();item='berserk_judeau_knife_hilt';f.inventory[item]=1
        f.choose('REMEMBER_JUDEAU','ITEM_JUDEAU');self.assertEqual(f.inventory[item],1)
        f.choose('ITEM_JUDEAU','KEEP_JUDEAU');self.assertEqual(f.inventory[item],1)
        f.choose('KEEP_JUDEAU','ITEM_GIVEN');self.assertEqual(f.inventory[item],0)
        self.assertEqual(f.npc_items[item],1);self.assertEqual(f.values['u_berserk_rickert_given_judeau'],1)
        self.assertNotIn(tid('ITEM_JUDEAU'),f.targets('REMEMBER_JUDEAU'))

    def test_respectful_invitation_defer_and_real_join_without_copy(self):
        f=Conversation();f.met();f.choose('ROAD','ROAD_LATER')
        self.assertEqual(f.values.get('n_berserk_rickert_recruit_refused',0),0)
        f.choose('ROAD','ROAD_MUTUAL');f.choose('ROAD_MUTUAL','ROAD_PLAN')
        f.choose('ROAD_PLAN','ROAD_READY');self.assertEqual(f.follow_calls,0)
        f.choose('ROAD_READY','JOINED');self.assertTrue(f.npc['following']);self.assertEqual(f.follow_calls,1)
        self.assertNotIn(tid('JOINED'),f.targets('ROAD_READY'))
        self.assertNotIn(tid('ROAD'),f.targets(''));self.assertIn(tid('COMPANION'),f.targets(''))

    def test_four_heavy_answers_permanently_refuse_but_leave_orders_available(self):
        for parent,target in [('ROAD','REFUSE'),('ROAD_CHOICE','REFUSE_PROPERTY'),('ROAD','REFUSE_THREAT'),('ROAD','REFUSE_DEAD')]:
            f=Conversation();f.met();f.values['u_berserk_rickert_heard_losses']=1
            f.choose(parent,target);self.assertEqual(f.values['n_berserk_rickert_recruit_refused'],1)
            f.choose('REFUSE_MENU','APOLOGY');self.assertEqual(f.values['n_berserk_rickert_recruit_refused'],1)
            self.assertNotIn(tid('ROAD'),f.targets(''));self.assertIn(tid('ORDERS'),f.targets(''))
            f.run('EOC_BERSERK_RICKERT_JOIN');self.assertFalse(f.npc['following'])

    def test_hidden_acceptance_is_not_omniscient_and_boundary_is_not_breakup(self):
        f=Conversation();f.met();f.npc['following']=True;f.demon()
        self.assertNotIn('body',f.line(''));self.assertNotIn('Tell me',f.line(''))
        self.assertIn('guess',f.line('TALK_BERSERK_APOSTOL_RICKERT'))
        f.choose('TALK_BERSERK_APOSTOL_RICKERT','CHANGED_BOUNDARY');self.assertTrue(f.npc['following'])
        self.assertEqual(f.values.get('n_berserk_rickert_recruit_refused',0),0)
        f.choose('TALK_BERSERK_APOSTOL_RICKERT','TALK_BERSERK_APOSTOL_RICKERT_ANSWER')
        self.assertEqual(f.values['u_berserk_apostol_rickert_told'],1)

    def test_demon_must_have_existing_counsel_before_new_join(self):
        f=Conversation();f.met();f.demon();f.values['n_berserk_rickert_respect']=1
        self.assertNotIn(tid('JOINED'),f.targets('ROAD_READY'))
        f.choose('TALK_BERSERK_APOSTOL_RICKERT_ANSWER','CHANGED_COUNSEL')
        self.assertIn(tid('JOINED'),f.targets('ROAD_READY'))

    def test_subjugation_breaks_existing_following_but_keeps_same_npc_and_work(self):
        f=Conversation();f.met();f.npc['following']=True;f.demon();f.values['u_berserk_godo_arm_state']=2
        original=f.npc
        f.choose('TALK_BERSERK_APOSTOL_RICKERT','CHANGED_BREAK')
        self.assertIs(f.npc,original);self.assertFalse(f.npc['following']);self.assertEqual(f.leaves,1)
        self.assertTrue(f.guarding);self.assertEqual(f.npc['chat'],tid(''))
        self.assertEqual(f.values['u_berserk_godo_arm_state'],2)
        self.assertEqual(f.values['n_berserk_rickert_recruit_refused'],1)

    def test_visible_observations_are_once_and_need_the_actual_body(self):
        f=Conversation();f.met();f.demon()
        self.assertNotIn(tid('VISIBLE_WINGS'),f.targets(''))
        f.flags.add('WINGS_2');self.assertIn(tid('VISIBLE_WINGS'),f.targets(''))
        f.choose('','VISIBLE_WINGS');self.assertNotIn(tid('VISIBLE_WINGS'),f.targets(''))
        f.flags.add('BERSERK_GRUNBELD_FLESH_FORM_ACTIVE')
        self.assertIn(tid('VISIBLE_SHELL'),f.targets(''));self.assertNotIn(tid('VISIBLE_HANDS'),f.targets(''))

    def test_save_reload_preserves_refusal_lie_and_item_receipt(self):
        f=Conversation();f.met();f.values.update(n_berserk_rickert_recruit_refused=1,u_berserk_rickert_eclipse_story=1,u_berserk_rickert_lied_before=1,u_berserk_rickert_arm_delivered=1)
        new=Conversation();new.values=json.loads(json.dumps(f.values));self.assertNotIn(tid('ROAD'),new.targets(''))
        self.assertEqual(new.values['u_berserk_rickert_lied_before'],1)
        self.assertEqual(new.values['u_berserk_rickert_arm_delivered'],1)

    def test_hurt_companion_does_not_claim_to_be_fine(self):
        f=Conversation();f.hp['torso']=30
        self.assertIn('hurt',f.line('COMPANION_STATE'))

    def test_modern_technology_needs_a_real_object_before_claiming_to_examine_it(self):
        f=Conversation();self.assertNotIn(tid('MODERN'),f.targets('MODERN_OFFER'))
        f.inventory['smart_phone']=1;f.choose('MODERN_OFFER','MODERN')
        f.inventory.clear();self.assertIn(tid('MODERN'),f.targets('MODERN_OFFER'))

    def test_companion_route_uses_only_selected_known_unfinished_goal(self):
        f=Conversation();self.assertIn('where we are going',f.line('COMPANION_ROUTE'))
        f.values['u_berserk_journal_goal']=2
        self.assertIn('where we are going',f.line('COMPANION_ROUTE'))
        f.values['u_berserk_journal_knows_breach']=1
        self.assertIn('retreat',f.line('COMPANION_ROUTE'))
        f.values['u_berserk_breach_sealed']=1
        self.assertIn('where we are going',f.line('COMPANION_ROUTE'))

    def test_all_refs_exist_no_traps_and_no_unsupported_dynamic_line_combinators(self):
        f=Conversation();all_ids={o['id'] for p in (MOD/'dialogue').glob('*.json') for o in json.loads(p.read_text()) if 'id' in o}
        ids=[x for x in f.topics if x.startswith(('TALK_BERSERK_RICKERT','TALK_BERSERK_APOSTOL_RICKERT'))]
        ids+=['TALK_BERSERK_GODO_ARM','TALK_BERSERK_GODO_ARM_STATUS','TALK_BERSERK_GODO_FITTING','TALK_BERSERK_GODO_SELF','TALK_BERSERK_GODO_PRAISE']
        for id in ids:
            row=f.topics[id]
            for n in walk(row['dynamic_line']):self.assertFalse(set(n)&{'and','or','not'},id)
            for n in walk(row):
                if 'test_eoc' in n:self.assertIn(n['test_eoc'],f.eocs)
            for r in row['responses']:
                if r['topic'].startswith('TALK_BERSERK'):self.assertIn(r['topic'],all_ids,(id,r['topic']))
            todo=[id];seen=set();out=False
            while todo:
                q=todo.pop()
                if q=='TALK_DONE':out=True;break
                if q in seen or q not in f.topics:continue
                seen.add(q);todo.extend(r['topic'] for r in f.topics[q]['responses'])
            self.assertTrue(out,id)

    def test_russian_has_no_author_stage_notes_or_untranslated_lines(self):
        with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:tr=gettext.GNUTranslations(stream)
        f=Conversation()
        for id,row in f.topics.items():
            if not id.startswith(('TALK_BERSERK_RICKERT','TALK_BERSERK_APOSTOL_RICKERT')):continue
            strings=[r['text'] for r in row['responses']]
            def collect(x):
                if isinstance(x,str):strings.append(x)
                elif isinstance(x,dict):
                    for k in ['yes','no']:collect(x.get(k))
            collect(row['dynamic_line'])
            for s in strings:
                self.assertNotEqual(s,tr.gettext(s),(id,s))
                self.assertNotRegex(tr.gettext(s),r'\[|\*\(|^\(|Запоминается|Условие:|Переход к|флаг|триггер|уровень доверия')


if __name__=='__main__':unittest.main()
