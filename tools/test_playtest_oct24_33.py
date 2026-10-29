"""Owner's October 24 regressions. JSON execution, not a native game test.

Unlike earlier fixtures, death alpha may be null/NPC/monster, beta is the
dying monster, and explicit empty beta really removes it from child calls.
World selection is an environment fixture; ring/forest checks validate the
native target parameters, not actual overmap generation or walking time.
"""
import copy
import gettext
import json
import re
import unittest

from test_reference_journal_33 import Book, EOCS, TOPICS, MOD, walk
from test_godo_dialogue_33 import Conversation as Godo
from test_rickert_dialogue_33 import Conversation as Rickert

P = 'EOC_BERSERK_FIX24_'
PARTS = 'head eyes mouth torso arm_l arm_r hand_l hand_r leg_l leg_r foot_l foot_r'.split()


class StrictActors(Book):
    def __init__(self, killer='avatar'):
        super().__init__()
        self.actor = killer
        self.beta = 'monster'
        self.beta_pos = (-17, 71, 0)
        self.hp = {p: 0 for p in PARTS}
        self.drops = []
        self.actor_scopes = []
        self.values['berserk_eclipse_era'] = 1

    def condition(self, c):
        if isinstance(c, str):
            if c == 'has_alpha': return self.actor is not None
            if c == 'has_beta': return self.beta is not None
            if c == 'npc_is_monster':
                assert self.beta is not None, 'invalid beta talker'
                return self.beta == 'monster'
            if c == 'u_is_monster': return self.actor == 'monster'
            if c == 'u_is_npc': return self.actor == 'npc'
        return super().condition(c)

    def value(self, expr):
        if re.search(r'\bn_(?:val|hp|npc_)', expr):
            assert self.beta is not None, 'invalid beta math'
        expr = re.sub(r"u_hp_max\('([^']+)'\)", '100', expr)
        expr = re.sub(r"u_hp\('([^']+)'\)", lambda m: str(self.hp[m[1]]), expr)
        return super().value(expr)

    def effect(self, x):
        if isinstance(x, dict):
            if 'run_eocs' in x:
                old_actor, old_beta = self.actor, self.beta
                # Native f_run_eocs copies context. Global/u writes persist;
                # context written by a child does not overwrite its caller.
                context = {k:v for k,v in self.values.items() if k.startswith('_')}
                if x.get('alpha_talker') == 'avatar': self.actor = 'avatar'
                if x.get('beta_talker') == '': self.beta = None
                self.run(x['run_eocs'])
                for k in list(self.values):
                    if k.startswith('_'): del self.values[k]
                self.values.update(context)
                self.actor, self.beta = old_actor, old_beta
                return
            if 'npc_location_variable' in x:
                assert self.beta is not None, 'invalid beta location'
            if 'u_run_npc_eocs' in x:
                # No party NPC in this death fixture; no fake beta supplied.
                return
            if 'location_variable_adjust' in x:
                var = x['location_variable_adjust']; v = self.getvar(var)
                k, name = next(iter(var.items()))
                key = {'u_val':'u_', 'global_val':'', 'context_val':'_'}[k] + name
                scale=24 if x.get('overmap_tile') else 1
                self.values[key]=(v[0]+x.get('x_adjust',0)*scale,
                    v[1]+x.get('y_adjust',0)*scale,
                    x.get('z_adjust',0) if x.get('z_override') else v[2]+x.get('z_adjust',0))
                return
            if 'assign_mission' in x:
                definitions={m['id']:m for p in (MOD/'missions').glob('*.json') for m in json.loads(p.read_text())}
                id_=x['assign_mission'];self.missions[id_]=self.getvar(definitions[id_]['start']['assign_mission_target']['var'])
                return
            if 'map_spawn_item' in x:
                self.drops.append((x['map_spawn_item'], self.getvar(x['loc'])))
                return
            if 'reveal_map' in x: return
            if 'u_lose_trait' in x: self.traits.discard(x['u_lose_trait']); return
            if 'u_lose_effect' in x or 'u_cast_spell' in x: return
            if 'math' in x:
                expr = x['math'][0]
                m = re.fullmatch(r"u_hp\('([^']+)'\) = (.+)", expr)
                if m:
                    self.hp[m[1]] = self.value(m[2]); return
                if expr.startswith(('u_vitamin(', 'u_pain(', 'u_val(')): return
        return super().effect(x)

    def run(self, id_):
        self.actor_scopes.append((id_, self.actor, self.beta))
        return super().run(id_)


