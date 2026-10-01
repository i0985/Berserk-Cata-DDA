"""Fixed-target breath lifecycle tests using the real EOC graph.

The small interpreter models actor variables, time, and recorded spell casts.
It does not simulate the native game, projectile armor, rendering, or save load.
"""
import copy
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
import unittest
from validate_mod_assets import validate_monster_attacks, validate_math_actor_scopes, ValidationError

MOD = Path(__file__).resolve().parents[1]/'mods/Berserk'


def load(path):
    return json.loads((MOD/path).read_text())


@dataclass
class Actor:
    pos: tuple
    hp: int = 950
    values: dict = field(default_factory=dict)
    effects: dict = field(default_factory=dict)


class BreathGraph:
    def __init__(self):
        self.eocs = {o['id']:o for o in load('effects/grunbeld_breath_eocs.json')}
        self.now = 100
        self.alpha = None
        self.beta = None
        self.casts = []
        self.clears = []
        self.sounds = []

    def actor(self,scope):
        return self.alpha if scope=='u' else self.beta

    def var(self,name):
        scope,key = name.split('_',1)
        return self.actor(scope).values.get(key,0)

    def evaluate(self,expression):
        expression = re.sub(r'has_var\((u_|n_)(\w+)\)',
                            lambda m:str(m[2] in self.actor(m[1][:-1]).values),expression)
        expression = re.sub(r'\b(u|n)_(berserk_\w+)\b',lambda m:'var('+repr(m[0])+')',expression)
        def distance(actor,loc):
            return max(abs(a-b) for a,b in zip(self.actor(actor).pos,loc))
        return eval(expression,{'__builtins__':{}},
                    {'var':self.var,'time':lambda _:self.now,'distance':distance,
                     'u_hp':lambda _:self.alpha.hp,'n_hp':lambda _:self.beta.hp})

    def active(self,actor,id):
        return actor.effects.get(id,0) > self.now

    def condition(self,v):
        if 'and' in v:return all(self.condition(c) for c in v['and'])
        if 'or' in v:return any(self.condition(c) for c in v['or'])
        if 'not' in v:return not self.condition(v['not'])
        if 'math' in v:return bool(self.evaluate(v['math'][0]))
        for scope in ('u','npc'):
            if scope+'_has_effect' in v:return self.active(self.actor(scope),v[scope+'_has_effect'])
        raise AssertionError(v)

    def run(self,id):
        e=self.eocs[id]
        if 'condition' not in e or self.condition(e['condition']):self.effect(e['effect'])

    def effect(self,v):
        if isinstance(v,list):
            for e in v:self.effect(e)
            return
        if 'if' in v:
            branch='then' if self.condition(v['if']) else 'else'
            if branch in v:self.effect(v[branch])
            return
        if 'math' in v:
            key,expr=v['math'][0].split(' = ',1)
            scope,key=key.split('_',1)
            self.actor(scope).values[key]=self.evaluate(expr)
            return
        if 'run_eocs' in v:
            self.run(v['run_eocs'])
            return
        for scope in ('u','npc'):
            actor=self.actor(scope)
            if scope+'_location_variable' in v:
                target_scope,key=next(iter(v[scope+'_location_variable'].items()))
                self.actor(target_scope.removesuffix('_val')).values[key]=tuple(actor.pos)
                return
            if scope+'_add_effect' in v:
                actor.effects[v[scope+'_add_effect']]=self.now+int(v['duration'].split()[0])
                return
            if scope+'_lose_effect' in v:
                actor.effects.pop(v[scope+'_lose_effect'],None)
                return
            if scope+'_cast_spell' in v:
                loc_scope,key=next(iter(v['loc'].items()))
                target=tuple(self.actor(loc_scope.removesuffix('_val')).values[key])
                self.casts.append({'id':v[scope+'_cast_spell']['id'],'source':tuple(actor.pos),
                                   'target':target,'phase':actor.values['berserk_grunbeld_breath_phase'],
                                   'time':self.now})
                return
        if 'u_transform_radius' in v:
            self.clears.append((tuple(self.alpha.values[v['target_var']['u_val']]),v['u_transform_radius']))
        elif 'u_make_sound' in v:
            self.sounds.append(tuple(self.alpha.pos))
        else:
            raise AssertionError(v)

    def begin(self,dragon,victim):
        # Native spell EOC actor order differs from attack conditions and tick.
        self.alpha,self.beta=victim,dragon
        self.run('EOC_BERSERK_GRUNBELD_BREATH_BEGIN')

    def tick(self,dragon,at):
        self.now=at
        self.alpha,self.beta=dragon,None
        self.run('EOC_BERSERK_GRUNBELD_BREATH_TICK')

    def shots(self):
        return [c for c in self.casts if c['id']=='berserk_grunbeld_breath_release']


