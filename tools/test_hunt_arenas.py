"""Arena state/geometry checks without a CDDA executable.

The model uses actual JSON, simple rock-occluded sight and occupied cells.
It does not simulate native vision caches, AI, saves or map loading.
"""
import copy
import gettext
import unittest

from test_apostle_hunts import connected
from test_behelit_rewards import MOD, objects
from test_named_apostle_hunts import NamedHuntGraph


SITES = {
    'first_hunt': ('first_hunt.json', 'berserk_first_hunt_lair', 'mon_berserk_hollow_apostle',
                   'u_berserk_first_hunt_spawned', 'u_berserk_first_hunt_spawn_attempts',
                   'u_berserk_first_hunt_done', 'u_berserk_first_hunt_location'),
    'breach': ('local_breach.json', 'berserk_local_breach', 'mon_berserk_breach_warden',
               'u_berserk_breach_guardian_spawned', 'u_berserk_breach_spawn_attempts',
               'u_berserk_breach_guardian_defeated', 'u_berserk_local_breach_location'),
    **{k: ('apostle_'+k+'.json', 'berserk_'+k+'_'+tail, boss,
           'berserk_hunt_'+k+'_spawned', 'berserk_hunt_'+k+'_attempts',
           'berserk_apostle_'+k+'_dead', 'berserk_hunt_'+k+'_location')
       for k, tail, boss in [('wyald', 'ring', 'mon_berserk_apostle_wyald'),
                             ('rosine', 'nest', 'mon_berserk_apostle_rosine'),
                             ('grunbeld', 'crucible', 'mon_berserk_grunbeld_knight')]},
}


def line(a, b):
    """Integer Bresenham line for testing rock cover, not the native LOS."""
    x,y=a;tx,ty=b;dx=abs(tx-x);dy=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1
    err=dx+dy
    while (x,y)!=(tx,ty):
        e=2*err
        if e>=dy:err+=dy;x+=sx
        if e<=dx:err+=dx;y+=sy
        yield x,y


class ArenaGraph(NamedHuntGraph):
    def __init__(self, kind):
        super().__init__({'u_berserk_first_hunt_done': int(kind!='first_hunt'),
                          'berserk_hunt_count_state':4, 'berserk_hunt_wyald_state':4,
                          'berserk_hunt_rosine_state':4})
        self.kind=kind;self.site=SITES[kind];self.prefix='EOC_BERSERK_'+kind.upper()
        self.origin=(-240,48,0)  # Negative/nonzero coordinates catch local/absolute errors.
        self.omt=self.site[1];self.avatar=(-228,60,0)
        self.flags[self.site[6]]=self.origin
        if kind in ('wyald','rosine','grunbeld'):
            self.flags['berserk_hunt_'+kind+'_state']=1
        if kind=='grunbeld':self.flags['berserk_hunt_grunbeld_site_registered']=1
        self.map=next(m['object'] for m in objects(MOD/'mapgen'/self.site[0])
                      if self.omt in m.get('om_terrain',[]))
        self.rows=self.map['rows'];self.visible_override=None;self.occupied=set()
        self.hp={};self.messages=[];self.placements=[];self.tags=[]
        for f in self.map.get('place_furniture',[]):
            self.furniture[(self.origin[0]+f['x'],self.origin[1]+f['y'],0)]=f['furn']

    def local(self, pos):return pos[0]-self.origin[0],pos[1]-self.origin[1]

    def visible(self, pos):
        if self.visible_override is not None:return self.visible_override
        return all(0<=x<24 and 0<=y<24 and self.rows[y][x]!='#'
                   for x,y in line(self.local(self.avatar),self.local(pos)))

    def condition(self, v):
        if isinstance(v,dict) and 'u_can_see_location' in v:
            return self.visible(self.resolve(v['u_can_see_location']))
        return super().condition(v)

    def effect(self, v):
        if isinstance(v,dict):
            if 'u_message' in v:self.messages.append(v['u_message']);return
            if 'u_run_monster_eocs' in v:
                self.tags.extend(v['mtype_ids']);return
            if 'u_spawn_monster' in v:
                pos=self.resolve(v['target_var']);x,y=self.local(pos)
                self.assert_exact_cell(v);self.placements.append(pos)
                free=(0<=x<24 and 0<=y<24 and self.rows[y][x] not in '#T' and
                      pos not in self.occupied and pos!=self.avatar and
                      not any(p==pos for _,p in self.monsters+self.spawned))
                self.spawn_attempts.append(v['u_spawn_monster'])
                if free:
                    self.spawned.append((v['u_spawn_monster'],pos));self.hp[pos]=290
                for id in v['true_eocs' if free else 'false_eocs']:self.run(id)
                return
        return super().effect(v)

    @staticmethod
    def assert_exact_cell(v):
        assert v['real_count']==1 and v['min_radius']==v['max_radius']==0

    def move_to(self, x, y):
        self.avatar=(self.origin[0]+x,self.origin[1]+y,0)
        self.run(self.prefix+'_ENTER')


