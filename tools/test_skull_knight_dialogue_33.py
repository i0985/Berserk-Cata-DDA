"""Execute dialogue predicates and saved state; not a native CDDA playtest."""
import copy
import gettext
import json
import re
import unittest

from test_godo_dialogue_33 import Conversation as Base
from test_recovery_33 import MOD, walk


def tid(s):return s if s.startswith('TALK_') else 'TALK_BERSERK_SKULL_KNIGHT_'+s


class Conversation(Base):
    def __init__(self):
        super().__init__()
        for p in (MOD/'dialogue').glob('*.json'):
            for o in json.loads(p.read_text()):self.topics[o['id']]=o
        self.values.update(u_berserk_eclipse_rescue_state=2,u_berserk_eclipse_route=1,u_berserk_godo_rescue_relocated=1)
        self.health=100;self.rescuer=True;self.scheduled=[];self.calls=[];self.retired=0
    def evaluate(self,s):
        s=re.sub(r"u_hp\('[^']+'\)",str(self.health),s)
        s=re.sub(r"u_hp_max\('[^']+'\)",'100',s)
        s=re.sub(r"n_monsters_nearby\([^)]*\)",str(int(self.rescuer)),s)
        return super().evaluate(s)
    def condition(self,c):
        if isinstance(c,dict) and 'compare_string' in c:
            a,b=c['compare_string'];return a==self.values.get('u_'+b['u_val'])
        return super().condition(c)
    def run(self,name):
        self.calls.append(name)
        if name=='EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL':return
        super().run(name)
    def effect(self,x):
        if isinstance(x,dict):
            if 'npc_die' in x:
                assert 'remove_from_creature_tracker' not in x['npc_die']
                assert x['npc_die']['remove_corpse'] and x['npc_die']['supress_message']
                self.retired+=1;self.rescuer=False;return
            if 'u_add_var'in x:self.values['u_'+x['u_add_var']]=x['value'];return
            if 'run_eocs'in x and 'time_in_future'in x:self.scheduled.append(x['run_eocs']);return
        super().effect(x)
    def line(self,s):
        def resolve(x):
            if isinstance(x,str):return x
            if 'concatenate'in x:return ''.join(map(resolve,x['concatenate']))
            c={k:v for k,v in x.items() if k not in ['yes','no']}
            return resolve(x['yes'] if self.condition(c) else x['no'])
        return resolve(self.topics[tid(s)]['dynamic_line'])
    def available(self,s):return super().available(tid(s))
    def choose(self,s,target):return super().choose(tid(s),tid(target))
    def targets(self,s):return [r['topic'] for r in self.available(s)]


