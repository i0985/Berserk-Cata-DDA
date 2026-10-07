"""Exercise 3.2 orders as JSON transactions; not native CDDA or a worldgen test."""
import collections
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'mods/Berserk'
def objects(path):
    rows=json.loads((MOD/path).read_text());return rows if isinstance(rows,list) else [rows]
class Forge:
    def __init__(self):
        self.eocs={r['id']:r for r in objects('effects/godo_eocs.json')}
        self.topics={r['id']:r for r in objects('dialogue/godo.json')}
        self.vars=collections.defaultdict(int, {'berserk_eclipse_era':1});self.items=collections.Counter()
        self.profession='unemployed'
        self.bionics={'bio_berserk_hand_stump'};self.now=1000;self.at_smith=True
        self.actor='rickert';self.at_forge=True;self.following=False
        self.missions=set();self.repair_item=None;self.item_hp=1000;self.item_max=4000
    def available(self,topic):
        return [r for r in self.topics[topic]['responses']
                if 'condition' not in r or self.condition(r['condition'])]
    def choose(self,topic,text):
        response=next(r for r in self.available(topic) if r['text']==text)
        if 'effect' in response:self.effect(response['effect'])
        return response['topic']
    def value(self,s):
        s=s.replace("time('now')",str(self.now))
        s=s.replace("n_hp('ALL')",str(self.item_hp)).replace("n_hp_max('torso')",str(self.item_max))
        s=s.replace("n_monsters_nearby('mon_berserk_godo', 'radius': 0, 'attitude': 'both')",str(int(self.at_smith and self.actor=='godo')))
        s=re.sub(r'\b(?:[un]_)?berserk_\w+\b',lambda match:str(self.vars[match[0]]),s)
        return eval(s,{'__builtins__':{}},{})
    def condition(self,c):
        if isinstance(c,str):
            return {'has_beta':self.actor!='book','npc_is_monster':self.actor=='godo',
                    'npc_is_npc':self.actor=='rickert','npc_following':self.following}[c]
        if 'and' in c:return all(self.condition(v) for v in c['and'])
        if 'or' in c:return any(self.condition(v) for v in c['or'])
        if 'not' in c:return not self.condition(c['not'])
        if 'math' in c:return bool(self.value(c['math'][0]))
        if 'test_eoc' in c:
            if c['test_eoc']=='EOC_BERSERK_GODO_KNOWN':return True
            return self.condition(self.eocs[c['test_eoc']]['condition'])
        if 'u_has_items' in c:
            v=c['u_has_items'];return self.items[v['item']]>=v.get('count',v.get('charges',0))
        if 'u_has_bionics' in c:return c['u_has_bionics'] in self.bionics
        if 'u_has_mission' in c:return c['u_has_mission'] in self.missions
        if 'u_profession' in c:return self.profession==c['u_profession']
        if 'npc_has_class' in c:return self.actor=='rickert' and c['npc_has_class']=='NC_BERSERK_RICKERT'
        if 'u_at_om_location' in c or 'npc_at_om_location' in c:return self.at_forge
        raise AssertionError(c)
    def run(self,id):
        row=self.eocs[id]
        if 'condition' not in row or self.condition(row['condition']):self.effect(row['effect'])
    def effect(self,v):
        if v=='follow':self.following=True
        elif isinstance(v,list):
            for part in v:self.effect(part)
        elif 'if' in v:
            branch='then' if self.condition(v['if']) else 'else'
            if branch in v:self.effect(v[branch])
        elif 'run_eocs' in v:self.run(v['run_eocs'])
        elif 'math' in v:
            left,right=v['math'][0].split(' = ')
            if left=="n_hp('ALL')":self.item_hp=self.value(right)
            else:self.vars[left]=self.value(right)
        elif 'u_consume_item' in v:
            number=v.get('charges',v.get('count',1));id=v['u_consume_item']
            assert self.items[id]>=number
            self.items[id]-=number
        elif 'u_spawn_item' in v:
            number=v.get('count',1)
            if isinstance(number,dict):number=self.vars['u_'+number['u_val']]
            self.items[v['u_spawn_item']]+=number
        elif 'assign_mission' in v:self.missions.add(v['assign_mission'])
        elif 'finish_mission' in v:self.missions.discard(v['finish_mission'])
        elif 'u_run_inv_eocs' in v:
            query=v['search_data'][0]
            if self.repair_item in query['id'] and self.condition(query['condition']):
                for id in v['true_eocs']:self.run(id)
        elif 'u_message' in v or 'turn_cost' in v:pass
        else:raise AssertionError(v)

