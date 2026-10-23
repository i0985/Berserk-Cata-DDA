"""Execute approved Flora predicates and state transitions, not native CDDA."""
import copy
import json
import re
import unittest
from pathlib import Path
from test_reference_journal_33 import Book, EOCS, TOPICS, walk

E='EOC_BERSERK_FLORA33_'
P='TALK_BERSERK_FLORA_'
MOD=Path(__file__).resolve().parents[1]/'mods/Berserk'
def tid(s):return s if s.startswith('TALK_') else P+s

class Flora(Book):
    def __init__(self,late=True):
        super().__init__();self.om='berserk_flora_manor';self.health=100;self.present=True;self.fires=0
        self.values.update(berserk_flora_stage=1,berserk_eclipse_era=1,u_berserk_eclipse_rescue_state=2)
        if late:self.values.update({'berserk_hunt_'+s+'_state':4 for s in ['count','wyald','rosine']})
        self.overrides['EOC_BERSERK_FLORA_AT_REGISTERED_MANOR']=True
    def value(self,s):
        s=re.sub(r"u_hp_max\('[^']+'\)",'100',s)
        s=re.sub(r"u_hp\('[^']+'\)",str(self.health),s)
        s=re.sub(r"n_monsters_nearby\([^)]*\)",str(int(self.present)),s)
        return super().value(s)
    def condition(self,c):
        if c=='npc_is_monster':return self.present
        if isinstance(c,dict) and 'u_has_bionics' in c:return c['u_has_bionics'] in self.bionics
        return super().condition(c)
    def run(self,id_):
        # Physical map registration and siege map/AI are environment fixtures.
        # Eligibility, receipt, timer, pact outcome and dialogue run real JSON.
        if id_ in ['EOC_BERSERK_FLORA_REGISTER_HERE','EOC_BERSERK_FLORA_SYNC_MANOR_CENTER','EOC_BERSERK_FLORA_TREEHOUSE_REGISTER','EOC_BERSERK_LATE_FLORA_RECOVER']:return
        if id_=='EOC_BERSERK_FLORA_PREPARE_SIEGE':
            if self.condition(EOCS[id_]['condition']):self.values['berserk_flora_siege_state']=1
            return
        if id_=='EOC_BERSERK_FLORA_START_SIEGE':
            if self.condition(EOCS['EOC_BERSERK_FLORA_CAN_START_SIEGE']['condition']):
                self.values.update(berserk_flora_siege_state=2,berserk_flora_stage=2,u_berserk_ref_flora_attack=1)
            return
        if id_=='EOC_BERSERK_FLORA_APOSTLES_ARRIVE':self.fires+=1;self.values['berserk_flora_fire_phase']=2;return
        return super().run(id_)
    def text(self,s):return self.line(tid(s))
    def targets(self,s):return [r['topic'] for r in self.available(tid(s))]
    def pick(self,s,target):
        rs=[r for r in self.available(tid(s)) if r['topic']==tid(target)]
        assert len(rs)==1,(s,target,self.targets(s))
        r=rs[0]
        if 'effect' in r:self.effect(r['effect'])
        if tid(target) in TOPICS:self.enter(tid(target))

