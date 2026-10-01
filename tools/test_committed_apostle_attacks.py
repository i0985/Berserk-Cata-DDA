"""Execute the actual committed-attack EOCs in an actor/time model.

No native CDDA process, spell rasterizer, AI, armor or rendering is simulated.
Collision fixtures test the intended safe-movement contract, not the engine.
"""
import copy
import gettext
import json
import math
import re
import unittest
from test_grunbeld_breath import Actor, BreathGraph, load, MOD

KINDS=('count','wyald','rosine','grunbeld_knight')

class CommittedGraph(BreathGraph):
    def __init__(self,kind):
        super().__init__();self.kind=kind
        self.eocs={o['id']:o for o in load('effects/apostle_committed_attacks.json')}
        self.blocked=set();self.teleports=[]
    def evaluate(self,s):
        s=re.sub(r'has_var\((u_|n_)(\w+)\)',lambda m:str(m[2] in self.actor(m[1][:-1]).values),s)
        s=re.sub(r'\b(u|n)_(berserk_\w+)\b',lambda m:'var('+repr(m[0])+')',s)
        def dist(a,p):return max(abs(x-y) for x,y in zip(self.actor(a).pos,p))
        return eval(s,{'__builtins__':{}},{'var':self.var,'time':lambda _:self.now,'distance':dist,'u_hp':lambda _:self.alpha.hp,'n_hp':lambda _:self.beta.hp,'u_val':lambda a:self.alpha.pos[{'pos_x':0,'pos_y':1,'pos_z':2}[a]],'n_val':lambda a:self.beta.pos[{'pos_x':0,'pos_y':1,'pos_z':2}[a]],'max':max,'abs':abs,'round':lambda n:math.floor(n+.5) if n>=0 else math.ceil(n-.5)})
    def effect(self,v):
        if isinstance(v,dict):
            for scope in ('u','npc'):
                if scope+'_location_variable' in v:
                    actor=self.actor(scope);dest,key=next(iter(v[scope+'_location_variable'].items()))
                    offsets=[self.evaluate(v[a+'_adjust']['math'][0]) if isinstance(v.get(a+'_adjust',0),dict) else v.get(a+'_adjust',0) for a in ('x','y','z')]
                    self.actor(dest.removesuffix('_val')).values[key]=tuple(actor.pos[i]+offsets[i] for i in range(3));return
                if scope+'_cast_spell' in v:
                    dest,key=next(iter(v['loc'].items()));actor=self.actor(scope)
                    self.casts.append({'id':v[scope+'_cast_spell']['id'],'source':tuple(actor.pos),'target':tuple(self.actor(dest.removesuffix('_val')).values[key]),'phase':actor.values['berserk_committed_'+self.kind+'_phase']});return
            if 'u_teleport' in v:
                p=tuple(self.alpha.values[v['u_teleport']['u_val']]);self.teleports.append(p)
                if p not in self.blocked:self.alpha.pos=p
                return
        return super().effect(v)
    def begin(self,a,b):
        self.alpha,self.beta=b,a;self.run('EOC_BERSERK_'+self.kind.upper()+'_COMMITTED_BEGIN')
    def tick(self,a,at):
        self.now=at;self.alpha,self.beta=a,None;self.run('EOC_BERSERK_'+self.kind.upper()+'_COMMITTED_TICK')
    def shots(self):return [c for c in self.casts if c['id'].endswith('_release')]

