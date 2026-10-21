"""Exercise native-data state transitions; no CDDA clothing or rendering runtime."""
import json
import unittest
from pathlib import Path

from test_recovery_33 import MOD, StateGraph, load, walk
from test_rickert_dialogue_33 import Conversation


class ReturnGraph(StateGraph):
    def run(self,name):
        if name in ['EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL','EOC_BERSERK_APOSTOL_CONTINUATION_BEGIN','EOC_BERSERK_APOSTOL_APPLY_REFUSAL_SCAR']:
            return  # journal/mission/refusal-scar flows have their own suites.
        super().run(name)


class BodyRules(unittest.TestCase):
    def begin(self,path,line):
        f=StateGraph();f.values.update(u_berserk_apostol_schema=1,u_berserk_apostol_path=path,
            u_berserk_apostol_lineage=line,u_berserk_apostol_stage=1,u_berserk_apostol_return_state=2,
            u_berserk_eclipse_route=2 if path==1 else 1)
        return f

    def test_all_thirteen_actual_beginnings_restore_missing_hand_once(self):
        for line,prefix in enumerate(['VOID','SLAN','UBIK','CONRAD','FEMTO','COUNT_FLESH','WYALD_FLESH','ROSINE_FLESH','GRUNBELD_FLESH','COUNT_PAWN','WYALD_PAWN','ROSINE_PAWN','GRUNBELD_PAWN'],1):
            path=1 if line<6 else 2 if line<10 else 3
            with self.subTest(prefix=prefix):
                f=self.begin(path,line);f.bionics.add('bio_berserk_hand_stump')
                f.effects.update(['berserk_missing_left_hand','berserk_left_arm_onehanded'])
                f.run('EOC_BERSERK_APOSTOL_'+prefix+'_BEGIN')
                self.assertNotIn('bio_berserk_hand_stump',f.bionics);self.assertFalse(f.effects)
                self.assertEqual(f.values['u_berserk_apostol_left_hand_regrown'],1)
                n=sum('hand has grown back' in s for s in f.messages)
                self.assertEqual(n,1)
                f.run('EOC_BERSERK_APOSTOL_BODY_MIGRATE')
                self.assertEqual(sum('hand has grown back' in s for s in f.messages),1)

    def test_intact_hand_does_not_get_a_false_message_or_future_free_regrowth(self):
        f=self.begin(1,1);f.run('EOC_BERSERK_APOSTOL_VOID_BEGIN')
        self.assertEqual(f.values['u_berserk_apostol_body_checked'],1)
        self.assertEqual(f.values.get('u_berserk_apostol_left_hand_regrown',0),0)
        f.bionics.add('bio_berserk_hand_stump');f.run('EOC_BERSERK_APOSTOL_BODY_MIGRATE')
        self.assertIn('bio_berserk_hand_stump',f.bionics)

    def test_cannon_its_chamber_brand_eye_and_other_bionics_are_not_removed(self):
        f=self.begin(2,6);remaining={'bio_berserk_arm_cannon','bio_berserk_lost_eye','bio_berserk_brand_of_sacrifice','bio_tools'}
        f.bionics.update(remaining|{'bio_berserk_hand_stump'})
        f.run('EOC_BERSERK_APOSTOL_COUNT_FLESH_BEGIN')
        self.assertEqual(f.bionics,remaining);self.assertFalse(f.inventory)
        body=f.eocs['EOC_BERSERK_APOSTOL_FIRST_BODY_CHANGE']
        self.assertEqual([n['u_lose_bionic'] for n in walk(body) if 'u_lose_bionic' in n],['bio_berserk_hand_stump'])
        self.assertFalse(any('hp(' in n.get('math',[''])[0] for n in walk(body)))

    def test_refusal_scars_plain_mutagen_and_path_flags_are_not_a_body(self):
        for trait in ['BERSERK_ECLIPSE_SCAR_SIGHT','BERSERK_ECLIPSE_SCAR_TREMOR','THRESH_BEAST',None]:
            f=self.begin(1,1);f.bionics.add('bio_berserk_hand_stump')
            if trait:f.traits.add(trait)
            f.run('EOC_BERSERK_APOSTOL_FIRST_BODY_CHANGE')
            self.assertIn('bio_berserk_hand_stump',f.bionics)

    def test_guts_keeps_his_existing_story_anatomy(self):
        f=self.begin(1,1);f.overrides['EOC_BERSERK_FORGE_GUTS']=True
        f.bionics.add('bio_berserk_hand_stump');f.traits.add('BERSERK_VOID_SEED')
        f.run('EOC_BERSERK_APOSTOL_FIRST_BODY_CHANGE')
        self.assertIn('bio_berserk_hand_stump',f.bionics)

    def test_old_completed_forms_recover_without_restarting_growth(self):
        f=self.begin(2,9);f.values.update(u_berserk_apostol_stage=3,u_berserk_apostol_growth_running=0,u_berserk_apostol_started_at=20)
        f.traits.add('BERSERK_GRUNBELD_FLESH_FORM');f.bionics.add('bio_berserk_hand_stump')
        f.run('EOC_BERSERK_APOSTOL_BODY_MIGRATE')
        self.assertNotIn('bio_berserk_hand_stump',f.bionics)
        self.assertEqual(f.values['u_berserk_apostol_stage'],3)
        self.assertEqual(f.values['u_berserk_apostol_started_at'],20)
        self.assertEqual(f.values['u_berserk_apostol_growth_running'],0)

    def test_story_wounds_replay_does_not_cut_off_the_regrown_hand(self):
        f=self.begin(2,6);f.bionics.add('bio_berserk_hand_stump')
        f.run('EOC_BERSERK_APOSTOL_COUNT_FLESH_BEGIN')
        f.run('EOC_BERSERK_ECLIPSE_APPLY_STORY_WOUNDS')
        self.assertNotIn('bio_berserk_hand_stump',f.bionics)

    def test_regrown_hand_can_close_paid_order_without_second_device(self):
        for state in [1,2,3]:
            f=Conversation();f.met();f.values.update(u_berserk_godo_arm_state=state,u_berserk_apostol_left_hand_regrown=1)
            f.choose('ORDER_STATUS','ARM_REGROWN_ORDER');f.choose('ARM_REGROWN_ORDER','ARM_REFUNDED')
            self.assertEqual(f.inventory['steel_lump'],8 if state>=2 else 0)
            self.assertEqual(f.inventory['charcoal'],200 if state>=3 else 0)
            self.assertEqual(f.inventory['bio_berserk_arm_cannon'],0)
            self.assertEqual(f.values['u_berserk_godo_arm_state'],4)
            self.assertNotIn('TALK_BERSERK_RICKERT_ARM_REGROWN_ORDER',f.targets('ORDER_STATUS'))

    def test_all_forms_restrict_relevant_clothes_without_destroying_them(self):
        forms={r['id']:r for p in (MOD/'mutations').glob('apostol_*.json') for r in json.loads(p.read_text()) if r.get('id','').endswith('_FORM')}
        self.assertEqual(len(forms),13)
        for id,r in forms.items():
            self.assertFalse(r['destroys_gear'],id);self.assertTrue(r['restricts_gear'],id)
            self.assertFalse(r['purifiable'],id);self.assertFalse(r.get('active',False),id)
        for id in ['BERSERK_GRUNBELD_FLESH_FORM','BERSERK_GRUNBELD_PAWN_FORM']:
            self.assertIn('torso',forms[id]['restricts_gear']);self.assertTrue(forms[id]['allow_soft_gear'])
        for id in ['BERSERK_ROSINE_FLESH_FORM','BERSERK_FEMTO_FORM']:
            self.assertEqual(forms[id]['restricts_gear'],['torso']);self.assertFalse(forms[id]['allow_soft_gear'])

    def test_sprite_manifest_has_one_permanent_body_overlay_per_line(self):
        manifest=json.loads((MOD.parents[1]/'docs/apostol_sprite_manifest.json').read_text())
        self.assertEqual(len(manifest),13)
        for r in manifest:
            self.assertEqual(r['overlay'],'overlay_mutation_'+r['mutation'])
            self.assertTrue(r['permanent']);self.assertNotIn('_active_',r['overlay'])

    def test_lab_loot_extends_vanilla_and_has_no_eclipse_gate_or_invalid_charges(self):
        r=load('itemgroups/rare_arm_cannon.json')[0]
        self.assertEqual(r['copy-from'],r['id']);self.assertEqual(r['id'],'bionics')
        self.assertEqual(r['extend']['entries'],[{'item':'bio_berserk_arm_cannon','prob':1}])
        self.assertNotIn('condition',r)
        self.assertAlmostEqual(100/951,0.1051524711)

    def test_alternative_acceptance_and_refusal_both_enable_world_demons(self):
        world_eoc=load('effects/eclipse_era_eocs.json')[0]
        for outcome in [1,2]:
            f=ReturnGraph();f.values.update(u_berserk_apostol_return_state=1,u_berserk_apostol_landing_ok=1,
                u_berserk_eclipse_route=2,u_berserk_apostol_outcome=outcome,u_berserk_apostol_path=1 if outcome==1 else 0,
                u_berserk_apostol_lineage=1 if outcome==1 else 0,u_berserk_apostol_stage=1)
            f.overrides['EOC_BERSERK_APOSTOL_LANDING_SAFE']=True
            f.run('EOC_BERSERK_APOSTOL_RETURN_COMMIT')
            self.assertEqual(f.values['berserk_eclipse_era'],1)
            self.assertEqual(f.values['u_berserk_apostol_return_state'],2)
        # Actual world EOC does not require a Brand or the human route.
        text=json.dumps(world_eoc['condition'])
        self.assertIn('berserk_eclipse_era == 1',text)
        self.assertNotIn('bio_berserk_brand_of_sacrifice',text);self.assertNotIn('HUMAN_ROUTE',text)

    def test_old_alternative_completed_return_restores_only_world_era(self):
        for outcome in [1,2]:
            f=StateGraph();f.values.update(u_berserk_eclipse_route=2,u_berserk_apostol_return_state=2,u_berserk_apostol_outcome=outcome)
            f.run('EOC_BERSERK_APOSTOL_RESTORE_WORLD_ERA')
            self.assertEqual(f.values['berserk_eclipse_era'],1)
            self.assertFalse(f.inventory);self.assertFalse(f.messages)
        f=StateGraph();f.values.update(u_berserk_eclipse_route=2,u_berserk_apostol_return_state=1,u_berserk_apostol_outcome=1)
        f.run('EOC_BERSERK_APOSTOL_RESTORE_WORLD_ERA');self.assertEqual(f.values.get('berserk_eclipse_era',0),0)