class HuntArenas(unittest.TestCase):
    def test_all_exterior_approaches_and_omt_edges_wait_for_the_inner_area(self):
        for kind in SITES:
            for outside,inside in [((12,7),(12,8)),((12,16),(12,15)),
                                   ((7,12),(8,12)),((16,12),(15,12))]:
                with self.subTest(kind=kind, approach=outside):
                    g=ArenaGraph(kind)
                    for p in [(0,12),(23,12),(12,0),(12,23),outside]:
                        g.move_to(*p);g.run(g.prefix+'_RETRY')
                    self.assertFalse(g.spawn_attempts)
                    self.assertNotEqual(g.flags.get(g.site[3]),1)
                    g.move_to(*inside)
                    self.assertEqual(len(g.spawned),1)
                    self.assertFalse(g.visible(g.spawned[0][1]))
                    self.assertEqual(g.flags[g.site[3]],1)

    def test_damage_position_and_identity_survive_retreat_and_copied_state(self):
        for kind in SITES:
            g=ArenaGraph(kind);g.move_to(12,12);id,pos=g.spawned[0]
            g.hp[pos]=37;g.monsters=[(id,(pos[0]+70,pos[1],0))]
            saved=copy.deepcopy(g);saved.spawned=[]  # Boss has left the loaded neighborhood.
            for p in [(12,0),(12,12),(9,14)]:
                saved.move_to(*p);saved.run(saved.prefix+'_RETRY')
            self.assertFalse(saved.spawned)
            self.assertEqual(saved.hp[pos],37)
            self.assertEqual(saved.monsters,g.monsters)

    def test_existing_boss_is_adopted_without_replacement_or_hp_reset(self):
        for kind in SITES:
            g=ArenaGraph(kind);pos=(g.origin[0]+28,g.origin[1]+4,0)
            g.monsters=[(g.site[2],pos)];g.hp[pos]=83
            g.furniture.clear()  # Already-generated legacy map.
            g.move_to(12,12)
            self.assertFalse(g.spawn_attempts)
            self.assertEqual(g.monsters,[(g.site[2],pos)])
            self.assertEqual(g.hp[pos],83)
            self.assertEqual(g.flags[g.site[3]],1)

    def test_unrecorded_legacy_map_never_fabricates_a_second_original(self):
        for kind in ('first_hunt','breach'):
            g=ArenaGraph(kind);g.furniture.clear()
            for _ in range(8):g.move_to(12,12);g.run(g.prefix+'_RETRY')
            self.assertFalse(g.spawn_attempts);self.assertEqual(len(g.messages),1)
            pos=(g.origin[0]+30,g.origin[1],0);g.monsters=[(g.site[2],pos)]
            g.run(g.prefix+'_RETRY')
            self.assertEqual(g.flags[g.site[3]],1);self.assertFalse(g.spawn_attempts)

    def test_visible_points_delay_without_consuming_retries_or_creating_a_boss(self):
        for kind in SITES:
            g=ArenaGraph(kind);g.visible_override=True
            for _ in range(8):g.move_to(12,12)
            self.assertFalse(g.spawn_attempts)
            self.assertFalse(g.flags.get(g.site[4]));self.assertEqual(len(g.messages),1)
            g.visible_override=None;g.move_to(12,12)
            self.assertEqual(len(g.spawned),1)

    def test_occupied_recess_is_skipped_and_all_blocked_attempts_stop_at_six(self):
        for kind in SITES:
            g=ArenaGraph(kind);g.occupied.add((g.origin[0]+6,g.origin[1]+6,0))
            g.move_to(12,12)
            self.assertEqual(len(g.spawned),1);self.assertNotIn(g.spawned[0][1],g.occupied)
            self.assertEqual(len(g.placements),2)
            g=ArenaGraph(kind)
            g.occupied={(g.origin[0]+x,g.origin[1]+y,0) for x,y in [(6,6),(17,6),(6,17),(17,17)]}
            for _ in range(10):g.move_to(12,12);g.run(g.prefix+'_RETRY')
            self.assertEqual(len(g.placements),6);self.assertFalse(g.spawned)
            self.assertEqual(g.flags[g.site[4]],6);self.assertEqual(len(g.messages),1)
            g.occupied.clear();g.run('EOC_BERSERK_HUNT_ARENA_MANUAL_RETRY')
            self.assertEqual(len(g.spawned),1)

    def test_finished_or_wrong_saved_lair_cannot_start_a_second_encounter(self):
        for kind in SITES:
            for condition in ('finished','wrong_lair','wrong_z','before_eclipse'):
                g=ArenaGraph(kind)
                if condition=='finished':g.flags[g.site[5]]=1
                if condition=='wrong_lair':g.flags[g.site[6]]=(g.origin[0]+24,g.origin[1],0)
                if condition=='wrong_z':g.flags[g.site[6]]=(*g.origin[:2],-1)
                if condition=='before_eclipse':g.flags['berserk_eclipse_era']=0
                g.move_to(12,12);g.run(g.prefix+'_RETRY')
                self.assertFalse(g.spawned,(kind,condition))

    def test_live_dragon_or_pending_second_form_does_not_spawn_a_knight(self):
        g=ArenaGraph('grunbeld');pos=(g.origin[0]+28,g.origin[1]+4,0)
        g.monsters=[('mon_berserk_grunbeld_dragon',pos)];g.hp[pos]=164
        g.move_to(12,12)
        self.assertFalse(g.spawned);self.assertEqual(g.flags['berserk_hunt_grunbeld_phase'],2)
        self.assertEqual(g.hp[pos],164);self.assertEqual(g.flags[g.site[3]],1)
        g=ArenaGraph('grunbeld');g.flags['berserk_hunt_grunbeld_dragon_pending']=1
        g.move_to(12,12);self.assertFalse(g.spawned)

    def test_geometry_all_entrances_recesses_and_objectives_remain_reachable(self):
        for kind in SITES:
            g=ArenaGraph(kind)
            for start in ((12,0),(12,23),(0,12),(23,12)):
                seen=connected(g.rows,start,blocked='#TbI?A')
                for p in ((12,12),(6,6),(17,6),(6,17),(17,17)):
                    self.assertIn(p,seen,(kind,start,p))
            for mob in g.map['place_monster']:
                self.assertNotEqual(mob['monster'],g.site[2])
                self.assertNotEqual(g.rows[mob['y']][mob['x']],'#')
            self.assertEqual(g.map['terrain']['#'],'t_rock')
            self.assertTrue(all(not g.visible((g.origin[0]+x,g.origin[1]+y,0))
                                for x,y in ((6,6),(17,6),(6,17),(17,17))))

    def test_no_freezing_teleporting_or_map_reset_is_added_to_encounters(self):
        es=objects(MOD/'effects/hunt_arena_eocs.json')
        for s in SITES.values():
            path={'first_hunt.json':'first_hunt','local_breach.json':'local_breach',
                  'apostle_wyald.json':'wyald_rosine_hunt','apostle_rosine.json':'wyald_rosine_hunt',
                  'apostle_grunbeld.json':'grunbeld_hunt'}[s[0]]
            es += [e for e in objects(MOD/'effects'/(path+'_eocs.json'))
                   if e['id'].endswith(('_ENTER','_RETRY','_ENSURE_BOSS'))]
        serialized=str(es)
        for operation in ('u_teleport','npc_teleport','mapgen_update','u_hp(',
                          'CANNOT_MOVE','IMMOBILE','CANNOT_ATTACK'):
            self.assertNotIn(operation,serialized)

    def test_new_strings_exist_in_both_compiled_catalogs(self):
        strings=set()
        def visit(v):
            if isinstance(v,list):
                for x in v:visit(x)
            elif isinstance(v,dict):
                for k,x in v.items():
                    if k in ('name','description','u_message') and isinstance(x,str):strings.add(x)
                    else:visit(x)
        for p in ['effects/hunt_arena_eocs.json','furniture/hunt_arenas.json']:visit(objects(MOD/p))
        for lang in ('ru','zh_CN'):
            with (MOD/'lang/mo'/lang/'LC_MESSAGES/Berserk.mo').open('rb') as f:cat=gettext.GNUTranslations(f)
            for s in strings:self.assertNotEqual(cat.gettext(s),s,(lang,s))
