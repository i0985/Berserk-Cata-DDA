#!/usr/bin/env python3
"""31 October owner annotation, forge referral and substantive Flora answers."""
import copy,json
from recover_apostol_33 import ROOT,MOD,read,write,index,walk,eoc
from build_playtest_fixes_20261024 import tr,localize
from reference_journal_content_33 import allof as both,anyof as either,no as neg,eq
P='EOC_BERSERK_FLORA_HOME31_'
def run(n):return {'run_eocs':n}
def msg(en,ru):return {'u_message':tr(en,ru),'type':'info'}
def text(en,ru):return tr(en,ru)
def response(en,ru,topic,**kw):return dict(text=tr(en,ru),topic=topic,**kw)
def main():
 import build_flora_treehouse as house
 # Export v4 only; never replace a visited map or old siege update.
 house.main()
 rows=read('effects/flora_treehouse_eocs.json');by=index(rows)
 node=by['EOC_BERSERK_FLORA_TREEHOUSE_REGISTER']['effect'][2]
 while node.get('if',{}).get('map_furniture_id') in ['f_berserk_flora_treehouse_threshold_v3','f_berserk_flora_treehouse_threshold_v4']:node=node['else']
 for version in [3,4]:
  node={'if':{'map_furniture_id':'f_berserk_flora_treehouse_threshold_v'+str(version),'loc':{'context_val':'flora_layout'}},'then':{'math':['berserk_flora_treehouse_layout = '+str(version)]},'else':node}
 by['EOC_BERSERK_FLORA_TREEHOUSE_REGISTER']['effect'][2]=node
 write('effects/flora_treehouse_eocs.json',rows)
 rows=read('effects/flora_siege_eocs.json')
 def strip_v4(value):
  if isinstance(value,list):return [strip_v4(x) for x in value]
  if not isinstance(value,dict):return value
  if value.get('if')==eq('berserk_flora_treehouse_layout',4):return strip_v4(value['else'])
  return {k:strip_v4(v) for k,v in value.items()}
 rows=strip_v4(rows)
 for obj in rows:
  for node in list(walk(obj)):
   if node.get('if')==eq('berserk_flora_treehouse_layout',3) and 'mapgen_update' in node.get('then',{}):
    old=copy.deepcopy(node);new=copy.deepcopy(node['then']);new['mapgen_update']=new['mapgen_update'].replace('_v3_','_v4_');node.clear();node.update({'if':eq('berserk_flora_treehouse_layout',4),'then':new,'else':old})
  if obj['id']=='EOC_BERSERK_FLORA_START_SIEGE':
   for node in walk(obj):
    if node.get('popup') and 'u_message' in node:node['u_message']=tr('A thunderous crash shakes the house, as though something has struck through the outer wall. Wood splinters beyond the ward. Flora turns toward the sound: "Away from the entrance. Now!"','Дом содрогается от оглушительного грохота — словно кто-то с чудовищной силой проломил наружную стену. За оберегом трещит дерево. Флора оборачивается на звук: «Отойди от входа. Немедленно!»')
 write('effects/flora_siege_eocs.json',rows)
 # Scenery notes are tables with readable papers, not papers hidden in a tree.
 ids={'f_berserk_flora_manuscript','f_berserk_flora_house_rules','f_berserk_flora_scene','f_berserk_flora_gallery_record','f_berserk_flora_guest_record','f_berserk_flora_garden_record','f_berserk_flora_west_sign','f_berserk_flora_south_sign'}
 for path in MOD.rglob('*.json'):
  data=json.loads(path.read_text());changed=False
  for obj in (data if isinstance(data,list) else [data]):
   if obj.get('id') in ids:obj['looks_like']='f_table';changed=True
  if changed:write(str(path.relative_to(MOD)),data)
 # Completion means the three early encounters, including an existing pact,
 # not Grunbeld, whose story encounter belongs after meeting Flora.
 rows=read('effects/new_horizon_progression_eocs.json');by=index(rows)
 old=by['EOC_BERSERK_LATE_FLORA_CHECK'];eligible=copy.deepcopy(old['condition'])
 old['effect']=[{'if':{'not':{'math':['has_var(berserk_godo_location)']}},'then':run('EOC_BERSERK_GODO_SEEK')},{'if':both(neg(eq('u_berserk_flora_referral_issued')),neg(eq('u_berserk_flora_referral_heard'))),'then':[{'assign_mission':'MISSION_BERSERK_FLORA_REFERRAL'},{'if':{'u_has_mission':'MISSION_BERSERK_FLORA_REFERRAL'},'then':[{'math':['u_berserk_flora_referral_issued = 1']},msg('Return to the woodland forge. Godot or Rickert may know someone who can help with what you have seen.','Вернитесь в лесную кузницу. Годо или Рикерт могут знать того, кто поможет разобраться с пережитым.')]}]}]
 route=by['EOC_BERSERK_FLORA_ROUTE_AVAILABLE'];route['condition']=both(eq('berserk_eclipse_era'),either(eq('u_berserk_eclipse_rescue_state',2),eq('u_berserk_apostol_return_state',2)),either(both({'test_eoc':'EOC_BERSERK_EARLY_HUNTS_CLOSED'},eq('u_berserk_flora_referral_heard')),both({'math':['berserk_flora_stage >= 1']},{'test_eoc':'EOC_BERSERK_FLORA_KNOWN_MANOR_VALID'})))
 write('effects/new_horizon_progression_eocs.json',rows)
 write('missions/flora_referral.json',[{'type':'mission_definition','id':'MISSION_BERSERK_FLORA_REFERRAL','name':tr('Ask at the woodland forge','Расспросить в лесной кузнице'),'description':tr('The three early trails are settled. Speak with Godot or Rickert about what you encountered. They may know someone who understands these beings.','Три ранних следа завершены. Поговорите с Годо или Рикертом о встреченных существах: возможно, они знают того, кто в них разбирается.'),'goal':'MGOAL_CONDITION','goal_condition':eq('u_berserk_flora_referral_heard'),'difficulty':1,'value':0,'origins':['ORIGIN_GAME_START'],'start':{'assign_mission_target':{'om_terrain':'berserk_godo_workshop','var':{'global_val':'berserk_godo_location'},'reveal_radius':0}}}])
 hear=eoc(P+'HEAR',[{'math':['u_berserk_flora_referral_heard = 1']},{'math':['u_berserk_flora_late_clue_given = 1']},{'math':['u_berserk_flora_directions_repaired = 1']},{'if':{'u_has_mission':'MISSION_BERSERK_FLORA_REFERRAL'},'then':{'finish_mission':'MISSION_BERSERK_FLORA_REFERRAL','success':True}},run('EOC_BERSERK_FLORA_DIRECTIONS')],both('u_is_avatar',{'test_eoc':'EOC_BERSERK_EARLY_HUNTS_CLOSED'},eq('berserk_eclipse_era')))
 write('effects/flora_home31_eocs.json',[hear])
 rows=[o for o in read('dialogue/godo.json') if not o['id'].endswith('_FLORA_REFERRAL')];by=index(rows)
 for who,en,ru in [('GODO','A woman lives beyond the deeper woods. Flora. People call her a witch; I have never heard of her turning away someone in need. She knows things I cannot hammer into shape. Rickert kept the turns in the road. Here, I will mark them.','За дальним лесом живёт женщина. Флора. Ведьмой зовут, но я не слышал, чтобы она прогнала того, кому нужна помощь. Есть вещи, с которыми молотом не разберёшься. Рикерт запомнил повороты. Давай отмечу.'),('RICKERT','There is someone you could ask. Flora lives beside an old tree in the woods. Travellers say she treats them kindly, though they call her a witch. Godot has heard of her too. I can show you the road.','Есть человек, которого можно расспросить. Флора живёт у старого дерева в лесу. Путники говорят, что она добра к ним, хотя и зовут ведьмой. Годо тоже о ней слышал. Я покажу дорогу.')]:
  topic='TALK_BERSERK_'+who+'_FLORA_REFERRAL'
  by['TALK_BERSERK_'+who]['responses'].insert(-1,response('Do you know anyone who understands these creatures?','Ты знаешь кого-нибудь, кто разбирается в этих существах?',topic,condition=both({'test_eoc':'EOC_BERSERK_EARLY_HUNTS_CLOSED'},eq('berserk_eclipse_era'),neg(eq('u_berserk_flora_met')))))
  rows.append({'type':'talk_topic','id':topic,'dynamic_line':tr(en,ru),'responses':[response('Show me the road.','Покажи дорогу.','TALK_BERSERK_'+who,effect=[run(P+'HEAR')]),response('Another question.','Я хотел спросить о другом.','TALK_BERSERK_'+who)]})
 write('dialogue/godo.json',rows)
 rows=[o for o in read('dialogue/flora.json') if not (o['id'].startswith('TALK_BERSERK_FLORA_KNOWN_') and o['id'].endswith('_MORE')) and o['id']!='TALK_BERSERK_FLORA_AFTER_VICTORY'];by=index(rows)
 by['TALK_BERSERK_FLORA_AID']['responses']=[response('About supplies for the road.','О припасах в дорогу.','TALK_BERSERK_FLORA_HELP'),response('Tell me about the armor.','Расскажи о доспехе.','TALK_BERSERK_FLORA_ARMOR'),response('What should I do next?','Что мне делать дальше?','TALK_BERSERK_FLORA_NEXT'),response('Another question.','Я хотел спросить о другом.','TALK_BERSERK_FLORA')]
 for res in by['TALK_BERSERK_FLORA_INTRO_SOURCE']['responses']:
  if res['topic']=='TALK_BERSERK_FLORA_INTRO_RECORD':res['condition']=eq('u_berserk_ref_flora_named_source')
 for k in ['COUNT','WYALD','ROSINE','GRUNBELD']:
  t=by['TALK_BERSERK_FLORA_KNOWN_'+k];target='TALK_BERSERK_FLORA_KNOWN_'+k+'_MORE'
  t['responses'].insert(0,response('How can someone become like that?','Как человек становится таким?',target))
  t['responses'].insert(1,response('Does defeating one end the danger?','Его поражение положит конец опасности?','TALK_BERSERK_FLORA_DANGER_BREACH'))
  replies={
   'COUNT':('Fear makes a prison long before iron bars do. If you found people in his house, listen to them. They know more about the price of his protection than any promise could tell you.','Страх строит тюрьму раньше железных решёток. Если ты нашёл в его доме людей, выслушай их. Они знают о цене его покровительства больше, чем любые обещания.'),
   'WYALD':('He gives his appetites the name of freedom. The people made to suffer for them have no freedom at all. Do not let his strength persuade you that cruelty is inevitable.','Он называет свободой собственные желания. У тех, кто за них расплачивается, свободы нет вовсе. Не позволяй его силе убедить тебя, что жестокость неизбежна.'),
   'ROSINE':('A refuge must allow someone to leave it. When every promise of safety demands that you surrender your voice, ask whose peace is really being protected.','Из убежища должно быть можно уйти. Когда за обещанную безопасность требуют отказаться от собственного голоса, стоит спросить, чей покой на самом деле охраняют.'),
   'GRUNBELD':('A sworn duty does not take away the hand that carries it out. Armor may protect its bearer, but it cannot answer for what he chooses to crush beneath it.','Клятва не отнимает у исполнителя собственной воли. Доспех защищает владельца, но не отвечает за то, что тот решает раздавить своей силой.')}
  rows.append({'type':'talk_topic','id':target,'dynamic_line':tr(*replies[k]),'responses':[response('I understand.','Понимаю.','TALK_BERSERK_FLORA_DANGERS')]})
  t['responses'][1]['topic']='TALK_BERSERK_FLORA_AFTER_VICTORY'
 rows.append({'type':'talk_topic','id':'TALK_BERSERK_FLORA_AFTER_VICTORY','dynamic_line':tr('A fallen creature cannot strike again. But the wound through which it reached us may remain. Examine what is left at the place; closing that wound is a separate task.','Павшее существо больше не нападёт. Но рана, через которую оно пришло, может остаться. Осмотри то, что осталось на месте: закрыть эту рану — отдельное дело.'),'responses':[response('Another question.','Я хотел спросить о другом.','TALK_BERSERK_FLORA_DANGERS')]})
 write('dialogue/flora.json',rows)
 localize()
if __name__=='__main__':main()
