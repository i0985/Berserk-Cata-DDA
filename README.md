# Berserk: New Horizon 3.2 — development build

Фанатский мод о столкновении мира Cataclysm с миром манги Кэнтаро Миуры. Поиск Бехелита, Затмение, Клеймо, протез руки-пушки, Рыцарь-Череп, защищённое пристанище, Флора и независимые охоты на апостолов образуют кампанию New Horizon. Противники рассчитаны на подготовленного персонажа середины игры: перед началом нужны защита, лечение и возможность отступить.

Текущая версия: **3.2.0-dev**, рабочая ветка `codex/3.2-godo-and-dialogues`.
Это предварительная сборка: полный проход на версии игрока ещё не выполнен.

- [Кузница Годо, диалоги, заказы и плейтест 3.2](docs/NEW_HORIZON_32_GODO.md)
- [Дорожные истории и редкая уникальная кузница](docs/NEW_HORIZON_32_ROAD_STORIES.md)
- [Редкость мест Бехелита, Рикерт-спутник и перенос заказа протеза](docs/NEW_HORIZON_32_RICKERT.md)
- [Возвращение в кузницу, память Рикерта, искры Годо и прощание Рыцаря](docs/NEW_HORIZON_32_FORGE_REUNION.md)
- [Изменения и ограничения 3.1](docs/3.1_GEOGRAPHY_AND_PROGRESSION.md)
- [Установка 3.1](docs/INSTALL_3.1.md)
- [Изменения 3.0: English / Русский / 中文](docs/RELEASE_3.0_DEV.md)
- [Установка и обновление](docs/INSTALL_3.0.md)
- [Состав сборки и оставшаяся приёмка](docs/P7_BUILD_AND_TRANSLATIONS.md)
- [Задание на спрайты и текущие размеры](docs/NEW_HORIZON_SPRITE_TASKS.md)
- [Исправление естественного появления мест Бехелита и ошибок осады](docs/P8_NATURAL_BEHELIT_SITES_HOTFIX.md)
- [Исправление маршрута первой охоты](docs/P9_FIRST_HUNT_ROUTE_HOTFIX.md)

История: [1.5.1](docs/RELEASE_1.5.1.md), [The Price of Rage 1.5](docs/RELEASE_1.5.md).
Инструкция публикации 1.5.1 относится к тому релизу; она не является разрешением
публиковать или объединять текущую ветку разработки.

## Поддерживаемая версия

Рабочая цель — CDDA 0.I-1; версия из отчётов игрока — `cdda-0.I-2026-09-19-2324`.
Прежние подтверждения совместимости 1.5.1 не подтверждают всю кампанию New Horizon.
Текущий статус и история указаны в [таблице совместимости](docs/COMPATIBILITY.md).
В 3.2 выполнены проверки данных и модели переходов; нативный игровой проход ещё нужен.
Новые реплики 3.2 имеют английский оригинал и русский перевод. Старый китайский
каталог сохранён; для новых реплик до его обновления используется английский.

## Установка

В репозитории находятся два независимых каталога модов:

- `mods/Berserk` — основной контент и графика для UltiCa (`UltimateCataclysm`);
- `mods/Berserk_chibi_tileset` — дополнительная графика для ChibiUltica, MSXotto+ и перечисленных в ней совместимых наборов.

Copy the chosen folders from this repository's `mods/` into the game's **user**
`mods/` directory. In a portable Windows build, this is `mods/` beside
`cataclysm-tiles.exe`. Extract the ZIP **inside that directory**: the final path
must be `<CDDA>/mods/Berserk/modinfo.json`, with the catalogs under
`<CDDA>/mods/Berserk/lang/mo/ru/LC_MESSAGES/Berserk.mo` and
`<CDDA>/mods/Berserk/lang/mo/zh_CN/LC_MESSAGES/Berserk.mo`.

Скопируйте нужные каталоги из `mods/` репозитория в **пользовательский** каталог
`mods/` игры. В портативной сборке Windows он находится рядом с
`cataclysm-tiles.exe`. Архив распаковывайте **в эту папку**: должны получиться
`<CDDA>/mods/Berserk/modinfo.json` и указанные выше файлы перевода.

