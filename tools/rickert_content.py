"""Rickert's NPC, services and save migration, applied by build_godo_content.py."""
def apply_rickert(effects, topics, missions, t, save):
    def m(s): return {'math': [s]}
    def allof(*v): return {'and': list(v)}
    def neg(v): return {'not': v}
    def call(s): return {'test_eoc': s}
    def run(s): return {'run_eocs': s}
    def r(en, ru, target, condition=None, effect=None):
        row = {'text': t(en, ru), 'topic': target}
        if condition is not None: row['condition'] = condition
        if effect is not None: row['effect'] = effect
        return row
    def back(target='TALK_BERSERK_RICKERT'):
        if target == 'TALK_BERSERK_GODO_ARM':
            return r('Return to the arm cannon order.', 'Вернуться к заказу руки-пушки.', target)
        return r('Ask something else.', 'Спросить о другом.', target)
    def topic(id, text, responses, **extra):
        topics.append({'type': 'talk_topic', 'id': id, 'dynamic_line': text,
                       'responses': responses, **extra})
    def eoc(id, effect, condition=None, **extra):
        row = {'type': 'effect_on_condition', 'id': id, 'effect': effect, **extra}
        if condition is not None: row['condition'] = condition
        effects.append(row)
    E = {row['id']: row for row in effects}
    T = {row['id']: row for row in topics}
    identity = allof('has_beta', 'npc_is_npc', {'npc_has_class': 'NC_BERSERK_RICKERT'})
    forge = allof({'u_at_om_location': 'berserk_godo_workshop'},
                  {'npc_at_om_location': 'berserk_godo_workshop'})
    eoc('EOC_BERSERK_GODO_AT_RICKERT', [], identity)
    eoc('EOC_BERSERK_GODO_AT_RICKERT_FORGE', [], allof(identity, forge))

    # Keep the order variables and mission/EOC IDs: prepaid old orders transfer intact.
    mission_descriptions = {
        'MISSION_BERSERK_GODO': (
            'Visit the woodland forge. Godot forges and repairs blades; Rickert builds the arm cannon and can become a traveling companion.',
            'Посетите лесную кузницу. Годо куёт и ремонтирует клинки; Рикерт изготовляет руку-пушку и может стать спутником.'),
        'MISSION_BERSERK_GODO_ARM_METAL': (
            'Bring Rickert 8 lumps of steel and 2 pipes at the woodland forge. He accepts them together.',
            'Принесите Рикерту в лесную кузницу 8 кусков стали и 2 трубы. Они передаются вместе.'),
        'MISSION_BERSERK_GODO_ARM_FITTINGS': (
            'Bring Rickert 2 springs, 4 leather patches and 200 charcoal at the forge. Allow six hours after this delivery.',
            'Принесите Рикерту в кузницу 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля. После доставки нужны шесть часов.'),
        'MISSION_BERSERK_GODO_ARM_COLLECT': (
            'Meet Rickert at the woodland forge six hours after the last delivery. Activate the finished cannon in your inventory to install it yourself.',
            'Встретьтесь с Рикертом в лесной кузнице через шесть часов после последней поставки. Активируйте готовую пушку в инвентаре, чтобы установить её самостоятельно.')}
    for row in missions:
        if row['id'] in mission_descriptions:
            row['description'] = t(*mission_descriptions[row['id']])
    T['TALK_BERSERK_GODO']['responses'][0] = r(
        'Who can build a prosthetic for my hand?', 'Кто сделает протез для моей руки?',
        'TALK_BERSERK_GODO_RICKERT')
    T['TALK_BERSERK_GODO_ENTER']['dynamic_line'] = t(
        '*The old smith rests his hammer against the anvil and looks up from the metal.',
        '*Старый кузнец кладёт молот на наковальню и поднимает взгляд от заготовки.')
    topic('TALK_BERSERK_GODO_RICKERT', t(
        "Speak with Rickert. He builds the moving joints, grip and hidden cannon himself. I forge blades. If you already paid me for the prosthetic, your materials are still in the workshop; he will finish that same order.",
        'Поговори с Рикертом. Сочленения, хват и скрытую пушку он собирает сам. Моё дело — клинки. Если уже передал мне материалы для протеза, они остались в мастерской: он закончит тот же заказ.'), [back('TALK_BERSERK_GODO')])
    T['TALK_BERSERK_GODO_SELF']['dynamic_line'] = t(
        'Making the cannon yourself requires fabrication 8, mechanics 4 and proper tools. Rickert can build it from your materials if you have not learned that craft. You can install the finished mechanism yourself.',
        'Чтобы изготовить пушку самому, нужны производство 8, механика 4 и подходящие инструменты. Рикерт соберёт механизм из твоих материалов, если ты ещё не освоил это ремесло. Готовый протез можно установить самостоятельно.')
    T['TALK_BERSERK_GODO_SELF']['responses'] = [back('TALK_BERSERK_GODO')]
    arm = T['TALK_BERSERK_GODO_ARM']
    arm['dynamic_line']['no']['yes'] = t(
        'That order is settled. If the mechanism you received needs attention, show it to me.',
        'Этот заказ завершён. Если полученному механизму нужен ремонт, покажи его мне.')
    arm['dynamic_line']['no']['no']['no'] = t(
        "I build the arm cannon here, using Godot's forge for the heavy work. Bring 8 steel lumps and 2 pipes, then 2 springs, 4 leather patches and 200 charcoal. Give me six hours after the last delivery. If we travel together, return here with me to deliver the materials and collect it.",
        'Я собираю руку-пушку здесь, используя горн Годо для тяжёлых деталей. Нужны 8 кусков стали и 2 трубы, затем 2 пружины, 4 лоскутка кожи и 200 единиц древесного угля. После последней поставки дай мне шесть часов. Если пойдём вместе, для передачи материалов и получения протеза вернёмся сюда.')
    # Only Rickert may run arm services. Keep the old topic IDs for saved conversations.
    for row in arm['responses']:
        if row.get('effect'):
            row['condition'] = allof(call('EOC_BERSERK_GODO_AT_RICKERT_FORGE'), row['condition'])
        if row['topic'] == 'TALK_BERSERK_GODO_FITTING':
            row['topic'] = 'TALK_BERSERK_RICKERT_ARM'
    arm['responses'] = [row for row in arm['responses'] if row['topic'] != 'TALK_BERSERK_GODO_PRAISE']
    arm['responses'].append(back())
    arm['responses'] = [row for row in arm['responses'] if row['topic'] != 'TALK_BERSERK_GODO']
    arm['responses'].insert(0, r('I assembled this prosthetic myself.', 'Этот протез я собрал сам.',
        'TALK_BERSERK_RICKERT_PRAISE', call('EOC_BERSERK_GODO_HAS_ARM')))
    T['TALK_BERSERK_GODO_ARM_STATUS']['responses'] = [back('TALK_BERSERK_GODO_ARM'), back()]
    # Godot's repair selector handles blades. Rickert's selector handles a loose cannon.
    E['EOC_BERSERK_GODO_REPAIR_PICK']['effect']['search_data'][0]['id'].remove('bio_berserk_arm_cannon')
    T['TALK_BERSERK_GODO_REPAIR']['dynamic_line'] = t(
        'For a damaged blade, bring one steel lump and 50 charcoal. Show me the piece; I repair the blade you carry. For the cannon and its moving parts, speak to Rickert.',
        'Для повреждённого клинка нужны один кусок стали и 50 единиц древесного угля. Покажи оружие: я починю тот клинок, который ты принёс. С пушкой и подвижными деталями обратись к Рикерту.')
    eoc('EOC_BERSERK_RICKERT_REPAIR_PICK', {
        'u_run_inv_eocs': 'manual', 'title': t('Choose a cannon for Rickert to repair', 'Выберите пушку для ремонта у Рикерта'),
        'search_data': [{'id': ['bio_berserk_arm_cannon'], 'condition': m("n_hp('ALL') < n_hp_max('torso')")}],
        'true_eocs': ['EOC_BERSERK_RICKERT_REPAIR_ITEM']
    }, allof(identity, forge, {'u_has_items': {'item': 'steel_lump', 'count': 1}},
             {'u_has_items': {'item': 'charcoal', 'count': 50}}))
    eoc('EOC_BERSERK_RICKERT_REPAIR_ITEM', [
        {'u_consume_item': 'steel_lump', 'charges': 1}, {'u_consume_item': 'charcoal', 'charges': 50},
        m("n_hp('ALL') = n_hp_max('torso')"), {'turn_cost': '1 minute'},
        {'u_message': t('Rickert straightens the mechanism and checks its joints.', 'Рикерт выправляет механизм и проверяет сочленения.'), 'type': 'good', 'popup': False}
    ], allof({'u_has_items': {'item': 'steel_lump', 'count': 1}},
             {'u_has_items': {'item': 'charcoal', 'count': 50}}, m("n_hp('ALL') < n_hp_max('torso')")))
    T['TALK_BERSERK_RICKERT']['dynamic_line'] = t(
        'Godot makes the blades. I build mechanisms: the arm cannon, joints, fastenings, things that have to work when your life depends on them. What do you need?',
        'Годо делает клинки. Я собираю механизмы: руку-пушку, сочленения, крепления — то, что должно работать, когда от этого зависит жизнь. Чем помочь?')
    T['TALK_BERSERK_RICKERT']['responses'] = [
        r('Can you build an arm cannon?', 'Соберёшь руку-пушку?', 'TALK_BERSERK_GODO_ARM'),
        r('How do I install the finished cannon?', 'Как установить готовую пушку?', 'TALK_BERSERK_RICKERT_ARM'),
        r('What do you build, and how do you fight?', 'Что ты умеешь делать и как сражаешься?', 'TALK_BERSERK_RICKERT_CRAFT'),
        r('Can you repair the mechanism?', 'Починишь механизм?', 'TALK_BERSERK_RICKERT_CARE'),
        r('What is it like working with Godot?', 'Каково работать рядом с Годо?', 'TALK_BERSERK_RICKERT_GODO'),
        r('Could we travel together?', 'Пойдёшь со мной?', 'TALK_BERSERK_RICKERT_ROAD', neg('npc_following')),
        r('Let us discuss equipment and our travel arrangements.', 'Обсудим снаряжение и порядок в пути.', 'TALK_FRIEND', m('n_berserk_rickert_recruited == 1')),
        r('Where may I leave supplies and rest?', 'Где оставить припасы и отдохнуть?', 'TALK_BERSERK_RICKERT_HOME'),
        r('Thank you.', 'Спасибо.', 'TALK_DONE')]
    T['TALK_BERSERK_RICKERT_ARM']['dynamic_line'] = t(
        'Keep the finished cannon in your pack and activate it there. The mount on your missing left hand must be free. You can fasten it with your remaining hand. I will build the mechanism if you bring the materials to this forge.',
        'Держи готовую пушку в рюкзаке и активируй её оттуда. Крепление на месте потерянной левой кисти должно быть свободным. Закрепить её можно оставшейся рукой. Сам механизм я соберу, если принесёшь материалы в эту кузницу.')
    T['TALK_BERSERK_RICKERT_ARM']['responses'].insert(0, back('TALK_BERSERK_GODO_ARM'))
    T['TALK_BERSERK_RICKERT_CARE']['dynamic_line'] = t(
        'Keep grit out of the hinge and change straps before they split. Here at the forge I can repair a damaged cannon that has not been installed: one steel lump and 50 charcoal. I will not ask you to tear an installed hand off; those fittings need ordinary care, not another copy.',
        'Не допускай песка в шарнир и меняй ремни, прежде чем они лопнут. Здесь, в кузнице, я починю повреждённую пушку, которая ещё не установлена: нужны один кусок стали и 50 единиц древесного угля. Срывать уже установленную руку я не попрошу: её креплениям нужен обычный уход, а не второй экземпляр.')
    T['TALK_BERSERK_RICKERT_CARE']['responses'].insert(0, r(
        'Show you an uninstalled damaged cannon.', 'Показать повреждённую неустановленную пушку.',
        'TALK_BERSERK_RICKERT_CARE', call('EOC_BERSERK_GODO_AT_RICKERT_FORGE'),
        run('EOC_BERSERK_RICKERT_REPAIR_PICK')))
    topic('TALK_BERSERK_RICKERT_PRAISE', {'u_has_bionics': 'bio_berserk_hand_stump',
        'yes': t('You assembled this with one hand? Those joints are not easy to fit with two. That is good work. Let us keep it working instead of making another.',
                 'Ты собрал это одной рукой? Такие шарниры и двумя-то подогнать непросто. Хорошая работа. Давай поддерживать её в порядке, а не делать второй протез.'),
        'no': t('You built the mechanism yourself? Good work. The joints tell me more than a boast would. Show it to me if it ever starts catching.',
                'Ты сам собрал механизм? Хорошая работа. Шарниры говорят больше, чем хвастовство. Покажи мне, если начнёт заедать.')}, [back('TALK_BERSERK_GODO_ARM'), back()])
    topic('TALK_BERSERK_RICKERT_CRAFT', t(
        'A blade needs strength; a mechanism needs each small part to fit the next. Godot taught me to respect the metal. I work on hinges, locks and the cannon hidden in the prosthesis. In a fight I prefer a small crossbow and a clear shot. I am useful at your side, but I am not an apostle-killer with a magic sword.',
        'Для клинка нужна сила, для механизма — чтобы каждая мелкая деталь подходила к соседней. Годо научил меня уважать металл. Я работаю с шарнирами, замками и пушкой, скрытой в протезе. В бою предпочитаю небольшой арбалет и хороший обзор. Рядом со мной будет польза, но я не охотник на апостолов с волшебным мечом.'), [
            r('Can you build my prosthesis?', 'Сделаешь мой протез?', 'TALK_BERSERK_GODO_ARM'),
            r('Then let us talk about traveling together.', 'Тогда поговорим о совместном пути.', 'TALK_BERSERK_RICKERT_ROAD', neg('npc_following')), back()])
    topic('TALK_BERSERK_RICKERT_ROAD', {'math': ['n_berserk_rickert_recruited == 1'],
        'yes': t('Ready to move again? Check the bolts and leave us a way back. If the hand still needs forge work, we return here for it.',
                 'Снова пора в путь? Проверь болты и оставь нам дорогу назад. Если руке ещё нужна работа у горна, вернёмся за ней сюда.'),
        'no': t('I can travel, but I will not be someone sent ahead to die. Godot has his forge; I want the things we make to help people beyond this house. What do you expect from me?',
                'Я могу пойти, но не стану тем, кого посылают вперёд умирать. У Годо есть кузница; мне хочется, чтобы наша работа помогала людям за пределами этого дома. Чего ты ждёшь от меня?')}, [
        r('I need a craftsman and a companion. We choose the route and retreat together.',
          'Мне нужен мастер и товарищ. Путь и отступление будем выбирать вместе.', 'TALK_BERSERK_RICKERT_ROAD_PLAN',
          m('n_berserk_rickert_recruited != 1'), m('n_berserk_rickert_respect = 1')),
        r('I need another fighter. You can take the first blows.', 'Нужен ещё один боец. Первые удары примешь ты.',
          'TALK_BERSERK_RICKERT_REFUSE', m('n_berserk_rickert_recruited != 1'), m('n_berserk_rickert_respect = 0')),
        r('Let us set out again.', 'Снова отправимся вместе.', 'TALK_BERSERK_RICKERT',
          m('n_berserk_rickert_recruited == 1'), run('EOC_BERSERK_RICKERT_JOIN')),
        back()])
    topic('TALK_BERSERK_RICKERT_ROAD_PLAN', t(
        'Then give me room to shoot, and do not count on me holding a monster in place. We can return for forge work when we need it. Will you listen when I say a road is too dangerous?',
        'Тогда оставляй мне место для выстрела и не рассчитывай, что я удержу чудовище в ближнем бою. Когда понадобится горн, вернёмся. Ты послушаешь, если я скажу, что дорога слишком опасна?'), [
        r('We protect each other. You have a say in where we go.', 'Будем защищать друг друга. Ты тоже решаешь, куда идти.',
          'TALK_BERSERK_RICKERT_JOINED', effect=run('EOC_BERSERK_RICKERT_JOIN')),
        r('I give the orders. You follow them.', 'Я приказываю, ты выполняешь.',
          'TALK_BERSERK_RICKERT_REFUSE', effect=m('n_berserk_rickert_respect = 0')), back()])
    topic('TALK_BERSERK_RICKERT_REFUSE', t(
        'Then I stay here. You can still bring work to the forge, but traveling together takes more than another pair of hands.',
        'Тогда я останусь здесь. Работа в кузнице по-прежнему доступна, но для совместного пути мало ещё одной пары рук.'), [back()])
    topic('TALK_BERSERK_RICKERT_JOINED', t(
        'All right. I will bring the crossbow and my tools. Keep a way back; we still have a forge to return to.',
        'Хорошо. Возьму арбалет и инструменты. Оставим дорогу назад: нам ещё есть куда вернуться.'), [back(),
        r('Let us discuss our equipment.', 'Обсудим снаряжение.', 'TALK_FRIEND')])
    eoc('EOC_BERSERK_RICKERT_JOIN', [m('n_berserk_rickert_recruited = 1'), 'follow'],
        allof(identity, {'or': [m('n_berserk_rickert_respect == 1'), m('n_berserk_rickert_recruited == 1')]}))

    # Migrate a living old talking monster. Spawn confirmation precedes its removal.
    # Do not delete the current beta monster while its conversation is running.
    topic('TALK_BERSERK_RICKERT_LEGACY', t(
        '*Rickert puts his work aside and reaches for his tool bag. "Give me a moment. We can talk beside the bench."',
        '*Рикерт откладывает работу и берётся за сумку с инструментами. «Дай мне минутку. Поговорим у верстака».') , [
        r('I will wait.', 'Подожду.', 'TALK_DONE', effect=[run('EOC_BERSERK_GODO_REGISTER'),
          {'run_eocs': 'EOC_BERSERK_RICKERT_MIGRATE', 'time_in_future': '1 second'}])])
    eoc('EOC_BERSERK_RICKERT_MARK_PRESENT', m('berserk_rickert_npc_present = 1'),
        {'u_has_class': 'NC_BERSERK_RICKERT'})
    eoc('EOC_BERSERK_RICKERT_REMOVE_LEGACY', {
        'u_run_monster_eocs': [{'id': 'EOC_BERSERK_RICKERT_RETIRE_OLD_ACTOR',
            'effect': {'u_die': {'remove_from_creature_tracker': True}}}],
        'mtype_ids': ['mon_berserk_rickert'], 'monster_range': 32
    })
    eoc('EOC_BERSERK_RICKERT_MIGRATE', [
        m('berserk_rickert_npc_present = 0'),
        {'u_run_npc_eocs': ['EOC_BERSERK_RICKERT_MARK_PRESENT'], 'unique_ids': ['BERSERK_RICKERT'], 'local': False},
        {'if': m('berserk_rickert_npc_present == 1'), 'then': run('EOC_BERSERK_RICKERT_REMOVE_LEGACY'),
         'else': [
            {'copy_var': {'global_val': 'berserk_godo_location'}, 'target_var': {'context_val': 'rickert_spawn'}},
            m('_rickert_spawn.x = _rickert_spawn.x + 15'), m('_rickert_spawn.y = _rickert_spawn.y + 12'),
            {'u_spawn_npc': 'berserk_rickert', 'unique_id': 'BERSERK_RICKERT', 'real_count': 1,
             'target_var': {'context_val': 'rickert_spawn'}, 'min_radius': 1, 'max_radius': 3,
             'true_eocs': ['EOC_BERSERK_RICKERT_REMOVE_LEGACY']}
         ]}
    ], allof({'u_at_om_location': 'berserk_godo_workshop'}, call('EOC_BERSERK_GODO_KNOWN'),
             m('berserk_rickert_dead != 1'), m("u_monsters_nearby('mon_berserk_rickert', 'radius': 32, 'attitude': 'both') > 0")))
    eoc('EOC_BERSERK_RICKERT_MIGRATE_TICK', [run('EOC_BERSERK_GODO_REGISTER'), run('EOC_BERSERK_RICKERT_MIGRATE')],
        allof({'u_at_om_location': 'berserk_godo_workshop'}, m('berserk_rickert_dead != 1'),
              m("u_monsters_nearby('mon_berserk_rickert', 'radius': 32, 'attitude': 'both') > 0")),
        eoc_type='RECURRING', recurrence='30 seconds')
    eoc('EOC_BERSERK_RICKERT_DEATH', m('berserk_rickert_dead = 1'), eoc_type='NPC_DEATH')
    E['EOC_BERSERK_GODO_BEGIN']['effect'].insert(1, run('EOC_BERSERK_RICKERT_MIGRATE'))

    skills = {'ALL': 0, 'fabrication': 8, 'mechanics': 6, 'tailor': 4, 'gun': 4,
              'pistol': 5, 'melee': 2, 'dodge': 3, 'survival': 3, 'firstaid': 2, 'speech': 2}
    save('npcs/rickert.json', [
        {'type': 'npc_class', 'id': 'NC_BERSERK_RICKERT', 'name': {'str': t('young engineer and smith', 'молодой механик и кузнец')},
         'job_description': t('I build mechanisms and keep them working. Godot handles the great blades.', 'Я собираю механизмы и слежу, чтобы они работали. Большими клинками занимается Годо.'),
         'common': False, 'sells_belongings': False,
         'skills': [{'skill': key, 'level': {'constant': value}} for key, value in skills.items()],
         'proficiencies': ['prof_metalworking', 'prof_blacksmithing', 'prof_gunsmithing_antique', 'prof_carving', 'prof_bowyery'],
         'worn_override': 'BERSERK_RICKERT_WORN', 'carry_override': 'BERSERK_RICKERT_CARRY',
         'weapon_override': 'BERSERK_RICKERT_WEAPON'},
        {'type': 'npc', 'id': 'berserk_rickert', 'class': 'NC_BERSERK_RICKERT',
         'name_unique': t('Rickert', 'Рикерт'), 'gender': 'male', 'age': 19, 'height': 170,
         'str': 8, 'dex': 10, 'int': 11, 'per': 10,
         'attitude': 0, 'mission': 7, 'faction': 'no_faction',
         'personality': {'aggression': -2, 'bravery': 1, 'collector': 0, 'altruism': 5},
         'chat': 'TALK_BERSERK_RICKERT', 'talk_friend': 'TALK_BERSERK_RICKERT',
         'talk_friend_guard': 'TALK_BERSERK_RICKERT', 'death_eocs': ['EOC_BERSERK_RICKERT_DEATH']}
    ])
    save('itemgroups/rickert.json', [
        {'type': 'item_group', 'id': 'BERSERK_RICKERT_WORN', 'subtype': 'collection',
         'entries': [{'item': id} for id in ['tunic', 'vest_leather', 'pants_leather', 'gloves_leather', 'socks', 'mocassins', 'leather_belt', 'backpack_leather']]},
        {'type': 'item_group', 'id': 'BERSERK_RICKERT_CARRY', 'subtype': 'collection',
         'entries': [{'item': id} for id in ['hammer', 'metalworking_tongs', 'metal_file', 'hotcut', 'swage', 'needle_wood']]
                    + [{'item': 'thread', 'charges': 100}, {'item': 'bolt_wood_bodkin', 'charges': 20}]},
        {'type': 'item_group', 'id': 'BERSERK_RICKERT_WEAPON', 'subtype': 'collection',
         'entries': [{'item': 'hand_crossbow', 'ammo-item': 'bolt_wood_bodkin', 'charges': 1}]}
    ])