class CommittedAttackTests(unittest.TestCase):
    def test_all_attacks_wait_and_commit_once_without_chasing_new_target(self):
        for kind in KINDS:
            with self.subTest(kind=kind):
                g=CommittedGraph(kind);a=Actor((0,0,0));b=Actor((2,0,0));g.begin(a,b)
                self.assertFalse(b.values);marked=[c['target'] for c in g.casts]
                b.pos=(2,3,0);g.tick(a,102.9);self.assertFalse(g.shots())
                g.tick(a,103);self.assertTrue(g.shots());self.assertTrue(all(c['phase']==0 for c in g.shots()))
                self.assertTrue(all(c['target'] in marked for c in g.shots()))
                count=len(g.shots());g.tick(a,103);g.tick(a,104);self.assertEqual(len(g.shots()),count)
                self.assertIn('berserk_apostle_attack_recovery',a.effects)
    def test_displacement_death_expiration_and_late_tick_cancel_all_kinds(self):
        for kind in KINDS:
            for mode in ('move','death','expire','late'):
                with self.subTest(kind=kind,mode=mode):
                    g=CommittedGraph(kind);a=Actor((0,0,0));b=Actor((2,0,0));g.begin(a,b)
                    if mode=='move':a.pos=(1,0,0)
                    elif mode=='death':a.hp=0
                    elif mode=='expire':a.effects.clear()
                    g.tick(a,105 if mode=='late' else 103)
                    self.assertFalse(g.shots());self.assertTrue(g.clears)
    def test_saved_actor_state_preserves_aim_and_only_one_resolution(self):
        for kind in KINDS:
            g=CommittedGraph(kind);a=Actor((-48,-48,-1));b=Actor((-46,-48,-1));g.begin(a,b)
            a.values=json.loads(json.dumps(a.values));a.effects=json.loads(json.dumps(a.effects))
            replacement=CommittedGraph(kind);replacement.tick(a,103)
            self.assertTrue(replacement.shots());before=len(replacement.shots());replacement.tick(a,104)
            self.assertEqual(len(replacement.shots()),before)
    def test_rush_stops_at_first_fixture_obstacle_and_never_forces_teleport(self):
        for kind in ('wyald','rosine'):
            g=CommittedGraph(kind);a=Actor((0,0,0));b=Actor((4,0,0));g.blocked={(2,0,0)}
            g.begin(a,b);b.pos=(4,1,0);g.tick(a,103)
            self.assertEqual([c['target'] for c in g.shots()],[(1,0,0),(2,0,0)])
            self.assertEqual(a.pos,(1,0,0));self.assertNotIn((3,0,0),g.teleports)
        for e in load('effects/apostle_committed_attacks.json'):
            if '_STEP_' in e['id']:
                teleport=next(v for v in e['effect'] if 'u_teleport' in v)
                self.assertIs(teleport['force'],False);self.assertNotIn('force_safe',teleport)
    def test_rush_does_not_overshoot_near_target_or_turn_after_snapshot(self):
        for kind in ('wyald','rosine'):
            g=CommittedGraph(kind);a=Actor((0,0,0));b=Actor((1,0,0));g.begin(a,b);b.pos=(0,1,0);g.tick(a,103)
            self.assertEqual([c['target'] for c in g.shots()],[(1,0,0)])
            self.assertEqual(a.pos,(1,0,0))
    def test_diagonal_negative_coordinate_steps_are_unique_adjacent_and_fixed(self):
        g=CommittedGraph('rosine');a=Actor((-48,-48,0));b=Actor((-52,-50,0));g.begin(a,b)
        marked=[c['target'] for c in g.casts];self.assertEqual(len(marked),4)
        p=a.pos
        for q in marked:self.assertEqual(max(abs(x-y) for x,y in zip(p,q)),1);p=q
        g.tick(a,103);self.assertEqual([c['target'] for c in g.shots()],marked)
    def test_prepare_has_zero_aoe_cone_marker_matches_strike_and_fields_are_safe(self):
        spells={s['id']:s for s in load('spells/apostle_committed_attacks.json')}
        for kind in KINDS:
            p=spells['berserk_committed_'+kind+'_prepare'];w=spells['berserk_committed_'+kind+'_warning'];s=spells['berserk_committed_'+kind+'_release']
            self.assertEqual(p['min_aoe'],0);self.assertEqual(p['max_aoe'],0);self.assertEqual(w['min_damage'],0)
            for key in ('shape','min_range','max_range','min_aoe','max_aoe'):self.assertEqual(w[key],s[key])
            self.assertNotIn('IGNORE_WALLS',s['flags']);self.assertNotIn('IGNORE_WALLS',w['flags'])
        for f in load('fields/apostle_committed_attacks.json'):
            if f['type']=='field_type':
                self.assertFalse(f['intensity_levels'][0]['dangerous']);self.assertEqual(f['percent_spread'],0)
    def test_warning_cleanup_keeps_unrelated_fields(self):
        for obj in load('fields/apostle_committed_attacks.json'):
            if obj['type']=='ter_furn_transform':self.assertEqual(len(obj['field'][0]['valid_field']),1)

if __name__=='__main__':unittest.main()
