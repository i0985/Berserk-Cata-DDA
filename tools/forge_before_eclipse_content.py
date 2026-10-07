"""Forge conversations by world era and character identity; preserve paid orders."""
import json
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'


def apply_forge_before_eclipse(effects, topics, missions, t, save):
    def m(s): return {'math': [s]}
    def allof(*v): return {'and': list(v)}
    def anyof(*v): return {'or': list(v)}
    def neg(v): return {'not': v}
    def call(id): return {'test_eoc': id}
    def run(id): return {'run_eocs': id}
    def has(id, count=1): return {'u_has_items': {'item': id, 'count': count}}
    def spawn(id, count=1): return {'u_spawn_item': id, 'count': count, 'suppress_message': True}
    def consume(id, count, charges=False): return {'u_consume_item': id, 'charges' if charges else 'count': count}
    def cond(c, yes, no): return {**c, 'yes': yes, 'no': no}
    def r(en, ru, target, condition=None, effect=None):
        row = {'text': t(en, ru), 'topic': target}
        if condition is not None: row['condition'] = condition
        if effect is not None: row['effect'] = effect
        return row
    def back(target='TALK_BERSERK_GODO'):
        labels = {
            'TALK_BERSERK_GODO_EARLY_SWORD': ('Return to the long sword order.', 'Вернуться к заказу длинного меча.'),
            'TALK_BERSERK_GODO_CRAFT': ('Return to questions about smithing.', 'Вернуться к вопросам о кузнечном деле.'),
            'TALK_BERSERK_GODO_METAL': ('Return to the discussion of steel.', 'Вернуться к разговору о стали.'),
            'TALK_BERSERK_GODO_DRAGON_STORY': ('Return to the great blade.', 'Вернуться к большому клинку.'),
            'TALK_BERSERK_GODO_HOME': ('Return to questions about the forge.', 'Вернуться к вопросам о кузнице.'),
            'TALK_BERSERK_RICKERT_CRAFT': ('Return to your craft.', 'Вернуться к твоему ремеслу.'),
            'TALK_BERSERK_RICKERT_APPRENTICE': ('Return to your apprenticeship.', 'Вернуться к разговору об учёбе.'),
            'TALK_BERSERK_RICKERT_HAWKS': ('Return to the Hawks.', 'Вернуться к разговору о Соколах.'),
            'TALK_BERSERK_RICKERT_BOLTS': ('Return to the bolt order.', 'Вернуться к заказу болтов.')}
        return r(*labels.get(target, ('Ask something else.', 'Спросить о другом.')), target)
    def put(id, text, responses, **extra):
        row = {'type': 'talk_topic', 'id': id, 'dynamic_line': text, 'responses': responses, **extra}
        if id in T: T[id].clear(); T[id].update(row)
        else: topics.append(row); T[id] = row
    def eoc(id, effect, condition=None):
        row = {'type': 'effect_on_condition', 'id': id, 'effect': effect}
        if condition is not None: row['condition'] = condition
        effects.append(row); E[id] = row
    def mission(id, en, ru, desc, desc_ru, goal):
        missions.append({'type': 'mission_definition', 'id': id, 'name': t(en, ru),
            'description': t(desc, desc_ru), 'goal': 'MGOAL_CONDITION', 'goal_condition': m(goal),
            'difficulty': 3, 'value': 0, 'origins': ['ORIGIN_GAME_START'],
            'has_generic_rewards': False, 'invisible_on_complete': False,
            'start': {'assign_mission_target': {'om_terrain': 'berserk_godo_workshop',
                'var': {'global_val': 'berserk_godo_location'}, 'reveal_radius': 0}}})
    E = {row['id']: row for row in effects}
    T = {row['id']: row for row in topics}
    godo, rickert = 'TALK_BERSERK_GODO', 'TALK_BERSERK_RICKERT'
    after = call('EOC_BERSERK_FORGE_AFTER_ECLIPSE')
    before = call('EOC_BERSERK_FORGE_BEFORE_ECLIPSE')
    guts = call('EOC_BERSERK_FORGE_GUTS')
    stranger = neg(guts)
    smith = call('EOC_BERSERK_GODO_AT_SMITH')
    engineer = call('EOC_BERSERK_GODO_AT_RICKERT_FORGE')
    identity = anyof({'u_profession': 'berserk'}, {'u_profession': 'berserk_before_eclipse'})
    # Numeric dialogue variable is invisible in character creation and mutation menus.
    # Profession fallback makes the very first line correct in older saves too.
    eoc('EOC_BERSERK_FORGE_GUTS_IDENTITY', m('u_berserk_is_guts = 1'), identity)
    eoc('EOC_BERSERK_FORGE_GUTS', [], anyof(m('u_berserk_is_guts == 1'), identity))
    eoc('EOC_BERSERK_FORGE_AFTER_ECLIPSE', [], anyof(
        m('berserk_eclipse_era == 1'), m('u_berserk_eclipse_rescue_state == 2')))
    eoc('EOC_BERSERK_FORGE_BEFORE_ECLIPSE', [], neg(after))
    E['EOC_BERSERK_GODO_BEGIN']['effect'].insert(0, run('EOC_BERSERK_FORGE_GUTS_IDENTITY'))
    professions = json.loads((MOD / 'professions/professions.json').read_text())
    for row in professions:
        if row['id'] in {'berserk', 'berserk_before_eclipse'}:
            row.setdefault('effect_on_conditions', [])
            if 'EOC_BERSERK_FORGE_GUTS_IDENTITY' not in row['effect_on_conditions']:
                row['effect_on_conditions'].insert(0, 'EOC_BERSERK_FORGE_GUTS_IDENTITY')
    save('professions/professions.json', professions)

    # Only a new Dragonslayer order is deferred until after the Eclipse.
    # Deliveries, collection and refunds for existing orders retain their behavior.
    E['EOC_BERSERK_GODO_START_SWORD']['condition'] = allof(after, E['EOC_BERSERK_GODO_START_SWORD']['condition'])
    for row in T['TALK_BERSERK_GODO_SWORD']['responses']:
        if row.get('effect') == run('EOC_BERSERK_GODO_START_SWORD'):
            row['condition'] = allof(after, row['condition'])

    early = 'TALK_BERSERK_GODO_EARLY_SWORD'
    own_early = has('true_guts_early_sword')
    requirements = [('steel_lump', 4, True), ('hc_steel_lump', 1, True),
                    ('charcoal', 200, True), ('leather', 2, False)]
    eoc('EOC_BERSERK_GODO_START_EARLY_SWORD', [m('u_berserk_godo_early_state = 1'),
        run('EOC_BERSERK_GODO_ORDER_SYNC')], allof(smith, before,
        m('u_berserk_godo_early_state == 0'), neg(own_early)))
    eoc('EOC_BERSERK_GODO_EARLY_MATERIALS', [consume(*v) for v in requirements] + [
        m("u_berserk_godo_early_ready_at = time('now') + 43200"),
        m('u_berserk_godo_early_state = 2'), run('EOC_BERSERK_GODO_ORDER_SYNC')],
        allof(smith, m('u_berserk_godo_early_state == 1'), neg(own_early),
              *[has(id, count) for id, count, _ in requirements]))
    eoc('EOC_BERSERK_GODO_EARLY_REFUND', [
        {'if': m('u_berserk_godo_early_state == 2'), 'then': [spawn(id, count) for id, count, _ in requirements]},
        m('u_berserk_godo_early_state = 3'), run('EOC_BERSERK_GODO_ORDER_SYNC')],
        allof(smith, own_early, m('u_berserk_godo_early_state > 0'), m('u_berserk_godo_early_state < 3')))
    eoc('EOC_BERSERK_GODO_EARLY_CLAIM', [
        {'if': own_early, 'then': run('EOC_BERSERK_GODO_EARLY_REFUND'),
         'else': [spawn('true_guts_early_sword'), m('u_berserk_godo_early_state = 3'), run('EOC_BERSERK_GODO_ORDER_SYNC')]}],
        allof(smith, m('u_berserk_godo_early_state == 2'), m("time('now') >= u_berserk_godo_early_ready_at")))
    for key, state, end, title, title_ru, desc, desc_ru in [
        ('MATERIALS', 1, 2, 'Steel for a long battle sword', 'Сталь для длинного боевого меча',
         'Bring Godot 4 steel lumps, 1 high-steel lump, 200 charcoal and 2 leather patches. Deliver the full set at the forge.',
         'Принесите Годо 4 куска стали, 1 кусок высокоуглеродистой стали, 200 единиц древесного угля и 2 лоскутка кожи. Весь набор передаётся в кузнице.'),
        ('COLLECT', 2, 3, 'Collect the long battle sword', 'Забрать длинный боевой меч',
         'Return to Godot twelve hours after delivering the materials. He repairs an early sword you already own rather than duplicating it.',
         'Вернитесь к Годо через двенадцать часов после передачи материалов. Уже имеющийся ранний меч он ремонтирует, а не выдаёт повторно.')]:
        mid = 'MISSION_BERSERK_GODO_EARLY_' + key
        mission(mid, title, title_ru, desc, desc_ru, f'u_berserk_godo_early_state >= {end}')
        E['EOC_BERSERK_GODO_ORDER_SYNC']['effect'].append({
            'if': m(f'u_berserk_godo_early_state >= {end}'),
            'then': {'if': {'u_has_mission': mid}, 'then': {'finish_mission': mid, 'success': True}},
            'else': {'if': allof(m(f'u_berserk_godo_early_state == {state}'), neg({'u_has_mission': mid})),
                     'then': {'assign_mission': mid}}})
    put(early, cond(own_early,
        t('You already have the long blade. Show me a damaged edge and I will mend it; another copy will not make the first one better.',
          'Длинный клинок у тебя уже есть. Покажи повреждённое лезвие — выправлю. Второй экземпляр первый лучше не сделает.'),
        t('A long battle sword, no gilding. Bring 4 steel lumps, 1 high-steel lump, 200 charcoal and 2 leather patches. Twelve hours after the delivery, come back for the tempered blade. Bring sound steel; raw ore still needs smelting.',
          'Длинный боевой меч, без позолоты. Нужны 4 куска стали, 1 кусок высокоуглеродистой стали, 200 единиц древесного угля и 2 лоскутка кожи. Через двенадцать часов после передачи заберёшь закалённый клинок. Приноси добрую сталь: сырую руду сперва нужно выплавить.')), [
        r('No ornaments. Forge a blade I can trust.', 'Без украшений. Выкуй клинок, на который можно положиться.', early,
          allof(guts, before, m('u_berserk_godo_early_state == 0'), neg(own_early)), run('EOC_BERSERK_GODO_START_EARLY_SWORD')),
        r('I agree. Take my order for the long sword.', 'Согласен. Прими заказ на длинный меч.', early,
          allof(stranger, before, m('u_berserk_godo_early_state == 0'), neg(own_early)), run('EOC_BERSERK_GODO_START_EARLY_SWORD')),
        r('Deliver the steel, charcoal and leather.', 'Передать сталь, уголь и кожу.', early,
          allof(m('u_berserk_godo_early_state == 1'), neg(own_early), *[has(id, count) for id, count, _ in requirements]),
          run('EOC_BERSERK_GODO_EARLY_MATERIALS')),
        r('Collect the long sword.', 'Забрать длинный меч.', early,
          allof(m('u_berserk_godo_early_state == 2'), m("time('now') >= u_berserk_godo_early_ready_at")), run('EOC_BERSERK_GODO_EARLY_CLAIM')),
        r('I already have this blade. Return my materials.', 'Такой клинок у меня уже есть. Верни материалы.', early,
          allof(own_early, m('u_berserk_godo_early_state > 0'), m('u_berserk_godo_early_state < 3')), run('EOC_BERSERK_GODO_EARLY_REFUND')),
        r('How is the order coming along?', 'Как продвигается заказ?', 'TALK_BERSERK_GODO_EARLY_STATUS'),
        r('Straighten my old blade, then.', 'Тогда выправь мой старый клинок.', 'TALK_BERSERK_GODO_REPAIR', own_early),
        r('Why do you need different steels?', 'Зачем тебе разные виды стали?', 'TALK_BERSERK_GODO_METAL'), back()])
    status = cond(m('u_berserk_godo_early_state == 1'),
        t('Bring 4 steel lumps, 1 high-steel lump, 200 charcoal and 2 leather patches. I take the complete set together.',
          'Принеси 4 куска стали, 1 кусок высокоуглеродистой стали, 200 единиц древесного угля и 2 лоскутка кожи. Принимаю весь набор вместе.'),
        cond(m('u_berserk_godo_early_state == 2'),
            t('Your material is at the forge. Give me twelve hours from the delivery, then collect the blade.',
              'Материал уже у горна. Дай двенадцать часов с момента передачи, потом забирай клинок.'),
            cond(m('u_berserk_godo_early_state == 3'),
                t('This order is settled. Keep the blade in good repair.', 'Заказ завершён. Следи за клинком.'),
                t('We have not agreed on this order. Speak to me about a long battle sword.', 'Этот заказ мы ещё не согласовали. Спроси меня о длинном боевом мече.'))))
    put('TALK_BERSERK_GODO_EARLY_STATUS', status, [back(early), back()])
    T[early]['dynamic_line']['no'] = cond(m('u_berserk_godo_early_state > 0'), status, T[early]['dynamic_line']['no'])

    put('TALK_BERSERK_GODO_ENTER', cond(after,
        cond(guts, t('Guts. Still alive, then. Let me see what you brought back before you tell me what you want.',
                     'Гатс. Значит, ещё жив. Дай посмотреть, с чем вернулся, прежде чем скажешь, чего хочешь.'),
                   t('You look as though the road tried to chew you up. Sit if you must. Tell me what work you need.',
                     'Вид у тебя такой, будто дорога пыталась тебя пережевать. Садись, если нужно. Говори, какая работа требуется.')),
        t('*The hammer keeps its rhythm. "What do you want? This is a forge, not an inn. And if you want a sword fit for a king, go bother someone else."',
          '*Молот продолжает отбивать ритм. «Чего надо? Здесь кузница, не постоялый двор. А если нужен меч для короля — иди донимай кого-нибудь другого».')), [
        r('Easy, old man. I need my old blade straightened.', 'Сбавь обороты, старик. Мне нужно выправить старый клинок.', 'TALK_BERSERK_GODO_RECOGNIZE', allof(before, guts)),
        r('I am passing through. I need a good smith.', 'Я проездом. Мне нужен хороший кузнец.', 'TALK_BERSERK_GODO_STRANGER', allof(before, stranger)),
        r('Let us talk about the work.', 'Поговорим о работе.', godo, after),
        r('I will come back later.', 'Зайду позже.', 'TALK_DONE')], speaker_effect={'effect': run('EOC_BERSERK_GODO_BEGIN')})
    put('TALK_BERSERK_GODO_RECOGNIZE', t(
        '*Godot stills the hammer and squints. "So it is you, Guts. The blade has taken a beating, but you have not broken it yet. All right. What does it need?"',
        '*Годо останавливает молот и прищуривается. «Так это ты, Гатс. Клинку досталось, но сломать его пока не сумел. Ладно. Что с ним делать?»'), [
        r('Let me show you the blade.', 'Дай покажу клинок.', 'TALK_BERSERK_GODO_REPAIR'),
        r('I came to ask a few things first.', 'Сначала хочу кое-что спросить.', godo)])
    put('TALK_BERSERK_GODO_STRANGER', t(
        'A good smith? You found the best. I stopped making ornaments for lords a long time ago. If you want honest iron, say what it must endure. If you want gilding, the door is behind you.',
        'Хорошего кузнеца? Ты нашёл лучшего. Украшения для господ я давно не делаю. Нужен добрый металл — скажи, что ему предстоит выдержать. Нужна позолота — дверь у тебя за спиной.'), [
        r('A long sword, heavy and plain.', 'Длинный меч, тяжёлый и без украшений.', early, before),
        r('Why did you stop working for lords?', 'Почему перестал работать на господ?', 'TALK_BERSERK_GODO_ISOLATION'), back()])
    old = T[godo]['responses']
    sparks = next(row for row in old if row['topic'] == 'TALK_BERSERK_GODO_SPARKS')
    put(godo, cond(guts,
        t('Speak, Guts. The iron will not stay hot forever.', 'Говори, Гатс. Железо не будет ждать вечно.'),
        t('Honest iron or an honest answer. What do you need?', 'Добрый металл или прямой ответ. Что тебе нужно?')), [
        r('I need a reliable long sword.', 'Мне нужен надёжный длинный меч.', early, anyof(before, m('u_berserk_godo_early_state > 0'))),
        r('Can you forge a weapon for fighting demons?', 'Можешь выковать оружие против демонов?', 'TALK_BERSERK_GODO_SWORD', anyof(after, m('u_berserk_godo_sword_state > 0'))),
        r('Can you repair my blade?', 'Починишь мой клинок?', 'TALK_BERSERK_GODO_REPAIR'),
        r('Tell me about your craft and your life here.', 'Расскажи о ремесле и жизни здесь.', 'TALK_BERSERK_GODO_CRAFT'), sparks,
        r('Who could help with a prosthetic?', 'Кто поможет с протезом?', 'TALK_BERSERK_GODO_RICKERT',
          anyof({'u_has_bionics': 'bio_berserk_hand_stump'}, call('EOC_BERSERK_GODO_HAS_ARM'), m('u_berserk_godo_arm_state > 0'))),
        r('May I rest here? And who is Rickert?', 'Можно здесь отдохнуть? Кто такой Рикерт?', 'TALK_BERSERK_GODO_HOME'),
        r('I will leave you to your work.', 'Не буду мешать работе.', 'TALK_DONE')])
    put('TALK_BERSERK_GODO_CRAFT', t('Ask. Just do not expect a pretty answer.', 'Спрашивай. Только красивого ответа не жди.'), [
        r('Why live so far from towns?', 'Почему живёшь так далеко от городов?', 'TALK_BERSERK_GODO_ISOLATION'),
        r('What makes a blade reliable?', 'От чего зависит надёжность клинка?', 'TALK_BERSERK_GODO_METAL'),
        r('Tell me about the blade you made to kill a dragon.', 'Расскажи о мече, который ты выковал для убийства дракона.', 'TALK_BERSERK_GODO_DRAGON_STORY'),
        r('Were you always a smith?', 'Ты всегда был кузнецом?', 'TALK_BERSERK_GODO_LIFE'),
        r('Which repairs do you take?', 'За какой ремонт берёшься?', 'TALK_BERSERK_GODO_REPAIR'), back()])
    put('TALK_BERSERK_GODO_ISOLATION', t(
        'A lord asks for a golden guard, then another asks for a blade nobody could use. They admire the polish and forget the steel. Here I can hear the hammer without somebody measuring how grand the weapon will look at a feast.',
        'Один господин просит золотую гарду, другой — меч, которым никто не сможет пользоваться. Любуются блеском, а про сталь забывают. Здесь я слышу молот, пока никто не прикидывает, как величественно оружие будет смотреться на пиру.'), [
        r('Then why make weapons at all?', 'Зачем тогда вообще делать оружие?', 'TALK_BERSERK_GODO_PRICE'),
        r('Does Rickert ever tire of this place?', 'Рикерту здесь не скучно?', 'TALK_BERSERK_GODO_HOME'), back('TALK_BERSERK_GODO_CRAFT')])
    put('TALK_BERSERK_GODO_METAL', t(
        'Too soft, and the edge folds. Too brittle, and it snaps. Good steel is only the beginning: heat, temper and shape must suit the work. No blade excuses a foolish blow into stone, and weight alone will not cut every breastplate.',
        'Мягкий металл замнётся, хрупкий — лопнет. Хорошая сталь лишь начало: нагрев, закалка и форма должны подходить работе. Никакой клинок не простит дурного удара о камень, и одним весом любой нагрудник не прорубишь.'), [
        r('Can I bring raw ore?', 'Можно принести сырую руду?', 'TALK_BERSERK_GODO_ORE'),
        r('Tell me about the long sword.', 'Расскажи о длинном мече.', early, anyof(before, m('u_berserk_godo_early_state > 0'))),
        r('Tell me about the Dragonslayer.', 'Расскажи о Драконоборце.', 'TALK_BERSERK_GODO_DRAGON_STORY'), back('TALK_BERSERK_GODO_CRAFT')])
    put('TALK_BERSERK_GODO_ORE', t(
        'Ore has to become iron, then steel fit for the blade. For your order, bring the steel itself. Sound recovered metal or steel you smelted will do. Judge the metal, not the fine story about the mine it came from.',
        'Руду сперва нужно превратить в железо, потом в сталь для клинка. Для заказа приноси уже сталь. Подойдёт добротный найденный металл или твоя собственная плавка. Смотреть надо на металл, а не на красивую историю о шахте, из которой его привезли.'), [back('TALK_BERSERK_GODO_METAL'), back()])
    put('TALK_BERSERK_GODO_DRAGON_STORY', cond(before,
        t('The Dragonslayer. A lord demanded a sword to kill a dragon, so I made one. Then his knights saw it and decided they preferred smaller legends. It is a slab of iron with an edge. Do not mistake its weight for proof that you can use it.',
          'Драконоборец. Господин потребовал меч для убийства дракона — я сделал. Рыцари посмотрели и решили, что предпочитают легенды поменьше. Это глыба железа с лезвием. Не думай, будто один её вес доказывает, что ты сумеешь ею пользоваться.'),
        t('That ridiculous blade finally has work worthy of its weight. Still, a Dragonslayer is no promise that you will survive. Iron can endure what flesh cannot. Remember the difference.',
          'У этого нелепого клинка наконец появилась работа под стать его весу. Но Драконоборец не обещает тебе выживания. Железо выдержит то, чего не выдержит плоть. Помни разницу.')), [
        r('Why keep it?', 'Зачем хранить его?', 'TALK_BERSERK_GODO_DRAGON_KEEP'),
        r('I need a sword I can use now.', 'Мне нужен меч, которым я смогу пользоваться сейчас.', early, before),
        r('Then let us discuss that great blade.', 'Тогда обсудим этот большой клинок.', 'TALK_BERSERK_GODO_SWORD', after), back('TALK_BERSERK_GODO_CRAFT')])
    put('TALK_BERSERK_GODO_DRAGON_KEEP', t(
        'Because I made it. Bad judgment does not erase good work. I kept it to remember that a smith must think about the hands that will carry his iron, not only the order he was given.',
        'Потому что я его сделал. Дурной замысел не отменяет хорошей работы. Храню, чтобы помнить: кузнец должен думать о руках, которые понесут его металл, а не только о заказе.'), [back('TALK_BERSERK_GODO_DRAGON_STORY'), back()])
    home = t('The forge is below; the loft has room to sleep. Rickert works on moving parts while I shape the heavy pieces. Keep the stair clear, and do not take tools away without asking.',
             'Внизу кузница, на чердаке найдётся место для сна. Рикерт занимается подвижными деталями, я — тяжёлыми заготовками. Не заставляй лестницу и не уноси инструменты без спроса.')
    put('TALK_BERSERK_GODO_HOME', cond({'u_has_bionics': 'bio_berserk_brand_of_sacrifice'},
        t('You can rest in the loft. We will help with what we can, but this roof will not silence the Brand. Keep a way to the door. Rickert builds the moving parts; I forge the blades.',
          'На чердаке можно отдохнуть. Поможем чем сумеем, но эта крыша не заставит Клеймо замолчать. Оставь дорогу к двери. Рикерт собирает подвижные детали, я кую клинки.'), home), [
        r('How did Rickert become your apprentice?', 'Как Рикерт стал твоим учеником?', 'TALK_BERSERK_GODO_APPRENTICE'), back()])
    put('TALK_BERSERK_GODO_APPRENTICE', t(
        'He looks at a crooked joint and wants to know why it sticks. That is a useful habit. He still gets carried away with clever mechanisms, but he will redo a bad piece instead of hiding it under polish. I can work with that.',
        'Увидит кривой шарнир — сразу хочет понять, почему заедает. Полезная привычка. С хитрыми механизмами иногда увлекается, зато плохую деталь переделает, а не спрячет под полировкой. С таким можно работать.'), [back('TALK_BERSERK_GODO_HOME'), back()])
    # Philosophical conversations must not lead to a future order before its era.
    for id in ['TALK_BERSERK_GODO_PRICE', 'TALK_BERSERK_GODO_SPARKS_HOME']:
        rs = T[id]['responses']
        for row in rs:
            if row['topic'] == 'TALK_BERSERK_GODO_SWORD': row['condition'] = after
        rs.insert(0, r('Then make a long sword I can return with.', 'Тогда сделай длинный меч, с которым я смогу вернуться.', early, before))
    del T['TALK_BERSERK_GODO_SPARKS_RAGE']['dynamic_line']['math']
    # Keep the survivor-specific wording out of worlds where only someone else saw the ritual.
    T['TALK_BERSERK_GODO_SPARKS_RAGE']['dynamic_line']['test_eoc'] = 'EOC_BERSERK_FORGE_WITNESS'
    eoc('EOC_BERSERK_FORGE_WITNESS', [], m('u_berserk_eclipse_rescue_state == 2'))

    post_line = T[rickert]['dynamic_line']
    post_line['yes'] = cond(guts,
        t('Guts! Thank goodness you are awake. The Skull Knight brought you barely alive. We tended your wounds. Where are Judeau, Pippin, Corkus? What happened to the Band?',
          'Гатс! Слава богу, ты очнулся. Рыцарь-Череп принёс тебя едва живым. Мы перевязали твои раны. Где Джудо, Пиппин, Коркус? Что произошло с отрядом?'), post_line['yes'])
    post_line['no'] = cond(guts,
        t('Guts. I am glad you came back. We can talk, or I can work on the mechanism. What do you need?',
          'Гатс. Я рад, что ты вернулся. Можем поговорить, или я займусь механизмом. Чем помочь?'), post_line['no'])
    T[rickert]['dynamic_line'] = cond(after, post_line, cond(guts,
        t('Guts! You came back! I am working on this crossbow; the lock keeps catching. Godot is grumbling as usual. Have you brought your blade, or just come to see us?',
          'Гатс! Ты вернулся! Вожусь с арбалетом: замок снова заедает. Годо ворчит, как обычно. Принёс клинок или просто заглянул к нам?'),
        t('Oh, hello! Sorry, I was checking the lock on my crossbow. Have you come to Godot? He sounds cross today, but he is easier to talk to when you ask about the work.',
          'Ой, привет! Извини, проверял замок арбалета. Ты к Годо? Он сегодня ворчит, но если спросить о работе, поговорить с ним проще.')))
    arm_needed = anyof({'u_has_bionics': 'bio_berserk_hand_stump'}, call('EOC_BERSERK_GODO_HAS_ARM'), m('u_berserk_godo_arm_state > 0'))
    for row in T[rickert]['responses']:
        if row['topic'] in {'TALK_BERSERK_GODO_ARM', 'TALK_BERSERK_RICKERT_ARM', 'TALK_BERSERK_RICKERT_CARE'}:
            row['condition'] = allof(arm_needed, row['condition']) if 'condition' in row else arm_needed
        if row['topic'] == 'TALK_BERSERK_RICKERT_CRAFT': row['text'] = t('Tell me about your craft.', 'Расскажи о своём ремесле.')
    T[rickert]['responses'][2:2] = [
        r('What are you working on?', 'Над чем ты работаешь?', 'TALK_BERSERK_RICKERT_MECHANISM'),
        r('Can you make crossbow bolts?', 'Сделаешь болты для арбалета?', 'TALK_BERSERK_RICKERT_BOLTS'),
        r('Tell me about the Band of the Hawk.', 'Расскажи об Отряде Сокола.', 'TALK_BERSERK_RICKERT_HAWKS', before)]
    put('TALK_BERSERK_RICKERT_MECHANISM', t(
        'The crossbow lock. I want it to release cleanly and hold safely while I load. Rushing the shot does not help if the string jumps before I aim. Godot calls these little mechanisms toys until one saves him work.',
        'Замок арбалета. Хочу, чтобы спуск срабатывал плавно, а при заряжании тетива держалась надёжно. Быстрый выстрел бесполезен, если она срывается до прицеливания. Годо зовёт такие механизмы игрушками, пока один из них не облегчает ему работу.'), [
        r('Where did you learn that?', 'Где ты этому научился?', 'TALK_BERSERK_RICKERT_APPRENTICE'),
        r('How do you fight with it?', 'Как ты с ним сражаешься?', 'TALK_BERSERK_RICKERT_TACTICS'),
        r('Then tell me about the bolts.', 'Тогда расскажи о болтах.', 'TALK_BERSERK_RICKERT_BOLTS'), back(rickert)])
    put('TALK_BERSERK_RICKERT_CRAFT', cond(before,
        t('I learn forging from Godot, but small moving parts are my favorite work. Locks, hinges, crossbows. Each piece can be sound on its own and still fail if it does not fit the next.',
          'Кузнечному делу учусь у Годо, но больше всего люблю подвижные детали. Замки, шарниры, арбалеты. Каждая деталь может быть хороша сама по себе, а вместе они не заработают, если плохо подогнаны.'),
        t('Godot taught me the metalwork; I put that skill into mechanisms and the arm cannon. Each fitting matters when it has to carry your weight or protect your life.',
          'Годо научил меня работать с металлом; это умение я вкладываю в механизмы и руку-пушку. Каждое крепление важно, когда ему предстоит выдержать твой вес или защитить жизнь.')), [
        r('What has Godot taught you?', 'Чему тебя научил Годо?', 'TALK_BERSERK_RICKERT_APPRENTICE'),
        r('Why a crossbow instead of a sword?', 'Почему арбалет, а не меч?', 'TALK_BERSERK_RICKERT_TACTICS'),
        r('Can you build my prosthesis?', 'Сделаешь мой протез?', 'TALK_BERSERK_GODO_ARM', arm_needed), back(rickert)])
    put('TALK_BERSERK_RICKERT_APPRENTICE', t(
        'On the road with the Hawks, I learned to keep equipment working with whatever we had. Here Godot makes me redo each bad fit. A clever design still needs careful hands. I would rather finish one reliable mechanism than boast about ten unfinished ones.',
        'В походах с Соколами учился поддерживать снаряжение тем, что было под рукой. Здесь Годо заставляет переделывать каждую плохую подгонку. Даже хитрому замыслу нужны внимательные руки. Лучше закончу один надёжный механизм, чем буду хвастаться десятью недоделанными.'), [
        r('What should I practice first?', 'С чего мне начать учиться?', 'TALK_BERSERK_RICKERT_LEARN'), back('TALK_BERSERK_RICKERT_CRAFT'), back(rickert)])
    put('TALK_BERSERK_RICKERT_LEARN', t(
        'Start with things you can examine after using them: a strap, a shaft, a simple fitting. See what bent or slipped, then correct it. Making a whole moving hand is advanced fabrication and mechanics; do not judge your first attempt by that.',
        'Начни с вещей, которые можно осмотреть после работы: ремня, древка, простого крепления. Посмотри, что согнулось или соскользнуло, исправь. Целая подвижная рука требует серьёзного производства и механики; не меряй ею свою первую попытку.'), [back('TALK_BERSERK_RICKERT_APPRENTICE'), back(rickert)])
    put('TALK_BERSERK_RICKERT_TACTICS', cond(guts,
        t('I cannot swing a blade like you, Guts. I look for a clear shot, a way to reload and somewhere to retreat. It is easier to help a companion from a good position than to prove I am brave in the middle of a melee.',
          'Я не могу махать клинком, как ты, Гатс. Ищу хороший обзор, место для перезарядки и путь отхода. С удобной позиции товарищу помочь проще, чем доказывать храбрость в гуще рукопашной.'),
        t('I am better with a crossbow than a heavy sword. A clear shot, space to reload and a way back matter more to me than standing in the front rank. I can help, but you should not expect me to stop a charging apostle alone.',
          'С арбалетом у меня получается лучше, чем с тяжёлым мечом. Обзор, место для перезарядки и дорога назад важнее переднего ряда. Я могу помочь, но не жди, что один остановлю несущегося апостола.')), [
        r('Can we travel together?', 'Можем пойти вместе?', 'TALK_BERSERK_RICKERT_ROAD',
          allof(neg('npc_following'), m('n_berserk_rickert_recruit_refused != 1'))),
        r('Let us talk about ammunition.', 'Поговорим о боеприпасах.', 'TALK_BERSERK_RICKERT_BOLTS'), back(rickert)])
    put('TALK_BERSERK_RICKERT_HAWKS', cond(guts,
        t('You remember the marches, Guts. When the fighting ended there were straps to mend, bolts to straighten and somebody needing help. I like making things that let them come back from the next battle.',
          'Ты помнишь переходы, Гатс. После боя нужно было чинить ремни, выправлять болты, кому-то помогать. Мне нравится делать вещи, с которыми они смогут вернуться из следующего сражения.'),
        t('I traveled with the Band of the Hawk. You hear stories about the battles, but much of life was marching, mending equipment and looking after one another. Judeau helped people quietly; Corkus complained loudly enough for everyone.',
          'Я ходил с Отрядом Сокола. Обычно рассказывают о битвах, но большая часть жизни — переходы, ремонт снаряжения и забота друг о друге. Джудо помогал людям тихо, а Коркус ворчал так, что всем было слышно.')), [
        r('What kind of commander is Griffith?', 'Какой Гриффит командир?', 'TALK_BERSERK_RICKERT_COMMANDER', before),
        r('Do you miss the others?', 'Скучаешь по остальным?', 'TALK_BERSERK_RICKERT_HAWK_HOME', before), back(rickert)])
    put('TALK_BERSERK_RICKERT_COMMANDER', t(
        'People believe him when he says we can go farther. I believe him too. But a march is still hard on the people carrying the packs. A commander needs those people to reach the end, not just a splendid plan.',
        'Люди ему верят, когда он говорит, что мы можем идти дальше. Я тоже верю. Но тем, кто несёт поклажу, переход от этого легче не становится. Командиру нужны люди, дошедшие до конца, а не один прекрасный замысел.'), [back('TALK_BERSERK_RICKERT_HAWKS'), back(rickert)])
    put('TALK_BERSERK_RICKERT_HAWK_HOME', t(
        'Of course. Here the fire is warm and the work makes sense, but sometimes I listen for the noise of the camp. I hope they find a place where returning from a battle is not the only thing worth celebrating.',
        'Конечно. Здесь тепло у огня и работа понятная, но иногда я всё равно прислушиваюсь, будто рядом лагерь. Надеюсь, они найдут место, где возвращение из боя будет не единственным поводом радоваться.'), [back('TALK_BERSERK_RICKERT_HAWKS'), back(rickert)])
    T['TALK_BERSERK_RICKERT_HOME']['dynamic_line'] = cond({'u_has_bionics': 'bio_berserk_brand_of_sacrifice'},
        T['TALK_BERSERK_RICKERT_HOME']['dynamic_line'],
        t('The stair leads to the sleeping loft. Leave the forge tools below, and keep the stair and doors clear. We need room to carry metal and water safely.',
          'Лестница ведёт на спальный чердак. Кузнечные инструменты оставь внизу, не заставляй лестницу и двери. Нам нужно место, чтобы безопасно носить металл и воду.'))

    # A real, repeatable mundane service rather than a promise of unimplemented explosives.
    supplies = [('steel_chunk', 1, True), ('stick', 1, False), ('thread', 20, True), ('feather', 10, True), ('charcoal', 50, True)]
    ready = allof(m('u_berserk_rickert_bolts_pending == 1'), m("time('now') >= u_berserk_rickert_bolts_ready_at"))
    eoc('EOC_BERSERK_RICKERT_ORDER_BOLTS', [consume(*v) for v in supplies] + [
        m('u_berserk_rickert_bolts_pending = 1'), m("u_berserk_rickert_bolts_ready_at = time('now') + 1800")],
        allof(engineer, m('u_berserk_rickert_bolts_pending != 1'), *[has(id, count) for id, count, _ in supplies]))
    eoc('EOC_BERSERK_RICKERT_COLLECT_BOLTS', [spawn('bolt_wood_bodkin', 10), m('u_berserk_rickert_bolts_pending = 0')], allof(engineer, ready))
    bolt_line = cond(m('u_berserk_rickert_bolts_pending == 1'),
        cond(m("time('now') >= u_berserk_rickert_bolts_ready_at"),
            t('Your ten bolts are ready at the forge. Collect them there before we start another batch.', 'Твои десять болтов готовы в кузнице. Забери их там, прежде чем закажешь следующую партию.'),
            t('I am working on the batch. It takes half an hour from the delivery. The material is already here.',
              'Работаю над партией. Нужны полчаса с момента передачи. Материал уже у меня.')),
        t('I can make ten wooden bodkin bolts with steel tips. Bring 1 steel chunk, 1 stick, 20 thread, 10 feathers and 50 charcoal. It takes half an hour here at the forge. These are ordinary bolts, not explosive tricks.',
          'Сделаю десять деревянных болтов с острыми стальными наконечниками. Нужны 1 обломок стали, 1 палка, 20 единиц ниток, 10 перьев и 50 единиц древесного угля. Работа займёт полчаса здесь, в кузнице. Это обычные болты, без взрывных ухищрений.'))
    put('TALK_BERSERK_RICKERT_BOLTS', bolt_line, [
        r('Make a batch of ten bolts.', 'Сделай партию из десяти болтов.', 'TALK_BERSERK_RICKERT_BOLTS',
          allof(engineer, m('u_berserk_rickert_bolts_pending != 1'), *[has(id, count) for id, count, _ in supplies]), run('EOC_BERSERK_RICKERT_ORDER_BOLTS')),
        r('Collect the ten bolts.', 'Забрать десять болтов.', 'TALK_BERSERK_RICKERT_BOLTS', allof(engineer, ready), run('EOC_BERSERK_RICKERT_COLLECT_BOLTS')),
        r('Will those pierce any armor?', 'Они пробьют любую броню?', 'TALK_BERSERK_RICKERT_BOLT_LIMITS'), back(rickert)])
    put('TALK_BERSERK_RICKERT_BOLT_LIMITS', t(
        'A pointed steel tip helps against armor; it does not make a small crossbow a siege engine. The shot and the target still matter. I would rather you have reliable bolts than trust a promise that one will kill anything.',
        'Острый стальной наконечник помогает против брони, но маленький арбалет осадной машиной не делает. Важны и выстрел, и цель. Лучше дам надёжные болты, чем обещание, будто одним можно убить что угодно.'), [back('TALK_BERSERK_RICKERT_BOLTS'), back(rickert)])


