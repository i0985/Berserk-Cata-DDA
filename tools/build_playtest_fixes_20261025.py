#!/usr/bin/env python3
"""Early discovery, authored sprite families and owner-marked chapel export."""
import copy
import hashlib
import json
from pathlib import Path

from recover_apostol_33 import ROOT, MOD, read, write, index, eoc
from reference_journal_content_33 import math, allof as both, anyof as either, no as neg, test, eq
from build_playtest_fixes_20261024 import tr, localize

P='EOC_BERSERK_FIX25_'
E=[]
def run(id_,**kw):return {'run_eocs':id_,**kw}


def authored_sprites():
    policy=json.loads((ROOT/'docs/authored-common-sprites-2026-10-25.json').read_text())
    for entry in policy['sheets']:
        assert hashlib.sha256((MOD/entry['file']).read_bytes()).hexdigest()==entry['sha256']
        rows=read(entry['definition']);obj=rows[0]
        obj['compatibility']=policy['compatibility']
        obj['tiles-new'][0]['tiles'][0]['id']=entry['ids'][0] if len(entry['ids'])==1 else entry['ids']
        write(entry['definition'],rows)
    rows=read('monsters/behelit_site_guardians.json')
    for obj in rows:
        if obj['id'] in ['mon_berserk_chapel_guardian','mon_berserk_expedition_guardian']:
            obj['looks_like']=obj['copy-from']
    write('monsters/behelit_site_guardians.json',rows)


def chapel():
    project=json.loads((ROOT/'docs/location_projects/chapel-3.3-01.json').read_text())
    maps=copy.deepcopy(project['mapgen'])
    loot=[{**item,'y':item['y']+i*24} for i,m in enumerate(maps) for item in m['object'].get('place_loot',[])]
    for item in loot:
        if item.get('item')=='berserk_chapel_ritual_note':item.update(x=19,y=25)
    for i,obj in enumerate(maps):
        body=obj['object'];body['rows']=project['rows'][24*i:24*i+24]
        body['place_furniture']=[{**f,'y':f['y']-24*i} for f in project['furniture'] if 24*i<=f['y']<24*i+24]
        body['place_loot']=[{**item,'y':item['y']-24*i} for item in loot if 24*i<=item['y']<24*i+24]
        for group in body.get('place_items',[]):
            if group.get('item')=='religious_books':group.update(x=19,y=14-24*i)
    rows=read('mapgen/behelit_sites.json');by={x['om_terrain'][0]:x for x in maps}
    for i,obj in enumerate(rows):
        key=obj.get('om_terrain',[''])[0]
        if key in by:rows[i]=by[key]
    write('mapgen/behelit_sites.json',rows)


def physical_directions():
    rows=read('effects/location_interactions_eocs.json');by=index(rows)
    obj=by['EOC_BERSERK_READ_EXPEDITION_TRANSFER_NOTE']
    marker='u_berserk_forge_trace_expedition_v25'
    grant={'if':neg(eq(marker)),'then':[math(marker+' = 1'),run('EOC_BERSERK_GODO_LEARN_TRACE'),run('EOC_BERSERK_GODO_ROUTE_MISSION')]}
    if grant not in obj['effect']:obj['effect'].insert(-1,grant)
    write('effects/location_interactions_eocs.json',rows)
    # The pinned log and entrance inscription are actual sources. Examining
    # them reads their contents, unlike a passive book or arrival notification.
    rows=read('effects/behelit_site_eocs.json');by=index(rows)
    by['EOC_BERSERK_CHAPEL_RECORD']['effect']=run('EOC_BERSERK_READ_CHAPEL_RELIEF_ROSTER')
    by['EOC_BERSERK_EXPEDITION_RECORD']['effect']=run('EOC_BERSERK_READ_EXPEDITION_TRANSFER_NOTE')
    write('effects/behelit_site_eocs.json',rows)
    rows=read('effects/location_scenery_eocs.json');by=index(rows)
    by['EOC_BERSERK_SCENERY_EXPEDITION']['effect']=run('EOC_BERSERK_READ_EXPEDITION_TRANSFER_NOTE')
    write('effects/location_scenery_eocs.json',rows)
    # The October 24 fallback must not grant a stranger unintroduced names.
    rows=read('dialogue/godo.json');by=index(rows)
    root=by['TALK_BERSERK_RICKERT_ECLIPSE']
    for response in root['responses']:
        if response.get('text')=='What do you remember of the Band?':
            response.update(text=tr('How have you been holding up?','Как ты сам держишься?'),topic='TALK_BERSERK_RICKERT_RECENT_DAYS')
    write('dialogue/godo.json',rows)


