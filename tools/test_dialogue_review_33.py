"""Editorial and state regressions for the full 29 October dialogue review.

Fixtures execute generated topics/conditions; no native CDDA game is launched.
"""
import collections
import gettext
import json
import re
import unittest
from pathlib import Path

from test_reference_journal_33 import Book, TOPICS, EOCS, MOD, RUSSIAN, walk
from test_flora_dialogue_33 import Flora
from test_rickert_dialogue_33 import Conversation as Rickert
from test_skull_knight_dialogue_33 import Conversation as Knight
from validate_mod_assets import validate_dynamic_lines

ROOT = MOD.parents[1]
SPEC = json.loads((ROOT/'docs/dialogue_sources/dialogue-review-2026-10-29.json').read_text())


def strings(n):
    if isinstance(n,str): yield n
    elif isinstance(n,dict):
        for v in n.values():yield from strings(v)
    elif isinstance(n,list):
        for v in n:yield from strings(v)


class Editorial(unittest.TestCase):
    def test_every_recorded_correction_is_exported_and_translated(self):
        self.assertEqual(len(SPEC['patches']),99)
        for p in SPEC['patches']:
            body='\n'.join(strings(TOPICS[p['topic']]))
            # The four master-death pairs are deliberately joined into prose.
            self.assertIn(p['after_en'].strip(),body,p['topic'])
            if p['topic']!='TALK_BERSERK_REF_T01':
                self.assertEqual(RUSSIAN.gettext(p['after_en']),p['after_ru'],p['topic'])

    def test_all_nine_dialogue_files_keep_their_topics_and_valid_references(self):
        files=list((MOD/'dialogue').glob('*.json'))
        self.assertEqual(len(files),9)
        self.assertGreaterEqual(len(TOPICS),1134)
        for f in files:
            rows=json.loads(f.read_text());validate_dynamic_lines(f,rows)
            for topic in rows:
                self.assertTrue(topic.get('responses'),topic['id'])
                for r in walk(topic.get('responses')):
                    target=r.get('topic','')
                    if isinstance(target,str) and target.startswith('TALK_BERSERK_'):
                        self.assertIn(target,TOPICS,(topic['id'],target))

    def test_no_author_state_labels_remain_in_npc_prose(self):
        pattern=r'^(?:Ранен:|Без значительных изменений:|Впервые вернулся с Клеймом:|Получил доспех у неё:)'
        for topic in TOPICS.values():
            for text in strings(topic.get('dynamic_line')):
                self.assertIsNone(re.search(pattern,RUSSIAN.gettext(text)),topic['id'])

    def test_road_scenes_do_not_add_a_fake_speaker_name(self):
        for suffix in ['CARAVAN','SCOUT','CAMP']:
            for node in walk(TOPICS['TALK_BERSERK_ROAD_'+suffix]['dynamic_line']):
                for k,v in node.items():
                    if k in ['yes','no'] and isinstance(v,str):self.assertTrue(v.startswith('&'))
            line=TOPICS['TALK_BERSERK_ROAD_'+suffix]['dynamic_line']
            if isinstance(line,str):self.assertTrue(line.startswith('&'))

    def test_refusal_memories_and_pauses_are_narration(self):
        for name in ['VOID','SLAN','UBIK','CONRAD','FEMTO']:
            s=TOPICS['TALK_BERSERK_APOSTOL_'+name+'_REFUSE']['dynamic_line']['yes']['no']
            self.assertTrue(s.startswith('&'));self.assertIn('memory',s.lower())
        for name in ['CONRAD','FEMTO']:
            self.assertTrue(TOPICS['TALK_BERSERK_APOSTOL_'+name+'_PAUSE']['dynamic_line']['yes'].startswith('&'))

    def test_ubik_does_not_speak_the_players_question_or_confess_the_trick(self):
        text=TOPICS['TALK_BERSERK_APOSTOL_UBIK_LIE']['dynamic_line']['yes']
        self.assertNotIn('Can the gift be undone',text)
        ru=RUSSIAN.gettext(TOPICS['TALK_BERSERK_APOSTOL_VOID_MEMORY_BIASED']['dynamic_line']['yes'])
        self.assertNotIn('подсунули',ru)

    def test_rosine_does_not_promise_a_flight_ability_the_pawn_does_not_get(self):
        self.assertNotIn('wings',TOPICS['TALK_BERSERK_APOSTOL_ROSINE_PAWN_CHANGE']['dynamic_line'].lower())
        self.assertIn('ROSINE_PAWN_ACCEPT',json.dumps(TOPICS['TALK_BERSERK_APOSTOL_ROSINE_PAWN_DECISION']))


