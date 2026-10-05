"""Exercise persisted layout dispatch through actual EOCs, without CDDA."""
import copy
import unittest

from test_flora_siege import ready


class FloraLayoutVersions(unittest.TestCase):
    def configured(self,version,marker=True):
        graph=ready()
        graph.flags['berserk_flora_treehouse_layout']=version
        if marker and version:
            graph.furniture[(-82,60,0)]=('f_berserk_flora_treehouse_threshold_v2'
                                       if version==2 else 'f_berserk_flora_treehouse_threshold')
        return graph

    def test_physical_threshold_selects_version_without_changing_story_or_gifts(self):
        for version in (1,2):
            g=self.configured(0)
            g.furniture[(-82,60,0)]=('f_berserk_flora_treehouse_threshold_v2'
                                     if version==2 else 'f_berserk_flora_treehouse_threshold')
            g.flags.update(berserk_flora_siege_state=1,berserk_flora_aid_authorized=1,
                           berserk_flora_armor_claimed=1)
            before=copy.deepcopy(g.flags)
            g.run('EOC_BERSERK_FLORA_TREEHOUSE_REGISTER')
            expected={**before,'berserk_flora_treehouse_layout':version}
            self.assertEqual(g.flags,expected)

    def test_missing_burned_marker_keeps_saved_version(self):
        for version in (0,1,2):
            g=self.configured(version,marker=False)
            before=copy.deepcopy(g.flags)
            g.run('EOC_BERSERK_FLORA_TREEHOUSE_REGISTER')
            self.assertEqual(g.flags,before)

    def test_all_four_stages_dispatch_to_actual_layout_and_do_not_repeat(self):
        for version in (0,1,2):
            g=self.configured(version)
            g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
            g.run('EOC_BERSERK_FLORA_START_SIEGE')
            for clock in (30,90,600):
                g.clock=clock;g.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            prefix=('berserk_flora_treehouse_v2_' if version==2 else
                    'berserk_flora_treehouse_' if version==1 else 'berserk_flora_')
            self.assertEqual(len(g.siege_updates),16)
            self.assertTrue(all(id.startswith(prefix) for id,_ in g.siege_updates))
            self.assertEqual({pos for id,pos in g.siege_updates},
                             {(-96,48,0),(-72,48,0),(-96,72,0),(-72,72,0)})
            saved=copy.deepcopy(g)
            for clock in (1200,3600):
                saved.clock=clock;saved.run('EOC_BERSERK_FLORA_SIEGE_TICK')
            self.assertEqual(saved.siege_updates,g.siege_updates)
            self.assertEqual(saved.spawns,g.spawns)

    def test_start_refreshes_version_before_first_patch(self):
        g=self.configured(2)
        g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
        g.flags['berserk_flora_treehouse_layout']=0
        g.run('EOC_BERSERK_FLORA_START_SIEGE')
        self.assertEqual(g.flags['berserk_flora_treehouse_layout'],2)
        self.assertTrue(all(id.startswith('berserk_flora_treehouse_v2_warning_')
                            for id,_ in g.siege_updates))

    def test_finished_old_siege_does_not_run_new_scene_or_give_another_suit(self):
        for version in (0,1,2):
            g=self.configured(version)
            g.flags.update(berserk_flora_stage=3,berserk_flora_siege_state=5,
                           berserk_flora_armor_claimed=1)
            g.run('EOC_BERSERK_FLORA_PREPARE_SIEGE')
            g.run('EOC_BERSERK_FLORA_START_SIEGE')
            self.assertFalse(g.siege_updates)
            self.assertFalse(g.spawns)
            self.assertFalse(g.inventory)


if __name__=='__main__':unittest.main()
