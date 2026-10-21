#!/usr/bin/env python3
"""Native mutation equipment rules, one-time hand growth and rare prosthesis loot.

Does not add a playable ritual, new sprites or a second relationship score.
Run after the Godo and Rickert dialogue builders.
"""
import json
import subprocess

from recover_apostol_33 import ROOT, MOD, read, write, index, walk, eoc, math, test, both
from recovery_33_translations import source

STRINGS={}


def tr(en,ru):STRINGS[en]=ru;return en
def neg(c):return {'not':c}
def either(*cs):return {'or':list(cs)}
def run(s):return {'run_eocs':s}


# Existing permanent FORM mutations carry the body and its overlay. SEED,
# SENSES and final title mutations must not draw the same body a second time.
FORMS={
 'VOID':(['hand_l','hand_r'],True,4,2,'Elongated fingers do not fit ordinary rigid gloves.','Удлинённые пальцы не помещаются в обычные жёсткие перчатки.','Вытянутый силуэт, длинные пальцы; пространственный эффект отдельно от тела.'),
 'SLAN':(['arm_l','arm_r','hand_l','hand_r'],True,7,4,'Rigid sleeves and gauntlets cannot follow the reshaped flesh.','Жёсткие наручи и латные перчатки не подходят к изменённой плоти.','Живая перестроенная плоть, гибкие руки; не рисовать постоянный хлыст вместо кисти.'),
 'UBIK':(['head','mouth'],True,5,3,'Ordinary rigid helmets and masks do not fit the altered head.','Обычные жёсткие шлемы и маски не подходят к изменённой голове.','Искажённый контур и изменённая голова; ложные цели не часть постоянного спрайта.'),
 'CONRAD':(['torso','leg_l','leg_r'],True,9,6,'The thickened body cannot fit ordinary rigid torso and leg armor.','Утолщённое тело не помещается в обычную жёсткую броню корпуса и ног.','Тяжёлое раздутое тело; облако разложения рисовать отдельным эффектом.'),
 'FEMTO':(['torso'],False,7,4,'The wings need an open back; ordinary torso clothing gets in their way.','Крыльям нужна свободная спина; обычная одежда на корпусе мешает им.','Крылатый тёмный силуэт, две кисти остаются; крылья за телом.'),
 'COUNT_FLESH':(['torso','arm_l','arm_r'],True,8,5,'The swollen torso and arms cannot fit ordinary rigid armor.','Раздувшиеся корпус и руки не помещаются в обычную жёсткую броню.','Тяжёлая пластичная плоть и толстые руки; не копия гигантского оригинала.'),
 'WYALD_FLESH':(['hand_l','hand_r','foot_l','foot_r'],True,8,5,'The changed hands and feet cannot fit ordinary rigid gloves and footwear.','Изменённые кисти и стопы не помещаются в обычные жёсткие перчатки и обувь.','Звероподобное тело с человеческим хватом; оружие не рисовать в самом теле.'),
 'ROSINE_FLESH':(['torso'],False,8,5,'The wings need an open back; ordinary torso clothing gets in their way.','Крыльям нужна свободная спина; обычная одежда на корпусе мешает им.','Крылатое насекомоподобное тело, отдельные прозрачные крылья сзади.'),
 'GRUNBELD_FLESH':(['torso','arm_l','arm_r','leg_l','leg_r'],True,10,5,'The carapace cannot fit beneath ordinary rigid torso or limb armor.','Панцирь не помещается под обычной жёсткой бронёй корпуса и конечностей.','Полный панцирный огненный облик; жар не постоянная горящая одежда.'),
 'COUNT_PAWN':(['torso'],True,5,3,'The thickened torso cannot fit ordinary rigid armor.','Утолщённый корпус не помещается в обычную жёсткую броню.','Неполная тяжёлая пластичная форма; меньше силуэта самостоятельного Графа.'),
 'WYALD_PAWN':(['hand_l','hand_r'],True,5,3,'The changed hands cannot fit ordinary rigid gloves.','Изменённые кисти не помещаются в обычные жёсткие перчатки.','Неполная звероподобная форма; кисти пригодны для грубого хвата.'),
 'ROSINE_PAWN':(['head','mouth','hand_l','hand_r'],True,6,4,'The insectlike head and hands do not fit ordinary rigid helmets, masks or gloves.','Насекомоподобные голова и кисти не подходят для обычных жёстких шлемов, масок и перчаток.','Пешка с насекомоподобной головой и кистями; без полноценных крыльев Розины.'),
 'GRUNBELD_PAWN':(['torso','arm_l','arm_r'],True,7,4,'The carapace cannot fit beneath ordinary rigid torso or arm armor.','Панцирь не помещается под обычной жёсткой бронёй корпуса и рук.','Неполный панцирь корпуса и рук; человеческие ноги и отдельные ботинки.'),
}


