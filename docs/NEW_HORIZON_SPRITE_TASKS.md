# Задание на графику New Horizon 3.0.0-dev

Срез данных: 4 октября 2026. Это задание художнику, не результат проверки
отрисовки. Полный [CSV-реестр](assets/new-horizon-art-registry.csv) содержит
фактические ID, файлы определения, `looks_like`, наследование и ссылки на
явно объявленные изображения UltiCa. Для поля без верхнего имени берётся
название его интенсивности. В реестре могут быть технические объекты: наличие
строки не означает, что каждому нужен отдельный рисунок.

## Размеры и точка опоры

- Для нового пола и обычной мебели UltiCa исходная сетка — 32 × 32 на клетку.
  Это проектная сетка новой графики, а не уже зарегистрированные параметры PNG.
- Пол непрозрачен по назначению; мебель и существа имеют прозрачный фон вокруг
  силуэта. Все состояния одного объекта сохраняют точку опоры.
- Крупные дуб, духовное дерево, гряды плоти и лица сначала рисуются общей
  композицией, затем разбиваются на стыкующиеся клетки. Не сжимать всю
  композицию до одного квадрата и не менять игровую площадь ради большого PNG.
- Для нового крупного монстра размеры согласуются отдельно. Текущий пример
  64 × 64 / offset −16,−32 не является обязательным размером всех будущих боссов.
- Не менять существующие offsets брони и руки-пушки вместе с декорациями.
- Пол под предметами относится к terrain, изображение записки — к предмету или
  осматриваемой мебели. Собственный рисунок не должен добавлять земляной квадрат.
- Поля подготовки читаются поверх разных полов; силуэт угрозы не должен
  совпадать с декором. Одно оформление можно переиспользовать для нескольких ID.

## Уже объявленные листы основного мода

Размеры ниже прочитаны из `mod_tileset`. Это текущие настройки, не новая
рекомендация уменьшить рисунок и не подтверждение положения на экране.

| Лист | Кадр | Offset x,y |
|---|---|---|
| `tileset/berserk_arm_cannon_open.png` | 32 × 48 | 0, -16 |
| `tileset/berserk_arm_cannon_closed.png` | 32 × 48 | 0, -16 |
| `tileset/berserk_armor_lower.png` | 32 × 32 | 0, -4 |
| `tileset/berserk_armor_upper.png` | 32 × 32 | 0, -15 |
| `tileset/berserk_armor_upper.png` | 32 × 32 | 0, -16 |
| `tileset/berserk_armor_upper.png` | 32 × 32 | 0, -17 |
| `tileset/cursed_oak_guardian.png` | 64 × 64 | -16, -32 |
| `tileset/demons_darkness.png` | 32 × 48 | 0, -16 |
| `tileset/echo_cave_guardian.png` | 64 × 64 | -16, -32 |
| `tileset/eclipse_butcher.png` | 64 × 64 | -16, -32 |
| `tileset/eclipse_elite.png` | 64 × 64 | -16, -32 |
| `tileset/eclipse_halfbreed.png` | 32 × 32 | 0, 0 |
| `tileset/eclipse_hunter.png` | 64 × 64 | -16, -32 |
| `tileset/eclipse_wretch.png` | 32 × 32 | 0, 0 |
| `forged_guts_sword.png` | 32 × 32 | 0, 0 |
| `tileset/griffith_reborn.png` | 64 × 64 | -20, -32 |
| `tileset/skull_knight.png` | 64 × 96 | -6, -65 |
| `true_guts_sword.png` | 32 × 32 | 0, 0 |
| `tileset/void_apostol.png` | 64 × 96 | -5, -68 |
| `nosferatu_zodd_sword.png` | 32 × 32 | 4, -7 |
| `tileset/zodd.png` | 64 × 96 | -20, -64 |

Монстры ночного Клейма переиспользуют образы обычных демонов. Боссы, стражи
и декорации с `looks_like` часто также переиспользуют изображение; это временная
графика, а не отдельный портрет. Наличие PNG в папке без записи `mod_tileset`
не делает его активным спрайтом. Для Chibi/MSX+/Undead нужна отдельная привязка
и последующая визуальная приёмка.

## 1. Состояния, которые игрок должен различать

