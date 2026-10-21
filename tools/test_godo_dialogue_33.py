"""Traverse the approved dialogue's actual JSON. Not a native CDDA run.

World registration, NPC presence and the safety of the forge are environment
fixtures. Dialogue predicates, memories, service transactions and rewards run
from the mod data; NPC iteration changes alpha exactly as native 0.I does.
"""
import collections
import copy
import gettext
import json
import re
import unittest

from test_recovery_33 import MOD, StateGraph, walk


def tid(s): return s if s.startswith('TALK_') else 'TALK_BERSERK_GODO'+('_'+s if s else '')


class Conversation(StateGraph):
    def __init__(self):
        super().__init__()
        self.topics={x['id']:x for x in json.loads((MOD/'dialogue/godo.json').read_text())}
        self.safe=True;self.flags=set();self.bionics=set();self.at_forge=True
        self.npc=None;self.npc_alpha=False;self.morale=[];self.missions=set()

    def evaluate(self,s):
        s=re.sub(r'has_var\((\w+)\)',lambda m:str(int(m[1] in self.values)),s)
        def variable(m):
            key=m[0]
            if self.npc_alpha and key.startswith('u_'):return str(self.npc.get(key[2:],0))
            return str(self.values.get(key,0))
        s=re.sub(r'\b(?:[un]_)?berserk_\w+\b',variable,s)
        return eval(s,{'__builtins__':{}},{'time':lambda x:self.now if x=='now' else 0,'min':min,'max':max})

    def condition(self,c):
        if isinstance(c,str):
            if c=='u_at_safe_space':return self.safe
            if c=='u_is_npc':return self.npc_alpha
            if c=='u_following':return bool(self.npc and self.npc.get('following'))
        if isinstance(c,dict):
            if 'u_has_flag' in c:return c['u_has_flag'] in self.flags
            if 'u_has_bionics' in c:return c['u_has_bionics'] in self.bionics
            if 'u_at_om_location' in c or 'npc_at_om_location' in c:return self.at_forge
            if 'u_has_class' in c:return self.npc_alpha and self.npc['class']==c['u_has_class']
            if 'u_has_mission' in c:return c['u_has_mission'] in self.missions
        return super().condition(c)

    def run(self,name):
        if name in ['EOC_BERSERK_GODO_BEGIN','EOC_BERSERK_GODO_ROUTE_MISSION']:
            return  # Physical forge registration is covered by its own suite.
        super().run(name)

    def effect(self,x):
        if isinstance(x,dict):
            if 'u_add_morale' in x:self.morale.append((x['u_add_morale'],x['bonus']));return
            if 'u_consume_item' in x:
                n=x.get('charges',x.get('count',1));assert self.inventory[x['u_consume_item']]>=n
                self.inventory[x['u_consume_item']]-=n;return
            if 'assign_mission' in x:self.missions.add(x['assign_mission']);return
            if 'finish_mission' in x:self.missions.discard(x['finish_mission']);return
            if 'u_run_npc_eocs' in x:
                if self.npc is not None:
                    self.npc_alpha=True
                    for id in x['u_run_npc_eocs']:self.run(id)
                    self.npc_alpha=False
                return
        super().effect(x)

    def line(self,topic):
        def resolve(x):
            if isinstance(x,str):return x
            c={k:v for k,v in x.items() if k not in ['yes','no']}
            return resolve(x['yes'] if self.condition(c) else x['no'])
        return resolve(self.topics[tid(topic)]['dynamic_line'])

    def available(self,topic):
        return [r for r in self.topics[tid(topic)]['responses'] if 'condition' not in r or self.condition(r['condition'])]

    def choose(self,topic,target):
        matches=[r for r in self.available(topic) if r['topic']==tid(target)]
        assert len(matches)==1,(topic,target,[r['topic'] for r in self.available(topic)])
        r=matches[0]
        if 'effect' in r:self.effect(r['effect'])
        next=r['topic']
        if next in self.topics and 'speaker_effect' in self.topics[next]:self.effect(self.topics[next]['speaker_effect']['effect'])
        return next

    def demon(self,path=1,line=1):
        self.values.update(u_berserk_apostol_schema=1,u_berserk_apostol_path=path,
                           u_berserk_apostol_lineage=line,u_berserk_apostol_stage=1,
                           u_berserk_apostol_return_state=2,u_berserk_eclipse_route=2)


