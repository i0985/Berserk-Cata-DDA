"""Author the forge reunion, sparks conversation and rescue destination."""
import json
from pathlib import Path

MOD = Path(__file__).resolve().parents[1] / 'mods/Berserk'


def apply_forge_story(effects, topics, t):
    def m(s): return {'math': [s]}
    def allof(*v): return {'and': list(v)}
    def run(id): return {'run_eocs': id}
    def r(en, ru, topic, condition=None, effect=None):
        row = {'text': t(en, ru), 'topic': topic}
        if condition is not None: row['condition'] = condition
        if effect is not None: row['effect'] = effect
        return row
    def topic(id, en, ru, responses):
        topics.append({'type': 'talk_topic', 'id': id, 'dynamic_line': t(en, ru), 'responses': responses})
    def eoc(id, effect, condition=None):
        row = {'type': 'effect_on_condition', 'id': id, 'effect': effect}
        if condition is not None: row['condition'] = condition
        effects.append(row)
    def back(id): return r('Ask something else.', 'Спросить о другом.', id)
    T = {row['id']: row for row in topics}
    godo = 'TALK_BERSERK_GODO'
    rickert = 'TALK_BERSERK_RICKERT'
    after = m('u_berserk_eclipse_rescue_state == 2')
    open_sparks = m('u_berserk_godo_sparks_closed != 1')
    eoc('EOC_BERSERK_GODO_CLOSE_SPARKS', m('u_berserk_godo_sparks_closed = 1'),
        {'test_eoc': 'EOC_BERSERK_GODO_AT_SMITH'})
    for row in topics:
        for response in row['responses']:
            if response['topic'] == 'TALK_BERSERK_GODO_SPARKS':
                response['condition'] = allof(open_sparks, response['condition']) if 'condition' in response else open_sparks
    T['TALK_BERSERK_GODO_SPARKS']['dynamic_line'] = {
        'math': ['u_berserk_godo_sparks_closed == 1'],
        'yes': t('*Godot returns to the iron. He does not take up the abandoned conversation.',
                 '*Годо возвращается к заготовке. К прерванному разговору он больше не возвращается.'),
        'no': t('*Godot strikes the hot iron. Sparks flare against the dark rafters. "Look closely. What do you see in that darkness?"',
                '*Годо бьёт по раскалённому железу. Под тёмными стропилами вспыхивают искры. «Посмотри внимательно. Что ты видишь в этой темноте?»')}
    T['TALK_BERSERK_GODO_SPARKS']['responses'] = [
        r('The fire, and the sparks.', 'Огонь… И искры.', 'TALK_BERSERK_GODO_SPARKS_LIGHT', open_sparks),
        r('Nothing. I do not want to talk about it.', 'Ничего. Не хочу об этом говорить.', 'TALK_BERSERK_GODO_SPARKS_DISMISSED', open_sparks,
          run('EOC_BERSERK_GODO_CLOSE_SPARKS')),
        r('Let me come back to this when I can listen.', 'Вернусь к этому, когда смогу выслушать.', godo, open_sparks), back(godo)]
    topic('TALK_BERSERK_GODO_SPARKS_LIGHT',
        'The fire stays in the hearth. The sparks live only until they fall. A moment of brightness, then ash. You can spend a whole night watching them and still be cold when the forge goes out.',
        'Огонь остаётся в очаге. Искры живут лишь до тех пор, пока не упадут. Мгновение света — и зола. Можно всю ночь смотреть на них и всё равно замёрзнуть, когда горн погаснет.', [
        r('What are you getting at, old man?', 'К чему ты клонишь, старик?', 'TALK_BERSERK_GODO_SPARKS_RAGE', open_sparks),
        r('Forging gives you more than a moment of light.', 'Но ковка даёт тебе больше, чем мгновение света.', 'TALK_BERSERK_GODO_LIFE'), back(godo)])
    topic('TALK_BERSERK_GODO_SPARKS_RAGE',
        'You came out of that darkness and reached for a weapon. I understand that. But hatred can make every blow look like a reason to live. Those are sparks too: bright enough to hide your pain for a moment, too brief to warm anyone. If all you keep is the next enemy, what will be left when you put the blade down?',
        'Ты вышел из той тьмы и потянулся к оружию. Я понимаю. Но ненависть умеет превращать каждый удар в подобие смысла жизни. Это тоже искры: они на миг заслоняют боль, но никого не согревают. Если у тебя останется только следующий враг, что будет, когда ты опустишь клинок?', [
        r('I cannot let their deaths go unanswered.', 'Я не могу оставить их смерть без ответа.', 'TALK_BERSERK_GODO_SPARKS_HOME'),
        r('Then what am I supposed to live for?', 'Тогда ради чего мне жить?', 'TALK_BERSERK_GODO_SPARKS_HOME'), back(godo)])
    topics[-1]['dynamic_line'] = {'math': ['u_berserk_eclipse_rescue_state == 2'],
        'yes': topics[-1]['dynamic_line'],
        'no': t('You came here from a world full of graves. A weapon can keep you alive, but hatred can make every blow look like a reason to live. Those are sparks too: bright enough to hide pain for a moment, too brief to warm anyone. What will remain when you put the blade down?',
                'Ты пришёл сюда из мира, полного могил. Оружие помогает выжить, но ненависть умеет превращать каждый удар в подобие смысла жизни. Это тоже искры: на миг они заслоняют боль, но никого не согревают. Что останется, когда ты опустишь клинок?')}
    topic('TALK_BERSERK_GODO_SPARKS_HOME',
        'Do not forget the dead. But do not make the living wait forever while you chase them. A hearth needs someone to tend it. A companion needs you to return. Protecting those things is harder than finding another monster to strike. I can forge you a blade; I cannot choose what you will come home to.',
        'Не забывай погибших. Но и не заставляй живых бесконечно ждать, пока ты преследуешь мёртвых. Очагу нужен тот, кто его поддерживает. Товарищу нужно, чтобы ты вернулся. Защищать это труднее, чем искать очередное чудовище для удара. Я выкую тебе клинок, но не выберу за тебя, ради чего возвращаться домой.', [
        r('I need a blade that lets me return.', 'Мне нужен клинок, с которым я смогу вернуться.', 'TALK_BERSERK_GODO_SWORD'),
        r('Tell me about your own life at the forge.', 'Расскажи о своей жизни у горна.', 'TALK_BERSERK_GODO_LIFE'), back(godo)])
    topic('TALK_BERSERK_GODO_SPARKS_DISMISSED',
        '*Godot lowers his eyes to the iron. "Then let us speak of the work. I will not force you to listen." The hammer rises again.',
        '*Годо опускает взгляд на заготовку. «Тогда поговорим о работе. Заставлять тебя слушать я не стану». Молот снова поднимается.', [back(godo)])

    reunion = 'TALK_BERSERK_RICKERT_ECLIPSE'
    T[rickert]['responses'].insert(0, r('About the Eclipse and the Band of the Hawk.', 'О Затмении и отряде Сокола.', reunion, after))
    T[rickert]['dynamic_line'] = {'test_eoc': 'EOC_BERSERK_RICKERT_REUNION_UNTOLD',
        'yes': t('You are awake. The Skull Knight brought you here barely alive. We dressed what wounds we could. Judeau, Pippin, Corkus... none of them came back with you. Can you tell me what happened?',
                 'Ты очнулся. Рыцарь-Череп принёс тебя сюда едва живым. Мы перевязали раны, какие смогли. Джудо, Пиппин, Коркус… никто из них не вернулся с тобой. Ты можешь рассказать, что произошло?'),
        'no': T[rickert]['dynamic_line']}
    eoc('EOC_BERSERK_RICKERT_REUNION_UNTOLD', [], allof(after,
        m('u_berserk_godo_rescue_relocated == 1'), m('u_berserk_rickert_eclipse_story == 0')))
    T[rickert]['responses'].insert(1, r('I need a little time before speaking of them.', 'Мне нужно немного времени, прежде чем говорить о них.',
        rickert, {'test_eoc': 'EOC_BERSERK_RICKERT_REUNION_UNTOLD'}, m('u_berserk_rickert_eclipse_story = 3')))
    untold = allof(after, m('u_berserk_rickert_eclipse_story == 0'))
    truth_effect = m('u_berserk_rickert_eclipse_story = 1')
    Tline = {'math': ['u_berserk_rickert_eclipse_story == 0'],
        'yes': t('I was not there. I heard no orders and saw none of what you saw. Where is the Band? Where is Griffith? Please, do not leave me to guess.',
                 'Меня там не было. Я не слышал приказов и не видел того, что видел ты. Где отряд? Где Гриффит? Прошу, не оставляй меня с одними догадками.'),
        'no': {'math': ['u_berserk_rickert_eclipse_story == 1'],
            'yes': t('I still cannot fit the commander I knew to what you told me. But the wounds and the Brand are real. Tell me about the others, if you can.',
                     'Я всё ещё не могу связать командира, которого знал, с тем, что ты рассказал. Но раны и Клеймо настоящие. Расскажи об остальных, если можешь.'),
            'no': t('There are things you have not told me. I will not drag them out of you, but I remember the people who never came back.',
                    'Есть вещи, о которых ты мне не рассказал. Вытягивать их силой я не буду, но людей, которые не вернулись, я помню.')}}
    topics.append({'type': 'talk_topic', 'id': reunion, 'dynamic_line': Tline, 'responses': [
        r('They are gone, Rickert. Almost the whole Band died.', 'Их больше нет, Рикерт. Почти весь отряд погиб.', 'TALK_BERSERK_RICKERT_ECLIPSE_DEAD', untold),
        r('You are better off not knowing. The Band you knew is gone.', 'Тебе лучше не знать. Отряда, который ты помнил, больше нет.', 'TALK_BERSERK_RICKERT_ECLIPSE_ANGER', untold),
        r('Remain silent and turn away.', 'Промолчать и отвернуться.', 'TALK_BERSERK_RICKERT_ECLIPSE_SILENCE', untold, m('u_berserk_rickert_eclipse_story = 3')),
        r('I can tell you the truth now.', 'Теперь я могу рассказать правду.', 'TALK_BERSERK_RICKERT_ECLIPSE_TRUTH',
          allof(after, m('u_berserk_rickert_eclipse_story >= 2')), truth_effect),
        r('How many of your comrades died?', 'Сколько твоих товарищей погибло?', 'TALK_BERSERK_RICKERT_ECLIPSE_LOSSES', after),
        r('I brought something that belonged to them.', 'Я принёс вещи, которые им принадлежали.', 'TALK_BERSERK_RICKERT_ECLIPSE_MEMORIES', after), back(rickert)]})
    truth_choice = r('Griffith offered the Band to the apostles. I saw the sacrifice.',
        'Гриффит принёс отряд в жертву апостолам. Я видел это.', 'TALK_BERSERK_RICKERT_ECLIPSE_TRUTH', effect=truth_effect)
    topic('TALK_BERSERK_RICKERT_ECLIPSE_DEAD',
        '*Rickert grips the edge of the bench. "Dead? All those people... Was it an army? Who did this?"',
        '*Рикерт сжимает край верстака. «Погибли? Столько людей… Это была армия? Кто это сделал?»', [truth_choice,
        r('We were surrounded by mercenaries and beasts. Griffith was taken away.', 'Нас окружили наёмники и звери. Гриффита забрали.',
          'TALK_BERSERK_RICKERT_ECLIPSE_LIE', effect=m('u_berserk_rickert_eclipse_story = 2')),
        r('I cannot say any more right now.', 'Сейчас я не могу сказать больше.', 'TALK_BERSERK_RICKERT_ECLIPSE_SILENCE', effect=m('u_berserk_rickert_eclipse_story = 3'))])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_ANGER',
        'I was one of them too. Judeau helped me when I was little. Pippin carried things the rest of us could not lift. You cannot make them disappear with one sentence. Tell me who took them from us.',
        'Я тоже был одним из них. Джудо помогал мне, когда я был совсем мал. Пиппин нёс то, что остальные не могли поднять. Нельзя заставить их исчезнуть одной фразой. Скажи, кто отнял их у нас.', [truth_choice,
        r('I need time. I cannot speak of it yet.', 'Мне нужно время. Я пока не могу об этом говорить.', 'TALK_BERSERK_RICKERT_ECLIPSE_SILENCE', effect=m('u_berserk_rickert_eclipse_story = 3'))])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_TRUTH',
        '*Rickert shakes his head. "Griffith? No... I followed him. We all did. I cannot understand it." He looks at your injuries, then at the Brand. "But you came back like this. I cannot call those wounds a lie. Give me time."',
        '*Рикерт качает головой. «Гриффит? Нет… Я шёл за ним. Мы все шли. Я не могу этого понять». Он смотрит на твои раны, затем на Клеймо. «Но ты вернулся вот таким. Эти раны я не могу назвать ложью. Дай мне время».', [
        r('What can we do for the people who remain?', 'Что мы можем сделать для тех, кто остался?', 'TALK_BERSERK_RICKERT_ECLIPSE_LIVING'),
        r('Can Godot make a weapon strong enough for them?', 'Годо сможет сделать оружие против них?', 'TALK_BERSERK_RICKERT_GODO'),
        r('Let us remember the others.', 'Давай вспомним остальных.', 'TALK_BERSERK_RICKERT_ECLIPSE_LOSSES'), back(rickert)])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_LIE',
        'Then Griffith could still be alive? We should look for him... No, you do not even want to say his name. I do not understand what you are keeping from me. I will work for a while. At least I know what to do with a piece of iron.',
        'Значит, Гриффит ещё может быть жив? Нам надо искать его… Нет, ты даже его имени произносить не хочешь. Я не понимаю, что ты от меня скрываешь. Пока поработаю. Хотя бы с куском железа я знаю, что делать.', [
        r('I cannot keep hiding it. I will tell you what happened.', 'Я не могу дальше скрывать. Расскажу, что произошло.', 'TALK_BERSERK_RICKERT_ECLIPSE_TRUTH', effect=truth_effect), back(rickert)])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_SILENCE',
        '*Rickert looks down. "I have seen men come back from battle unable to speak. I will not force you. But do not forget that they were my friends too. When you can, tell me."',
        '*Рикерт опускает глаза. «Я видел людей, которые возвращались из боя и не могли говорить. Заставлять тебя я не буду. Но не забывай: они были и моими друзьями. Когда сможешь, расскажи».', [
        r('I need a weapon before I can face any of this.', 'Мне нужно оружие, прежде чем я смогу со всем этим справиться.', 'TALK_BERSERK_RICKERT_ECLIPSE_LIVING'), back(rickert)])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_LIVING',
        'I can help replace your hand. Godot can make a blade. But neither of those things replaces a friend. Speak to him about the weapon, and come to me when you are ready to work on the mechanism. We still have people to help.',
        'Я помогу заменить кисть. Годо сделает клинок. Но ни то ни другое не заменит друга. Поговори с ним об оружии, а ко мне приходи, когда будешь готов заняться механизмом. Нам ещё есть кому помогать.', [
        r('Let us discuss the prosthetic.', 'Поговорим о протезе.', 'TALK_BERSERK_GODO_ARM'), back(rickert)])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_LOSSES',
        'I cannot give you an honest number. I was outside the sacrifice; there was no roll call afterwards. Almost the whole Band was lost. Judeau, Pippin, Corkus and Gaston did not return. To me they are names, not a tally. You survived, and I was never taken into that place. I will not declare every other missing person dead without knowing.',
        'Честного числа я тебе не назову. Я был вне жертвоприношения; после него никто не делал перекличку. Погиб почти весь отряд. Джудо, Пиппин, Коркус и Гастон не вернулись. Для меня это имена, а не счёт. Ты выжил, а меня туда не забирали. Объявлять погибшим каждого пропавшего, о котором ничего не известно, я не стану.', [
        r('I brought something that belonged to them.', 'Я принёс вещи, которые им принадлежали.', 'TALK_BERSERK_RICKERT_ECLIPSE_MEMORIES'), back(reunion)])
    memories = []
    for key, item, en, ru, reply, reply_ru in [
        ('JUDEAU', 'berserk_judeau_knife_hilt', "Judeau's knife hilt.", 'Рукоять ножа Джудо.',
         'He always had something ready when another person needed it. Even a small knife. I wish I could have been there to help him for once.',
         'У него всегда находилось что-то нужное другому. Даже маленький нож. Хотел бы я хоть раз оказаться рядом и помочь ему самому.'),
        ('PIPPIN', 'berserk_pippin_broken_clasp', "Pippin's broken clasp.", 'Сломанная застёжка Пиппина.',
         'He spoke so little that people forgot how much he did for them. I remember his hands, and how carefully he used all that strength.',
         'Он говорил так мало, что люди забывали, сколько он для них делал. Я помню его руки и то, как осторожно он пользовался своей силой.'),
        ('CORKUS', 'berserk_corkus_scabbard_fragment', "A piece of Corkus's scabbard.", 'Обломок ножен Коркуса.',
         'He could complain for an entire march. Sometimes that made the road easier. He wanted a life beyond marching and fighting. I want to remember that too.',
         'Он мог ворчать весь переход. Иногда от этого дорога становилась легче. Он хотел жить, а не только идти и сражаться. Это я тоже хочу помнить.'),
        ('GASTON', 'berserk_gaston_sewing_roll', "Gaston's sewing roll.", 'Свёрток швейных принадлежностей Гастона.',
         'Tools for work after the war. He kept them while carrying a sword. Do not throw them away; someone can still use them for the life he wanted.',
         'Инструменты для работы после войны. Он хранил их, пока носил меч. Не выбрасывай: кто-то ещё сможет пустить их в дело ради жизни, которой он хотел.')]:
        id = 'TALK_BERSERK_RICKERT_REMEMBER_' + key
        memories.append(r(en, ru, id, {'u_has_items': {'item': item, 'count': 1}}))
        topic(id, reply, reply_ru, [r('Remember another comrade.', 'Вспомнить другого товарища.', 'TALK_BERSERK_RICKERT_ECLIPSE_MEMORIES'), back(rickert)])
    topic('TALK_BERSERK_RICKERT_ECLIPSE_MEMORIES',
        'If you brought something of theirs, you may show me. You do not have to give it up. Remembering them is not a price for my help.',
        'Если ты принёс что-то из их вещей, можешь показать. Отдавать не обязательно. Память о них — не плата за мою помощь.', memories + [back(reunion)])

    # Find the unique special, validate its ground OMT, then use an empty ground-floor anchor.
    eoc('EOC_BERSERK_GODO_RESCUE_FOUND', [
        {'copy_var': {'context_val': 'godo_rescue_candidate'}, 'target_var': {'global_val': 'berserk_godo_location'}},
        m('berserk_godo_location.x = floor(berserk_godo_location.x / 24) * 24'),
        m('berserk_godo_location.y = floor(berserk_godo_location.y / 24) * 24'),
        run('EOC_BERSERK_GODO_RESCUE_TELEPORT')],
        {'overmap_at_point': 'berserk_godo_workshop', 'point': {'context_val': 'godo_rescue_candidate'}})
    eoc('EOC_BERSERK_GODO_RESCUE_TELEPORT', [
        {'copy_var': {'global_val': 'berserk_godo_location'}, 'target_var': {'u_val': 'berserk_godo_rescue_point'}},
        m('u_berserk_godo_rescue_point.x = u_berserk_godo_rescue_point.x + 9'),
        m('u_berserk_godo_rescue_point.y = u_berserk_godo_rescue_point.y + 14'),
        {'u_teleport': {'u_val': 'berserk_godo_rescue_point'}, 'force_safe': True},
        {'if': {'u_at_om_location': 'berserk_godo_workshop'}, 'then': [
            m('u_berserk_godo_rescue_relocated = 1'),
            {'reveal_map': {'global_val': 'berserk_godo_location'}, 'radius': 1}]}],
        {'test_eoc': 'EOC_BERSERK_GODO_KNOWN'})
    eoc('EOC_BERSERK_GODO_RESCUE_TRANSFER', [
        m('u_berserk_godo_rescue_attempted = 1'),
        run('EOC_BERSERK_GODO_LOCATE'),
        {'if': {'test_eoc': 'EOC_BERSERK_GODO_KNOWN'}, 'then': run('EOC_BERSERK_GODO_RESCUE_TELEPORT')}],
        allof(m('u_berserk_eclipse_rescue_state == 1'), m('u_berserk_godo_rescue_attempted != 1')))


