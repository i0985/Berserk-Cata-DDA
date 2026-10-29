"""Owner's shorter art brief, native mission dialogue and one-use cave prop.

JSON schema and narrowly modelled delayed effects; not a running CDDA AI test.
"""
import copy
import gettext
import heapq
import json
import unittest
from unittest.mock import patch

import validate_mod_assets as validator

ROOT = validator.ROOT
MOD = ROOT/'mods/Berserk'


def load(file):
    data = json.loads((MOD/file).read_text())
    return data if isinstance(data, list) else [data]


FURN = {o['id']: o for file in ['furniture/behelit_sites.json',
                              'furniture/behelit_distractions.json'] for o in load(file)}
EOCS = {o['id']: o for file in ['effects/behelit_site_eocs.json',
                              'effects/behelit_distraction_eocs.json'] for o in load(file)}


class Missions(unittest.TestCase):
    path = MOD/'missions/woodland_stone.json'

    def test_native_npc_origins_require_all_nine_dialogue_members(self):
        fields = ['describe','offer','accepted','rejected','advice','inquire',
                  'success','success_lie','failure']
        for origin in ['ORIGIN_SECONDARY','ORIGIN_ANY_NPC','ORIGIN_OPENER_NPC']:
            mission = {'type':'mission_definition', 'id':'test', 'origins':[origin]}
            with self.subTest(origin=origin):
                with self.assertRaisesRegex(validator.ValidationError,'dialogue.describe'):
                    validator.validate_mission_dialogue(self.path,[mission])
                mission['dialogue'] = {key:'A real line.' for key in fields}
                validator.validate_mission_dialogue(self.path,[mission])
                del mission['dialogue']['failure']
                with self.assertRaisesRegex(validator.ValidationError,'dialogue.failure'):
                    validator.validate_mission_dialogue(self.path,[mission])

    def test_repository_guard_reports_the_original_unknown_source_error_by_file(self):
        original = validator.top_level_objects
        def broken(path):
            rows = original(path)
            if path == self.path:
                rows = copy.deepcopy(rows)
                rows[0]['origins'] = ['ORIGIN_SECONDARY']
            return rows
        with patch.object(validator,'top_level_objects',side_effect=broken):
            with self.assertRaisesRegex(validator.ValidationError,'woodland_stone.json.*describe'):
                validator.validate_repository()

    def test_both_scripted_routes_use_existing_non_npc_origin(self):
        for file in ['missions/woodland_stone.json','missions/early_caravan.json']:
            mission, = load(file)
            self.assertEqual(mission['origins'],['ORIGIN_GAME_START'])
            validator.validate_mission_dialogue(MOD/file,[mission])


class OwnerArt(unittest.TestCase):
    def test_all_removed_art_has_registered_matching_native_appearance(self):
        policy = json.loads((ROOT/'docs/owner-art-scope-2026-10-30.json').read_text())
        native = json.loads((ROOT/'docs/owner-art-native-ids-2026-10-30.json').read_text())['ids']
        objects = {o.get('id'):o for p in MOD.rglob('*.json')
                   for o in validator.top_level_objects(p) if o.get('id')}
        self.assertEqual(len(policy['ordinary_appearances']),40)
        for ident,appearance in policy['ordinary_appearances'].items():
            with self.subTest(ident=ident):
                self.assertEqual(objects[ident]['looks_like'],appearance)
                self.assertIn(appearance,native)
                self.assertEqual(objects[ident]['type'],native[appearance]['type'])
        self.assertEqual(objects['f_berserk_flora_aid_pantry']['examine_action']['effect_on_conditions'],
                         ['EOC_BERSERK_FLORA_AID_PANTRY'])

    def test_current_russian_clues_describe_rockfall_not_chime(self):
        with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:
            ru = gettext.GNUTranslations(stream)
        self.assertEqual(ru.gettext(FURN['f_berserk_cave_noisemaker']['name']),
                         'расшатанная пещерная подпорка')
        for file in ['furniture/behelit_sites.json','furniture/behelit_distractions.json',
                     'effects/behelit_site_eocs.json','effects/behelit_distraction_eocs.json',
                     'effects/location_interactions_eocs.json','effects/behelit_adventure_eocs.json',
                     'dialogue/road_journal.json']:
            def strings(value):
                if isinstance(value,str): yield value
                elif isinstance(value,list):
                    for part in value: yield from strings(part)
                elif isinstance(value,dict):
                    for part in value.values(): yield from strings(part)
            for text in strings(load(file)):
                if '_' not in text or ' ' in text:
                    self.assertNotIn('stone pendant',text)
                    self.assertNotIn('stone chime',text)