class Dialogue(unittest.TestCase):
    def test_first_intro_requires_personal_conversation_not_road_marker(self):
        f=Conversation();f.values['u_berserk_journal_knows_godo']=1
        self.assertIn('bucket',f.line('ENTER'));self.assertFalse(f.condition({'test_eoc':'EOC_BERSERK_GODO_SMITH_ACQUAINTED'}))
        f.choose('ENTER','STRANGER');self.assertEqual(f.values['u_berserk_godo_personally_met'],1)
        self.assertEqual(f.values.get('u_berserk_rickert_met',0),0)
        self.assertIn('Back again',f.line('ENTER'))

    def test_guts_and_stranger_greetings_before_and_after(self):
        for after in [0,1]:
            f=Conversation();f.overrides['EOC_BERSERK_FORGE_GUTS']=True
            f.values['berserk_eclipse_era']=after
            self.assertIn('Guts',f.line('ENTER'));self.assertNotIn('strangers',f.line('ENTER'))
            if not after:self.assertNotIn('Griffith',[r['text'] for r in f.available('ENTER')])
        f=Conversation();f.values['berserk_eclipse_era']=1
        self.assertNotIn('carried',f.line('ENTER'));self.assertNotIn('wounds',f.line('ENTER'))

    def test_wake_scene_and_missing_hand_are_independent(self):
        f=Conversation();f.values.update(u_berserk_eclipse_rescue_state=2,u_berserk_godo_rescue_relocated=1)
        self.assertIn('I am Godot',f.line('ENTER'))
        f.choose('ENTER','WAKE_RIDER');self.assertIn('waiting outside',f.line('WAKE_RIDER'))
        self.assertEqual(f.values['u_berserk_godo_wake_greeted'],1)
        f.values['u_berserk_knight_farewell_confirmed']=1;self.assertIn('gone on his way',f.line('WAKE_RIDER'))
        f=Conversation();f.overrides['EOC_BERSERK_FORGE_GUTS']=True
        f.values.update(u_berserk_eclipse_rescue_state=2,u_berserk_godo_rescue_relocated=1)
        self.assertFalse(any('my hand' in r['text'] for r in f.available('ENTER')))
        f.bionics.add('bio_berserk_hand_stump')
        self.assertTrue(any('my hand' in r['text'] for r in f.available('ENTER')))

    def test_current_orders_hidden_when_none_and_status_is_exact(self):
        f=Conversation();self.assertNotIn(tid('ORDERS'),[r['topic'] for r in f.available('')])
        f.values['u_berserk_godo_early_state']=1
        self.assertIn(tid('ORDERS'),[r['topic'] for r in f.available('')])
        self.assertIn('200 charcoal',f.line('EARLY_STATUS'))
        f.values.update(u_berserk_godo_early_state=2,u_berserk_godo_early_ready_at=200)
        self.assertIn('does not like haste',f.line('EARLY_STATUS'))
        f.now=200;self.assertIn('Finished',f.line('EARLY_STATUS'))

    def test_early_delivery_uses_real_transaction_and_receipt_only_once(self):
        f=Conversation();f.inventory.update(steel_lump=4,hc_steel_lump=1,charcoal=200,leather=2)
        f.choose('EARLY_SWORD','EARLY_SWORD');self.assertEqual(f.values['u_berserk_godo_early_state'],1)
        f.choose('EARLY_SWORD','EARLY_DELIVERY');self.assertEqual(f.inventory['charcoal'],0)
        self.assertNotIn(tid('EARLY_DELIVERED'),[r['topic'] for r in f.available('EARLY_SWORD')])
        f.now+=43200;f.choose('EARLY_SWORD','EARLY_DELIVERED')
        self.assertEqual(f.inventory['true_guts_early_sword'],1)
        self.assertEqual(f.values['u_berserk_godo_early_delivered'],1)
        self.assertNotIn(tid('EARLY_DELIVERED'),[r['topic'] for r in f.available('EARLY_SWORD')])

    def test_refund_is_not_mistaken_for_personal_weapon_delivery(self):
        f=Conversation();f.values['u_berserk_godo_early_state']=2;f.inventory['true_guts_early_sword']=1
        f.run('EOC_BERSERK_GODO_EARLY_REFUND')
        self.assertEqual(f.values.get('u_berserk_godo_early_delivered',0),0)
        self.assertNotIn('worth the work',f.line('OWNER_GOOD'))

    def test_long_sword_installments_and_why_question_once(self):
        f=Conversation();f.values['berserk_eclipse_era']=1;f.inventory['steel_lump']=32
        f.choose('SWORD','SWORD')
        for _ in range(4):f.choose('SWORD','SWORD_DELIVERY')
        self.assertEqual(f.values['u_berserk_godo_sword_iron_given'],32)
        self.assertIn('600 charcoal',f.line('SWORD_STATUS'))
        f.inventory.update(hc_steel_lump=8,charcoal=600,leather=4)
        f.choose('SWORD','SWORD_DELIVERY');f.choose('SWORD','SWORD_WHY')
        self.assertNotIn(tid('SWORD_WHY'),[r['topic'] for r in f.available('SWORD')])
        f.now+=172800;f.choose('SWORD','SWORD_DELIVERED')
        self.assertEqual(f.inventory['true_guts_sword'],1)

    def test_hidden_gift_does_not_make_godot_omniscient_and_refund_survives(self):
        f=Conversation();f.demon();f.values.update(u_berserk_godo_sword_state=1,u_berserk_godo_sword_iron_given=8)
        self.assertNotIn('body',f.line(''))
        self.assertIn('tell me before we continue',f.line('SWORD'))
        f.choose('','TALK_BERSERK_APOSTOL_GODO')
        self.assertEqual(f.values['u_berserk_apostol_godo_told'],1)
        self.assertIn('no new blade',f.line('SWORD'))
        f.choose('TALK_BERSERK_APOSTOL_GODO','CHANGED_SWORD')
        f.choose('CHANGED_SWORD','REFUND_DONE')
        self.assertEqual(f.inventory['steel_lump'],8)
        self.assertEqual(f.inventory['true_guts_sword'],0)
        self.assertNotIn(tid('CHANGED_SWORD'),[r['topic'] for r in f.available('TALK_BERSERK_APOSTOL_GODO')])

    def test_visible_change_is_remembered_after_form_is_no_longer_shown(self):
        f=Conversation();f.demon();f.flags.add('BERSERK_VOID_FORM_ACTIVE')
        self.assertIn('body',f.line(''));f.run('EOC_BERSERK_GODO_DIALOGUE_SYNC');f.flags.clear()
        self.assertIn('body',f.line(''))

    def test_legacy_accepted_traits_can_be_disclosed_without_numeric_growth_fields(self):
        f=Conversation();f.traits.add('BERSERK_CONRAD_APOSTLE')
        f.values.update(u_berserk_godo_sword_state=1,u_berserk_godo_sword_iron_given=8)
        f.choose('','TALK_BERSERK_APOSTOL_GODO')
        self.assertTrue(f.condition({'test_eoc':'EOC_BERSERK_APOSTOL_GODO_KNOWS_GIFT'}))
        f.choose('TALK_BERSERK_APOSTOL_GODO','CHANGED_SWORD');f.choose('CHANGED_SWORD','REFUND_DONE')
        self.assertEqual(f.inventory['steel_lump'],8)

    def test_refusal_scars_remain_human_and_legacy_latch_recovers_narrowly(self):
        for t in ['HEARING','SIGHT','TREMOR','MEMORIES','DREAD']:
            f=Conversation();f.traits.add('BERSERK_ECLIPSE_SCAR_'+t)
            self.assertTrue(f.condition({'test_eoc':'EOC_BERSERK_APOSTOL_HUMAN_EQUIPMENT_ALLOWED'}))
            f.values.update(u_berserk_apostol_outcome=2,u_berserk_apostol_return_state=2,u_berserk_apostol_human_equipment_locked=1)
            f.run('EOC_BERSERK_GODO_REPAIR_REFUSAL_CLASSIFICATION')
            self.assertEqual(f.values['u_berserk_apostol_human_equipment_locked'],0)
            f.demon();f.values['u_berserk_apostol_human_equipment_locked']=1
            f.run('EOC_BERSERK_GODO_REPAIR_REFUSAL_CLASSIFICATION')
            self.assertEqual(f.values['u_berserk_apostol_human_equipment_locked'],1)

    def test_copy_praise_requires_proven_crafting_not_possession(self):
        f=Conversation();f.inventory['forged_guts_early_sword']=1
        self.assertNotIn(tid('COPY_SELF'),[r['topic'] for r in f.available('WORK')])
        f.run('EOC_BERSERK_GODO_RECORD_EARLY_COPY')
        self.assertIn(tid('COPY_SELF'),[r['topic'] for r in f.available('WORK')])
        f.inventory.clear();self.assertNotIn(tid('COPY_SELF'),[r['topic'] for r in f.available('WORK')])

    def test_rickert_report_reads_the_actual_npc_not_godots_variables(self):
        f=Conversation();f.values['n_berserk_rickert_recruit_refused']=1
        f.run('EOC_BERSERK_GODO_DIALOGUE_SYNC')
        self.assertEqual(f.values['berserk_godo_rickert_refused'],0)
        f.npc={'class':'NC_BERSERK_RICKERT','following':True,'berserk_rickert_recruit_refused':0}
        f.run('EOC_BERSERK_GODO_DIALOGUE_SYNC');self.assertIn(tid('APPRENTICE_TRAVEL'),[r['topic'] for r in f.available('APPRENTICE_MENU')])
        f.npc.update(following=False,berserk_rickert_recruit_refused=1)
        f.run('EOC_BERSERK_GODO_DIALOGUE_SYNC');self.assertIn(tid('APPRENTICE_REFUSAL'),[r['topic'] for r in f.available('APPRENTICE_MENU')])
        f.npc=None;f.run('EOC_BERSERK_GODO_DIALOGUE_SYNC')
        self.assertNotIn(tid('APPRENTICE_TRAVEL'),[r['topic'] for r in f.available('APPRENTICE_MENU')])

    def test_grief_truth_lie_and_silence_do_not_mix(self):
        for n in [1,2,3]:
            f=Conversation();f.values['u_berserk_rickert_eclipse_story']=n
            choices=[r['topic'] for r in f.available('APPRENTICE_GRIEF')]
            self.assertEqual(tid('APPRENTICE_GRIEF_WORDS') in choices,n==1)
            self.assertEqual(tid('APPRENTICE_GRIEF_WAIT') in choices,n>=2)
        f=Conversation();self.assertNotIn('lost his companions',f.line('APPRENTICE_HOME'))

    def test_trauma_needs_personal_witness_and_does_not_invent_dead_friends(self):
        f=Conversation();f.values['berserk_eclipse_era']=1
        self.assertNotIn(tid('TRAUMA'),[r['topic'] for r in f.available('PERSONAL')])
        f.values['u_berserk_eclipse_rescue_state']=2
        self.assertIn(tid('TRAUMA'),[r['topic'] for r in f.available('PERSONAL')])
        self.assertFalse(any(r['topic'].startswith(tid('MEMORY_')) for r in f.available('TRAUMA_VOICES')))
        f.values['u_berserk_godo_witness_judeau']=1
        self.assertIn(tid('MEMORY_JUDEAU'),[r['topic'] for r in f.available('TRAUMA_VOICES')])
        f.run('EOC_BERSERK_GODO_END_TRAUMA');f.run('EOC_BERSERK_GODO_END_TRAUMA')
        self.assertEqual(len(f.morale),1)

    def test_sparks_defer_does_not_close_and_dismiss_is_permanent(self):
        f=Conversation();f.values['u_berserk_godo_hearth_trust']=1
        f.choose('SPARKS_INVITE','SPARKS_LATER')
        self.assertIn(tid('SPARKS_INVITE'),[r['topic'] for r in f.available('HEARTH')])
        f.choose('SPARKS_INVITE','SPARKS');f.choose('SPARKS','SPARKS_DISMISSED')
        self.assertNotIn(tid('SPARKS_INVITE'),[r['topic'] for r in f.available('HEARTH')])
        self.assertFalse(f.morale)

    def test_sparks_four_contexts_finish_once_and_save_reload(self):
        for kind,target in [('human','SPARKS_HUMAN'),('guts_before','SPARKS_GUTS_BEFORE'),('guts_after','SPARKS_GUTS_AFTER'),('demon','SPARKS_DEMON')]:
            f=Conversation();f.values['u_berserk_godo_hearth_trust']=1
            if kind.startswith('guts'):f.overrides['EOC_BERSERK_FORGE_GUTS']=True
            if kind=='guts_after':f.values['berserk_eclipse_era']=1
            if kind=='demon':f.demon();f.values['u_berserk_apostol_godo_told']=1
            f.choose('SPARKS_INVITE','SPARKS');f.choose('SPARKS','SPARKS_WORK');f.choose('SPARKS_WORK','SPARKS_IRON');f.choose('SPARKS_IRON','SPARKS_PEOPLE')
            self.assertIn(tid(target),[r['topic'] for r in f.available('SPARKS_PEOPLE')])
            if kind=='guts_before':f.choose('SPARKS_PEOPLE',target);f.choose(target,'SPARKS_GUTS_PEACE');last='SPARKS_GOAL';f.choose('SPARKS_GUTS_PEACE',last)
            elif kind=='guts_after':f.choose('SPARKS_PEOPLE',target);f.choose(target,'SPARKS_GUTS_ALIVE');last='SPARKS_FIGHT';f.choose('SPARKS_GUTS_ALIVE',last)
            else:f.choose('SPARKS_PEOPLE',target);last='SPARKS_SAFE' if kind=='human' else 'SPARKS_SURVIVE';f.choose(target,last)
            f.choose(last,'SPARKS_END');self.assertEqual(len(f.morale),1)
            loaded=Conversation();loaded.values=json.loads(json.dumps(f.values));loaded.run('EOC_BERSERK_GODO_FINISH_SPARKS')
            self.assertFalse(loaded.morale);self.assertIn(tid('SPARKS_RECALL'),[r['topic'] for r in loaded.available('HEARTH')])

    def test_major_navigation_is_still_available_after_backtracking(self):
        f=Conversation();f.choose('HEARTH','KEEP_FORGING');f.choose('KEEP_FORGING','HEARTH')
        self.assertIn(tid('KEEP_FORGING'),[r['topic'] for r in f.available('HEARTH')])
        f.choose('HEARTH','KEEP_FORGING');f.choose('KEEP_FORGING','KEEP_REASON');f.choose('KEEP_REASON','KEEP_UNDERSTAND')
        self.assertIn(tid('SPARKS_INVITE'),[r['topic'] for r in f.available('KEEP_UNDERSTAND')])

    def test_every_public_topic_has_a_structural_route_out_and_valid_references(self):
        f=Conversation();rows=f.topics
        all_ids={o['id'] for p in (MOD/'dialogue').glob('*.json')
                 for o in json.loads(p.read_text()) if isinstance(o,dict) and 'id' in o}
        for id,row in rows.items():
            for r in row['responses']:
                if r['topic'].startswith('TALK_BERSERK_'):self.assertIn(r['topic'],all_ids,(id,r['topic']))
            if not id.startswith(('TALK_BERSERK_GODO','TALK_BERSERK_APOSTOL_GODO')):continue
            todo=[id];seen=set();found=False
            while todo:
                q=todo.pop()
                if q=='TALK_DONE':found=True;break
                if q in seen or q not in rows:continue
                seen.add(q);todo += [r['topic'] for r in rows[q]['responses']]
            self.assertTrue(found,id)
        for p in [MOD/'dialogue/godo.json',MOD/'effects/godo_dialogue_33_eocs.json']:
            for n in walk(json.loads(p.read_text())):
                if 'test_eoc' in n:self.assertIn(n['test_eoc'],f.eocs)

    def test_russian_text_has_no_author_notes_or_untranslated_new_lines(self):
        with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:tr=gettext.GNUTranslations(stream)
        f=Conversation()
        for id,row in f.topics.items():
            if not id.startswith(('TALK_BERSERK_GODO','TALK_BERSERK_APOSTOL_GODO')):continue
            strings=[r['text'] for r in row['responses']]
            def collect(x):
                if isinstance(x,str):strings.append(x)
                elif isinstance(x,dict):
                    for k in ['yes','no']:collect(x.get(k,[]))
            collect(row['dynamic_line'])
            for en in strings:
                ru=tr.gettext(en)
                self.assertNotEqual(en,ru,(id,en))
                self.assertNotRegex(ru,r'→|\[|Механика|ВЫБОР|Разговор закрывается|бафф|скрипт|триггер|Переход к окну')


if __name__=='__main__':unittest.main()