def apply_forge_journal(t, read, write):
    """Read-only order views; book dialogues never gain smith/engineer services."""
    rows = read('dialogue/road_journal.json')
    T = {row['id']: row for row in rows}
    def m(s): return {'math': [s]}
    def cond(c, yes, no): return {**c, 'yes': yes, 'no': no}
    def r(en, ru, target): return {'text': t(en, ru), 'topic': target}
    menu = T['TALK_BERSERK_JOURNAL_ORDERS']
    menu['responses'] = [row for row in menu['responses'] if row['topic'] not in {'TALK_BERSERK_JOURNAL_EARLY', 'TALK_BERSERK_JOURNAL_BOLTS'}]
    menu['responses'].insert(0, r('Long battle sword order.', 'Заказ длинного боевого меча.', 'TALK_BERSERK_JOURNAL_EARLY'))
    menu['responses'].insert(-1, r('Crossbow bolt batch.', 'Партия арбалетных болтов.', 'TALK_BERSERK_JOURNAL_BOLTS'))
    for row in menu['responses']:
        if row['topic'] == 'TALK_BERSERK_JOURNAL_SWORD':
            row['condition'] = {'or': [{'test_eoc': 'EOC_BERSERK_FORGE_AFTER_ECLIPSE'}, m('u_berserk_godo_sword_state > 0')]}
        if row['topic'] == 'TALK_BERSERK_JOURNAL_ARM':
            row['condition'] = {'or': [{'u_has_bionics': 'bio_berserk_hand_stump'},
                                     {'test_eoc': 'EOC_BERSERK_GODO_HAS_ARM'}, m('u_berserk_godo_arm_state > 0')]}
    stages = [
        ('Before the Eclipse, speak with Godot about a long battle sword. If you already have the early sword, ask about repairs.',
         'До Затмения спросите Годо о длинном боевом мече. Если ранний меч уже есть, обратитесь за ремонтом.'),
        ('Deliver 4 steel lumps, 1 high-steel lump, 200 charcoal and 2 leather patches to Godot at the forge.',
         'Передайте Годо в кузнице 4 куска стали, 1 кусок высокоуглеродистой стали, 200 единиц древесного угля и 2 лоскутка кожи.'),
        ('Return twelve hours after the delivery to collect the long blade. An order started before the Eclipse can still be completed afterward.',
         'Вернитесь через двенадцать часов после передачи и заберите длинный клинок. Начатый до Затмения заказ можно закончить и после него.'),
        ('The long sword order is settled. Godot can repair your existing blade.', 'Заказ длинного меча завершён. Годо может отремонтировать имеющийся клинок.')]
    early = t(*stages[3])
    for stage in range(2, -1, -1): early = cond(m(f'u_berserk_godo_early_state == {stage}'), t(*stages[stage]), early)
    bolts = cond(m('u_berserk_rickert_bolts_pending == 1'),
        cond(m("time('now') >= u_berserk_rickert_bolts_ready_at"),
             t('Ten bolts are ready. Collect them from Rickert at the forge.', 'Десять болтов готовы. Заберите их у Рикерта в кузнице.'),
             t('Rickert needs half an hour from delivery to finish the batch.', 'Рикерту нужны полчаса с момента передачи, чтобы закончить партию.')),
        t('Rickert can make ten bodkin bolts at the forge: 1 steel chunk, 1 stick, 20 thread, 10 feathers and 50 charcoal.',
          'Рикерт сделает десять болтов с острыми наконечниками в кузнице: 1 обломок стали, 1 палка, 20 единиц ниток, 10 перьев и 50 единиц древесного угля.'))
    for id, line in [('TALK_BERSERK_JOURNAL_EARLY', early), ('TALK_BERSERK_JOURNAL_BOLTS', bolts)]:
        row = {'type': 'talk_topic', 'id': id, 'dynamic_line': line,
               'responses': [r('Review forge orders.', 'Проверить заказы в кузнице.', 'TALK_BERSERK_JOURNAL_ORDERS'),
                             r('Return to the roads.', 'Вернуться к дорогам.', 'TALK_BERSERK_ROAD_JOURNAL')]}
        if id in T: T[id].clear(); T[id].update(row)
        else: rows.append(row)
    write('dialogue/road_journal.json', rows)
