# Спрайты локаций New Horizon

Актуальный указатель для сборки 3.0.0-dev от 4 октября:
[задание на спрайты](NEW_HORIZON_SPRITE_TASKS.md) и
[реестр фактических ID](assets/new-horizon-art-registry.csv).
Ниже сохранены тематические заметки предыдущих этапов. Их утверждения об
отсутствии авторских PNG относятся к соответствующей итерации, а не ко всему моду.

## Дополнение 4.8–4.9: пристанище и резиденция Графа

Стены, печь, кровати, полки и мебель пока ванильные. Для авторских изображений:

| ID | Образ / состояния |
| --- | --- |
| `f_berserk_shelter_ward` | Кольцо костей и камней с защитными насечками; не горящий костёр |
| `f_berserk_count_notice` | Объявления о казнях на каменном дворе |
| `f_berserk_count_family_door` | Табличка комнаты Терезии / спокойная семейная деталь |
| `f_berserk_location_count_property`, `_empty` | Изъятое имущество узников / обысканный сундук |
| `f_berserk_location_count_clerk`, `_empty` | Сундук бумаг писаря / пустой |
| `f_berserk_location_count_pantry`, `_empty` | Кладовая еды в кухне / обысканная |
| `f_berserk_location_count_armory`, `_empty` | Старое оружие, броня и ремонтное снаряжение / пустой запас |
| `f_berserk_location_count_physician`, `_empty` | Полотно и травяное масло в бурдюке / обысканный сундук |
| `f_berserk_location_count_family`, `_empty` | Нетронутая шкатулка для шитья / осмотренная |
| `f_berserk_count_service_grate`, `f_berserk_count_service_grate_open` | Закрытая решётка / отведённая, проход читается свободным |
| `berserk_refuge_journal` | Небольшой бумажный журнал подготовки |
| `berserk_count_prison_list`, `berserk_count_physician_ledger`, `berserk_count_next_trace` | Список, записи лекаря, пометки маршрутов; необязательные отдельные значки |
| `berserk_count_family_ribbon`, `berserk_count_service_key` | Сложенная тканевая лента и простой железный ключ |

Полные имена `_empty` продолжают соответствующий ID строки. Пример:
`f_berserk_location_count_physician_empty`. Сначала важнее различить полные
и обысканные запасы, а также открытую и закрытую решётку. PNG/смещения старых
тайлсетов в этой итерации не изменены.


## Дополнение 4.6–4.7: низина и Пепельный прорыв

Пока новые ID используют штатные изображения. Основной размер клетки такой же,
как у прочих поверхностей UltiCa; рисунок должен совпадать с её сеткой. Для
начала нужны эти собственные изображения и явно различимые состояния:

| ID | Рисунок / состояния |
| --- | --- |
| `t_berserk_hunt_hollow` | Вытоптанная земля со следами волочения, без современного покрытия |
| `f_berserk_hunt_warning` | Камень с короткими глубокими царапинами |
| `f_berserk_hunt_victims` | Разные вещи путников, без алтаря |
| `f_berserk_location_hunt_shelter`, `_empty` | Узелок у корней; разорённая обёртка |
| `f_berserk_location_hunt_reward`, `_empty` | Собранные вещи жертв; остатки после обыска |
| `f_berserk_hunt_obscured_trail`, `f_berserk_hunt_revealed_trail` | Затоптанный пепел; различимый маршрут |
| `t_berserk_breach_ash` | Пепельная обочина старого поста |
| `t_berserk_breach_wound`, `t_berserk_breach_scar` | Открытая влажная трещина; остывший каменный шов |
| `f_berserk_breach_failed_line` | Сломанные колья и оборванные тканевые обереги |
| `f_berserk_location_breach_defenders`, `_empty` | Запас защитников в сундуке; обысканный сундук |
| `f_berserk_breach_fallen_beam` | Балка поперёк прохода |
| `f_berserk_breach_beam_end`, `f_berserk_breach_beam_moved` | Свободный конец балки; отодвинутый край |

Полные ID состояний `_empty` начинаются с того же имени строки, например
`f_berserk_location_hunt_shelter_empty`. Обломки и стены пока ванильные.
Для трещины полезны вариации соединений; первая версия может быть отдельными
читаемыми клетками. Новые PNG и настройки смещения здесь не добавлены.


Пока используются ванильные `looks_like`. Собственных рисунков в этой сборке
нет: их можно заменить твоими PNG, сохранив указанные ID.