class Knight(unittest.TestCase):
    def test_guts_and_stranger_first_greeting_and_repeat(self):
        for guts in [True,False]:
            f=Conversation();f.overrides['EOC_BERSERK_FORGE_GUTS']=guts
            self.assertIn('swordsman' if guts else 'stand again',f.line('AFTER'))
            f.choose('AFTER','RESCUED');self.assertIn('something else',f.line('AFTER'))
            self.assertNotIn(tid('RESCUED'),f.targets('AFTER'))
            self.assertEqual(f.values.get('u_berserk_godo_personally_met',0),0)
            self.assertEqual(f.values.get('u_berserk_rickert_met',0),0)

    def test_fallback_rescue_does_not_invent_caregivers(self):
        f=Conversation();f.values['u_berserk_godo_rescue_relocated']=0
        self.assertIn('did not reach',f.line('RESCUED'));self.assertNotIn(tid('MASTERS'),f.targets('RESCUED'))

    def test_master_marker_is_not_rickert_acquaintance(self):
        f=Conversation();f.values['u_berserk_journal_knows_godo']=1
        self.assertIn('meet them',f.line('MASTERS'))
        f.values['u_berserk_godo_personally_met']=1
        self.assertIn('yet to meet him',f.line('MASTERS'))

    def test_help_is_exactly_one_reply_and_no_practical_category(self):
        f=Conversation();self.assertIn('saving your life',f.line('HELP'))
        self.assertEqual(f.targets('HELP'),[tid('AFTER')])
        self.assertNotIn(tid('PRACTICAL'),f.targets('AFTER'))

    def test_now_never_opens_the_book_or_calls_a_locator(self):
        f=Conversation();f.choose('AFTER','NOW')
        self.assertEqual(f.targets('NOW'),[tid('AFTER')]);self.assertFalse(f.calls)
        self.assertIn('forest hollow',f.line('NOW'))
        f.health=20;self.assertIn('wounds close',f.line('NOW'))

    def test_completed_first_hunt_does_not_send_back_after_clue_is_read(self):
        f=Conversation();f.values['u_berserk_first_hunt_done']=1
        self.assertIn('Examine',f.line('NOW'))
        f.values.update(u_berserk_journal_read_berserk_apostle_burned_clue=1,u_berserk_journal_knows_breach=1)
        self.assertIn('wound itself',f.line('NOW'))
        f.values['u_berserk_breach_sealed']=1
        self.assertIn('exhausted',f.line('NOW'))

    def test_brand_questions_require_the_real_mark(self):
        f=Conversation();self.assertNotIn(tid('BRAND'),f.targets('AFTER'))
        f.bionics.add('bio_berserk_brand_of_sacrifice');self.assertIn(tid('BRAND'),f.targets('AFTER'))
        f.values['u_berserk_refuge_ready']=1;self.assertIn('already begun',f.line('WARD'))

    def test_four_memories_require_studied_evidence_not_carried_keepsakes(self):
        f=Conversation();f.inventory['berserk_judeau_knife_hilt']=1
        self.assertNotIn(tid('MEMORIES'),f.targets('AFTER'))
        f.values['u_berserk_godo_witness_judeau']=1;f.inventory.clear()
        self.assertIn(tid('MEMORIES'),f.targets('AFTER'))
        self.assertIn(tid('MEMORY_JUDEAU'),f.targets('MEMORIES'))
        self.assertNotIn(tid('MEMORY_PIPPIN'),f.targets('MEMORIES'))
        f=copy.deepcopy(f);self.assertIn(tid('MEMORY_JUDEAU'),f.targets('MEMORIES'))

    def test_personal_memory_replies_only_for_guts(self):
        f=Conversation();self.assertNotIn(tid('MEMORY_PIPPIN_437'),f.targets('MEMORY_PIPPIN'))
        f.overrides['EOC_BERSERK_FORGE_GUTS']=True
        self.assertIn(tid('MEMORY_PIPPIN_437'),f.targets('MEMORY_PIPPIN'))
        self.assertNotIn(tid('MEMORY_GASTON_453'),f.targets('MEMORY_GASTON'))
        f.inventory['berserk_gaston_sewing_roll']=1
        self.assertIn(tid('MEMORY_GASTON_453'),f.targets('MEMORY_GASTON'))

    def test_projection_question_requires_actual_victory(self):
        f=Conversation();self.assertNotIn(tid('PROJECTIONS'),f.targets('GOD_HAND'))
        f.values['u_berserk_griffith_projection_defeated']=1
        self.assertIn(tid('PROJECTIONS'),f.targets('GOD_HAND'))

    def test_window_close_and_warning_do_not_remove_actor(self):
        f=Conversation();f.choose('AFTER','TALK_DONE')
        self.assertNotEqual(f.values.get('u_berserk_knight_farewell_confirmed'),1)
        f.choose('AFTER','FAREWELL');self.assertIn('continue my journey',f.line('FAREWELL'))
        f.choose('FAREWELL','AFTER');f.choose('AFTER','FAREWELL')
        self.assertIn('finished',f.line('FAREWELL'));self.assertFalse(f.scheduled)

    def test_confirmed_farewell_is_saved_once_without_extra_popup(self):
        f=Conversation();f.choose('AFTER','FAREWELL');f.choose('FAREWELL','FINAL')
        self.assertEqual(f.values['u_berserk_knight_farewell_confirmed'],1)
        self.assertEqual(f.retired,1);self.assertFalse(f.scheduled);self.assertFalse(f.messages)
        f.run('EOC_BERSERK_KNIGHT_FAREWELL');self.assertEqual(f.retired,1)
        self.assertIn('Live on',f.line('FINAL'))

    def test_farewell_cannot_remove_an_unrelated_actor_or_alternative_rescue(self):
        f=Conversation();f.rescuer=False;f.run('EOC_BERSERK_KNIGHT_FAREWELL');self.assertFalse(f.scheduled)
        f.rescuer=True;f.values['u_berserk_eclipse_route']=2
        f.run('EOC_BERSERK_KNIGHT_FAREWELL');self.assertFalse(f.scheduled)

    def test_archive_contains_only_heard_answers_and_survives_reload(self):
        f=Conversation();archive='TALK_BERSERK_JOURNAL_KNIGHT_ADVICE'
        self.assertNotIn('God Hand',f.line(archive))
        f.choose('AFTER','ECLIPSE');self.assertIn('harvest',f.line(archive))
        self.assertNotIn('God Hand',f.line(archive))
        self.assertNotIn('come every night',f.line(archive))
        f=copy.deepcopy(f);self.assertIn('harvest',f.line(archive))
        self.assertFalse(f.inventory)

    def test_reachable_topics_have_no_flora_spoiler_or_journal_transition(self):
        f=Conversation();seen=set();todo=[tid('AFTER')]
        while todo:
            s=todo.pop()
            if s in seen or s=='TALK_DONE':continue
            seen.add(s)
            self.assertIn(s,f.topics)
            for r in f.topics[s]['responses']:todo.append(r['topic'])
        self.assertFalse(any('FLORA' in s or s.startswith('TALK_BERSERK_JOURNAL') or s=='TALK_BERSERK_ROAD_JOURNAL' for s in seen))

    def test_all_new_strings_have_real_russian_translations(self):
        with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as f:translator=gettext.GNUTranslations(f)
        data=json.loads((MOD/'dialogue/skull_knight.json').read_text())
        texts=[]
        for obj in data:
            if obj['id'] in [tid('RESCUE'),tid('RESCUE_REPLY'),tid('VICTORY')]:continue
            for x in walk(obj):
                texts += [v for k,v in x.items() if k in ['dynamic_line','yes','no','text'] and isinstance(v,str) and v]
        self.assertGreater(len(texts),100)
        for s in texts:
            if s.startswith('TALK_'):continue
            ru=translator.gettext(s)
            self.assertRegex(ru,'[А-Яа-я]');self.assertNotIn('цензур',ru);self.assertNotIn('переход к',ru)


if __name__=='__main__':unittest.main()
