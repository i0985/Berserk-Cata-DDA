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
    project=json.loads((ROOT/'docs/location_projects/chapel-3.3-02.json').read_text())
    write('furniture/chapel_layout_version.json',[{'type':'furniture','id':'f_berserk_chapel_record_v2',
        'copy-from':'f_berserk_chapel_record','looks_like':'f_berserk_chapel_record'}])
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
        same=both(math('has_var(u_berserk_hint_'+key.lower()+')'),
            *[math('floor(u_berserk_hint_'+key.lower()+'.'+a+' / 24) == floor(_berserk_hint_point.'+a+' / 24)') for a in 'xy'],
            math('u_berserk_hint_'+key.lower()+'.z == _berserk_hint_point.z'))
        actions=[{'u_location_variable':point},
            math('_berserk_hint_point.x = floor(_berserk_hint_point.x / 24) * 24'),
            math('_berserk_hint_point.y = floor(_berserk_hint_point.y / 24) * 24')]
        if key=='CHAPEL':actions.append({'if':{'u_at_om_location':'berserk_desecrated_chapel_nave'},'then':{'location_variable_adjust':point,'overmap_tile':True,'y_adjust':-1}})
        actions.append({'if':neg(same),'then':[{'copy_var':point,'target_var':saved},{'u_message':tr(en,ru),'type':'info','popup':True}]})
        E.append(eoc(P+'HINT_'+key,actions,both('u_is_avatar',either(*[{'u_at_om_location':t} for t in terrains]))))
    E.append(eoc(P+'ARRIVAL',[run(P+'HINT_'+k) for k,*_ in hints],'u_is_avatar',eoc_type='EVENT',required_event='avatar_moves'))


def reliable_hunt():
    # Native special placement checks actual generated submaps, independently
    # of overmap visibility. The zero-population radius uses the engine's
    # SAFE_AT_WORLDGEN exclusion to keep the lair away from the forge; it
    # neither spawns monsters nor pretends target_params.min_distance works
    # for forced specials. Fixed GLOBALLY_UNIQUE sites are reused by native.
    group='GROUP_BERSERK_STORY_PLACEMENT_BUFFER'
    write('monstergroups/story_placement_buffer.json',[{'type':'monstergroup','id':group,
        'default':'mon_berserk_eclipse_wretch','monsters':[]}])
    for name in ['godo_workshop','first_hunt','local_breach']:
        rows=read('overmap/'+name+'.json')
        for obj in rows:
            if obj.get('type')!='overmap_special':continue
            flags=obj.setdefault('flags',[])
            for flag in ['SAFE_AT_WORLDGEN','GLOBALLY_UNIQUE']:
                if flag not in flags:flags.append(flag)
            if name!='godo_workshop':
                obj['spawns']={'group':group,'population':[0,0],'radius':[24,24]}
                obj['//']='Story-only native placement; 24-OMT safe-site exclusion, zero population; generated local maps are never overwritten.'
        write('overmap/'+name+'.json',rows)
    E.append(eoc(P+'PREPARE_RING',[],'u_is_avatar'))  # Saved public alias.
    rows=read('effects/playtest_fixes_20261024_eocs.json');obj=index(rows)['EOC_BERSERK_FIX24_FIRST_CREATE']
    near={'u_location_variable':{'context_val':'berserk_first_hunt_candidate'},
        'target_params':{'om_terrain':'berserk_first_hunt_lair','om_special':'berserk_first_hunt_special',
            'random':True,'search_range':48,'min_distance':0,'z':0},
        'true_eocs':['EOC_BERSERK_FIRST_HUNT_VALIDATE'],'false_eocs':['EOC_BERSERK_FIRST_HUNT_SEARCH_FAILED']}
    far=copy.deepcopy(near);far['target_params']['search_range']=80
    obj['effect']={'if':eq('u_berserk_first_hunt_search_attempts'),'then':near,'else':far}
    write('effects/playtest_fixes_20261024_eocs.json',rows)
    rows=read('effects/local_breach_eocs.json');obj=index(rows)['EOC_BERSERK_BREACH_FIND']
    def replace(x):
        if isinstance(x,dict):
            if 'target_params' in x:
                x['target_params']={'om_terrain':'berserk_local_breach','om_special':'berserk_local_breach_special',
                    'random':True,'search_range':80,'min_distance':0,'z':0}
            for v in x.values():replace(v)
        elif isinstance(x,list):
            for v in x:replace(v)
    replace(obj['effect'])
    obj['effect']=[x for x in obj['effect'] if x!=run(P+'PREPARE_RING')]
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
        {'if':neg(eq('u_berserk_hunt_repair_v25b')),'then':[math('u_berserk_hunt_repair_v25b = 1'),
            {'if':neg(valid),'then':math('u_berserk_first_hunt_retry_at = 0')}]},run(P+'FIRST_RETRY')],
        eligible,eoc_type='EVENT',required_event='game_load'))
    E.append(eoc(P+'WATCH',run(P+'FIRST_RETRY'),eligible,eoc_type='RECURRING',recurrence='10 minutes',**{'global':True}))