def mutation_rules():
    body_ids=[];manifest=[]
    for path in sorted((MOD/'mutations').glob('apostol_*.json')):
        rows=json.loads(path.read_text());changed=False
        for row in rows:
            if row.get('type')!='mutation' or row['id'].startswith('BERSERK_ECLIPSE_SCAR_'):continue
            id=row['id']
            if id.endswith(('_SEED','_SENSES','_FORM','_APOSTLE','_PAWN')):
                body_ids.append(id)
            if not id.endswith('_FORM'):continue
            stem=id.removeprefix('BERSERK_').removesuffix('_FORM')
            if stem not in FORMS:continue
            parts,soft,visibility,ugliness,en,ru,art=FORMS[stem]
            row.update(restricts_gear=parts,allow_soft_gear=soft,destroys_gear=False,visibility=visibility,ugliness=ugliness)
            # Strip only our own previous suffix before reapplying, preserving
            # every existing combat bonus, disadvantage and spell description.
            description=row['description'].split('\n\nClothing: ',1)[0]
            old_ru=old_translation(description)
            row['description']=tr(description+'\n\nClothing: '+en,old_ru+'\n\n'+ru)
            changed=True
            manifest.append(dict(mutation=id,overlay='overlay_mutation_'+id,
                overlay_male='overlay_male_mutation_'+id,overlay_female='overlay_female_mutation_'+id,
                art_notes=art,restricted_parts=parts,soft_clothing=soft,
                permanent=True,proposed_layers=['back_wings_if_present','body','equipment','hands_and_weapon']))
        if changed:write(str(path.relative_to(MOD)),rows)
    (ROOT/'docs/apostol_sprite_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return body_ids


def old_translation(en):
    # Existing compiled RU is authoritative; no reverse translation or missing
    # strings silently becoming English in the new appended descriptions.
    import gettext
    with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as f:tr=gettext.GNUTranslations(f)
    ru=tr.gettext(en)
    if ru==en:raise RuntimeError('No existing RU description: '+en)
    return ru


def body_hooks(ids):
    actual=either(*[{'u_has_trait':id} for id in ids])
    first=both('u_is_avatar',neg(test('EOC_BERSERK_FORGE_GUTS')),actual,math('u_berserk_apostol_body_checked != 1'))
    hand_message=tr('Bone presses through the scar. Tendons tighten, fingers uncurl: your left hand has grown back.','Под рубцом проступает кость. Натягиваются сухожилия, распрямляются пальцы: ваша левая кисть отросла вновь.')
    helpers=[eoc('EOC_BERSERK_APOSTOL_FIRST_BODY_CHANGE',[
        {'if':{'u_has_bionics':'bio_berserk_hand_stump'},'then':[
            # required_bionic is an INSTALLATION prerequisite. The cannon added
            # by SELF_INSTALL is an independent bionic (parent uid is zero).
            # Keep it and its live/stored chamber intact; only remove the stump.
            {'u_lose_bionic':'bio_berserk_hand_stump'},
            {'u_lose_effect':'berserk_missing_left_hand','target_part':'hand_l'},
            {'u_lose_effect':'berserk_left_arm_onehanded','target_part':'arm_l'},
            math('u_berserk_apostol_left_hand_regrown = 1'),
            {'u_message':hand_message,'type':'good','popup':True}]},
        math('u_berserk_apostol_body_checked = 1')],first)]
    world=both('u_is_avatar',math('u_berserk_eclipse_route == 2'),math('u_berserk_apostol_return_state == 2'),
        either(math('u_berserk_apostol_outcome == 1'),math('u_berserk_apostol_outcome == 2')),math('berserk_eclipse_era != 1'))
    helpers.append(eoc('EOC_BERSERK_APOSTOL_RESTORE_WORLD_ERA',math('berserk_eclipse_era = 1'),world))
    helpers.append(eoc('EOC_BERSERK_APOSTOL_UNUSED_ARM_ORDER',[],both(math('u_berserk_godo_arm_state > 0'),math('u_berserk_godo_arm_state < 4'))))
    helpers.append(eoc('EOC_BERSERK_APOSTOL_BODY_MIGRATE',[
        run('EOC_BERSERK_APOSTOL_FIRST_BODY_CHANGE'),run('EOC_BERSERK_APOSTOL_RESTORE_WORLD_ERA')],
        either(first,world),eoc_type='RECURRING',recurrence='1 minute',**{'global':True}))
    write('effects/apostol_body_rules_eocs.json',helpers)
    # u_add_trait directly installs mutations; it does not emit gains_mutation.
    # Hook the real writers instead of relying on an event that never fires.
    hook=run('EOC_BERSERK_APOSTOL_FIRST_BODY_CHANGE')
    for path in sorted((MOD/'effects').glob('apostol_*.json')):
        if path.name=='apostol_body_rules_eocs.json':continue
        rows=json.loads(path.read_text());changed=False
        for row in rows:
            if not any(n.get('u_add_trait') in ids for n in walk(row.get('effect'))):continue
            body=row['effect'] if isinstance(row['effect'],list) else [row['effect']]
            if hook not in body:body.append(hook);row['effect']=body;changed=True
        if changed:write(str(path.relative_to(MOD)),rows)
    # An old event replay must not remove the regrown hand again.
    rows=read('effects/eclipse_story_wounds_eocs.json')
    for row in rows:
        if row['id']=='EOC_BERSERK_ECLIPSE_APPLY_STORY_WOUNDS':
            guard=math('u_berserk_apostol_left_hand_regrown != 1')
            if guard not in row['condition'].get('and',[]):row['condition']=both(guard,row['condition'])
    write('effects/eclipse_story_wounds_eocs.json',rows)
    # The gun remains a forearm attachment after the hand grows; installation on
    # a naturally intact hand is still prohibited by SELF_INSTALL's stump check.
    rows=read('bionics/arm_cannon.json')
    index(rows)['bio_berserk_arm_cannon']['description']=tr(
        'A mechanical cannon attached to the left forearm. Deploy it to wield and reload its single chamber, then retract it to use another weapon. It burns powder charges instead of bionic power.',
        'Механическая пушка на левом предплечье. Разверните её, чтобы зарядить единственный ствол и выстрелить, затем уберите, чтобы взять другое оружие. Вместо электричества она использует пороховые заряды.')
    write('bionics/arm_cannon.json',rows)


def refund_and_journal():
    rows=read('effects/godo_eocs.json');r=index(rows)['EOC_BERSERK_GODO_ARM_REFUND']
    regrown=math('u_berserk_apostol_left_hand_regrown == 1')
    if not any(n==regrown for n in walk(r['condition'])):
        def replace(x):
            if x==test('EOC_BERSERK_GODO_HAS_ARM'):return either(x,regrown)
            if isinstance(x,dict):return {k:replace(v) for k,v in x.items()}
            if isinstance(x,list):return [replace(v) for v in x]
            return x
        r['condition']=replace(r['condition'])
    write('effects/godo_eocs.json',rows)
    rows=read('dialogue/road_journal.json');r=index(rows)['TALK_BERSERK_JOURNAL_ARM']
    key=regrown['math']
    if r['dynamic_line'].get('math')!=key:
        r['dynamic_line']={**regrown,'yes':{
            'test_eoc':'EOC_BERSERK_APOSTOL_UNUSED_ARM_ORDER',
            'yes':tr('Your hand has grown back. Speak with Rickert at the forge to settle the unnecessary prosthesis order and collect any materials already delivered.','Кисть восстановилась. Поговорите с Рикертом в кузнице: закройте ненужный заказ протеза и заберите уже переданные материалы.'),
            'no':tr('Your hand has grown back. You no longer need a replacement.','Кисть восстановилась. Замена ей больше не нужна.')},'no':r['dynamic_line']}
    else:
        # Recollect source strings during an idempotent build.
        tr('Your hand has grown back. Speak with Rickert at the forge to settle the unnecessary prosthesis order and collect any materials already delivered.','Кисть восстановилась. Поговорите с Рикертом в кузнице: закройте ненужный заказ протеза и заберите уже переданные материалы.')
        tr('Your hand has grown back. You no longer need a replacement.','Кисть восстановилась. Замена ей больше не нужна.')
    write('dialogue/road_journal.json',rows)


def laboratory_loot():
    # Native 0.I bionics has weight 950. Extend it, do not replace its entries.
    # 1 / (950 + 1) = 0.10515% per draw before other mods alter the denominator.
    write('itemgroups/rare_arm_cannon.json',[{
        'type':'item_group','id':'bionics','copy-from':'bionics','subtype':'distribution',
        'extend':{'entries':[{'item':'bio_berserk_arm_cannon','prob':1}]}}])


def translations():
    for filename,localized in [('ru.po',True),('Berserk.pot',False)]:
        path=MOD/'lang/po'/filename;remaining=dict(STRINGS);out=[]
        for block in [b for b in path.read_text().split('\n\n') if b.strip()]:
            key=source(block)
            if key in remaining:
                ru=remaining.pop(key)
                block='#. Apostol body rules 2026-10-21\nmsgid '+json.dumps(key,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False)
            out.append(block.strip('\n'))
        for en,ru in remaining.items():out.append('#. Apostol body rules 2026-10-21\nmsgid '+json.dumps(en,ensure_ascii=False)+'\nmsgstr '+json.dumps(ru if localized else '',ensure_ascii=False))
        path.write_text('\n\n'.join(out)+'\n')
    subprocess.run(['msgfmt','--check','-o',str(MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo'),str(MOD/'lang/po/ru.po')],check=True)


def main():
    ids=mutation_rules();body_hooks(ids);refund_and_journal();laboratory_loot();translations()
    print('Native body restrictions:',len(FORMS),'body traits:',len(ids),'rare prosthesis weight: 1/951')


if __name__=='__main__':main()
