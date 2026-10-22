#!/usr/bin/env python3
"""Award known directions as real missions without opening/owning a journal.

Does not reveal an unread source, reset a saved target, respawn a reward or
reroll a location. A bounded hourly retry repairs known routes in old saves.
"""
import json
import subprocess
from recover_apostol_33 import MOD, read, write, index, eoc, math, test, both, walk
from recovery_33_translations import source

STRINGS={}
def tr(en,ru):STRINGS[en]=ru;return en
def run(s):return {'run_eocs':s}
def neg(c):return {'not':c}


def main():
    eligible=both('u_is_avatar',math('berserk_eclipse_era == 1'),math('u_berserk_eclipse_trial_active != 1'),math("u_val('pos_z') == 0"))
    body=[]
    for key in ['BREACH','COUNT','WYALD','ROSINE','FLORA','GRUNBELD']:
        known=math('u_berserk_journal_knows_'+key.lower()+' == 1')
        # Existing LOCATE handlers validate/reuse the exact stored target and
        # assign the ordinary mission; an owned paper item is never tested.
        unfinished=neg(test('EOC_BERSERK_JOURNAL_DONE_'+key))
        needs={'or':[neg(test('EOC_BERSERK_JOURNAL_VALID_'+key)),neg({'u_has_mission':'MISSION_BERSERK_'+key})]}
        body.append({'if':both(known,unfinished,needs),'then':run('EOC_BERSERK_JOURNAL_LOCATE_'+key)})
    # Breach used a historical word-order alias; use the actual public ID.
    body[0]['then']=run('EOC_BERSERK_JOURNAL_BREACH_LOCATE')
    write('effects/direct_hunt_missions_33_eocs.json',[
        eoc('EOC_BERSERK_KNOWN_ROUTES_NOW',[math("u_berserk_known_routes_retry_at = time('now') + 3600")]+body,eligible),
        eoc('EOC_BERSERK_KNOWN_ROUTES_RETRY',run('EOC_BERSERK_KNOWN_ROUTES_NOW'),
            both(eligible,math("time('now') >= u_berserk_known_routes_retry_at")),
            **{'global':True,'recurrence':'30 minutes'})])
    p='effects/local_breach_eocs.json';data=read(p);by=index(data)
    clue=by['EOC_BERSERK_BREACH_READ_CLUE']
    # First reading gives its actual evidence, then locates/assigns the target.
    # Re-reading repeats neither the scene nor the journal's menu tree.
    clue['effect']['then']=[run('EOC_BERSERK_JOURNAL_BREACH_LOCATE')]
    clue['effect']['else']=[x for x in clue['effect']['else'] if 'open_dialogue' not in x and x.get('run_eocs')!='EOC_BERSERK_JOURNAL_REPLACE_MISSING' and x.get('u_message')!='A new entry has been added to your road journal.']
    commit=by['EOC_BERSERK_BREACH_CLOSE_COMMIT']
    hook=run('EOC_BERSERK_KNOWN_ROUTES_NOW')
    if hook not in commit['effect']:commit['effect'].append(hook)
    for obj in walk(commit):
        msg=obj.get('u_message','')
        if msg.startswith('The wound cools'):
            ru='Рана остывает, её пульс замирает. Здесь стало тише. Среди уцелевших отметок защитников различимы три направления: резиденция Графа, лагерь Чёрных Псов и туманная долина.'
            obj['u_message']=tr('The wound cools and its heartbeat stops. This place is quieter. The defenders\' surviving marks reveal three trails: the Count\'s residence, the Black Dogs\' camp and a misty valley.',ru)
    write(p,data)
    p='effects/apostol_continuation_eocs.json';data=read(p)
    obj=index(data)['EOC_BERSERK_APOSTOL_CONTINUATION_BEGIN']
    if hook not in obj['effect']:obj['effect'].append(hook)
    write(p,data)
    # The physical object's description makes the separation explicit.
    p='items/campaign_journal.json';data=read(p)
    data[0]['description']=tr('Notes about known places, the smiths\' work and what you have learned. It is a reference: your missions and map markers remain if this book is lost.',
        'Записи об известных местах, работе мастеров и том, что вам довелось узнать. Это справочник: задания и отметки на карте сохраняются, даже если книга потеряна.')
    write(p,data)
    # Native assignment already selects/stores a real target. Avoid a repeated
    # tutorial claiming the physical book is required to track it.
    p='effects/hunt_mission_eocs.json';data=read(p)
    for obj in walk(data):
        if obj.get('u_message','').startswith('A new objective has been added to your missions.'):
            obj['u_message']=tr('A new objective is marked on your map.','Новая цель отмечена на карте.')
    write(p,data)
    for filename,localized in [('ru.po',True),('Berserk.pot',False)]:
        path=MOD/'lang/po'/filename;remaining=dict(STRINGS);out=[]
        for block in [x for x in path.read_text().split('\n\n') if x.strip()]:
            key=source(block)
            if key in remaining:
                ru=remaining.pop(key);block='#. Direct mission routes 2026-10-22\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False)
            out.append(block.strip('\n'))
        for en,ru in remaining.items():out.append('#. Direct mission routes 2026-10-22\nmsgid '+json.dumps(en,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False))
        path.write_text('\n\n'.join(out)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)
    print('Known routes awarded from story events; physical journal optional.')


if __name__=='__main__':main()