class DeathScope(unittest.TestCase):
    def test_each_final_death_for_every_native_killer_has_no_invalid_beta(self):
        for boss in ['COUNT','WYALD','ROSINE','GRUNBELD']:
            for killer in ['avatar','npc','monster',None]:
                with self.subTest(boss=boss,killer=killer):
                    f=StrictActors(killer)
                    f.run('EOC_BERSERK_APOSTOL_'+boss+'_FLESH_DEATH_'+boss+'_DIES')
                    self.assertEqual(f.drops, [('berserk_apostol_'+boss.lower()+'_flesh', f.beta_pos)])
                    self.assertEqual(f.values['berserk_hunt_'+boss.lower()+'_state'],3)
                    if boss=='COUNT':self.assertEqual(f.values['berserk_hunt_count_location'],(-24,48,0))
                    downstream=False
                    for id_,alpha,beta in f.actor_scopes:
                        if id_==P+boss+'_DIES_AVATAR':downstream=True
                        if downstream:self.assertEqual((alpha,beta),('avatar',None),id_)

    def test_reload_and_duplicate_death_do_not_issue_another_flesh_or_reward(self):
        f=StrictActors();id_='EOC_BERSERK_APOSTOL_WYALD_FLESH_DEATH_WYALD_DIES'
        f.run(id_);old_inventory=copy.deepcopy(f.inventory)
        f.values=json.loads(json.dumps(f.values));f.run(id_)
        self.assertEqual(len(f.drops),1);self.assertEqual(f.inventory,old_inventory)

    def test_no_beta_means_death_wrapper_does_nothing(self):
        f=StrictActors();f.beta=None
        f.run('EOC_BERSERK_APOSTOL_WYALD_FLESH_DEATH_WYALD_DIES')
        self.assertFalse(f.drops);self.assertNotIn('berserk_apostle_wyald_dead',f.values)

    def test_legacy_public_death_without_any_victim_does_not_fake_victory(self):
        for name in ['COUNT','WYALD','ROSINE','GRUNBELD']:
            f=StrictActors();f.beta=None
            f.run('EOC_BERSERK_'+name+'_DIES')
            self.assertFalse(f.drops)
            self.assertNotIn('berserk_hunt_'+name.lower()+'_state',f.values)

    def test_grunbeld_withdrawal_does_not_create_flesh(self):
        # Preserve the siege's withdrawal guard; first knight phase still
        # uses its separate transformation handler, never this wrapper.
        f=StrictActors();f.values['berserk_grunbeld_grove_withdrawn']=1
        f.run('EOC_BERSERK_APOSTOL_GRUNBELD_FLESH_DEATH_FLORA_GRUNBELD_DIES')
        self.assertFalse(f.drops)
        monster=json.loads((MOD/'monsters/apostle_grunbeld.json').read_text())
        knight=next(x for x in monster if 'KNIGHT_DIES' in json.dumps(x.get('death_function',{})))
        self.assertNotIn('FLESH_DEATH',json.dumps(knight['death_function']))


