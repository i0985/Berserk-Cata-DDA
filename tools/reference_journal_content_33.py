"""Bindings for the owner's complete, approved reference-book manuscript.

Only quoted prose is published. Author notes stay in docs/dialogue_sources.
All predicates are native CDDA conditions; no knowledge is stored on the item.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT / 'docs/dialogue_sources/road-journal-2026-10-22.json').read_text())
MANUSCRIPT = {x['code']: x for x in SOURCE['entries']}


def math(s): return {'math': [s]}
def allof(*cs): return {'and': list(cs)}
def anyof(*cs): return {'or': list(cs)}
def no(c): return {'not': c}
def eq(v, n=1): return math(f'{v} == {n}')
def gt(v, n=0): return math(f'{v} > {n}')
def test(s): return {'test_eoc': s if s.startswith('EOC_') else 'EOC_BERSERK_' + s}
def fact(s): return eq('u_berserk_ref_' + s)
def read(s): return eq('u_berserk_journal_read_berserk_' + s)
def visited(s): return fact('visit_' + s)
def trait(s): return {'u_has_trait': 'BERSERK_' + s}
def item(s): return {'u_has_item': s}
def bionic(s): return {'u_has_bionics': s}
def known(s): return eq('u_berserk_journal_knows_' + s)
def p(code, n): return MANUSCRIPT[code]['paragraphs'][n]

GUTS = test('FORGE_GUTS')
NORMAL = allof(eq('u_berserk_eclipse_rescue_state', 2), no(eq('u_berserk_eclipse_route', 2)))
ALTER = allof(eq('u_berserk_eclipse_route', 2), eq('u_berserk_apostol_return_state', 2))
DEMON = gt('u_berserk_apostol_path')
BRAND = bionic('bio_berserk_brand_of_sacrifice')
REFUSED = allof(ALTER, eq('u_berserk_apostol_outcome', 2))
ARM = bionic('bio_berserk_arm_cannon')
SEALED = eq('u_berserk_breach_sealed')

RECORDS = []


def record(code, section, parts, title=None, title_variants=None):
    obj = {'code': code, 'key': code.translate(str.maketrans('МЛСТРП', 'mlctrp')).lower(),
           'section': section, 'title': title or MANUSCRIPT[code]['title'], 'parts': []}
    for condition, text in parts:
        obj['parts'].append({'condition': condition, 'text': text})
    obj['title_variants'] = title_variants or []
    RECORDS.append(obj)
    return obj


def named(s): return fact('name_' + s)
def dead(s): return fact('dead_' + s)
def sealed(s): return fact('sealed_' + s)
def pact(s): return allof(eq('u_berserk_apostol_path', 3), test('APOSTOL_' + s.upper() + '_PAWN_LINE'))
def knight(s): return eq('u_berserk_knight_read_' + s)


def replace_when(code, changes, changed):
    """Keep the same record while replacing demonstrably outdated claims."""
    obj = next(r for r in RECORDS if r['code'] == code)
    original = obj['parts'][:]
    for i, past in changes.items():
        part = original[i]
        proof = part['condition']
        part['condition'] = allof(proof, no(changed))
        obj['parts'].append({'condition': allof(proof, changed), 'text': past})


def living_or_remembered(code, changes, person):
    replace_when(code, changes, fact(person + '_dead'))


def places():
    record('М01', 'places', [
        (allof(named('godo'), no(GUTS)), p('М01', 0)),
        (allof(named('godo'), GUTS), p('М01', 1)),
        (allof(visited('godo'), no(named('godo'))), 'В лесу стоит дом с кузницей. Кто здесь работает, я ещё не узнал.'),
        (visited('godo'), p('М01', 2)),
        (eq('u_berserk_forge_rest_allowed'), p('М01', 3)),
        (allof(NORMAL, eq('u_berserk_godo_rescue_relocated')), p('М01', 4)),
        (fact('forge_damage_observed'), p('М01', 5)),
    ])
    record('М02', 'places', [
        (anyof(visited('oak'), read('chapel_forest_route'), read('oak_last_note'), read('oak_broken_rootcutter')), p('М02', 0)),
        (anyof(read('oak_broken_rootcutter'), read('oak_last_note'), read('chapel_forest_route')), p('М02', 1)),
        (visited('oak'), p('М02', 2)), (fact('behelit_oak'), p('М02', 3))])
    record('М03', 'places', [
        (anyof(visited('cave'), read('cave_scout_note'), read('cave_last_scrap')), p('М03', 0)),
        (read('cave_scout_note'), p('М03', 1)),
        (anyof(fact('cave_chime'), read('cave_scout_note'), read('cave_last_scrap')), p('М03', 2)),
        (anyof(fact('cave_prop'), read('cave_scout_note'), read('cave_last_scrap')), p('М03', 3)),
        (fact('behelit_cave'), p('М03', 4))])
    record('М04', 'places', [
        (anyof(visited('expedition'), read('expedition_transfer_note'), read('expedition_alarm_note')), p('М04', 0)),
        (read('expedition_transfer_note'), p('М04', 1)), (read('expedition_alarm_note'), p('М04', 2)),
        (fact('behelit_expedition'), p('М04', 3))])
    record('М05', 'places', [
        (anyof(visited('chapel'), read('chapel_relief_roster'), read('chapel_ritual_note'), read('chapel_last_vigil')), p('М05', 0)),
        (read('chapel_relief_roster'), p('М05', 1)), (read('chapel_ritual_note'), p('М05', 2)),
        (anyof(read('chapel_forest_route'), read('chapel_last_vigil'), fact('chapel_bypass')), p('М05', 3)),
        (fact('behelit_chapel'), p('М05', 4))])
    record('М06', 'places', [
        (anyof(known('first'), visited('first')), p('М06', 0)),
        (allof(eq('u_berserk_first_hunt_done'), no(read('apostle_burned_clue'))), p('М06', 1)),
        (read('apostle_burned_clue'), p('М06', 2))])
    record('М07', 'places', [
        (anyof(known('breach'), visited('breach')), p('М07', 0)),
        (allof(fact('breach_keeper_dead'), no(SEALED)), p('М07', 1)),
        (SEALED, p('М07', 2)), (fact('breach_directions'), p('М07', 3)),
        (allof(SEALED, BRAND), p('М07', 4)), (allof(SEALED, DEMON), p('М07', 5))])
    for code, stem, unknown_title, unknown_text in [
        ('М08', 'count', 'Укреплённая резиденция', 'Укреплённый дом за внешней оградой. Кто распоряжается им, я ещё не узнал.'),
        ('М09', 'wyald', 'Военный лагерь', 'Среди леса разбит военный лагерь. Я ещё не узнал, кому подчиняются его обитатели.'),
        ('М10', 'rosine', 'Туманная долина', 'Дорога привела в туманную долину. Кто скрывается среди её обитателей, я ещё не узнал.'),
        ('М12', 'grunbeld', 'Крепость', 'Мощные укрепления закрывают внутренний двор. Чей приказ здесь исполняют, я ещё не узнал.')]:
        parts = [(named(stem), p(code, 0)), (allof(visited(stem), no(named(stem))), unknown_text)]
        if stem == 'count':
            parts += [(anyof(read('count_prison_list'), read('count_physician_ledger')), p(code, 1)),
                      (fact('prisoner_met'), p(code, 2)), (dead(stem), p(code, 3)), (sealed(stem), p(code, 4)), (pact(stem), p(code, 5))]
        elif stem == 'wyald':
            parts += [(read('wyald_muster_roll'), p(code, 1)), (read('wyald_muster_roll'), p(code, 2)),
                      (dead(stem), p(code, 3)), (pact(stem), p(code, 4))]
        elif stem == 'rosine':
            parts += [(anyof(read('rosine_witness_note'), fact('rosine_creatures')), p(code, 1)),
                      (anyof(read('rosine_witness_note'), fact('cocoon_examined')), p(code, 2)),
                      (dead(stem), p(code, 3)), (pact(stem), p(code, 4))]
        else:
            parts += [(allof(fact('grunbeld_siege_alive'), no(dead(stem))), p(code, 1)),
                      (fact('grunbeld_siege_dead'), p(code, 2)),
                      (allof(fact('grunbeld_siege_seen'), no(fact('grunbeld_siege_alive')), no(dead(stem))), p(code, 3)),
                      (fact('grunbeld_castle_victory'), p(code, 4)), (sealed(stem), p(code, 5)), (pact(stem), p(code, 6))]
        record(code, 'places', parts, title=unknown_title, title_variants=[(named(stem), MANUSCRIPT[code]['title'])])
    record('М11', 'places', [
        (named('flora'), p('М11', 0)),
        (allof(visited('flora'), no(named('flora'))), 'Жилой дом соединён с огромными корнями. Его хозяйка мне пока не представилась.'),
        (allof(visited('flora'), eq('u_berserk_flora_met')), p('М11', 1)),
        (fact('flora_aid_allowed'), p('М11', 2)), (fact('flora_armor'), p('М11', 3)),
        (allof(fact('flora_attack'), no(eq('u_berserk_flora_escaped'))), p('М11', 4)),
        (allof(eq('u_berserk_flora_escaped'), no(fact('flora_home_lost'))), p('М11', 5)),
        (fact('flora_home_lost'), p('М11', 6))], title='Дом у огромного дерева',
        title_variants=[(named('flora'), 'Дом у духовного дерева')])
    record('М13', 'places', [
        (fact('refuge_chosen'), p('М13', 0)),
        (allof(fact('refuge_chosen'), eq('u_berserk_refuge_ready')), p('М13', 1)),
        (fact('refuge_lost'), p('М13', 2))])
    living_or_remembered('М01', {
        0: 'В этой лесной кузнице работал Годо. Он брался за тяжёлые клинки и оружие, от которого отказывались другие мастера.',
        1: 'Годо держал кузницу вдали от городов. Он знал, для чего нужен клинок, и не любил тратить железо на украшения.',
    }, 'godo')
    replace_when('М11', {
        1: 'Жилые комнаты были соединены с огромными корнями. Здесь находилось место для чтения, работы и отдыха. Укрытие держалось не только на силе дерева, но и на заботе хозяйки.',
        3: 'Флора рассказывала о доспехе, который позволяет телу продолжать бой ценой самого владельца.',
    }, fact('flora_home_lost'))


def people():
    met = eq('u_berserk_godo_personally_met')
    record('Л01', 'people', [(allof(met, no(GUTS)), p('Л01', 0)), (allof(met, GUTS), p('Л01', 1)),
        (fact('godo_work'), p('Л01', 2)), (fact('godo_care'), p('Л01', 3)),
        (eq('u_berserk_godo_sparks_completed'), p('Л01', 4)),
        (eq('u_berserk_godo_sparks_closed'), 'Я не стал слушать его разговор у горна.'),
        (eq('u_berserk_godo_demon_refused'), p('Л01', 5))])
    story = 'u_berserk_rickert_eclipse_story'
    record('Л02', 'people', [
        (eq('u_berserk_rickert_met'), p('Л02', 0)), (fact('rickert_band'), p('Л02', 1)),
        (allof(eq('u_berserk_rickert_met'), eq('u_berserk_rickert_care_present')), p('Л02', 2)),
        (allof(eq(story), no(eq('u_berserk_rickert_lied_before'))), p('Л02', 3)),
        (anyof(eq(story, 2), eq('u_berserk_rickert_lied_before')), p('Л02', 4)),
        (eq(story, 3), p('Л02', 5)), (eq('u_berserk_rickert_lied_before'), p('Л02', 6)),
        (allof(eq('u_berserk_rickert_lied_before'), fact('rickert_trust_restored')), p('Л02', 7)),
        (fact('rickert_joined'), p('Л02', 8)), (eq('u_berserk_rickert_recruit_refused'), p('Л02', 9))])
    record('Л03', 'people', [(NORMAL, p('Л03', 0)), (knight('purpose'), p('Л03', 1)),
        (knight('self'), p('Л03', 2)), (eq('u_berserk_knight_farewell_confirmed'), p('Л03', 3))], title='Рыцарь-Череп')
    record('Л04', 'people', [(eq('u_berserk_flora_met'), p('Л04', 0)),
        (fact('flora_brand'), p('Л04', 1)), (fact('flora_armor'), p('Л04', 2)),
        (fact('flora_aid_taken'), p('Л04', 3)), (fact('flora_demon_counsel'), p('Л04', 4))])
    record('Л05', 'people', [(fact('prisoner_met'), p('Л05', 0)), (fact('prisoner_help'), p('Л05', 1)),
        (allof(fact('prisoner_freed'), no(fact('prisoner_dead'))), p('Л05', 2))])
    record('Л06', 'people', [(fact('forge_orders'), p('Л06', 0)), (fact('forge_orders'), p('Л06', 1))])
    record('Л07', 'people', [(fact('repair_explained'), p('Л07', 0)), (fact('repair_handoff'), p('Л07', 1))])
    record('Л08', 'people', [(fact('early_blade_known'), p('Л08', 0)),
        (eq('u_berserk_godo_crafted_early_copy'), p('Л08', 1)), (fact('dragonslayer_story'), p('Л08', 2))])
    record('Л09', 'people', [
        (fact('prosthesis_explained'), p('Л09', 0)),
        (allof(fact('arm_device_owned'), no(ARM)), p('Л09', 1)), (ARM, p('Л09', 2)),
        (eq('u_berserk_arm_cannon_self_made'), p('Л09', 3)),
        (allof(eq('u_berserk_arm_cannon_self_made_one_hand'), fact('rickert_one_hand_praise')), p('Л09', 4))], title='Протез и рука-пушка')
    record('Л10', 'people', [(fact('crossbow_explained'), p('Л10', 0)), (fact('bolts_explained'), p('Л10', 1))])
    living_or_remembered('Л01', {
        0: 'Годо был хозяином лесной кузницы. Говорил резко и быстро переходил к делу. Сначала хотел увидеть оружие, а уже потом слушать просьбы о нём.',
        1: 'Годо узнал меня. Ворчал на мои клинки и не берёг слов. О железе он судил увереннее, чем другие — о людях.',
        2: 'Его делом были клинки, железные детали и ремонт. Механизмы и арбалеты он оставлял Рикерту.',
        5: 'Годо отказался делать для меня этот клинок. Он знал о принятой мной силе и считал, что дальше я должен отвечать за свой выбор.',
    }, 'godo')
    living_or_remembered('Л02', {
        0: 'Рикерт работал рядом с Годо. Разбирался в арбалетах, спусках и креплениях. Мог долго возиться с маленькой деталью, если от неё зависела надёжность оружия.',
        1: 'Он путешествовал с Отрядом Сокола. В бою рассчитывал на арбалет, позицию и подготовку больше, чем на силу удара мечом.',
    }, 'rickert')
    living_or_remembered('Л04', {
        0: 'Флора была ведьмой, жившей у духовного дерева. Говорила спокойно и не обещала избавления от любой беды. Знания для неё были связаны с заботой о живых.',
        2: 'Флора знала цену доспеха Берсерка. Он способен заставить тело продолжать бой, когда обычный человек уже не мог бы стоять.',
    }, 'flora')
    living_or_remembered('Л05', {
        0: 'Человек, которого держали в резиденции Графа. Он знал привычки слуг и часть служебных помещений. Боялся хозяина и не был уверен, что помощь извне вообще возможна.',
    }, 'prisoner')
    living_or_remembered('Л09', {
        0: 'Рикерт рассказывал, как собрать механическую замену потерянной кисти. В устройстве совмещены подвижная часть и скрытая пушка. Для работы нужны не только железо, но и точные крепления.',
    }, 'rickert')
    for code, person, met, text in [('Л01', 'godo', met, 'Годо погиб.'),
                                   ('Л02', 'rickert', eq('u_berserk_rickert_met'), 'Рикерт погиб.'),
                                   ('Л04', 'flora', eq('u_berserk_flora_met'), 'Флора погибла.'),
                                   ('Л05', 'prisoner', fact('prisoner_met'), 'Пленник погиб.')]:
        obj = next(r for r in RECORDS if r['code'] == code)
        # An unfamiliar corpse does not reveal a character's biography.
        obj['parts'].append({'condition': allof(met, fact(person + '_dead')), 'text': text})


def experiences():
    record('С01', 'past', [(fact('behelit_examined'), p('С01', 0)),
        (anyof(read('expedition_transfer_note'), read('chapel_ritual_note'), read('oak_last_note')), p('С01', 1)),
        (fact('behelit_call'), p('С01', 2))])
    record('С02', 'past', [(fact('behelit_distorted'), p('С02', 0)), (fact('distorted_warning'), p('С02', 1))])
    record('С03', 'past', [(allof(NORMAL, GUTS), p('С03', 0)), (allof(NORMAL, no(GUTS)), p('С03', 1)),
        (NORMAL, p('С03', 2)), (fact('eclipse_hand_lost'), p('С03', 3)), (fact('eclipse_eye_lost'), p('С03', 4)),
        (fact('eclipse_manifestation_defeated'), p('С03', 5))])
    record('С04', 'past', [(fact('circle_reached'), p('С04', 0)), (fact('gift_choice_explained'), p('С04', 1)),
        (allof(ALTER, eq('u_berserk_apostol_outcome')), p('С04', 2)), (REFUSED, p('С04', 3))])
    record('С05', 'past', [(eq('u_berserk_apostol_hand_' + name + '_introduced'), p('С05', i))
        for i, name in enumerate(['void', 'slan', 'ubik', 'conrad', 'femto'])], title='Те, кто стоял у круга')
    record('С06', 'past', [(REFUSED, p('С06', 0))] + [
        (allof(REFUSED, trait('ECLIPSE_SCAR_' + name)), p('С06', i + 1))
        for i, name in enumerate(['HEARING', 'SIGHT', 'TREMOR', 'MEMORIES', 'DREAD'])])
    record('С07', 'past', [
        (anyof(knight('brand'), fact('flora_brand'), fact('brand_explained')), p('С07', 0)),
        (anyof(knight('brand_pain'), fact('flora_brand_pain')), p('С07', 1)),
        (anyof(knight('local_wounds'), allof(SEALED, BRAND), fact('flora_brand')), p('С07', 2))])
    record('С08', 'past', [(anyof(knight('nights'), knight('prepare'), fact('night_experienced')), p('С08', 0)),
        (knight('doors'), p('С08', 1)), (anyof(knight('dawn'), fact('brand_dawn_seen')), p('С08', 2))])
    record('С09', 'past', [(anyof(knight('ward'), fact('ward_examined'), read('flora_travel_folio')), p('С09', 0)),
        (anyof(knight('ward_build'), fact('ward_recipe_explained')), p('С09', 1)),
        (anyof(knight('ward_build'), fact('ward_examined')), p('С09', 2))])
    record('С10', 'past', [(anyof(knight('world_collision'), fact('flora_world'), visited('breach'), SEALED), p('С10', 0)),
        (anyof(knight('local_wounds'), fact('breach_keeper_dead')), p('С10', 1)),
        (anyof(knight('local_wounds'), SEALED), p('С10', 2))])
    record('С11', 'past', [(anyof(knight('projections'), fact('projection_studied')), p('С11', 0)),
        (allof(eq('u_berserk_griffith_projection_defeated'), anyof(knight('projections'), fact('griffith_projection_understood'))), p('С11', 1)),
        (fact('projection_behelit'), p('С11', 2))])
    for code, stem, keep in [('С12', 'judeau', 'berserk_judeau_knife_hilt'), ('С13', 'pippin', 'berserk_pippin_broken_clasp'),
                             ('С14', 'corkus', 'berserk_corkus_scabbard_fragment'), ('С15', 'gaston', 'berserk_gaston_sewing_roll')]:
        proof = eq('u_berserk_godo_witness_' + stem)
        parts = [(allof(proof, GUTS), p(code, 0)), (allof(proof, no(GUTS)), p(code, 1)),
                 (fact('keepsake_' + stem), p(code, 2))]
        if code != 'С15': parts.append((knight('memory_' + stem), p(code, 3)))
        record(code, 'past', parts)
    record('С16', 'past', [(fact('armor_properties'), p('С16', 0)), (fact('armor_cost'), p('С16', 1)),
        (allof(fact('armor_properties'), test('FLORA_FULL_SET')), p('С16', 2)),
        (allof(fact('armor_properties'), fact('armor_part_known'), no(test('FLORA_FULL_SET'))), p('С16', 3)),
        (fact('flora_armor_refused'), p('С16', 4))])
    record('С17', 'past', [(fact('flora_home_lost'), p('С17', 0)), (fact('flora_home_lost'), p('С17', 1)),
        (allof(fact('flora_home_lost'), known('grunbeld'), fact('grunbeld_siege_alive'), no(dead('grunbeld'))), p('С17', 2)),
        (allof(fact('flora_home_lost'), dead('grunbeld')), p('С17', 3)),
        (allof(fact('flora_home_lost'), fact('grunbeld_siege_seen'), no(fact('grunbeld_siege_alive')), no(dead('grunbeld'))), p('С17', 4))])
    done = fact('chapter_closed_known')
    contracts = anyof(*(eq('u_berserk_pact_resolved_'+s) for s in ['count','wyald','rosine','grunbeld']))
    record('С18', 'past', [(allof(done,no(contracts)), p('С18', 0)),
        (allof(done,contracts),'Известные дороги этого пути пройдены. Не каждое решение было победой: принятый договор тоже оставил след. Там, где прорывы закрылись, окрестности получили передышку. Оставшиеся раны и пришедшие существа никуда не исчезли.'), (allof(done, BRAND), p('С18', 1)),
        (allof(done, DEMON), p('С18', 2)), (allof(done, REFUSED), p('С18', 3))])


def body():
    parts = [(allof(eq('u_berserk_apostol_path'), no(eq('u_berserk_apostol_stage', 3))), p('Т01', 0)),
             (allof(eq('u_berserk_apostol_path'), fact('body_changed')), p('Т01', 1)),
             (eq('u_berserk_apostol_path', 2), p('Т02', 0)), (eq('u_berserk_apostol_path', 2), p('Т02', 1)),
             (eq('u_berserk_apostol_left_hand_regrown'), p('Т03', 0)),
             (allof(eq('u_berserk_apostol_left_hand_regrown'), ARM), p('Т03', 1))]
    forms = [
        ('Т04', 'VOID', 'APOSTLE'), ('Т05', 'SLAN', 'APOSTLE'), ('Т06', 'UBIK', 'APOSTLE'),
        ('Т07', 'CONRAD', 'APOSTLE'), ('Т08', 'FEMTO', 'APOSTLE'),
        ('Т09', 'COUNT_FLESH', 'APOSTLE'), ('Т10', 'WYALD_FLESH', 'APOSTLE'),
        ('Т11', 'ROSINE_FLESH', 'APOSTLE'), ('Т12', 'GRUNBELD_FLESH', 'APOSTLE'),
        ('Т13', 'COUNT_PAWN', 'PAWN'), ('Т14', 'WYALD_PAWN', 'PAWN'),
        ('Т15', 'ROSINE_PAWN', 'PAWN'), ('Т16', 'GRUNBELD_PAWN', 'PAWN')]
    for code, name, final in forms:
        condition = trait(name + '_' + final)
        parts += [(condition, text) for text in MANUSCRIPT[code]['paragraphs']]
    parts += [(allof(eq('u_berserk_apostol_path', 3), eq('u_berserk_apostol_pawn_oath_broken')), p('Т17', 0)),
              (allof(eq('u_berserk_apostol_path', 3), eq('u_berserk_apostol_pawn_master_dead')), p('Т17', 1)),
              (allof(anyof(test('APOSTOL_GIFT_COMPLETE'), test('APOSTOL_FLESH_COMPLETE')), fact('body_changed')), p('Т18', 0))]
    record('Т01', 'past', parts, title='Моё тело')


LETTER_ITEMS = [
    'road_caravan_note', 'road_scout_note', 'road_camp_note', 'flora_travel_folio',
    'flora_rescued_manuscript', 'flora_scorched_bookmark', 'apostle_burned_clue',
    'oak_broken_rootcutter', 'oak_wayfarer_ward', 'oak_last_note', 'flora_herbal_folio',
    'cave_scout_note', 'chapel_relief_roster', 'chapel_ritual_note', 'chapel_forest_route',
    'expedition_transfer_note', 'eclipse_last_stand_note', 'count_prison_list',
    'count_physician_ledger', 'count_family_ribbon', 'count_next_trace', 'wyald_muster_roll',
    'wyald_prisoner_account', 'wyald_command_orders', 'rosine_witness_note', 'rosine_faded_ribbon',
    'expedition_alarm_note', 'chapel_last_vigil', 'cave_last_scrap', 'grunbeld_scorched_badge']
RELIC_ITEMS = ['berserk_count_iron_seal', 'berserk_wyald_beast_knot', 'berserk_rosine_mistvale_veil', 'berserk_grunbeld_carapace_shard']


def finds():
    for i, stem in enumerate(RELIC_ITEMS, 1):
        code = f'Р{i:02}'
        proof = fact('relic_' + str(i))
        if i == 1: proof = anyof(proof, read('count_iron_seal'))
        record(code, 'past', [(proof, text) for text in MANUSCRIPT[code]['paragraphs']])
    for i, stem in enumerate(LETTER_ITEMS, 1):
        code = f'П{i:02}'
        record(code, 'past', [(read(stem), text) for text in MANUSCRIPT[code]['paragraphs']])


def build():
    RECORDS.clear()
    places(); people(); experiences(); body(); finds()
    assert len(RECORDS) == 76
    assert len({r['key'] for r in RECORDS}) == 76
    return RECORDS