def wall_hotfix():
    # Narrow, once-per-instance repair for the erroneous visited chapel reported
    # by the owner. No map rebuild, loot or NPC changes. The existing plaque's
    # invisible layout variant marks each repaired instance, including saves.
    point={'context_val':'berserk_chapel_south_omt'}
    effects=[{'u_location_variable':point},
        math('_berserk_chapel_south_omt.x = floor(_berserk_chapel_south_omt.x / 24) * 24'),
        math('_berserk_chapel_south_omt.y = floor(_berserk_chapel_south_omt.y / 24) * 24')]
    plaque={'context_val':'berserk_chapel_version_point'}
    effects += [{'copy_var':point,'target_var':plaque},{'location_variable_adjust':plaque,'x_adjust':12,'y_adjust':16}]
    checks=[{'map_furniture_id':'f_berserk_chapel_record','loc':plaque}]
    fixed=[{'map_furniture_id':'f_berserk_chapel_record_v2','loc':plaque}]
    for i,y in enumerate(range(7,11)):
        pos={'context_val':'berserk_chapel_wall_'+str(i)}
        effects += [{'copy_var':point,'target_var':pos},{'location_variable_adjust':pos,'x_adjust':7,'y_adjust':y}]
        checks += [{'map_terrain_id':'t_wall','loc':pos},{'map_furniture_id':'f_null','loc':pos}]
        fixed.append({'map_terrain_id':'t_floor','loc':pos})
    E.append(eoc(P+'WALL_FIXED',math('berserk_chapel_wall_hotfix25b = 1'),both(*fixed)))
    effects.append({'if':both(*checks),'then':[{'mapgen_update':'berserk_chapel_remove_added_wall_v1','target_var':point},run(P+'WALL_FIXED')]})
    E.append(eoc(P+'WALL_HOTFIX',effects,both('u_is_avatar',{'u_at_om_location':'berserk_desecrated_chapel_nave'})))
    write('mapgen/chapel_layout_hotfix.json',[{'type':'mapgen','update_mapgen_id':'berserk_chapel_remove_added_wall_v1',
        'object':{'set':[{'point':'terrain','id':'t_floor','x':7,'y':y} for y in range(7,11)]+
            [{'point':'furniture','id':'f_berserk_chapel_record_v2','x':12,'y':16}]}}])
    E.append(eoc(P+'LOCAL_LOAD',[run(P+'HINT_CHAPEL'),run(P+'WALL_HOTFIX')],'u_is_avatar',eoc_type='EVENT',required_event='game_load'))
    index(E)[P+'ARRIVAL']['effect'].append(run(P+'WALL_HOTFIX'))


def main():
    authored_sprites();chapel();physical_directions();entry_hints();reliable_hunt();wall_hotfix()
    write('effects/playtest_fixes_20261025_eocs.json',E);localize()
    print('25 October: real early leads, authored demon families, approved chapel and stalled hunt retry.')


if __name__=='__main__':main()
