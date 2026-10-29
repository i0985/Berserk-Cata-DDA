#!/usr/bin/env python3
"""Owner's 30 October cave prop: one delayed rockfall, not a wound chime."""
import copy

from recover_apostol_33 import read, write, index
from build_playtest_fixes_20261024 import tr, localize

IDLE = 'f_berserk_cave_noisemaker'
ARMED = IDLE + '_armed'
SPENT = 'f_berserk_cave_rockfall_spent'


def main():
    rows = read('furniture/behelit_sites.json')
    prop = index(rows)[IDLE]
    prop['name'] = tr('loosened cave prop', 'расшатанная пещерная подпорка')
    prop['description'] = tr(
        'An old timber braces loose stones in the western side chamber. Its wedge is slipping. Loosen it to start a rockfall, then get behind the bend before the stones come down.',
        'Старый брус удерживает рыхлые камни в западном боковом зале. Клин под ним расшатался. Если ослабить его, начнётся обвал; успейте скрыться за поворотом, пока камни не посыпались.')
    prop['looks_like'] = 'f_wooden_flagpole'
    write('furniture/behelit_sites.json', rows)

    rows = read('furniture/behelit_distractions.json')
    active = index(rows)[ARMED]
    active['name'] = tr('cracking cave prop', 'трещащая пещерная подпорка')
    active['description'] = tr(
        'The loosened timber is giving way. Stones scrape overhead. The collapse has already begun; move away from it.',
        'Ослабленный брус подаётся. Наверху скребут камни. Обвал уже начался; лучше отойти.')
    active['looks_like'] = 'f_wooden_flagpole'
    rows[:] = [o for o in rows if o.get('id') not in {SPENT, 'berserk_cave_rockfall_finish'}]
    rows.extend([
        {'type': 'furniture', 'id': SPENT,
         'name': tr('fallen cave stones', 'осыпавшиеся камни'),
         'description': tr('The broken prop lies beneath a low pile of stones. Nothing here can be set off again.',
                           'Сломанная подпорка лежит под невысоким завалом. Повторно обрушить здесь уже нечего.'),
         'looks_like': 'f_rubble_rock', 'symbol': ':', 'color': 'dark_gray',
         'move_cost_mod': 1, 'required_str': -1, 'flags': ['TRANSPARENT'],
         'examine_action': 'none'},
        {'type': 'ter_furn_transform', 'id': 'berserk_cave_rockfall_finish',
         'furniture': [{'valid_furniture': [ARMED], 'result': SPENT}]}
    ])
    # An old queued reset may survive upgrading a save. It now leaves spent
    # stones, never restores the prop or supplies an infinite noise source.
    index(rows)['berserk_noisemakers_reset']['furniture'] = [
        {'valid_furniture': [ARMED], 'result': SPENT, 'valid_flags': []}]
    write('furniture/behelit_distractions.json', rows)

    rows = read('effects/behelit_site_eocs.json')
    start = index(rows)['EOC_BERSERK_CAVE_DISTRACTION']['effect'][0]
    start['then'] = [
        {'u_transform_radius': 0, 'ter_furn_transform': 'berserk_cave_noisemaker_arm',
         'target_var': {'context_val': 'pos'}},
        {'math': ["_berserk_noise_z = u_val('pos_z')"]},
        {'u_message': tr('You loosen the wedge. The prop creaks and dust trickles from above. Get behind the bend before the stones fall.',
                         'Вы ослабляете клин. Подпорка скрипит, сверху сыплется пыль. Уходите за поворот, пока не рухнули камни.'), 'type': 'warning'},
        {'run_eocs': 'EOC_BERSERK_CAVE_DISTRACTION_PULSE', 'time_in_future': '20 seconds'},
        # Native timed transforms also finish an unloaded-floor collapse.
        # 0.I adds one second, so this is a fallback after the sound at t+20.
        {'u_transform_radius': 0, 'ter_furn_transform': 'berserk_cave_rockfall_finish',
         'target_var': {'context_val': 'pos'}, 'time_in_future': '20 seconds'},
        {'turn_cost': '1 second'}]
    write('effects/behelit_site_eocs.json', rows)

    rows = read('effects/behelit_distraction_eocs.json')
    pulse = index(rows)['EOC_BERSERK_CAVE_DISTRACTION_PULSE']
    # Retain native source-position, floor and furniture guards. The first
    # callback consumes ARMED; remaining callbacks in old saves are harmless.
    guarded = pulse['effect']['then']
    sound = guarded['then']
    if isinstance(sound, list):
        sound = next(o for o in sound if 'u_make_sound' in o)
    sound = copy.deepcopy(sound)
    sound['u_make_sound'] = tr('Stones crash through the side chamber!', 'В боковом зале с грохотом рушатся камни!')
    guarded['then'] = [sound, {'u_transform_radius': 0,
                              'ter_furn_transform': 'berserk_cave_rockfall_finish',
                              'target_var': {'context_val': 'pos'}}]
    index(rows)['EOC_BERSERK_DISTRACTION_BUSY']['effect']['u_message'] = tr(
        'The prop is already giving way. Get clear of the falling stones.',
        'Подпорка уже подаётся. Отойдите от падающих камней.')
    write('effects/behelit_distraction_eocs.json', rows)

    replacements = [
        ('the pendant before we saw what followed its sound',
         'a rockfall before we saw what followed its sound',
         'подвеску раньше, чем увидели то, что пошло на её звук',
         'обвал раньше, чем увидели то, что пошло на грохот'),
        ('We circled the stone pendant and approached the prop from below.',
         'We skirted the loose stones and approached the passage brace from below.',
         'Мы вернулись вокруг каменной подвески и подошли к подпорке снизу.',
         'Мы обошли рыхлые камни и подошли к подпорке прохода снизу.'),
        ('The ring of a stone pendant carries around corners. The creature deeper inside reacts to it. The sound may buy time if the way to the stairs is prepared beforehand.',
         'A loose timber holds stones in the side chamber. Loosening its wedge starts a rockfall. The crash may draw the creature away if I get out of sight before it follows the sound.',
         'Звон каменной подвески слышен за поворотами. Существо в глубине реагирует на него. Звук может выиграть время, если путь к лестнице подготовлен заранее.',
         'В боковом зале камни держатся на расшатанном брусе. Если ослабить клин, начнётся обвал. Грохот может отвлечь существо, если успеть скрыться с глаз до его приближения.')
    ]
    # Mirror real clues in the passive archive without replaying their effects.
    import gettext
    from recover_apostol_33 import MOD
    with (MOD/'lang/mo/ru/LC_MESSAGES/Berserk.mo').open('rb') as f:
        russian = gettext.GNUTranslations(f)

    def prose(value):
        if isinstance(value, list): return [prose(v) for v in value]
        if isinstance(value, dict): return {k: prose(v) for k,v in value.items()}
        if not isinstance(value, str): return value
        changed = value
        translated = russian.gettext(value)
        for before, after, before_ru, after_ru in replacements:
            if before in changed:
                changed = changed.replace(before, after)
                translated = translated.replace(before_ru, after_ru)
        if changed != value:
            if translated == value:
                raise ValueError('Missing Russian cave source: '+value)
            return tr(changed, translated)
        return value

    for file in ['effects/location_interactions_eocs.json',
                 'effects/behelit_adventure_eocs.json', 'dialogue/road_journal.json']:
        write(file, prose(read(file)))
    localize()
    print('Cave prop: one delayed rockfall, persistent spent stones and matching clue text.')


if __name__ == '__main__': main()
