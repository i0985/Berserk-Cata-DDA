"""Owner playtest regressions for permanent costs and forest placement.

Native stamina equation and fixed-special footprint checks, not a CDDA run.
"""
import gettext
import hashlib
import json
import unittest

from test_named_apostle_dialogues_33 import Contract, STEMS, OLD, MUTATIONS
from test_reference_journal_33 import MOD, EOCS, walk

ROOT = MOD.parents[1]


def mutation(kind, line, suffix):
    return MUTATIONS['BERSERK_'+kind+'_'+line+'_'+suffix]


def stat(kind, line, name):
    return sum(v.get('add',0) for suffix in ['SEED','FORM']
               for ench in mutation(kind,line,suffix).get('enchantments',[])
               for v in ench.get('values',[]) if v['value']==name)


class PawnCosts(unittest.TestCase):
    def test_pawns_no_longer_receive_near_flesh_strength_or_damage(self):
        for kind in STEMS:
            self.assertLess(stat(kind,'PAWN','STRENGTH'),stat(kind,'FLESH','STRENGTH'))
            pawn = mutation(kind,'PAWN','FORM')
            flesh = mutation(kind,'FLESH','FORM')
            self.assertLess(pawn['armor'][0]['cut'],flesh['armor'][0]['cut'])
        self.assertEqual(stat('COUNT','PAWN','STRENGTH'),0)
        self.assertEqual(stat('WYALD','PAWN','STRENGTH'),1)
        self.assertFalse(any(v['value']=='MELEE_DAMAGE' and (v.get('add',0)>0 or v.get('multiply',0)>0)
                             for ench in mutation('WYALD','PAWN','FORM')['enchantments']
                             for v in ench.get('values',[])))

    def test_native_zero_based_stamina_modifier_is_a_real_penalty(self):
        # Character::update_stamina evaluates modify_value(STAMINA_REGEN_MOD,0)
        # and adds the result to its base multiplier. multiply=-0.15 gave zero.
        for kind in ['WYALD','GRUNBELD']:
            ench = mutation(kind,'PAWN','SEED')['enchantments'][0]
            values = [v for v in ench['values'] if v['value']=='STAMINA_REGEN_MOD']
            result = (0 + sum(v.get('add',0) for v in values)) * (
                1 + sum(v.get('multiply',0) for v in values))
            self.assertLess(1+result,0.85)
            self.assertGreater(1+result,0.1)

    def test_rosine_pawn_keeps_senses_but_has_no_full_wings_or_large_speed_bonus(self):
        form=mutation('ROSINE','PAWN','FORM')
        self.assertIn('ANTENNAE',form['enchantments'][0]['mutations'])
        self.assertFalse({'WING_GLIDE','FEATHER_FALL','WINGS_2'} & set(form['flags']))
        self.assertLess(stat('ROSINE','PAWN','SPEED'),stat('ROSINE','FLESH','SPEED')/2)
        self.assertLess(stat('ROSINE','PAWN','STRENGTH'),0)

    def test_favor_expiry_and_master_death_leave_the_same_irreversible_body(self):
        for kind in STEMS:
            world=Contract(kind);world.accept()
            world.values['u_berserk_apostol_pawn_favor_until']=world.now+21600
            world.traits.add('BERSERK_'+kind+'_PAWN_POWER')
            self.assertTrue(world.condition({'test_eoc':OLD+kind+'_PAWN_FAVOR'}))
            before={t for t in world.traits if t.endswith(('_FORM','_SEED','_SENSES'))}
            world.now+=21601
            self.assertFalse(world.condition({'test_eoc':OLD+kind+'_PAWN_FAVOR'}))
            world.died();world.run(OLD+kind+'_PAWN_MASTER_SYNC')
            self.assertEqual(before,{t for t in world.traits if t.endswith(('_FORM','_SEED','_SENSES'))})
            body=mutation(kind,'PAWN','FORM')
            self.assertFalse(body['purifiable']);self.assertNotIn('transform',body)
            self.assertEqual(body['enchantments'][0]['condition'],'ALWAYS')

    def test_new_reaction_replaces_one_success_message_without_extra_popup(self):
        with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:
            ru=gettext.GNUTranslations(stream)
        for kind in STEMS:
            accept=EOCS[OLD+kind+'_PAWN_ACCEPT']
            warnings=[x for x in walk(accept) if 'u_message' in x and x.get('type')=='warning']
            self.assertEqual(len(warnings),1)
            self.assertNotEqual(warnings[0]['u_message'],ru.gettext(warnings[0]['u_message']))
            self.assertFalse(warnings[0].get('popup',False))
            for suffix in ['SEED','FORM']:
                text=mutation(kind,'PAWN',suffix)['description']
                self.assertNotEqual(text,ru.gettext(text))

    def test_wyald_paws_restrict_rigid_footwear_as_the_description_says(self):
        self.assertTrue({'hand_l','hand_r','foot_l','foot_r','mouth'} <=
                        set(mutation('WYALD','PAWN','FORM')['restricts_gear']))
        self.assertFalse(mutation('WYALD','PAWN','FORM')['destroys_gear'])


class CanineArt(unittest.TestCase):
    def test_both_wyald_bodies_use_real_native_muzzle_and_ear_layers(self):
        manifest=json.loads((ROOT/'docs/apostol-native-sprite-sources-33.json').read_text())
        for body in ['WYALD_PAWN','WYALD_FLESH']:
            for sex in ['male','female']:
                layers=[s['native_overlay'] for s in manifest['sources'] if s['target']==body and s['sex']==sex]
                self.assertEqual(len(layers),3)
                self.assertTrue(any('MUZZLE' in layer for layer in layers))
                self.assertTrue(any('EARS' in layer for layer in layers))
        self.assertEqual(hashlib.sha256((MOD/manifest['sheet']).read_bytes()).hexdigest(),manifest['sha256'])


class FloraForest(unittest.TestCase):
    def test_native_fixed_special_requires_unvisited_forest_on_every_surrounding_cell(self):
        rows=json.loads((MOD/'overmap/flora_manor.json').read_text())
        special=next(o for o in rows if o['type']=='overmap_special')
        cells={tuple(o['point']):o for o in special['overmaps']}
        self.assertEqual(set(cells),{(x,y,0) for y in range(-4,6) for x in range(-4,6)})
        for point,cell in cells.items():
            self.assertEqual(cell['locations'],['forest'])
            if point not in {(0,0,0),(1,0,0),(0,1,0),(1,1,0)}:
                self.assertEqual(cell['overmap'],'forest')
        self.assertEqual(special['occurrences'],[0,0])
        self.assertIn('GLOBALLY_UNIQUE',special['flags'])

    def test_city_edge_houses_and_existing_submaps_fail_the_native_required_cells(self):
        special=next(o for o in json.loads((MOD/'overmap/flora_manor.json').read_text())
                     if o['type']=='overmap_special')
        cells={tuple(o['point']) for o in special['overmaps']}
        # Port of the fixed-special all_of required_locations predicate only.
        def eligible(terrain,generated):
            return all(terrain.get(p) in ['forest','forest_thick'] and p not in generated for p in cells)
        forest={p:'forest' for p in cells}
        self.assertTrue(eligible(forest,set()))  # Works with no cities at all.
        town_edge=dict(forest);town_edge[(0,-1,0)]='house'
        self.assertFalse(eligible(town_edge,set()))
        self.assertFalse(eligible(forest,{(5,5,0)}))


if __name__ == '__main__':
    unittest.main()