Для мебели начни с **32×32 пикселей на одну клетку**, прозрачный фон,
масштаб под установленную UltiCa. Это отдельные спрайты мебели на земле,
а не оверлеи одежды: смещения шлема, перчаток и руки-пушки здесь не нужны.
Если рисунок должен занимать несколько клеток, сначала согласуем форму и
разобьём композицию на клетки. Не сжимай большой рисунок целиком до 32×32.
Названия файлов лучше латиницей; окончательные `fg` и листы привяжем после
получения рисунков. Размеры ниже — рекомендуемая первая сетка для мебели,
а не ограничение движка на крупные существа.

## В первую очередь — коконы

| ID | Что рисовать | Рекомендуемый файл |
|---|---|---|
| `f_berserk_rosine_cocoon_sealed` | Целый непрозрачный кокон | `rosine_cocoon_sealed.png` |
| `f_berserk_rosine_cocoon_inhabited` | Целый, но с выпирающим силуэтом/разрывами, заметно отличающийся от спящего | `rosine_cocoon_inhabited.png` |
| `f_berserk_rosine_cocoon` | Вскрытая пустая оболочка; старый ID сохранён | `rosine_cocoon_empty.png` |
| `f_berserk_rosine_cocoon_destroyed` | Раздавленный кокон и лоскуты шёлка | `rosine_cocoon_destroyed.png` |

Одинаковая точка опоры и силуэт масштаба у всех четырёх вариантов. По рисунку
должно быть понятно, что это разные состояния одного предмета.

## Новые сюжетные декорации

| ID | Рисунок |
|---|---|
| `f_berserk_expedition_scene` | Стол экспедиции: приборы, раскрытый журнал, меловая схема |
| `f_berserk_chapel_scene` | Осквернённый памятник с выскобленными именами |
| `f_berserk_first_hunt_scene` | Останки и следы волочения |
| `f_berserk_breach_scene` | Расколотый камень/фрагмент фундамента рядом с разломом |
| `f_berserk_wyald_scene` | Стойка с щитами, кандалами и трофеями Чёрных Псов |
| `f_berserk_rosine_scene` | Маленькие туфли, игрушки и цветы у коконов |
| `f_berserk_flora_scene` | Рабочий дневник, травы и заготовки защитных чар |
| `f_berserk_grunbeld_scene` | Обгоревшее знамя и расплавленные крепления |

Эти декорации можно осмотреть: они открывают короткий текст о месте. Они не
являются обязательными ключами прохождения и не выдают второй артефакт.

## Уже существующие устройства отвлечения

Для каждого нужны обычный и заведённый варианты. Пока устройство заведено,
оно остаётся в той же клетке; второй рисунок может показывать натянутый трос
или движение механизма.

| Основной ID | Заведённый ID | Вид |
|---|---|---|
| `f_berserk_oak_noisemaker` | `f_berserk_oak_noisemaker_armed` | Костяные подвески у дерева |
| `f_berserk_cave_noisemaker` | `f_berserk_cave_noisemaker_armed` | Каменный шумовой механизм |
| `f_berserk_chapel_noisemaker` | `f_berserk_chapel_noisemaker_armed` | Колокол с тросом |
| `f_berserk_expedition_noisemaker` | `f_berserk_expedition_noisemaker_armed` | Сигнальное устройство экспедиции |

Полноценный рисунок отдельной колокольни можно позже собрать из нескольких
клеток. Сам активируемый механизм сейчас занимает одну клетку.

## Можно оставить ванильными

Палатки, спальники, ящики, столы, стулья, кровати, книжные шкафы, обычные цветы,
сетки клеток и обломки уже имеют игровые определения. Их не нужно рисовать
заново ради этой итерации. Приоритет: четыре кокона, устройства, затем восемь
сюжетных декораций. Полы/крупные декорации Затмения — отдельная работа.

## Дополнение 4.10–4.11: лагерь и ложный рай

Пока все новые рисунки — ванильные `looks_like`, без изменений PNG брони и
смещений. Для мебели первая сетка **32 × 32 на клетку**, прозрачный фон и
единая точка опоры в UltiCa. Не сжимай всё дерево или весь обоз в один тайл:
для крупных композиций сначала нужны стыкующиеся фрагменты на несколько клеток.