def entry_hints():
    hints=[('CARAVAN',['berserk_road_caravan'],
        'Supplies and a bundle of papers show beneath the broken wagon. You could approach the wreckage and examine what is still there.',
        'Под обломками обоза виднеются припасы и свёрток бумаг. Можно подойти к завалу и осмотреть, что там уцелело.'),
        ('EXPEDITION',['berserk_lost_expedition'],
        'A field log is pinned to the table in the northwestern tent. Its pages are still legible; you could examine the abandoned equipment beside it.',
        'На столе в северо-западной палатке прижат полевой журнал. Страницы ещё можно разобрать — стоит осмотреть брошенное снаряжение рядом.'),
        ('CHAPEL',['berserk_desecrated_chapel_nave','berserk_desecrated_chapel_reliquary'],
        'An old list of travelers and donated supplies survives near the southern entrance. Some writing remains beneath the later scratches.',
        'У южного входа уцелел старый список путников и принесённых припасов. Под поздними царапинами ещё можно разобрать записи.')]
    for key,terrains,en,ru in hints:
        point={'context_val':'berserk_hint_point'};saved={'u_val':'berserk_hint_'+key.lower()}
        same=both(math('has_var(u_berserk_hint_'+key.lower()+')'),*[math('u_berserk_hint_'+key.lower()+'.'+a+' == _berserk_hint_point.'+a) for a in 'xyz'])
        actions=[{'u_location_variable':point},{'location_variable_adjust':point,'overmap_tile':True}]
        if key=='CHAPEL':actions.append({'if':{'u_at_om_location':'berserk_desecrated_chapel_nave'},'then':{'location_variable_adjust':point,'overmap_tile':True,'y_adjust':-1}})
        actions.append({'if':neg(same),'then':[{'copy_var':point,'target_var':saved},{'u_message':tr(en,ru),'type':'info','popup':True}]})
        E.append(eoc(P+'HINT_'+key,actions,both('u_is_avatar',either(*[{'u_at_om_location':t} for t in terrains]))))
    E.append(eoc(P+'ARRIVAL',[run(P+'HINT_'+k) for k,*_ in hints],'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))


def reliable_hunt():
    # 0.I's replace branch searches existing overmaps, and mutates its search
    # type before the second pass. Load the *overmaps*, not local forest maps,
    # before replacement. All four corners cover the complete 80-OMT square.
    point={'context_val':'berserk_prefetch_point'};actions=[]
    for x,y in [(-80,-80),(-80,80),(80,-80),(80,80)]:
        actions += [{'u_location_variable':point},
            {'location_variable_adjust':point,'overmap_tile':True,'x_adjust':x,'y_adjust':y},
            {'if':{'overmap_at_point':'forest','point':point},
             'then':math('_berserk_prefetch_checked = 1'),'else':math('_berserk_prefetch_checked = 0')}]
    E.append(eoc(P+'PREPARE_RING',actions,'u_is_avatar'))
    rows=read('effects/playtest_fixes_20261024_eocs.json');by=index(rows)
    obj=by['EOC_BERSERK_FIX24_FIRST_CREATE']
    near=copy.deepcopy(obj['effect'][1]['then'] if isinstance(obj['effect'],list) else obj['effect']);near['target_params']['om_terrain_replace']='forest'
    far=copy.deepcopy(near);far['target_params']['search_range']=80
    obj['effect']=[run(P+'PREPARE_RING'),{'if':eq('u_berserk_first_hunt_search_attempts'),'then':near,'else':far}]
    write('effects/playtest_fixes_20261024_eocs.json',rows)
    rows=read('effects/local_breach_eocs.json');obj=index(rows)['EOC_BERSERK_BREACH_FIND']
    def replace(x):
        if isinstance(x,dict):
            if 'target_params' in x:x['target_params']['om_terrain_replace']='forest'
            for v in x.values():replace(v)
        elif isinstance(x,list):
            for v in x:replace(v)
    replace(obj['effect'])
    if obj['effect'][0]!=run(P+'PREPARE_RING'):obj['effect'].insert(0,run(P+'PREPARE_RING'))
    write('effects/local_breach_eocs.json',rows)
    # Repair stalled October 24 saves once, without changing a real target.
    valid=both(math('has_var(u_berserk_first_hunt_location)'),{'overmap_at_point':'berserk_first_hunt_lair','point':{'u_val':'berserk_first_hunt_location'}})
    eligible=both('u_is_avatar',eq('berserk_eclipse_era'),eq('u_berserk_eclipse_rescue_state',2),
        math("u_val('pos_z') == 0"),neg(eq('u_berserk_first_hunt_done')),test('APOSTOL_HUMAN_ROUTE'))
    E.append(eoc(P+'FIRST_RETRY',[
        math("u_berserk_first_hunt_retry_at = time('now') + 3600"),
        math('u_berserk_first_hunt_search_attempts = 0'),run('EOC_BERSERK_FIRST_HUNT_REQUEST')],
        both(eligible,neg(valid),math("time('now') >= u_berserk_first_hunt_retry_at"))))
    E.append(eoc(P+'LOAD',[
        {'if':neg(eq('u_berserk_hunt_repair_v25')),'then':[math('u_berserk_hunt_repair_v25 = 1'),
            {'if':neg(valid),'then':math('u_berserk_first_hunt_retry_at = 0')}]},run(P+'FIRST_RETRY')],
        eligible,eoc_type='EVENT',required_event='game_load'))
    E.append(eoc(P+'WATCH',run(P+'FIRST_RETRY'),eligible,eoc_type='RECURRING',recurrence='10 minutes',**{'global':True}))


def main():
    authored_sprites();chapel();physical_directions();entry_hints();reliable_hunt()
    write('effects/playtest_fixes_20261025_eocs.json',E);localize()
    print('25 October: real early leads, authored demon families, approved chapel and stalled hunt retry.')


if __name__=='__main__':main()