class RecoveryAndMissions(unittest.TestCase):
    def rescued(self):
        f=StrictActors();f.beta=None
        f.values.update(u_berserk_eclipse_rescue_state=2)
        f.bionics.update(['bio_berserk_hand_stump','bio_berserk_lost_eye'])
        f.traits.add('BERSERK_BRAND')
        return f

    def test_rescue_restores_all_major_and_minor_hp_once_without_undoing_story(self):
        f=self.rescued();before=set(f.bionics)
        f.run('EOC_BERSERK_ECLIPSE_RETURN_RECOVER')
        self.assertTrue(all(v==100 for v in f.hp.values()),f.hp)
        self.assertEqual(f.bionics,before);self.assertIn('BERSERK_BRAND',f.traits)
        f.hp['eyes']=4;f.hp['arm_r']=9;f.run('EOC_BERSERK_ECLIPSE_RETURN_RECOVER')
        self.assertEqual((f.hp['eyes'],f.hp['arm_r']),(4,9))

    def test_old_save_repair_is_only_at_forge_before_first_hunt_and_once(self):
        f=self.rescued();f.values['u_berserk_eclipse_return_recovered']=1
        f.om='field';f.run(P+'OLD_RESCUE_ANATOMY');self.assertEqual(f.hp['eyes'],0)
        f.om='berserk_godo_workshop';f.run(P+'OLD_RESCUE_ANATOMY');self.assertEqual(f.hp['eyes'],100)
        f.hp['eyes']=0;f.run(P+'OLD_RESCUE_ANATOMY');self.assertEqual(f.hp['eyes'],0)
        f=self.rescued();f.values.update(u_berserk_eclipse_return_recovered=1,u_berserk_first_hunt_done=1)
        f.om='berserk_godo_workshop';f.run(P+'OLD_RESCUE_ANATOMY');self.assertEqual(f.hp['eyes'],0)

    def test_missing_hand_gets_real_optional_target_without_a_book(self):
        f=self.rescued();pos=(1200,2400,0);f.values['berserk_godo_location']=pos
        f.run(P+'HAND_GOAL');self.assertEqual(f.missions['MISSION_BERSERK_RECOVERY_HAND'],pos)
        f.bionics.add('bio_berserk_arm_cannon');f.run(P+'HAND_GOAL')
        self.assertNotIn('MISSION_BERSERK_RECOVERY_HAND',f.missions)
        f.bionics.remove('bio_berserk_arm_cannon');f.run(P+'HAND_GOAL')
        self.assertNotIn('MISSION_BERSERK_RECOVERY_HAND',f.missions)
        self.assertNotIn('berserk_campaign_journal',f.inventory)
        self.assertNotIn('recovery_hand',json.dumps(EOCS['EOC_BERSERK_FIRST_HUNT_REQUEST']))

    def test_intact_hand_or_installed_device_gets_no_prosthesis_mission(self):
        for has_hand,installed in [(True,False),(False,True)]:
            f=self.rescued();f.values['berserk_godo_location']=(0,0,0)
            if has_hand:f.bionics.clear()
            if installed:f.bionics.add('bio_berserk_arm_cannon')
            f.run(P+'HAND_GOAL');self.assertFalse(f.missions)

    def test_mission_completion_explains_examination_and_collecting_relic(self):
        missions={x['id']:x for p in (MOD/'missions').glob('*.json') for x in json.loads(p.read_text())}
        for name in ['BREACH','COUNT','WYALD','ROSINE','GRUNBELD']:
            d=missions['MISSION_BERSERK_'+name]['description'].lower()
            self.assertIn('examine',d);self.assertIn('close',d)
        self.assertIn('surviving trail',missions['MISSION_BERSERK_FIRST_HUNT']['description'])