| ID | Рисунок и важные состояния |
| --- | --- |
| `t_berserk_campaign_mat` | Солома и грубая ткань; сплошной пол палатки, видимый также под предметами |
| `t_berserk_campaign_palisade` | Высокие грубые брёвна, закрывающие обзор; варианты соединений |
| `f_berserk_wyald_wagon_wreck` | Ось, колесо и порванный тент телеги; фрагменты для композиции |
| `f_berserk_wyald_wagon_chime`, `_armed`, `_spent` | Колокольчики, заведённый шнур, оборванный шнур; три различимых состояния |
| `f_berserk_wyald_cage_gate`, `_open` | Деревянная дверца с перевязью; открытая дверца без препятствия |
| `f_berserk_wyald_charge_obstacle` | Тяжёлая разбитая баррикада; сейчас три пары клеток, по две на преграду |
| `f_berserk_wyald_punishment_post` | Грубый столб с разрезанными путами, без подробного изображения насилия |
| `f_berserk_campaign_bedding` | Соломенная постель и старое одеяло |
| `f_berserk_wyald_prisoner_trace` | Разрезанный шнур и выцарапанный след в клетке |
| `f_berserk_wyald_ring_warning` | Глубокие следы на подступе к арене |
| `f_berserk_location_wyald_baggage`, `_empty` | Сундук обоза; вскрытый пустой сундук |
| `f_berserk_location_wyald_kitchen`, `_empty` | Запасы кухни; пустая упаковка |
| `f_berserk_location_wyald_repair`, `_empty` | Повреждённое оружие и ремонтные вещи; обысканный сундук |
| `f_berserk_location_wyald_command`, `_empty` | Сундук приказов и доспеха; пустой сундук |
| `f_berserk_location_wyald_prisoners`, `_empty` | Связанные чужие вещи; остатки после обыска |
| `t_berserk_mistvale_petals` | Почва с лепестками, несколько будущих вариаций без ровной садовой дорожки |
| `t_berserk_mistvale_gully` | Неглубокий овраг, края и влажная почва; не бесконечная пропасть |
| `t_berserk_rosine_giant_trunk` | Клетки огромного ствола; несколько стыкующихся частей, единый силуэт |
| `t_berserk_rosine_root_screen` | Толстые корни и зажатые камни; высокий непрозрачный силуэт |
| `f_berserk_rosine_cocoon_watchful` | Набухающий кокон с видимым силуэтом; отличается от тихого целого |
| `f_berserk_rosine_cocoon_waking` | Расходящийся шёлк, заметная угроза перед выходом существа |
| `f_berserk_rosine_cocoon`, `_destroyed` | Прежняя пустая оболочка и раздавленная; общая точка опоры с новыми состояниями |
| `f_berserk_rosine_shell_material`, `_empty` | Сухая покинутая оболочка с пригодной тканью; обобранные хрупкие нити |
| `f_berserk_rosine_story_cocoon` | Расколотая оболочка с привязанной меткой; отдельный сюжетный осмотр |
| `f_berserk_rosine_missing_trace` | Брошенные башмаки и небольшие лоскуты у входа |
| `f_berserk_rosine_nest_warning` | Порог из корней и шёлка, указывающий к гнезду |
| `f_berserk_location_rosine_travelers`, `_empty` | Узелок искателя у входа; вскрытая упаковка |
| `f_berserk_location_rosine_keepsake`, `_empty` | Лента у игрушек; пустое место после сбора |
| `f_berserk_location_rosine_waycamp`, `_empty` | Старый привал с бурдюком; остатки без припасов |

`_empty`/`_armed` и прочие суффиксы дописываются к полному ID перед ними.
Например, `f_berserk_wyald_wagon_chime_spent` и
`f_berserk_rosine_cocoon_destroyed`. Существующие рисунки демонов, Узла Зверя
и Покрова Туманной долины остаются прежними. Обычные палатки, кострища,
столы и природные цветы можно оставить ванильными.

## Дополнение 4.12: дом Флоры вокруг духовного дерева

Новая планировка — 48 × 48 клеток. **Ствол занимает примерно 7 × 13 клеток,
не один тайл.** Для окончательного рисунка сначала согласуем композицию
крупных стыкующихся фрагментов: кора, края ствола, развилки корней и крылья
дома. Не сжимать целое дерево или дом в один спрайт 32 × 32.

Клеточная основа мебели — **32 × 32**, прозрачный фон и опора по полу
актуальной модели UltiCa. Открытый/пустой/обгоревший варианты имеют ту же
опору, что исходный. PNG брони и её смещения здесь не меняются.
Сейчас все новые определения используют ванильные `looks_like`.
Крыша и верхняя крона не созданы отдельным новым этажом: их художественную
композицию нужно согласовать отдельно, чтобы рисунок не закрывал проходы
и предметы при игре сверху.