class FloraDialogue(unittest.TestCase):
    def test_marker_not_acquaintance_and_first_stranger_introduces(self):
        f=Flora();f.values['u_berserk_journal_knows_flora']=1
        self.assertIn(tid('INTRO_STRANGER'),f.targets('ENTER'))
        self.assertNotIn('TALK_BERSERK_FLORA',f.targets('ENTER'))
        f.pick('ENTER','INTRO_STRANGER')
        self.assertEqual(f.values['u_berserk_flora_met'],1)
        self.assertIn('TALK_BERSERK_FLORA',f.targets('ENTER'))
        self.assertNotIn('INTRO_STRANGER',f.targets('ENTER'))
    def test_guts_is_named_only_after_introduction(self):
        f=Flora();f.guts=True
        self.assertNotIn('Гатс',f.text('ENTER'))
        self.assertIn(tid('INTRO_GUTS'),f.targets('ENTER'))
        f.pick('ENTER','INTRO_GUTS');self.assertIn('Гатс',f.text('INTRO_GUTS'))
    def test_early_visit_has_peaceful_topics_without_armor_grant_or_continuation(self):
        f=Flora(late=False);f.values['berserk_eclipse_era']=0
        options=f.targets('TALK_BERSERK_FLORA')
        self.assertIn(tid('HOME'),options);self.assertIn(tid('WORLD'),options)
        self.assertNotIn(tid('ARMOR'),options)
        f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertFalse(f.inventory)
        self.assertNotEqual(f.values.get('u_berserk_flora33_queued'),1)
    def test_brand_topic_requires_actual_mark(self):
        f=Flora();self.assertNotIn(tid('BRAND'),f.targets('TALK_BERSERK_FLORA'))
        f.bionics.add('bio_berserk_brand_of_sacrifice');self.assertIn(tid('BRAND'),f.targets('TALK_BERSERK_FLORA'))
    def test_grant_schedules_three_seconds_closes_dialogue_and_fires_once(self):
        f=Flora();self.assertIn('TALK_DONE',f.targets('ARMOR_CONFIRM'))
        f.pick('ARMOR_CONFIRM','TALK_DONE')
        self.assertEqual(sum(f.inventory[x] for x in ['berserk_helmet','berserk_chestplate','berserk_gloves','berserk_armguards','berserk_legguards','berserk_boots']),6)
        self.assertEqual(f.values['u_berserk_flora33_due'],f.now+3)
        self.assertFalse(f.fires)
        f.now+=2;f.run(E+'DUE');self.assertFalse(f.fires)
        f=copy.deepcopy(f);f.now+=1;f.run(E+'DUE');self.assertEqual(f.fires,1)
        f.run(E+'DUE');self.assertEqual(f.fires,1)
    def test_partial_kit_gets_only_missing_pieces_and_no_repeat(self):
        f=Flora();f.inventory.update(berserk_helmet=1,berserk_boots=1)
        f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertEqual(f.inventory['berserk_helmet'],1)
        old=copy.deepcopy(f.inventory);f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertEqual(f.inventory,old)
    def test_full_owner_never_receives_duplicate_but_can_continue(self):
        f=Flora();f.full_armor=True
        self.assertNotIn(tid('OFFER'),f.targets('ARMOR'))
        actions=[r for r in f.available('TALK_BERSERK_FLORA') if r.get('effect')==[{'run_eocs':E+'QUEUE'}]]
        self.assertEqual(len(actions),1);f.effect(actions[0]['effect'])
        self.assertEqual(f.values['u_berserk_flora33_queued'],1)
    def test_demon_notice_has_three_answers_and_armor_is_forbidden(self):
        f=Flora();f.values.update(u_berserk_apostol_path=1,u_berserk_apostol_human_equipment_locked=1)
        f.traits.add('BERSERK_SLAN_FORM')  # Visible truth; hidden gifts now have a LIE trial.
        self.assertIn(tid('APOSTOL_PRIVATE'),f.targets('TALK_BERSERK_FLORA'))
        f.pick('TALK_BERSERK_FLORA','APOSTOL_PRIVATE')
        self.assertEqual(f.values['u_berserk_flora33_demon_noticed'],1)
        self.assertIn(tid('HOME'),f.targets('TALK_BERSERK_FLORA'))
        f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertFalse(f.inventory)
        f.run(E+'QUEUE');self.assertEqual(f.values['u_berserk_flora33_queued'],1)
    def test_refusal_is_human_and_can_get_armor(self):
        f=Flora();f.values.update(u_berserk_apostol_outcome=2,u_berserk_apostol_return_state=2)
        self.assertIn(tid('REFUSED'),f.targets('TALK_BERSERK_FLORA'))
        f.run('EOC_BERSERK_FLORA_GIVE_ARMOR');self.assertEqual(f.inventory['berserk_helmet'],1)
    def test_projection_requires_killed_projection_not_ownership_or_global_death(self):
        f=Flora();f.inventory['berserk_behelit']=1
        self.assertNotIn(tid('DANGER_PROJECTION'),f.targets('DANGERS'))
        f.values['_victim_type']='mon_zombie';f.run(E+'PROJECTION_KILL')
        self.assertNotIn(tid('DANGER_PROJECTION'),f.targets('DANGERS'))
        f.values['_victim_type']='mon_berserk_projection_count';f.run(E+'PROJECTION_KILL')
        self.assertIn(tid('DANGER_PROJECTION'),f.targets('DANGERS'))
        self.assertNotIn('послал',f.text('PROJECTION_ANSWER'))
    def test_no_mysterious_combat_experience_or_evacuation(self):
        f=Flora();self.assertNotIn(tid('ARMOR_USED'),f.targets('OWNED'))
        f.values['u_berserk_mode_state']=1;f.run(E+'ARMOR_COMBAT_CHARACTER_MELEE_ATTACKS_MONSTER')
        self.assertIn(tid('ARMOR_USED'),f.targets('OWNED'))
        self.assertNotRegex(f.text('SIEGE_FIGHT'),'эвакуац|кто выходит|жител')
    def test_departed_knight_is_not_offered_as_available(self):
        f=Flora();f.values['u_berserk_knight_farewell_confirmed']=1
        self.assertNotIn('спроси его',f.text('KNIGHT_PAST').lower())
    def test_pacts_complete_real_mission_without_death_seal_or_reward(self):
        for n,stem in enumerate(['count','wyald','rosine','grunbeld'],10):
            f=Flora(late=False);f.values.update(u_berserk_apostol_path=3,u_berserk_apostol_lineage=n,u_berserk_apostol_stage=3,u_berserk_apostol_schema=1)
            mission='MISSION_BERSERK_'+stem.upper();f.missions[mission]=(0,0,0)
            f.run('EOC_BERSERK_APOSTOL_'+stem.upper()+'_PAWN_SUSPEND_HUNT')
            self.assertEqual(f.finished,[(mission,True)]);self.assertFalse(f.inventory)
            self.assertEqual(f.values.get('berserk_apostle_'+stem+'_dead',0),0)
            self.assertEqual(f.values.get('berserk_hunt_'+stem+'_state',0),0)
            self.assertTrue(f.condition(EOCS['EOC_BERSERK_JOURNAL_DONE_'+stem.upper()]['condition']))
    def test_pact_opens_late_gate_with_two_other_closed_hunts(self):
        f=Flora();f.values['berserk_hunt_rosine_state']=1
        self.assertFalse(f.condition(EOCS[E+'LATE']['condition']))
        f.values['u_berserk_pact_resolved_rosine']=1
        self.assertTrue(f.condition(EOCS[E+'LATE']['condition']))
        f.sync();self.assertNotEqual(f.values.get('u_berserk_ref_dead_rosine'),1)
    def test_old_charm_cannot_start_or_repeat_attack(self):
        obj=json.loads((MOD/'items/flora_escape_charm.json').read_text())[0]
        self.assertEqual(obj['use_action']['effect_on_conditions'],[E+'CHARM'])
        f=Flora();f.run(E+'CHARM');self.assertFalse(f.fires)
    def test_all_targets_exist_and_no_author_metadata_is_spoken(self):
        for id_,obj in TOPICS.items():
            if not id_.startswith(P):continue
            for r in obj['responses']:
                self.assertTrue(r['topic']=='TALK_DONE' or r['topic'] in TOPICS,r)
            text=json.dumps(obj,ensure_ascii=False)
            self.assertNotRegex(text,'Условие:|Запоминается:|ВООБЩЕ БЫ|реальный выход|действительное место|что land')
        for obj in EOCS.values():
            if not obj['id'].startswith(E):continue
            for node in walk(obj):
                if isinstance(node.get('run_eocs'),str):self.assertIn(node['run_eocs'],EOCS)

if __name__=='__main__':unittest.main()