def apply_story_world(t, save):
    def read(path): return json.loads((MOD / path).read_text())
    def m(s): return {'math': [s]}
    def run(id): return {'run_eocs': id}
    def r(en, ru, topic, effect=None):
        row = {'text': t(en, ru), 'topic': topic}
        if effect is not None: row['effect'] = effect
        return row
    rescue = read('effects/eclipse_rescue_eocs.json')
    returned = next(row for row in rescue if row['id'] == 'EOC_BERSERK_ECLIPSE_RESCUE_RETURN')
    if run('EOC_BERSERK_GODO_RESCUE_TRANSFER') not in returned['effect']:
        returned['effect'].insert(1, run('EOC_BERSERK_GODO_RESCUE_TRANSFER'))
    save('effects/eclipse_rescue_eocs.json', rescue)

    aftermath = read('effects/eclipse_aftermath_eocs.json')
    A = {row['id']: row for row in aftermath}
    steps = A['EOC_BERSERK_ECLIPSE_AFTERMATH']['effect']
    for i, part in enumerate(steps):
        fallback_guard = m('u_berserk_godo_rescue_relocated != 1')
        popup = part.get('then', {}) if part.get('if') == fallback_guard else part
        if isinstance(popup, dict) and 'u_message' in popup and popup.get('popup'):
            popup['u_message'] = t(
                'The Skull Knight carried you out of the Eclipse. The wounds have been tended, but your left hand and an eye are lost, and the Brand remains. Rickert can build a prosthesis; you can also make and fit it yourself. Speak with the Knight before he leaves.',
                'Рыцарь-Череп вынес тебя из Затмения. Раны перевязаны, но левая кисть и глаз потеряны, а Клеймо осталось. Рикерт поможет с протезом; его также можно изготовить и установить самостоятельно. Поговори с Рыцарем, прежде чем он уйдёт.')
            steps[i] = {'if': fallback_guard, 'then': popup}
        if part.get('u_spawn_monster') == 'mon_skull_knight_rescuer':
            steps[i] = run('EOC_BERSERK_ECLIPSE_PLACE_KNIGHT')
    A['EOC_BERSERK_ECLIPSE_KNIGHT_ARRIVED']['effect'] = [
        {'u_add_var': 'berserk_knight_waiting', 'value': 'placed'},
        run('EOC_BERSERK_KNIGHT_FORGE_NOTICE')]
    A['EOC_BERSERK_ECLIPSE_KNIGHT_RETRY']['effect'] = run('EOC_BERSERK_ECLIPSE_PLACE_KNIGHT')
    restore = A['EOC_BERSERK_RESTORE_DISMISSED_KNIGHT']
    guard = m('u_berserk_knight_farewell_confirmed != 1')
    if guard not in restore['condition']['and']: restore['condition']['and'].append(guard)
    # Fixed anchor survives loading; fallback exits retain a nearby interlocutor.
    extra = [
        {'type': 'effect_on_condition', 'id': 'EOC_BERSERK_KNIGHT_FORGE_NOTICE',
         'condition': {'and': [m('u_berserk_eclipse_rescue_state == 2'),
             m('u_berserk_godo_rescue_relocated == 1'), m('u_berserk_knight_forge_notice_shown != 1'),
             m('u_berserk_knight_farewell_confirmed != 1'),
             {'or': [{'u_at_om_location': 'berserk_godo_workshop'}, {'u_at_om_location': 'berserk_godo_loft'}]}]},
         'effect': [m('u_berserk_knight_forge_notice_shown = 1'),
             {'u_message': t(
                 "You awaken in Godot's forge. Your wounds have been dressed, but the lost hand and eye are gone, and the Brand remains. The Skull Knight waits outside the western door. He wishes to speak with you before continuing his journey.",
                 'Ты очнулся в кузнице Годо. Раны перевязаны, но потерянные кисть и глаз уже не вернуть, а Клеймо осталось. Рыцарь-Череп ждёт за западной дверью. Он хочет сказать тебе несколько слов, прежде чем продолжит свой путь.'),
              'type': 'warning', 'popup': True}]},
        {'type': 'effect_on_condition', 'id': 'EOC_BERSERK_ECLIPSE_PLACE_KNIGHT',
         'condition': {'and': [m('u_berserk_knight_farewell_confirmed != 1'),
              {'compare_string': ['yes', {'u_val': 'berserk_knight_waiting'}]}]},
         'effect': {'if': m("u_monsters_nearby('mon_skull_knight_rescuer', 'radius': 60, 'attitude': 'both') > 0"),
            'then': run('EOC_BERSERK_ECLIPSE_KNIGHT_ARRIVED'),
            'else': {'if': {'and': [m('u_berserk_godo_rescue_relocated == 1'), {'test_eoc': 'EOC_BERSERK_GODO_KNOWN'}]},
                'then': {'if': {'or': [{'u_at_om_location': 'berserk_godo_workshop'}, {'u_at_om_location': 'berserk_godo_loft'}]},
                    'then': [
                        {'copy_var': {'global_val': 'berserk_godo_location'}, 'target_var': {'u_val': 'berserk_knight_forge_point'}},
                        m('u_berserk_knight_forge_point.x = u_berserk_knight_forge_point.x + 2'),
                        m('u_berserk_knight_forge_point.y = u_berserk_knight_forge_point.y + 15'),
                        {'u_spawn_monster': 'mon_skull_knight_rescuer', 'real_count': 1,
                         'target_var': {'u_val': 'berserk_knight_forge_point'}, 'min_radius': 0, 'max_radius': 1,
                         'true_eocs': ['EOC_BERSERK_ECLIPSE_KNIGHT_ARRIVED']}]},
                'else': {'u_spawn_monster': 'mon_skull_knight_rescuer', 'real_count': 1, 'min_radius': 1, 'max_radius': 5,
                         'true_eocs': ['EOC_BERSERK_ECLIPSE_KNIGHT_ARRIVED']}}}},
        {'type': 'effect_on_condition', 'id': 'EOC_BERSERK_KNIGHT_FAREWELL',
         'condition': {'and': ['has_beta', 'npc_is_monster', m('u_berserk_eclipse_rescue_state == 2'),
              m("n_monsters_nearby('mon_skull_knight_rescuer', 'radius': 0, 'attitude': 'both') > 0")]},
         'effect': [m('u_berserk_knight_farewell_confirmed = 1'), m('u_berserk_knight_return_fix = 1'),
             {'u_add_var': 'berserk_knight_farewell', 'value': 'yes'},
             {'u_add_var': 'berserk_knight_waiting', 'value': 'gone'},
             run('EOC_BERSERK_CAMPAIGN_GIVE_JOURNAL'),
             {'run_eocs': 'EOC_BERSERK_KNIGHT_DEPART', 'time_in_future': '1 second'}]},
        {'type': 'effect_on_condition', 'id': 'EOC_BERSERK_KNIGHT_DEPART',
         'condition': m('u_berserk_knight_farewell_confirmed == 1'),
         'effect': {'u_run_monster_eocs': [{'id': 'EOC_BERSERK_KNIGHT_REMOVE_DEPARTED',
                    'effect': {'u_die': {'remove_from_creature_tracker': True}}}],
                    'mtype_ids': ['mon_skull_knight_rescuer'], 'monster_range': 60}}
    ]
    place = next(row for row in extra if row['id'] == 'EOC_BERSERK_ECLIPSE_PLACE_KNIGHT')
    decision = place['effect']
    decision['if'] = m('berserk_knight_local_present == 1')
    place['effect'] = [
        m('berserk_knight_local_present = 0'),
        m("berserk_knight_probe_z = u_val('pos_z')"),
        {'if': {'and': [m('u_berserk_godo_rescue_relocated == 1'), {'test_eoc': 'EOC_BERSERK_GODO_KNOWN'}]},
         'then': m('berserk_knight_probe_z = 0')},
        {'u_run_monster_eocs': [{'id': 'EOC_BERSERK_KNIGHT_MARK_LOCAL',
                               'effect': m('berserk_knight_local_present = 1')}],
         'mtype_ids': ['mon_skull_knight_rescuer'], 'monster_range': 60,
         'z_min': {'global_val': 'berserk_knight_probe_z'}, 'z_max': {'global_val': 'berserk_knight_probe_z'}},
        decision]
    ids = {row['id'] for row in extra}
    save('effects/eclipse_aftermath_eocs.json', [row for row in aftermath if row['id'] not in ids] + extra)

    knight = read('dialogue/skull_knight.json')
    K = {row['id']: row for row in knight}
    root = 'TALK_BERSERK_SKULL_KNIGHT_AFTER'
    K[root]['responses'][-1] = r('I need to go.', 'Мне пора.', 'TALK_BERSERK_SKULL_KNIGHT_FAREWELL')
    K[root]['dynamic_line'] = {'math': ['u_berserk_godo_rescue_relocated == 1'],
        'yes': t('You are under the smith\'s roof now. The life you brought out of the sacrifice is still yours. Ask what you need to know before I ride on.',
                 'Теперь ты под крышей кузнеца. Жизнь, которую удалось вынести из жертвоприношения, всё ещё твоя. Спроси о том, что нужно знать, прежде чем я продолжу путь.'),
        'no': "'You escaped, but the Eclipse has marked you. Your hand is gone. What comes next is yours to decide.'"}
    K['TALK_BERSERK_SKULL_KNIGHT_GODO']['dynamic_line'] = {'u_at_om_location': 'berserk_godo_workshop',
        'yes': t('I brought you to Godot\'s forge. The old master works on blades; Rickert builds mechanisms. Speak with them inside. Neither can remove the Brand, but they can help you face what follows.',
                 'Я принёс тебя в кузницу Годо. Старый мастер занимается клинками, Рикерт — механизмами. Поговори с ними внутри. Клеймо они не снимут, но помогут встретить то, что последует.'),
        'no': K['TALK_BERSERK_SKULL_KNIGHT_GODO']['dynamic_line']}
    first_now = K['TALK_BERSERK_SKULL_KNIGHT_NOW']['dynamic_line']
    first_now['yes'] = {'u_at_om_location': 'berserk_godo_workshop',
        'yes': t('Tend your wounds here. Ask Rickert about replacing the hand, and Godot about a blade. The marked hollow can wait until you have armor, dressings and a way to retreat.',
                 'Позаботься о ранах здесь. Спроси Рикерта о замене кисти, а Годо — о клинке. Отмеченная низина подождёт, пока не будут готовы броня, перевязка и путь отхода.'),
        'no': first_now['yes']}
    farewell = {'type': 'talk_topic', 'id': 'TALK_BERSERK_SKULL_KNIGHT_FAREWELL',
        'dynamic_line': t('I ride on when we part. My own road does not wait. If you still have questions, ask them now. The directions you have learned will remain in your notes.',
                          'Когда мы простимся, я продолжу путь. Мои дела не ждут. Если остались вопросы, задай их сейчас. Известные тебе направления останутся в записях.'),
        'responses': [r('I still have questions.', 'У меня ещё есть вопросы.', root),
                      r('I understand. Farewell, Skull Knight.', 'Я понял. Прощай, Рыцарь-Череп.', 'TALK_DONE', run('EOC_BERSERK_KNIGHT_FAREWELL'))]}
    save('dialogue/skull_knight.json', [row for row in knight if row['id'] != farewell['id']] + [farewell])
