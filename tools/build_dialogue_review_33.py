#!/usr/bin/env python3
"""Owner-requested dialogue review, after all story and utility passes.

The editorial manifest records exact EN/RU before/after pairs. Predicates below
only change presentation and advice; orders, rewards and story choices remain.
"""
import copy
import hashlib
import json

from recover_apostol_33 import ROOT, MOD, read, write, index
from build_playtest_fixes_20261024 import tr, localize


def both(*cs): return {'and': list(cs)}
def either(*cs): return {'or': list(cs)}
def neg(c): return {'not': c}
def eq(name, value=1): return {'math': [f'{name} == {value}']}
HELPERS = {}


def choose(condition, yes, no):
    # Native dynamic_line accepts test_eoc, not logical and/or/not wrappers.
    if any(k in condition for k in ['and', 'or', 'not']):
        name = 'EOC_BERSERK_REVIEW29_LINE_'+hashlib.sha1(json.dumps(condition,sort_keys=True).encode()).hexdigest()[:12].upper()
        HELPERS[name] = {'type':'effect_on_condition','id':name,'effect':[], 'condition':condition}
        condition = {'test_eoc':name}
    return {**condition, 'yes': yes, 'no': no}


def prose():
    spec = json.loads((ROOT/'docs/dialogue_sources/dialogue-review-2026-10-29.json').read_text())
    files = {}
    for p in spec['patches']:
        rows = files.setdefault(p['file'], read(p['file']))
        obj = index(rows)[p['topic']]
        parts = p['path'].strip('/').split('/')
        for part in parts[:-1]: obj = obj[int(part)] if isinstance(obj, list) else obj[part]
        last = int(parts[-1]) if isinstance(obj, list) else parts[-1]
        if obj[last] not in [p['before_en'], p['after_en']]:
            raise ValueError('Editorial source changed: '+p['topic']+p['path'])
        obj[last] = tr(p['after_en'], p['after_ru'])
    # The reference book contains quoted, already heard Knight answers. Keep
    # those copies consistent; do not replay any of their speaker effects.
    candidates = {}
    for p in spec['patches']:
        candidates.setdefault(p['before_en'], set()).add(p['after_en'])
    mirrors = {old:next(iter(new)) for old,new in candidates.items() if len(new)==1}
    def mirror(n):
        if isinstance(n,str):
            if n in mirrors:return mirrors[n]
            if n.endswith('\n\n') and n[:-2] in mirrors:return mirrors[n[:-2]]+'\n\n'
            return n
        if isinstance(n,list):return [mirror(v) for v in n]
        if isinstance(n,dict):return {k:mirror(v) for k,v in n.items()}
        return n
    name='dialogue/road_journal.json'
    files[name]=mirror(files.get(name,read(name)))
    for name, rows in files.items(): write(name, rows)


def flora():
    rows = read('dialogue/flora.json'); by = index(rows)
    # A previously acknowledged Brand used to swallow the armor branch forever.
    # Only the first new Brand gets a special greeting; actual ownership matters.
    entry = by['TALK_BERSERK_FLORA_ENTER']['dynamic_line']['yes']['concatenate']
    old = entry[2]
    hurt = {'test_eoc': old['test_eoc']}
    wounded = old['yes']; quiet = old['no']['yes']
    brand = old['no']['no']['yes']; armor = old['no']['no']['no']['yes']
    new_brand = both({'u_has_bionics': 'bio_berserk_brand_of_sacrifice'},
                     neg(eq('u_berserk_flora33_greeted_brand')))
    owned = both(eq('u_berserk_flora_armor_resolved'),
                 {'test_eoc': 'EOC_BERSERK_FLORA_FULL_SET'})
    entry[2] = choose(hurt, wounded, choose(new_brand, brand, choose(owned, armor, quiet)))
    # Record that she has seen it after the greeting, just as the ceremony
    # records a first encounter. A new mark must not be "new" on every visit.
    seen = {'if': both(new_brand,neg(hurt),eq('u_berserk_flora_met')),
            'then': {'math':['u_berserk_flora33_greeted_brand = 1']}}
    actions = by['TALK_BERSERK_FLORA_ENTER']['speaker_effect']['effect']
    if seen not in actions: actions.append(seen)

    # A follow-up asks for the next step, not the same scolding with six names.
    node = by['TALK_BERSERK_FLORA_NEXT']['dynamic_line']
    places = [
        ('the forest hollow', 'лесной низине'), ('the ashen breach', 'пепельному разрыву'),
        ("the Count's residence", 'резиденции Графа'), ("the Black Dogs' camp", 'лагерю Чёрных Псов'),
        ('the misty valley', 'туманной долине'), ("Grunbeld's stronghold", 'крепости Грюнбельда')]
    for en, ru in places:
        node['yes'] = tr(f'You already have a trail to {en}. Rest and prepare what you need, then follow it. You need not take on every danger at once.',
                         f'У тебя уже есть след к {ru}. Отдохни, собери необходимое и продолжи его. Не нужно браться за все опасности разом.')
        node = node['no']
        if not isinstance(node, dict): break
    write('dialogue/flora.json', rows)