| Полный ID | Что нарисовать |
| --- | --- |
| `t_berserk_flora_spiritual_trunk` | Большая композиция ствола: стыкующиеся внутренние клетки и края, не ряд маленьких деревьев |
| `t_berserk_flora_living_roots` | Массивные корни вокруг дома; соединения и окончания |
| `t_berserk_flora_living_wall` | Бревенчатая стена с переплетёнными живыми корнями, соединения и углы |
| `t_berserk_flora_wood_floor` | Тёплые потёртые доски; непрерывный пол также под предметами |
| `t_berserk_flora_woven_rug` | Мягкий тканый ковёр гостиной, края и центр |
| `t_berserk_flora_root_window` | Маленькое окно в ветвях и деревянной раме |
| `t_berserk_flora_scorched_root_path` | Разорванный внешний рубеж: земля и обломки корней, проходимая клетка |
| `t_berserk_flora_charred_trunk`, `t_berserk_flora_charred_roots` | Обгоревшие версии тех же крупных форм, сохранившийся узнаваемый силуэт |
| `t_berserk_flora_charred_timber` | Чёрный каркас стены; те же соединения и углы |
| `t_berserk_flora_ash_floor` | Уже существующий пол руин: пепел поверх прежних досок |
| `f_berserk_flora_cosmology_shelf` | Полка астральных исследований, рукописи и схемы |
| `f_berserk_flora_ward_shelf` | Полка защитных начертаний, камни и тканевые закладки |
| `f_berserk_flora_chronicle_shelf` | Домашние хроники и письма |
| `f_berserk_flora_botany_shelf` | Травники, рисунки листьев и засушенные растения |
| `f_berserk_flora_banked_hearth` | Каменный очаг с тихими углями; свет локальный, не огненная клетка |
| `f_berserk_flora_reading_lamp` | Маленькая средневековая лампа для чтения |
| `f_berserk_flora_wooden_chair`, `f_berserk_flora_wooden_bench` | Резной деревянный стул и скамья без промышленных деталей |
| `f_berserk_flora_linen_bed` | Низкая деревянная постель с чистым бельём и набитой подстилкой |
| `f_berserk_flora_wooden_rack` | Деревянные полки мастерской, не металлический стеллаж |
| `f_berserk_flora_drying_herbs` | Связки трав рядом с кухонной столешницей |
| `f_berserk_flora_rain_basin` | Крытая керамическая чаша |
| `f_berserk_flora_herb_bed` | Низкие ухоженные лекарственные растения |
| `f_berserk_flora_armor_stand` | Рабочая подставка с кожаными прокладками и принадлежностями подгонки |
| `f_berserk_flora_aid_pantry`, `f_berserk_flora_aid_pantry_empty` | Приготовленная еда, бурдюк и ткань; пустое место после выдачи |
| `f_berserk_flora_aid_workshop`, `f_berserk_flora_aid_workshop_empty` | Набор иглы, кожи и ткани; разобранная упаковка |
| `f_berserk_flora_aid_ward`, `f_berserk_flora_aid_ward_empty` | Камни, кости и две свечи; оставшаяся пустая перевязь |
| `f_berserk_flora_manuscript`, `f_berserk_flora_manuscript_taken` | Стол с открытой прошитой рукописью и тот же пустой стол |
| `f_berserk_flora_charred_archive`, `f_berserk_flora_saved_archive` | Сгоревший стол с пеплом страниц; сгоревший стол, с которого их вынесли |
| `f_berserk_flora_fallen_bough` | Тяжёлая ветвь поперёк северной галереи; непроходимая клетка |
| `f_berserk_flora_charred_books` | Пепел и обугленные переплёты на месте полок |
| `f_berserk_flora_charred_bedroom` | Остов постели/письменного места, узнаваемая спальня |
| `f_berserk_flora_charred_fittings` | Обгоревшая домашняя обстановка и разбитая посуда |
| `f_berserk_flora_aid_lost` | Выгоревший набор без выдачи нового лута |
| `f_berserk_flora_root_niche` | Каменное укрытие под корнями южного крыльца |
| `f_berserk_flora_ruin_keepsake`, `f_berserk_flora_ruin_keepsake_empty` | Та же ниша с уцелевшей закладкой и пустая после её сбора |
| `f_berserk_flora_treehouse_threshold` | Тканая циновка порога у корней |
| `f_berserk_flora_house_rules`, `f_berserk_flora_guest_record`, `f_berserk_flora_gallery_record` | Домашние рукописные памятки в соответствующих местах |
| `f_berserk_flora_garden_record`, `f_berserk_flora_west_sign`, `f_berserk_flora_south_sign` | Садовая табличка и два читаемых указателя путей побега |
| `berserk_flora_travel_folio` | Небольшая дорожная тетрадь, значок предмета |
| `berserk_flora_rescued_manuscript` | Прошитая спасённая рукопись, значок предмета |
| `berserk_flora_scorched_bookmark` | Маленькая деревянная закладка-лист с обгоревшим краем |