| Фактический ID | Что подготовить |
|---|---|
| `f_berserk_oak_noisemaker` | Костяная подвеска в покое |
| `f_berserk_oak_noisemaker_armed` | Та же подвеска с натянутым приводом |
| `f_berserk_cave_noisemaker` | Каменный шумовой механизм |
| `f_berserk_cave_noisemaker_armed` | Заведённый механизм |
| `f_berserk_chapel_noisemaker` | Треснувший колокол |
| `f_berserk_chapel_noisemaker_armed` | Колокол: натянутый трос |
| `f_berserk_expedition_noisemaker` | Полевая сирена |
| `f_berserk_expedition_noisemaker_armed` | Сирена: заведённый привод |
| `f_berserk_rosine_cocoon_sealed` | Целая непрозрачная оболочка |
| `f_berserk_rosine_cocoon_inhabited` | Оболочка с различимым существом внутри |
| `f_berserk_rosine_cocoon` | Вскрытая пустая оболочка; старый ID |
| `f_berserk_rosine_cocoon_destroyed` | Разорванный и раздавленный кокон |
| `fd_berserk_committed_oak_warning` | Поднимающаяся земля над корнями |
| `fd_berserk_committed_count_warning` | Сектор тяжёлого удара |
| `fd_berserk_committed_wyald_warning` | Линия рывка |
| `fd_berserk_committed_rosine_warning` | Линия пикирования |
| `fd_berserk_committed_grunbeld_knight_warning` | Сектор молота |
| `fd_berserk_grunbeld_breath_warning` | Предвестие огненной линии |
| `fd_berserk_grunbeld_breath_flash` | Короткое огненное воздействие |

## 2. Четыре места Бехелита

| Фактический ID | Что подготовить |
|---|---|
| `f_berserk_oak_low_roots` | Низкие корни с читаемым свободным проходом |
| `f_berserk_oak_visitor_remains` | Останки у дерева |
| `f_berserk_oak_relic` | Корни с наградой |
| `f_berserk_oak_relic_empty` | Те же корни после осмотра |
| `t_berserk_cave_scree` | Каменная осыпь |
| `f_berserk_cave_broken_support` | Обломанная подпорка |
| `f_berserk_cave_return_brace` | Закрытая перемычка |
| `f_berserk_cave_return_release` | Механизм освобождения изнутри |
| `f_berserk_cave_return_release_opened` | Открытая перемычка |
| `f_berserk_cave_claw_marks` | Царапины хранителя |
| `f_berserk_cave_relic` | Каменная ниша с наградой |
| `f_berserk_cave_relic_empty` | Пустая ниша |
| `f_berserk_chapel_altar` | Осквернённый алтарь |
| `f_berserk_chapel_stone_pillar` | Каменная колонна |
| `f_berserk_chapel_relic` | Закрытый реликварий |
| `f_berserk_chapel_relic_empty` | Обысканный реликварий |
| `t_berserk_expedition_groundsheet` | Тканевый настил палатки |
| `f_berserk_expedition_torn_canvas` | Смятое и разорванное полотно |
| `f_berserk_expedition_relic` | Контейнер образца |
| `f_berserk_expedition_relic_empty` | Пустой контейнер |

## 3. Затмение: поле и памятные следы

| Фактический ID | Что подготовить |
|---|---|
| `f_berserk_eclipse_body_heap_low` | Низкая груда тел |
| `f_berserk_eclipse_body_heap_high` | Высокая груда тел, перекрывающая обзор |
| `f_berserk_eclipse_braided_flesh` | Переплетённая плоть |
| `f_berserk_eclipse_bone_spur` | Костяной выступ |
| `f_berserk_eclipse_congealed_vein` | Сгустившаяся жила |
| `f_berserk_eclipse_cart_wreck` | Разбитая телега |
| `f_berserk_eclipse_shield_barricade` | Щиты последнего сопротивления |
| `f_berserk_eclipse_shortcut_block` | Закрытый короткий переход |
| `f_berserk_eclipse_shortcut_opened` | Открытый проход |
| `f_berserk_eclipse_judeau_remains` | Следы Джудо |
| `f_berserk_eclipse_pippin_remains` | Следы Пиппина |
| `f_berserk_eclipse_corkus_remains` | Следы Коркуса |
| `f_berserk_eclipse_gaston_remains` | Следы Гастона |

### Уже определённые поверхности и границы

Эти ID уже существуют в палитре Затмения. Для пепельной поверхности уже есть `t_berserk_eclipse_ashen_flesh`. Для жил и присутствия высших сил
спрайт передаёт цвет и образ, но не добавляет поддержку цветного света движка.

