"""Owner room annotation and referral gates; static/native-grid checks."""
import json,unittest,gettext
from pathlib import Path
from test_reference_journal_33 import MOD,EOCS,TOPICS,walk
ROOT=MOD.parents[1]
D=json.loads((ROOT/'docs/location_projects/flora-3.3-04.json').read_text())
class Home(unittest.TestCase):
 def test_notes_and_rooms_match_owner_coordinates(self):
  f={(x,y):k for k,x,y in D['furniture']}
  self.assertEqual(f[11,17],'f_berserk_flora_stone_hearth');self.assertEqual(f[19,17],'f_berserk_flora_house_rules')
  self.assertEqual(f[11,19],'f_berserk_flora_scene');self.assertEqual(f[12,6],'f_berserk_flora_manuscript')
  self.assertEqual(f[11,28],'f_berserk_flora_linen_bed');self.assertEqual(f[16,29],'f_berserk_flora_linen_bed')
 def test_box_aisle_and_new_doors_are_open(self):
  f={(x,y):k for k,x,y in D['furniture']}
  for y in range(25,28):self.assertNotIn((34,y),f)
  for x,y in [(20,7),(29,7),(29,25),(24,28)]:self.assertEqual(D['rows'][y][x],'+')
  for x in [34,35]:self.assertEqual(D['rows'][29][x],'#')
 def test_stock_is_real_and_no_modern_cans_or_powered_tools(self):
  f={(x,y):k for k,x,y in D['furniture']}
  for obj in D['stock']:self.assertIn((obj['x'],obj['y']),f);self.assertGreater(obj['amount'],0)
  ids={x['item'] for x in D['stock']};self.assertIn('dry_meat',ids);self.assertFalse(any('can_' in x or 'electric' in x for x in ids))
 def test_aid_always_has_real_answers(self):
  rs=TOPICS['TALK_BERSERK_FLORA_AID']['responses']
  self.assertGreaterEqual(len([r for r in rs if r['topic']!='TALK_BERSERK_FLORA' and 'condition' not in r]),3)
 def test_four_dangers_have_substantive_followups(self):
  for k in ['COUNT','WYALD','ROSINE','GRUNBELD']:
   t=TOPICS['TALK_BERSERK_FLORA_KNOWN_'+k]
   self.assertGreater(len(t['responses']),1)
   self.assertGreater(len(TOPICS[t['responses'][0]['topic']]['dynamic_line']),80)
 def test_automatic_completion_does_not_reveal_or_search_for_flora(self):
  body=EOCS['EOC_BERSERK_LATE_FLORA_CHECK']['effect']
  self.assertFalse(any(x.get('run_eocs') in ['EOC_BERSERK_FLORA_DIRECTIONS','EOC_BERSERK_FLORA_SEEK'] for x in walk(body)))
  self.assertTrue(any(x.get('assign_mission')=='MISSION_BERSERK_FLORA_REFERRAL' for x in walk(body)))
 def test_both_smiths_offer_the_same_saved_route(self):
  for who in ['GODO','RICKERT']:
   t=TOPICS['TALK_BERSERK_'+who+'_FLORA_REFERRAL']
   self.assertEqual(t['responses'][0]['effect'],[{'run_eocs':'EOC_BERSERK_FLORA_HOME31_HEAR'}])
 def test_published_gettext_plural_entries_are_complete(self):
  for lang,n in [('ru',3),('zh_CN',1)]:
   with (MOD/f'lang/mo/{lang}/LC_MESSAGES/Berserk.mo').open('rb') as stream:g=gettext.GNUTranslations(stream)
   for k in {k[0] for k in g._catalog if isinstance(k,tuple)}:
    for i in range(n):self.assertIn((k,i),g._catalog)
if __name__=='__main__':unittest.main()