def cardinal_jet(source,target,walls=()):
    """Independent cardinal-line collision contract, not the native rasterizer."""
    x,y,z=source
    tx,ty,tz=target
    assert z==tz and (x==tx or y==ty)
    dx,dy=(tx>x)-(tx<x),(ty>y)-(ty<y)
    cells=[]
    while (x,y)!=(tx,ty):
        x,y=x+dx,y+dy
        if (x,y,z) in walls:break
        cells.append((x,y,z))
    return cells


class FixedBreathTests(unittest.TestCase):
    def test_prepare_has_no_damage_and_cast_waits_then_commits_once(self):
        g=BreathGraph();d=Actor((0,0,0));v=Actor((4,0,0),hp=100)
        g.begin(d,v)
        self.assertEqual(v.values,{})
        self.assertEqual(d.values['berserk_grunbeld_breath_target'],(4,0,0))
        self.assertEqual(len(g.casts),1)
        self.assertEqual(g.casts[0]['id'],'berserk_grunbeld_breath_warning')
        g.tick(d,102.9);self.assertFalse(g.shots())
        g.tick(d,103)
        self.assertEqual(len(g.shots()),1)
        self.assertEqual(g.shots()[0]['phase'],0) # committed before damage callbacks
        self.assertEqual(d.effects['berserk_grunbeld_breath_recovery'],106)
        self.assertNotIn('berserk_grunbeld_flame_ready',d.effects)
        for at in (103,104,106,140):g.tick(d,at)
        self.assertEqual(len(g.shots()),1)

    def test_sideways_movement_does_not_redirect_the_marked_line(self):
        g=BreathGraph();d=Actor((0,0,0));v=Actor((4,0,0))
        g.begin(d,v);marked=copy.deepcopy(g.casts[0])
        v.pos=(4,1,0)
        g.tick(d,103)
        shot=g.shots()[0]
        self.assertEqual(shot['target'],marked['target'])
        self.assertNotIn(v.pos,cardinal_jet(shot['source'],shot['target']))
        self.assertIn((2,0,0),cardinal_jet(shot['source'],shot['target']))

    def test_wall_stops_the_jet_instead_of_hitting_the_current_target(self):
        g=BreathGraph();d=Actor((0,0,0));v=Actor((5,0,0))
        g.begin(d,v);g.tick(d,103)
        shot=g.shots()[0]
        cells=cardinal_jet(shot['source'],shot['target'],walls={(2,0,0)})
        self.assertEqual(cells,[(1,0,0)])
        self.assertNotIn(v.pos,cells)

    def test_caster_displacement_or_death_cancels_without_reanchoring(self):
        for mutation in ('move','death'):
            g=BreathGraph();d=Actor((0,0,0));v=Actor((4,0,0));g.begin(d,v)
            if mutation=='move':d.pos=(1,0,0)
            else:d.hp=0
            g.tick(d,103)
            self.assertFalse(g.shots())
            self.assertEqual(g.clears,[((0,0,0),6)])
            self.assertEqual(d.values['berserk_grunbeld_breath_phase'],0)

    def test_late_or_expired_preparation_cannot_fire_after_reentry(self):
        for at in (104.1,130,1000):
            g=BreathGraph();d=Actor((0,0,0));v=Actor((4,0,0));g.begin(d,v)
            g.tick(d,at)
            self.assertFalse(g.shots())
            self.assertEqual(d.values['berserk_grunbeld_breath_phase'],0)
        g=BreathGraph();d=Actor((0,0,0));v=Actor((4,0,0));g.begin(d,v)
        d.effects.clear();g.tick(d,102)
        self.assertFalse(g.shots())

    def test_save_model_retains_negative_absolute_target_and_floor(self):
        g=BreathGraph();d=Actor((-100,-200,-1));v=Actor((-104,-200,-1));g.begin(d,v)
        d.values=json.loads(json.dumps(d.values))
        d.effects=json.loads(json.dumps(d.effects))
        v.pos=(-104,-205,-1)
        g.tick(d,103)
        self.assertEqual(g.shots()[0]['target'],(-104,-200,-1))
        self.assertEqual(g.shots()[0]['source'],(-100,-200,-1))

    def test_two_dragons_retain_their_own_targets_and_cooldowns(self):
        g=BreathGraph();a=Actor((0,0,0));b=Actor((20,20,0));v=Actor((4,0,0))
        g.begin(a,v);v.pos=(20,24,0);g.begin(b,v)
        v.pos=(50,50,0)
        g.tick(a,103);g.tick(b,103)
        self.assertEqual([s['target'] for s in g.shots()],[(4,0,0),(20,24,0)])
        self.assertEqual(a.values['berserk_grunbeld_breath_cooldown'],121)
        self.assertEqual(b.values['berserk_grunbeld_breath_cooldown'],121)
        g.now=110;g.begin(a,v)
        self.assertEqual(len(g.casts),4)
        g.now=125;v.pos=(5,0,0);g.begin(a,v)
        self.assertEqual(a.values['berserk_grunbeld_breath_target'],(5,0,0))
        self.assertEqual(b.values['berserk_grunbeld_breath_target'],(20,24,0))

    def test_legacy_or_missing_target_state_is_cleared_without_phantom_damage(self):
        for values in ({},{'berserk_grunbeld_breath_phase':1,'berserk_grunbeld_breath_origin':(0,0,0)}):
            g=BreathGraph();d=Actor((0,0,0),values=values,
                                  effects={'berserk_grunbeld_flame_ready':107})
            g.tick(d,101)
            self.assertFalse(g.casts)
            self.assertEqual(d.values['berserk_grunbeld_breath_phase'],0)
            self.assertNotIn('berserk_grunbeld_flame_ready',d.effects)

    def test_expired_pending_state_cannot_be_overwritten_before_cancellation(self):
        g=BreathGraph();d=Actor((0,0,0));v=Actor((4,0,0));g.begin(d,v)
        g.now=110;v.pos=(0,4,0)
        g.begin(d,v)
        self.assertEqual(d.values['berserk_grunbeld_breath_target'],(4,0,0))
        self.assertEqual(len(g.casts),1)
        g.tick(d,110)
        self.assertFalse(g.shots())
        self.assertEqual(d.values['berserk_grunbeld_breath_phase'],0)

    def test_preview_and_damage_share_exact_shape_and_finite_visual_fields(self):
        spells={s['id']:s for s in load('spells/grunbeld_breath.json')}
        preview=spells['berserk_grunbeld_breath_warning'];release=spells['berserk_grunbeld_breath_release']
        for key in ('shape','min_range','max_range','min_aoe','max_aoe','valid_targets'):
            self.assertEqual(preview[key],release[key])
        self.assertEqual(release['shape'],'line');self.assertEqual(release['min_aoe'],0)
        self.assertEqual(preview['min_damage'],0);self.assertEqual(release['min_damage'],36)
        self.assertEqual(release['damage_type'],'heat')
        self.assertTrue(all('IGNORE_WALLS' not in s['flags'] for s in (preview,release)))
        prepare=spells['berserk_grunbeld_breath_prepare']
        self.assertIn('NO_PROJECTILE',prepare['flags'])
        self.assertEqual(prepare['valid_targets'],['hostile'])
        fields=load('fields/grunbeld_breath.json')
        for f in fields[:2]:
            self.assertEqual(f['half_life'],'1 second')
            self.assertTrue(f['linear_half_life'])
            self.assertFalse(f.get('has_fire',False))
            self.assertFalse(f['intensity_levels'][0]['dangerous'])
            self.assertNotIn('effects',f['intensity_levels'][0])
        self.assertEqual(fields[2]['field'],[{'result':'fd_null','valid_field':['fd_berserk_grunbeld_breath_warning']}])

    def test_locks_and_heartbeat_are_bounded_and_old_attack_is_not_used(self):
        effects={e['id']:e for e in load('effects/grunbeld_combat_effects.json')}
        for id,duration in [('berserk_grunbeld_flame_ready','4 seconds'),('berserk_grunbeld_breath_recovery','3 seconds')]:
            self.assertEqual(set(effects[id]['flags']),{'CANNOT_MOVE','CANNOT_ATTACK'})
            self.assertEqual(effects[id]['max_duration'],duration)
        dragon=next(m for m in load('monsters/apostle_grunbeld.json') if m['id']=='mon_berserk_grunbeld_dragon')
        self.assertEqual(dragon['special_attacks'],[{'id':'berserk_grunbeld_flame_b_prepare','cooldown':24}])
        watch=BreathGraph().eocs['EOC_BERSERK_GRUNBELD_BREATH_WATCH']
        self.assertTrue(watch['global']);self.assertEqual(watch['recurrence'],'1 second')
        self.assertEqual(watch['effect']['monster_range'],48)
        text=(MOD/'effects/grunbeld_breath_eocs.json').read_text()
        self.assertNotIn('time_in_future',text)
        self.assertNotIn('u_spawn_monster',text)
        self.assertNotIn('u_location_variable',json.dumps(BreathGraph().eocs['EOC_BERSERK_GRUNBELD_BREATH_RELEASE']))

    def test_attack_loader_accepts_spell_actor_and_rejects_unsupported_names(self):
        path=MOD/'monster_special_attacks/grunbeld_attacks.json'
        attacks=load('monster_special_attacks/grunbeld_attacks.json')
        validate_monster_attacks(path,attacks)
        prepare=next(a for a in attacks if a['id']=='berserk_grunbeld_flame_b_prepare')
        self.assertEqual(prepare['attack_type'],'spell')
        invalid=copy.deepcopy(prepare);invalid['attack_type']='spellcasting'
        with self.assertRaises(ValidationError):validate_monster_attacks(path,[invalid])
        invalid=copy.deepcopy(prepare);invalid.pop('spell_data')
        with self.assertRaises(ValidationError):validate_monster_attacks(path,[invalid])

    def test_math_uses_n_scope_while_json_location_keys_use_npc_val(self):
        path=MOD/'effects/grunbeld_breath_eocs.json'
        data=load('effects/grunbeld_breath_eocs.json')
        validate_math_actor_scopes(path,data)
        begin=next(e for e in data if e['id']=='EOC_BERSERK_GRUNBELD_BREATH_BEGIN')
        self.assertEqual(begin['effect'][0],{'u_location_variable':{'npc_val':'berserk_grunbeld_breath_target'}})
        self.assertEqual(begin['effect'][2],{'math':['n_berserk_grunbeld_breath_phase = 1']})
        for expr in ("npc_hp('ALL') > 0",'npc_berserk_grunbeld_breath_phase = 1','g_berserk_breath_phase = 1'):
            with self.assertRaises(ValidationError):validate_math_actor_scopes(path,[{'math':[expr]}])


if __name__=='__main__':
    unittest.main()