Глиняную печь, обычные столы, шкафы и письменные столы пока можно оставить
ванильными. Для картинки дома в стиле манги первыми нужны **композиция
ствола и корней, деревянные стены/окна и края крыши**, затем обстановка.
Подробная схема, состояния и игровые проверки: `FLORA_TREEHOUSE_DETAIL.md`.

## Крепость Грюнбельда — новая детализация

Размеры и привязку к UltiCa выбирать по существующим тайлам стены, каменного пола и мебели. Сейчас все новые объекты используют ванильные `looks_like`; схема в `docs/assets/grunbeld-stronghold-layout.png` не является игровым рендером.

| ID | Объект |
| --- | --- |
| `t_berserk_grunbeld_wall` | breached fortress masonry |
| `t_berserk_grunbeld_cover` | broken stone bulwark |
| `t_berserk_grunbeld_flagstones` | garrison flagstones |
| `t_berserk_grunbeld_scorched_inside` | scorched smithy floor |
| `t_berserk_grunbeld_scorched_court` | scorched inner courtyard |
| `t_berserk_grunbeld_quarry_floor` | uneven quarry bed |
| `f_berserk_grunbeld_siege_orders` | torn siege orders |
| `f_berserk_grunbeld_garrison_roll` | garrison evacuation roll |
| `f_berserk_grunbeld_quarry_note` | quarry escape marks |
| `f_berserk_grunbeld_soldier_letter` | unfinished soldier's letter |
| `f_berserk_grunbeld_dresser_note` | dressing-room tally |
| `f_berserk_grunbeld_smith_note` | smith's heat notes |
| `f_berserk_grunbeld_inner_warning` | charred inner-defense marker |
| `f_berserk_grunbeld_last_warning` | melted shield beside the arena |
| `f_berserk_grunbeld_fallen_garrison` | last stand of the garrison |
| `f_berserk_grunbeld_smith_hearth` | cold smithy hearth |
| `f_berserk_grunbeld_anvil_stump` | scarred anvil stump |
| `f_berserk_grunbeld_evacuated_cart` | abandoned evacuation cart |
| `f_berserk_grunbeld_evacuated_cart_empty` | searched garrison supplies |
| `f_berserk_grunbeld_armory` | damaged garrison armory |
| `f_berserk_grunbeld_armory_empty` | searched garrison supplies |
| `f_berserk_grunbeld_ration_store` | gatehouse ration chest |
| `f_berserk_grunbeld_ration_store_empty` | searched garrison supplies |
| `f_berserk_grunbeld_quarry_rope` | quarry escape bundle |
| `f_berserk_grunbeld_quarry_rope_empty` | searched garrison supplies |
| `f_berserk_grunbeld_dressing_store` | last garrison dressings |
| `f_berserk_grunbeld_dressing_store_empty` | searched garrison supplies |
| `f_berserk_grunbeld_barrack_pantry` | barrack kitchen supplies |
| `f_berserk_grunbeld_barrack_pantry_empty` | searched garrison supplies |
| `f_berserk_grunbeld_repair_store` | barrack repair bundle |
| `f_berserk_grunbeld_repair_store_empty` | searched garrison supplies |
| `f_berserk_grunbeld_forge_store` | smith's remaining tools |
| `f_berserk_grunbeld_forge_store_empty` | searched garrison supplies |
| `f_berserk_grunbeld_heat_clothing` | scorched work clothing |
| `f_berserk_grunbeld_heat_clothing_empty` | searched garrison supplies |
| `f_berserk_grunbeld_standard_keepsake` | fallen garrison standard |
| `f_berserk_grunbeld_standard_keepsake_empty` | searched garrison supplies |

Для каждого тайника предусмотрены полный и осмотренный варианты; удобно рисовать их парой. Каменные заслоны непрозрачны. Приоритет: обгоревшая кладка и двор, осадные заслоны, кузнечный очаг, следы гарнизона, комплекты запасов. Для уникальной реликвии используется прежний спрайт. Дополнительный памятный предмет: `berserk_grunbeld_scorched_badge`.