def rickert():
    rows = read('dialogue/godo.json'); by = index(rows)
    menu = by['TALK_BERSERK_RICKERT_MECHANISMS']['responses']
    guts_line = next(r for r in menu if r['topic']=='TALK_BERSERK_RICKERT_GUTS_CROSSBOW')
    trigger = next(r for r in menu if r['topic']=='TALK_BERSERK_RICKERT_INTRO_LOCK')
    trigger['condition'] = neg(copy.deepcopy(guts_line['condition']))
    # All missing-hand checks continue to live on the existing service option.
    order = by['TALK_BERSERK_RICKERT_ORDERS']
    needs = next(r['condition'] for r in order['responses'] if r['topic']=='TALK_BERSERK_GODO_ARM')
    order['dynamic_line'] = choose(needs,
        tr('I can help with the replacement hand and crossbow bolts. For blades, ask Godot. What do you need?',
           'С протезом и арбалетными болтами помогу. За клинками — к Годо. Что тебе сейчас нужно?'),
        tr('Crossbows, fittings and bolts are my work. For a blade, ask Godot. What do you need?',
           'Арбалеты, крепления и болты — моя работа. За клинком — к Годо. Что тебе нужно?'))
    write('dialogue/godo.json', rows)


def knight():
    rows = read('dialogue/skull_knight.json'); by = index(rows)
    masters = by['TALK_BERSERK_SKULL_KNIGHT_MASTERS']['dynamic_line']
    masters['no'] = choose(eq('u_berserk_rickert_met'),
        tr('You know Rickert. Godot is the master of this forge. He took you in; you have yet to speak with him yourself.',
           'Рикерта ты знаешь. Годо — хозяин этой кузницы. Он принял тебя под своей крышей; с ним тебе ещё предстоит поговорить.'),
        masters['no'])
    need = both({'u_has_bionics': 'bio_berserk_hand_stump'},
                neg({'u_has_bionics': 'bio_berserk_arm_cannon'}))
    now = by['TALK_BERSERK_SKULL_KNIGHT_NOW']['dynamic_line']
    now['no'] = choose(need,
        tr('Speak to Rickert first. He can make a replacement for the hand you lost. Regain a reliable grip before setting out on the known trail.',
           'Сначала поговори с Рикертом. Он может сделать замену потерянной кисти. Верни себе надёжный хват, прежде чем отправляться по известному следу.'),
        now['no'])
    # Both farewell routes retain useful practical advice after the NPC leaves.
    summary = by['TALK_BERSERK_SKULL_KNIGHT_SUMMARY']
    summary['dynamic_line'] = choose(need,
        tr('Ask Rickert about a replacement hand. Prepare a place for the night and keep your way out clear. The trail you already know will wait.',
           'Обратись к Рикерту за заменой кисти. Подготовь место для ночлега и оставь свободным выход. Известная тебе дорога подождёт.'),
        summary['dynamic_line'])
    write('dialogue/skull_knight.json', rows)


def book():
    rows = read('dialogue/road_journal.json'); by = index(rows)
    body = by['TALK_BERSERK_REF_T01']['dynamic_line']['concatenate']
    # The late per-master additions repeated both the generic death paragraph
    # and each other. Keep one paragraph per master, preserve every fact flag.
    first = body[:38]; specific = []
    for start in range(38, 46, 2):
        a, b = body[start:start+2]
        ca = {k:v for k,v in a.items() if k not in ['yes','no']}
        cb = {k:v for k,v in b.items() if k not in ['yes','no']}
        specific.append(either(ca, cb))
        en = a['yes'].strip()+' '+b['yes'].strip()+'\n\n'
        # Each sentence has just been registered by the editorial manifest.
        spec = json.loads((ROOT/'docs/dialogue_sources/dialogue-review-2026-10-29.json').read_text())
        ru = {p['after_en']:p['after_ru'] for p in spec['patches']}
        # Grunbeld's short first sentence is unchanged and needs its old gettext.
        if a['yes'] not in ru:
            import gettext
            with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as stream:
                old = gettext.GNUTranslations(stream)
            ru[a['yes']] = old.gettext(a['yes'])
        assert a['yes'] in ru and b['yes'] in ru
        text = tr(en, ru[a['yes']].strip()+' '+ru[b['yes']].strip()+'\n\n')
        first.append(choose(either(ca,cb),text,''))
    generic = first[36]
    generic_condition = {k:v for k,v in generic.items() if k not in ['yes','no']}
    first[36] = choose(both(generic_condition,neg(either(*specific))),generic['yes'],'')
    by['TALK_BERSERK_REF_T01']['dynamic_line']['concatenate'] = first+body[46:]
    write('dialogue/road_journal.json', rows)


def main():
    prose(); flora(); rickert(); knight(); book()
    write('effects/dialogue_review_33_eocs.json',list(HELPERS.values()))
    localize()
    print('Dialogue review: 99 EN/RU corrections, contextual greetings, useful followups and fewer duplicate choices.')


if __name__ == '__main__': main()