| ID | Название в исходных данных |
|---|---|
| `t_berserk_eclipse_open_flesh` | living ground |
| `t_berserk_eclipse_luminous_flesh` |  |
| `t_berserk_eclipse_ashen_flesh` | ash-covered ground |
| `t_berserk_eclipse_trampled_flesh` | trampled flesh |
| `t_berserk_eclipse_dim_vein` | dim vein |
| `t_berserk_eclipse_ridge` | flesh ridge |
| `t_berserk_eclipse_bruised_flesh` | bruised living ground |
| `t_berserk_eclipse_sinew_ground` | exposed sinews |
| `t_berserk_eclipse_face_boundary` | wall of enormous faces |
| `t_berserk_eclipse_body_boundary` | entwined bodies |
| `t_berserk_eclipse_godhand_presence` | distant God Hand silhouette |
| `t_berserk_eclipse_pulsing_vein` | swelling luminous vein |
| `t_berserk_eclipse_open_chasm` | open cleft in the living ground |
| `t_berserk_eclipse_chasm_lip` | ragged cleft edge |

## 4. Дом Флоры: уют и утрата

| Фактический ID | Что подготовить |
|---|---|
| `t_berserk_flora_spiritual_trunk` | Крупный ствол: фрагменты общей композиции |
| `t_berserk_flora_living_roots` | Живые корни |
| `t_berserk_flora_wood_floor` | Деревянный пол |
| `t_berserk_flora_living_wall` | Жилая стена, вплетённая в корни |
| `t_berserk_flora_woven_rug` | Тканый ковёр |
| `t_berserk_flora_root_window` | Окно среди корней |
| `f_berserk_flora_cosmology_shelf` | Книжная полка |
| `f_berserk_flora_ward_shelf` | Полка защитных знаний |
| `f_berserk_flora_armor_stand` | Стойка доспеха |
| `f_berserk_flora_drying_herbs` | Сушащиеся травы |
| `f_berserk_flora_herb_bed` | Лекарственная грядка |
| `f_berserk_flora_rain_basin` | Чаша дождевой воды |
| `t_berserk_flora_charred_trunk` | Обгоревший ствол |
| `t_berserk_flora_charred_roots` | Обгоревшие корни |
| `t_berserk_flora_charred_timber` | Сгоревшая деревянная стена |
| `f_berserk_flora_charred_books` | Остатки библиотеки |
| `f_berserk_flora_charred_bedroom` | Узнаваемый след спальни |

## 5. Крепость и собственные образы апостолов

| Фактический ID | Что подготовить |
|---|---|
| `f_berserk_grunbeld_wagon_wreck` | Осадная телега |
| `f_berserk_grunbeld_broken_mantlet` | Разбитый щит осадного прикрытия |
| `f_berserk_grunbeld_split_spears` | Обломки копий |
| `f_berserk_grunbeld_quarry_hoist` | Подъёмный механизм карьера |
| `f_berserk_grunbeld_smith_hearth` | Каменный кузнечный очаг |
| `f_berserk_grunbeld_anvil_stump` | Наковальня на деревянном основании |
| `t_berserk_grunbeld_scorched_inside` | Следы жара внутри |
| `t_berserk_grunbeld_scorched_court` | Обгоревший двор |
| `mon_berserk_apostle_count` | Граф: собственный слизнеподобный силуэт |
| `mon_berserk_apostle_wyald` | Уайлд: живой оригинал нашей адаптации |
| `mon_berserk_apostle_rosine` | Розина: летящий насекомоподобный силуэт |
| `mon_berserk_grunbeld_knight` | Грюнбельд: рыцарь |
| `mon_berserk_grunbeld_dragon` | Грюнбельд: дракон |

## Объекты, которым сначала нужен проект привязки

Большой дуб, многоклеточная композиция вокруг уже существующего маркера
`t_berserk_eclipse_godhand_presence`, новые варианты соединений провалов,
крупная колокольня и портреты говорящих персонажей не получают выдуманных
ванильных ID. Перед рисованием согласовать, какие клетки композиции образуют
фрагменты и какие состояния реально есть в JSON. Пока не добавлять новый ID
ради названия файла. Коконы, устройства и перечисленные выше объекты уже имеют
определения; их можно передать с точным ID сейчас.

## Передача рисунков

1. PNG без потери исходного разрешения; файлы с латинскими именами.
2. Для каждого — объект/ID, размеры кадра, точка опоры и порядок состояний.
3. Для большой композиции — цельный исходник и схема разбиения на клетки.
4. Нормальный / заведённый, полный / пустой, мирный / обгоревший варианты должны
   различаться формой и деталями, а не только едва заметным оттенком.
5. При импорте отдельно назначаются `fg`, лист, размеры и offsets. После этого
   требуется просмотр в выбранном тайлсете; в текущем пакете он не выполнялся.

Обычные палатки, скамьи, ящики, инструменты и базовую мебель можно оставить
ванильными. Собственная графика в первую очередь нужна для механически важных
состояний, лиц локаций и узнаваемых форм апостолов.