class Orders(unittest.TestCase):
    def run_eoc(self,f,id):f.run('EOC_BERSERK_GODO_'+id)
    def arm(self,f):
        f.actor='rickert'
        f.items.update({'steel_lump':8,'pipe':2,'spring':2,'leather':4,'charcoal':200})
        for id in ['START_ARM','ARM_METAL','ARM_FITTINGS']:self.run_eoc(f,id)
    def sword(self,f):
        f.actor='godo'
        f.items.update({'steel_lump':32,'hc_steel_lump':8,'charcoal':600,'leather':4})
        self.run_eoc(f,'START_SWORD')
        for _ in range(4):self.run_eoc(f,'SWORD_IRON')
        self.run_eoc(f,'SWORD_TEMPER')
    def test_arm_wait_and_repeat_claim(self):
        f=Forge();self.arm(f);self.run_eoc(f,'ARM_CLAIM')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],0)
        f.now+=21600
        for _ in range(3):self.run_eoc(f,'ARM_CLAIM')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],1)
        self.assertEqual(f.vars['u_berserk_godo_arm_state'],4)
    def test_sword_partial_delivery_wait_and_repeat(self):
        f=Forge();f.actor='godo';f.items['steel_lump']=16;self.run_eoc(f,'START_SWORD')
        self.run_eoc(f,'SWORD_IRON');self.run_eoc(f,'SWORD_IRON')
        self.assertEqual(f.vars['u_berserk_godo_sword_iron_given'],16)
        self.assertEqual(f.vars['u_berserk_godo_sword_state'],1)
        f.items.update({'steel_lump':16,'hc_steel_lump':8,'charcoal':600,'leather':4})
        for id in ['SWORD_IRON','SWORD_IRON','SWORD_TEMPER','SWORD_CLAIM']:self.run_eoc(f,id)
        self.assertEqual(f.items['true_guts_sword'],0)
        f.now+=172800
        for _ in range(2):self.run_eoc(f,'SWORD_CLAIM')
        self.assertEqual(f.items['true_guts_sword'],1)
    def test_missing_materials_consume_nothing(self):
        f=Forge();f.items['steel_lump']=7;self.run_eoc(f,'START_ARM');self.run_eoc(f,'ARM_METAL')
        self.assertEqual(f.items['steel_lump'],7);self.assertEqual(f.vars['u_berserk_godo_arm_state'],1)
    def test_orders_are_independent(self):
        f=Forge();self.arm(f);self.sword(f)
        self.assertEqual(f.vars['u_berserk_godo_arm_state'],3)
        self.assertEqual(f.vars['u_berserk_godo_sword_state'],3)
        f.now+=172800;f.actor='rickert';self.run_eoc(f,'ARM_CLAIM');f.actor='godo';self.run_eoc(f,'SWORD_CLAIM')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],1);self.assertEqual(f.items['true_guts_sword'],1)
    def test_existing_start_equipment_cannot_start_duplicate_order(self):
        f=Forge();f.items['true_guts_sword']=1;f.bionics.add('bio_berserk_arm_cannon')
        self.run_eoc(f,'START_ARM');f.actor='godo';self.run_eoc(f,'START_SWORD')
        self.assertEqual(f.vars['u_berserk_godo_arm_state'],0);self.assertEqual(f.vars['u_berserk_godo_sword_state'],0)
    def test_partial_sword_deposit_refunded_once(self):
        f=Forge();f.actor='godo';f.items['steel_lump']=16;self.run_eoc(f,'START_SWORD')
        for _ in range(2):self.run_eoc(f,'SWORD_IRON')
        f.items['true_guts_sword']=1
        for _ in range(2):self.run_eoc(f,'SWORD_REFUND')
        self.assertEqual(f.items['steel_lump'],16);self.assertEqual(f.items['true_guts_sword'],1)
    def test_installing_another_cannon_returns_order_deposits(self):
        f=Forge();self.arm(f);f.bionics.add('bio_berserk_arm_cannon');f.now+=21600
        self.run_eoc(f,'ARM_CLAIM');self.run_eoc(f,'ARM_REFUND')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],0)
        self.assertEqual(f.items['steel_lump'],8);self.assertEqual(f.items['charcoal'],200)
    def test_remote_order_actions_do_not_consume_or_award(self):
        f=Forge();self.arm(f);f.now+=21600;f.actor='book'
        self.run_eoc(f,'ARM_CLAIM');self.assertEqual(f.items['bio_berserk_arm_cannon'],0)
    def test_repair_cancel_and_healthy_piece_are_free(self):
        f=Forge();f.actor='godo';f.items.update({'steel_lump':1,'charcoal':50})
        self.run_eoc(f,'REPAIR_PICK');self.assertEqual(f.items['steel_lump'],1)
        f.repair_item='true_guts_sword';f.item_hp=f.item_max
        self.run_eoc(f,'REPAIR_PICK');self.assertEqual(f.items['charcoal'],50)
    def test_repair_preserves_existing_piece_and_costs_once(self):
        f=Forge();f.actor='godo';f.items.update({'steel_lump':2,'charcoal':100,'true_guts_sword':1});f.repair_item='true_guts_sword'
        self.run_eoc(f,'REPAIR_PICK');self.run_eoc(f,'REPAIR_PICK')
        self.assertEqual(f.item_hp,f.item_max);self.assertEqual(f.items['true_guts_sword'],1)
        self.assertEqual(f.items['steel_lump'],1);self.assertEqual(f.items['charcoal'],50)
    def test_prepaid_arm_order_transfers_without_reset(self):
        f=Forge();f.vars['u_berserk_godo_arm_state']=2
        f.items.update({'spring':2,'leather':4,'charcoal':200})
        self.run_eoc(f,'START_ARM');self.run_eoc(f,'ARM_FITTINGS');f.now+=21600
        f.actor='godo';self.run_eoc(f,'ARM_CLAIM')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],0)
        f.actor='rickert';self.run_eoc(f,'ARM_CLAIM');self.run_eoc(f,'ARM_CLAIM')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],1)
    def test_recruitment_requires_respect_and_allows_rejoining(self):
        f=Forge();f.run('EOC_BERSERK_RICKERT_JOIN');self.assertFalse(f.following)
        f.vars['n_berserk_rickert_respect']=1;f.actor='book'
        f.run('EOC_BERSERK_RICKERT_JOIN');self.assertFalse(f.following)
        f.actor='rickert';f.run('EOC_BERSERK_RICKERT_JOIN');self.assertTrue(f.following)
        f.following=False;f.vars['n_berserk_rickert_respect']=0
        f.run('EOC_BERSERK_RICKERT_JOIN');self.assertTrue(f.following)
    def test_both_bad_replies_permanently_close_all_recruitment_entries(self):
        for bad in ['I need another fighter. You can take the first blows.',
                    'I give the orders. You follow them.']:
            with self.subTest(reply=bad):
                f=Forge();topic=f.choose('TALK_BERSERK_RICKERT','Could we travel together?')
                if bad.startswith('I give'):
                    topic=f.choose(topic,'I need a craftsman and a companion. We choose the route and retreat together.')
                self.assertEqual(f.choose(topic,bad),'TALK_BERSERK_RICKERT_REFUSE')
                self.assertEqual(f.vars['n_berserk_rickert_recruit_refused'],1)
                # Stored NPC variables still close the branch in a fresh dialogue context.
                loaded=Forge();loaded.vars.update(json.loads(json.dumps(f.vars)))
                for id in ['TALK_BERSERK_RICKERT','TALK_BERSERK_RICKERT_CRAFT']:
                    self.assertFalse(any(r['topic']=='TALK_BERSERK_RICKERT_ROAD' for r in loaded.available(id)))
                for id in ['TALK_BERSERK_RICKERT_ROAD','TALK_BERSERK_RICKERT_ROAD_PLAN']:
                    self.assertEqual([r['topic'] for r in loaded.available(id)],['TALK_BERSERK_RICKERT'])
                loaded.vars['n_berserk_rickert_respect']=1
                loaded.run('EOC_BERSERK_RICKERT_JOIN');self.assertFalse(loaded.following)
    def test_neutral_departure_and_previous_default_respect_do_not_refuse(self):
        f=Forge();topic=f.choose('TALK_BERSERK_RICKERT','Could we travel together?')
        f.choose(topic,'Ask something else.')
        self.assertEqual(f.vars['n_berserk_rickert_recruit_refused'],0)
        topic=f.choose('TALK_BERSERK_RICKERT','Could we travel together?')
        topic=f.choose(topic,'I need a craftsman and a companion. We choose the route and retreat together.')
        f.choose(topic,'Ask something else.')
        self.assertEqual(f.vars['n_berserk_rickert_recruit_refused'],0)
        f.choose(topic,'We protect each other. You have a say in where we go.')
        self.assertTrue(f.following)
        f.run('EOC_BERSERK_RICKERT_REFUSE_RECRUITMENT')
        self.assertEqual(f.vars['n_berserk_rickert_recruit_refused'],0)
    def test_refusal_preserves_prepaid_order_and_forge_services(self):
        f=Forge();self.arm(f)
        topic=f.choose('TALK_BERSERK_RICKERT','Could we travel together?')
        f.choose(topic,'I need another fighter. You can take the first blows.')
        self.assertEqual(f.vars['u_berserk_godo_arm_state'],3)
        self.assertTrue(any(r['topic']=='TALK_BERSERK_GODO_ARM' for r in f.available('TALK_BERSERK_RICKERT')))
        f.now+=21600;self.run_eoc(f,'ARM_CLAIM')
        self.assertEqual(f.items['bio_berserk_arm_cannon'],1)
        self.sword(f);f.now+=172800;self.run_eoc(f,'SWORD_CLAIM')
        self.assertEqual(f.items['true_guts_sword'],1)
    def test_companion_orders_require_return_to_forge(self):
        f=Forge();self.arm(f);f.now+=21600;f.at_forge=False
        self.run_eoc(f,'ARM_CLAIM');self.assertEqual(f.items['bio_berserk_arm_cannon'],0)
        f.at_forge=True;self.run_eoc(f,'ARM_CLAIM');self.assertEqual(f.items['bio_berserk_arm_cannon'],1)
    def test_cannon_repair_is_rickerts_work(self):
        f=Forge();f.items.update({'steel_lump':1,'charcoal':50});f.repair_item='bio_berserk_arm_cannon'
        f.actor='godo';self.run_eoc(f,'REPAIR_PICK');self.assertLess(f.item_hp,f.item_max)
        f.actor='rickert';f.run('EOC_BERSERK_RICKERT_REPAIR_PICK');self.assertEqual(f.item_hp,f.item_max)
        self.assertEqual(f.items['steel_lump'],0)