CDDA 0.I-1 сначала регистрирует моды из `data/mods/`, а затем из
пользовательского `mods/`. Если один и тот же мод есть в обоих местах, игра
оставляет старую копию из `data/mods/` и игнорирует новую. Переводы сторонних
модов она при этом ищет только в пользовательском `mods/`. Для обновления
обязательно уберите `data/mods/Berserk/` и `data/mods/Berserk_chibi_tileset/`,
затем полностью перезапустите игру. Папки `save/` и `config/` не затрагивайте.
Не копируйте весь репозиторий как один мод.

Если перевод всё ещё не виден, откройте `debug.log`: строки загрузки файлов
Berserk должны указывать на `mods\\Berserk\\`, а не на `data/mods\\Berserk\\`.

When updating from earlier development archives, close the game and remove
`<CDDA>/cache/mods/Berserk/` and, if present,
`<CDDA>/cache/mods/Berserk_chibi_tileset/`. These are generated caches, not
the installed mods or saves. Earlier archives assigned every file the same
timestamp, allowing CDDA 0.I-1 to reuse obsolete JSON even after replacing
the mod folder. New archives preserve source file modification times.

При обновлении с прежних предварительных архивов закройте игру и удалите
`<CDDA>/cache/mods/Berserk/` и, если есть,
`<CDDA>/cache/mods/Berserk_chibi_tileset/`. Это кэш, который игра создаст заново.
Прежний упаковщик ставил всем файлам одну дату: CDDA 0.I-1 могла читать старый
JSON из кэша даже после полной замены папки мода. Это вызывало повторную ошибку
`Unread data ... tiles-new` у руки-пушки. Новые архивы сохраняют даты изменения
исходных файлов. Предупреждение `Stale game data detected` также означает
несовпадение с кэшем; указанная очистка его устраняет. `save/` и `config/` не удаляйте.

从旧的 1.5 测试压缩包更新时，请先关闭游戏，然后删除
`<CDDA>/cache/mods/Berserk/` 和（如果存在）
`<CDDA>/cache/mods/Berserk_chibi_tileset/`。这些是游戏自动生成的缓存，
不是模组或存档。旧压缩包给所有文件设置了相同的修改时间，导致 CDDA 0.I-1
即使在替换模组文件夹后仍可能读取旧 JSON。新压缩包保留源文件的修改时间。
请勿删除 `save/` 或 `config/`。

Для UltiCa включите только **Berserk**. Для ChibiUltica или MSXotto+ включите **Berserk** и **Berserk: Extended tileset** в одном мире.

При обновлении сначала удалите старые каталоги `Berserk` и `Berserk_chibi_tileset` из обоих каталогов модов, затем скопируйте новые только в пользовательский `mods/`. Это предотвращает загрузку второй копии мода и файлов, оставшихся от прежней структуры `optional/chibi_tileset`. Для UltiCa не включайте дополнительный мод `Berserk_chibi_tileset`.

## Проверка для будущей приёмки

Из корня репозитория:

```bash
python tools/validate_mod_assets.py
python tools/package_release.py
```

Эти команды включают валидацию. Архивы сохраняют даты исходных файлов.
Для 3.2 дополнительно проверяются переходы заказов, разговоры и сохранённые
правила прогресса 3.1. Это не запуск игры: список игрового прохода находится
в [документе 3.2](docs/NEW_HORIZON_32_GODO.md).

## Разработка графики

Общий список совместимых тайлсетов хранится в `tools/tileset/tileset_compatibility.txt`. После его изменения выполните:

```bash
python tools/tileset/apply_tileset_compatibility.py
```

Исходные изображения Ber_Suit не входят в репозиторий. Если они доступны отдельно, листы можно пересобрать командой:

```bash
python tools/tileset/build_ber_suit_eq_sheets.py --source /path/to/Ber_Suit
```

![Предпросмотр брони](assets/preview/chibi_ber_suit_preview.png)

## Правовой статус

Это некоммерческий фанатский проект. Он не связан с правообладателями Berserk и не одобрен ими.