class WorldAndConversations(unittest.TestCase):
    def test_story_sites_not_natural_and_manual_finders_require_eclipse(self):
        for file in ['apostle_count','wyald_rosine_hunts','grunbeld_hunt','first_hunt','local_breach','flora_manor']:
            for x in json.loads((MOD/'overmap'/f'{file}.json').read_text()):
                if x['type']=='overmap_special':self.assertEqual(x['occurrences'],[0,0],x['id'])
        f=Book();f.values['berserk_eclipse_era']=0
        for name in ['COUNT','WYALD','ROSINE','BREACH']:
            self.assertFalse(f.condition(EOCS['EOC_BERSERK_'+name+'_FIND']['condition']))

    def test_four_behelit_sites_are_ten_times_rarer_but_retained(self):
        sites=[x for x in json.loads((MOD/'overmap/behelit_sites.json').read_text()) if x['type']=='overmap_special']
        self.assertEqual(len(sites),4)
        for x in sites:
            self.assertEqual(x['occurrences'],[1,100]);self.assertIn('OVERMAP_UNIQUE',x['flags'])

    def test_new_single_omt_sites_use_native_special_placement(self):
        calls=[x for x in walk(EOCS[P+'FIRST_CREATE']) if 'target_params' in x]
        calls += [x for x in walk(EOCS['EOC_BERSERK_BREACH_FIND']) if 'target_params' in x]
        for x in calls:
            params=x['target_params']
            self.assertEqual(params['min_distance'],0);self.assertEqual(params['search_range'],96)
            self.assertIn('om_special',params);self.assertNotIn('om_terrain_replace',params)
            self.assertNotIn('cant_see',params);self.assertTrue(params['random'])
            maps=[m for p in (MOD/'mapgen').glob('*.json') for m in json.loads(p.read_text()) if m.get('om_terrain')]
            self.assertTrue(any(params['om_terrain'] in m['om_terrain'] for m in maps))
        # Persisted targets are checked before native creation, never moved.
        request=EOCS['EOC_BERSERK_FIRST_HUNT_REQUEST']['effect']
        self.assertIn({'overmap_at_point':'berserk_first_hunt_lair','point':{'u_val':'berserk_first_hunt_location'}},
                      [x for x in walk(request)])

    def test_known_first_lair_is_reused_even_inside_the_new_exclusion_ring(self):
        f=StrictActors();f.beta=None;pos=(24,0,0)
        f.values.update(u_berserk_eclipse_rescue_state=2,u_berserk_first_hunt_location=pos)
        f.terrain[pos]='berserk_first_hunt_lair'
        f.run('EOC_BERSERK_FIRST_HUNT_REQUEST')
        self.assertEqual(f.values['u_berserk_first_hunt_location'],pos)
        self.assertNotIn('EOC_BERSERK_FIRST_HUNT_LOCATE',f.calls)
        self.assertEqual(f.missions['MISSION_BERSERK_FIRST_HUNT'],pos)

    def test_rickert_topic_never_only_back_and_never_replaces_truth_or_lie(self):
        for story in [-1,0,1,2,3,4,5]:
            f=Rickert();f.values.update(u_berserk_eclipse_rescue_state=2,u_berserk_rickert_eclipse_story=story)
            replies=f.available('TALK_BERSERK_RICKERT_ECLIPSE')
            self.assertGreater(len(replies),1,story)
            if story not in [1,2]:
                self.assertTrue(any('STORY_TRUTH' in json.dumps(r) for r in replies),story)
            else:
                self.assertFalse(any('STORY_TRUTH' in json.dumps(r.get('effect',{})) for r in replies),story)
        f=Rickert();self.assertGreater(len(f.available('TALK_BERSERK_RICKERT_ECLIPSE')),1)

    def test_godo_listens_to_guts_story_instead_of_reciting_biographies(self):
        f=Godo();f.overrides['EOC_BERSERK_FORGE_GUTS']=True
        for name in ['JUDEAU','PIPPIN','CORKUS','GASTON']:
            r=next(r for r in f.available('TRAUMA_VOICES') if r['topic']=='TALK_BERSERK_GODO_MEMORY_'+name)
            self.assertGreater(len(r['text']),60)
            self.assertGreater(len(f.available('MEMORY_'+name)),2)
        f.overrides['EOC_BERSERK_FORGE_GUTS']=False
        self.assertFalse(any('MEMORY_' in r['topic'] for r in f.available('TRAUMA_VOICES')))
        f.values['u_berserk_godo_witness_judeau']=1
        r=next(r for r in f.available('TRAUMA_VOICES') if 'MEMORY_' in r['topic'])
        self.assertIn('did not know him',r['text'])
        self.assertIn('Neither of us knew',f.line('MEMORY_JUDEAU'))
        self.assertFalse(any('voices' in r['text'] for r in f.available('MEMORY_JUDEAU')))
        f.values['berserk_rickert_dead']=1
        self.assertNotIn('Tell the boy',f.line('MEMORY_KEEP'))

    def test_new_english_texts_have_russian_translations(self):
        # Do not invoke a builder inside tests; inspect all changed runtime
        # lines against the compiled catalog, including the new mission.
        with open(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo','rb') as stream:ru=gettext.GNUTranslations(stream)
        for topic in ['TALK_BERSERK_GODO_MEMORY_KEEP','TALK_BERSERK_GODO_MEMORY_SURVIVED']:
            line=Godo().line(topic);self.assertNotEqual(ru.gettext(line),line)
        mission=json.loads((MOD/'missions/recovery_hand_33.json').read_text())[0]
        for k in ['name','description']:self.assertNotEqual(ru.gettext(mission[k]),mission[k])


if __name__=='__main__':unittest.main()