class Data(unittest.TestCase):
    def test_topic_references_and_no_duplicate_questions(self):
        rows=[r for p in (MOD/'dialogue').glob('*.json') for r in objects(p.relative_to(MOD))]
        ids={r['id'] for r in rows}
        for row in rows:
            if row['id'].startswith(('TALK_BERSERK_GODO','TALK_BERSERK_RICKERT','TALK_BERSERK_JOURNAL','TALK_BERSERK_ROAD','TALK_BERSERK_FLORA','TALK_BERSERK_SKULL')):
                names=[r['text'] for r in row['responses']]
                self.assertEqual(len(names),len(set(names)),row['id'])
                for r in row['responses']:
                    if r['topic'].startswith('TALK_BERSERK_'):self.assertIn(r['topic'],ids)
    def test_routes_and_matching_stairs(self):
        data=json.loads((ROOT/'docs/location_projects/godo-3.2-02.json').read_text())
        for rows in data['floors'].values():
            self.assertEqual(len(rows),24);self.assertTrue(all(len(row)==24 for row in rows))
            seen={(11,18)};queue=collections.deque(seen)
            while queue:
                x,y=queue.popleft()
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    p=(x+dx,y+dy)
                    if 0<=p[0]<24 and 0<=p[1]<24 and p not in seen and rows[p[1]][p[0]] not in '#wTFAbrcstk':
                        seen.add(p);queue.append(p)
            if rows[18][11]=='<':
                for key in ['godo','rickert','rescue_arrival','knight_wait','west_exit','east_exit']:
                    x,y,z=data['anchors'][key];self.assertIn((x,y),seen,key)
        self.assertEqual(data['floors']['ground'][18][11],'<')
        self.assertEqual(data['floors']['loft'][18][11],'>')
        old=json.loads((ROOT/'docs/location_projects/godo-3.2-01.json').read_text())
        for key in ['godo','rickert','stairs','rescue_arrival','knight_wait']:
            self.assertEqual(data['anchors'][key],old['anchors'][key],key)
    def test_native_menu_no_yes_no_chain(self):
        e=next(r for r in objects('effects/wyald_rosine_hunt_eocs.json') if r['id']=='EOC_BERSERK_HUNT_JOURNAL_USE')
        self.assertEqual(e['effect']['open_dialogue']['topic'],'TALK_BERSERK_ROAD_JOURNAL')
    def test_recipe_and_sword_sources(self):
        r=objects('recipes/arm_cannon_recipes.json')[0];self.assertEqual(r['difficulty'],8)
        self.assertFalse(any(r.get('result')=='true_guts_sword' for p in (MOD/'recipes').glob('*.json') for r in objects(p.relative_to(MOD))))
    def test_spoilers_absent_from_peaceful_preparation(self):
        rows={r['id']:r for r in objects('dialogue/flora.json')}
        for id in ['PREPARATION','SIEGE_CONFIRM','SIEGE_OWNER_CONFIRM','PREPARED']:
            text=rows['TALK_BERSERK_FLORA_'+id]['dynamic_line'].lower()
            for word in ['burn','attack','siege','one-time','trigger']:self.assertNotIn(word,text)

if __name__=='__main__':unittest.main()