class NativeTrust(unittest.TestCase):
    def confess(self,trust=0):
        f=Conversation();f.normal_return();f.met();f.npc['trust']=trust
        f.values.update(n_berserk_rickert_respect=1,u_berserk_rickert_eclipse_story=2)
        f.run('EOC_BERSERK_RICKERT_STORY_CONFESS')
        return f

    def test_confession_uses_real_npc_opinion_once(self):
        f=self.confess(6);self.assertEqual(f.npc['trust'],2)
        self.assertEqual(f.values['n_berserk_rickert_lie_trust_target'],6)
        f.run('EOC_BERSERK_RICKERT_STORY_CONFESS');self.assertEqual(f.npc['trust'],2)
        self.assertNotIn('TALK_BERSERK_RICKERT_JOINED',f.targets('ROAD_READY'))
        self.assertIn('TALK_BERSERK_RICKERT_ORDERS',f.targets(''))

    def test_four_honest_daily_conversations_restore_baseline_without_farming(self):
        f=self.confess()
        self.assertEqual(f.npc['trust'],-4)
        f.run('EOC_BERSERK_RICKERT_REBUILD_TRUST');self.assertEqual(f.npc['trust'],-4)
        for i in range(4):
            f.now+=86400;f.run('EOC_BERSERK_RICKERT_REBUILD_TRUST')
            self.assertEqual(f.npc['trust'],-3+i)
            f.run('EOC_BERSERK_RICKERT_REBUILD_TRUST');self.assertEqual(f.npc['trust'],-3+i)
        self.assertTrue(f.condition({'test_eoc':'EOC_BERSERK_RICKERT_TRUST_RESTORED'}))
        f.choose('ROAD_READY','JOINED');self.assertTrue(f.npc['following'])

    def test_native_trust_from_other_actions_also_counts(self):
        f=self.confess(8);f.npc['trust']=8
        self.assertFalse(f.condition({'test_eoc':'EOC_BERSERK_RICKERT_TRUST_RESTORED'}))
        f.now+=86400;self.assertTrue(f.condition({'test_eoc':'EOC_BERSERK_RICKERT_TRUST_RESTORED'}))

    def test_permanent_refusal_survives_trust_restoration_and_apology(self):
        f=self.confess();f.values['n_berserk_rickert_recruit_refused']=1
        f.npc['trust']=100;f.now+=86400;f.run('EOC_BERSERK_RICKERT_JOIN')
        self.assertFalse(f.npc['following'])
        f.choose('REFUSE_MENU','APOLOGY');self.assertEqual(f.values['n_berserk_rickert_recruit_refused'],1)

    def test_jobs_and_casual_talk_do_not_raise_relationship_score(self):
        f=self.confess();before=f.npc['trust']
        f.choose('PERSONAL','FEAR');f.choose('FEAR','FEAR_HELP')
        self.assertEqual(f.npc['trust'],before)
        f.safe=False;f.now+=86400;f.run('EOC_BERSERK_RICKERT_REBUILD_TRUST')
        self.assertEqual(f.npc['trust'],before)


if __name__=='__main__':unittest.main()