class Rockfall:
    """Execute only the actual prop's conditional/queue/transform vocabulary.

    The map is a fixture. Hearing/pathfinding and real unloaded-map IO are not
    represented. Queued contexts are copied through JSON to check save safety.
    """
    def __init__(self):
        self.time=0; self.serial=0; self.events=[]; self.cells={}; self.sounds=[]
        self.player=(0,0,-1)

    @staticmethod
    def key(pos): return ','.join(map(str,pos))

    def check(self,condition,ctx):
        if 'and' in condition:
            return all(self.check(c,ctx) for c in condition['and'])
        if 'map_furniture_id' in condition:
            return self.cells.get(self.key(ctx['pos'])) == condition['map_furniture_id']
        expression, = condition['math']
        if expression == "u_val('pos_z') == _berserk_noise_z":
            return self.player[2] == ctx['noise_z']
        if expression == "distance('u', _pos) <= 48":
            return max(abs(a-b) for a,b in zip(self.player,ctx['pos'])) <= 48
        raise AssertionError('Unmodelled condition: '+repr(condition))

    def effect(self,effect,ctx):
        if isinstance(effect,list):
            for part in effect:self.effect(part,ctx)
            return
        if 'if' in effect:
            if self.check(effect['if'],ctx):self.effect(effect['then'],ctx)
        elif 'math' in effect:
            if effect['math'] == ["_berserk_noise_z = u_val('pos_z')"]:
                ctx['noise_z']=self.player[2]
        elif 'time_in_future' in effect:
            delay=int(effect['time_in_future'].split()[0])
            callback={k:v for k,v in effect.items() if k!='time_in_future'}
            if 'u_transform_radius' in effect:delay+=1  # native timed-event delay
            self.serial+=1
            heapq.heappush(self.events,(self.time+delay,self.serial,callback,copy.deepcopy(ctx)))
        elif 'run_eocs' in effect:
            if effect['run_eocs'] in EOCS:self.effect(EOCS[effect['run_eocs']]['effect'],ctx)
        elif 'u_transform_radius' in effect:
            self.assert_exact_source(effect)
            key=self.key(ctx['pos'])
            for rule in FURN[effect['ter_furn_transform']]['furniture']:
                if self.cells.get(key) in rule['valid_furniture']:
                    self.cells[key]=rule['result'];break
        elif 'u_make_sound' in effect:
            self.assert_exact_source(effect)
            self.sounds.append((self.time,list(ctx['pos'])))
        elif not ('u_message' in effect or 'turn_cost' in effect):
            raise AssertionError('Unmodelled effect: '+repr(effect))

    @staticmethod
    def assert_exact_source(effect):
        assert effect['target_var'] == {'context_val':'pos'}

    def arm(self,pos):
        self.effect(EOCS['EOC_BERSERK_CAVE_DISTRACTION']['effect'],{'pos':list(pos)})

    def advance(self,end):
        while self.events and self.events[0][0]<=end:
            self.time,_,callback,ctx=heapq.heappop(self.events)
            self.effect(callback,ctx)
        self.time=end

    def reload(self):
        state=json.loads(json.dumps(vars(self)))
        self.__dict__.update(state)
        self.events=[tuple(e) for e in self.events];heapq.heapify(self.events)


class CaveProp(unittest.TestCase):
    source=(8,0,-1)
    def world(self):
        w=Rockfall();w.cells[w.key(self.source)]='f_berserk_cave_noisemaker';return w

    def test_one_collapse_survives_reload_and_never_rearms(self):
        w=self.world();w.arm(self.source);w.arm(self.source)
        self.assertEqual(len(w.events),2)
        w.advance(19);self.assertFalse(w.sounds);w.reload()
        w.player=(16,0,-1);w.advance(90)
        self.assertEqual(w.sounds,[(20,list(self.source))])
        self.assertEqual(w.cells[w.key(self.source)],'f_berserk_cave_rockfall_spent')
        w.arm(self.source);self.assertFalse(w.events)

    def test_leaving_floor_finishes_without_remote_sound_or_restoring_prop(self):
        w=self.world();w.arm(self.source);w.player=(8,0,0);w.reload();w.advance(90)
        self.assertFalse(w.sounds)
        self.assertEqual(w.cells[w.key(self.source)],'f_berserk_cave_rockfall_spent')

    def test_destroyed_prop_is_not_recreated(self):
        w=self.world();w.arm(self.source);w.cells[w.key(self.source)]='f_null';w.advance(90)
        self.assertFalse(w.sounds);self.assertEqual(w.cells[w.key(self.source)],'f_null')

    def test_old_queued_pulses_and_reset_cannot_repeat_collapse(self):
        w=self.world();w.cells[w.key(self.source)]='f_berserk_cave_noisemaker_armed'
        ctx={'pos':list(self.source),'noise_z':-1}
        for time in [20,35,50,65]:
            w.time=time
            w.effect(EOCS['EOC_BERSERK_CAVE_DISTRACTION_PULSE']['effect'],ctx)
        w.effect({'u_transform_radius':0,'ter_furn_transform':'berserk_noisemakers_reset',
                  'target_var':{'context_val':'pos'}},ctx)
        self.assertEqual(len(w.sounds),1)
        self.assertEqual(w.cells[w.key(self.source)],'f_berserk_cave_rockfall_spent')


if __name__ == '__main__':unittest.main()