class Context(unittest.TestCase):
    def test_flora_no_longer_hides_armor_greeting_behind_known_brand(self):
        f=Flora();f.values.update(u_berserk_flora_met=1,u_berserk_flora33_greeted_brand=1,
                                  u_berserk_flora_armor_resolved=1)
        f.bionics.add('bio_berserk_brand_of_sacrifice');f.full_armor=True
        self.assertIn('справляешься с доспехом',f.text('ENTER'))
        f.full_armor=False;self.assertNotIn('справляешься с доспехом',f.text('ENTER'))

    def test_new_brand_greeting_is_acknowledged_once_and_wounds_take_priority(self):
        f=Flora();f.values['u_berserk_flora_met']=1;f.bionics.add('bio_berserk_brand_of_sacrifice')
        self.assertIn('С нашей прошлой встречи',f.text('ENTER'))
        f.enter('TALK_BERSERK_FLORA_ENTER')
        self.assertEqual(f.values['u_berserk_flora33_greeted_brand'],1)
        self.assertNotIn('С нашей прошлой встречи',f.text('ENTER'))
        f.health=20;self.assertIn('бережёшь рану',f.text('ENTER'))

    def test_knight_introduces_only_the_unmet_smith(self):
        f=Knight();f.values['u_berserk_rickert_met']=1
        text=f.line('MASTERS');self.assertIn('You know Rickert',text)
        self.assertNotIn('meet them for yourself',text)
        f.values.update(u_berserk_godo_personally_met=1,u_berserk_rickert_met=0)
        self.assertIn('You know Godot',f.line('MASTERS'))

    def test_wounded_greeting_does_not_consume_unspoken_brand_remark(self):
        f=Flora();f.values['u_berserk_flora_met']=1;f.bionics.add('bio_berserk_brand_of_sacrifice')
        f.health=20;f.enter('TALK_BERSERK_FLORA_ENTER')
        self.assertNotEqual(f.values.get('u_berserk_flora33_greeted_brand'),1)
        f.health=100;self.assertIn('С нашей прошлой встречи',f.text('ENTER'))

    def test_knight_first_advice_changes_only_for_an_actual_missing_hand(self):
        f=Knight();f.bionics.add('bio_berserk_hand_stump')
        self.assertIn('Speak to Rickert first',f.line('NOW'))
        self.assertIn('replacement hand',f.line('SUMMARY'))
        f.bionics.add('bio_berserk_arm_cannon')
        self.assertNotIn('Speak to Rickert first',f.line('NOW'))

    def test_rickert_crossbow_questions_are_mutually_exclusive(self):
        for guts in [False,True]:
            for after in [False,True]:
                f=Rickert();f.overrides['EOC_BERSERK_FORGE_GUTS']=guts
                f.overrides['EOC_BERSERK_FORGE_BEFORE_ECLIPSE']=not after
                targets=[r['topic'] for r in f.available('TALK_BERSERK_RICKERT_MECHANISMS')]
                self.assertEqual(sum(t in targets for t in ['TALK_BERSERK_RICKERT_INTRO_LOCK','TALK_BERSERK_RICKERT_GUTS_CROSSBOW']),1)

    def test_rickert_does_not_assume_self_crafting_was_one_handed(self):
        f=Rickert()
        self.assertNotIn('one hand',f.line('PRAISE_TRIES').lower())
        self.assertNotIn('one hand',f.line('PRAISE_ADAPT').lower())
        f.values['u_berserk_prosthesis_self_made_after_loss']=1
        # The original confirmed one-handed evaluation branch is retained.
        self.assertIn('hand',json.dumps(TOPICS['TALK_BERSERK_RICKERT_PRAISE']['dynamic_line']).lower())

    def test_flora_gives_practical_recovery_instead_of_repeating_two_lectures(self):
        f=Flora();line=f.text('ARMOR_RECOVER')
        self.assertIn('Очисти и перевяжи',line);self.assertIn('Поешь, попей и отдохни',line)
        self.assertNotEqual(line,f.text('ARMOR_HEAL')+'\n\n'+f.text('COST'))

    def test_four_known_dangers_get_distinct_state_neutral_answers(self):
        f=Flora();texts=[f.text('KNOWN_'+x) for x in ['COUNT','WYALD','ROSINE','GRUNBELD']]
        self.assertEqual(len(set(texts)),4)
        for text in texts:self.assertNotIn('go there again',text)

    def test_master_death_is_one_paragraph_and_old_generic_record_still_works(self):
        f=Book();f.values.update(u_berserk_ref_active_t01_33=1,u_berserk_ref_active_t01_35=1,
                                u_berserk_ref_active_t01_36=1)
        line=f.line('TALK_BERSERK_REF_T01')
        self.assertEqual(line.count('Граф мёртв.'),1)
        self.assertNotIn('Хозяин погиб.',line)
        self.assertNotIn('вы получили',line)
        f.values.update(u_berserk_ref_active_t01_35=0,u_berserk_ref_active_t01_36=0)
        self.assertIn('Хозяин погиб.',f.line('TALK_BERSERK_REF_T01'))


if __name__=='__main__':unittest.main()
