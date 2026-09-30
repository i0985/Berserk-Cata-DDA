# New Horizon 3.0: the Count and independent local breaches

Target: **CDDA 0.I-1**. Test branch: `codex/3.0-new-horizon`.
Only static checks were run. The game was not launched.

## Included

- A separate world record for each named hunt and its local breach.
- A complete Count encounter: a locator, a 2 × 2 OMT fortified residence,
  a dungeon below the northeastern hall, eight finite servants, an optional
  talking prisoner, death handling, a trophy and an examined breach to seal.
- Directions from the Skull Knight after the first lesser-apostle hunt.
  The existing first-breach journal can also locate the Count after the
  player chooses the pursuit path, even if the Knight has already departed.
- Fixed local quiet zones for the first breach and the Count. ERA mapgen
  updates check the **target** OMT before spawning; entering a neighboring
  unprotected OMT cannot seed a quiet target. Nightly Brand hunts retain
  a one-in-three attempt in a quiet zone; the shelter ward remains separate.
- A larger echo cave: four underground OMTs, two paths through the galleries,
  rock spines blocking direct sight, and a keeper distant from the stairs.
- Visible fallback art and a one-second action cost for the site chimes,
  chapel bell and expedition siren. The cave chime now has volume 45.
- English source text, Russian and Simplified Chinese catalogs, including
  monster plural forms.

## Count balance and limits

| Creature | HP | Speed | Ordinary hit before armor | Bash / cut armor | Special |
| --- | ---: | ---: | --- | --- | --- |
| Count | 560 | 85 | 20 bash + 2d6 (22–32, mean 27) | 8 / 12 | Prepared sweep: 18–36 bash, range 2, 14-turn cooldown, 180 move cost |
| Twisted servant | 160 | 92 | 12 cut + 1d6 bash (total 13–18) | 2 / 3 | No special attack or regeneration |

The zero-damage windup applies a visible four-turn preparation effect and
spends 180 moves before the separate sweep can be attempted. Windup cooldown
is 18 turns. These are configured values, not measured combat results.
Exact warning timing, AI selection and opportunities to dodge need a game test.
The Count and servants use the existing butcher/half-demon art as placeholders.
They retain the existing demon faction's hostility to zombies.

The Count's original trophy ID is retained as the wearable **Seal of Severed
Flesh**. It now adds 20% post-defense damage to an explicit demon whitelist
when worn; its activation still explains the breach. See
[APOSTLE_RELICS_TEST.md](APOSTLE_RELICS_TEST.md) for the artifact prototype
and its separate, pending in-game checks. The quiet-region reward remains. There are no recurring summons or random world spawns of the
Count. The eight servants are placed once by mapgen, six above and two below.

The prisoner is a friendly, immobile conversable monster in a closed cell,
not a full human NPC. The cell door blocks initial sight from the patrols.
Open it to talk, but nearby servants can endanger the prisoner after that.
His dialogue is optional; losing him cannot block the hunt. This unnamed
encounter and the residence layout are our adaptation, not a canonical scene.

## Registry

| Record | Current role |
| --- | --- |
| `berserk_hunt_first_breach_state` / `_location` | Migrated legacy breach; closure records its actual surface position |
| `berserk_hunt_count_state` / `_location` | Count's independent world progress and location |
| `berserk_hunt_wyald_state` / `_location` | Reserved; no encounter implemented here |
| `berserk_hunt_rosine_state` / `_location` | Reserved; no encounter implemented here |
| `berserk_hunt_grunbeld_state` / `_location` | Reserved; no encounter implemented here |

Count states: absent/0 = unknown, 1 = located, 2 = entered dungeon,
3 = defeated, 4 = breach sealed. The late records are only predicate slots;
this build does not spawn those apostles or imply their hunts are playable.

Locations used for quiet checks are absolute map-square coordinates at the
surface OMT origin. The radius is 48 map squares, roughly two OMTs, measured
with the game's `rl_dist` metric. Old first-breach flags and all earlier IDs
remain intact. A recurring one-time migration imports a saved closed breach
if its old location variable is available. The legacy terrain-based fallback
remains until this import succeeds.

The Count's death EOC captures **beta**, the dying monster, then selects the
avatar for the notification. NPC kills, monster kills and unattributed deaths
therefore share the same completion path. It never replaces the sealed record
on a repeat death. Sealing first checks that the furniture update succeeded;
a failed update cannot grant completion or a second trophy. The old first
breach now checks its furniture before committing the journal and quiet zone
as well. Existing demons are not removed, armor shadows remain independent,
and none of this globally disables the Brand.

## Finding the locations

| Place | Overmap special | Terrain / coordinates |
| --- | --- | --- |
| Count's residence | `berserk_count_residence_special` | `berserk_count_prison` NW; `berserk_count_hall` NE; west/east courtyards south; `berserk_count_dungeon` below NE |
| Echo cave | `berserk_echo_cave_special` | Legacy `berserk_echo_cave_depth` NW underground, `berserk_echo_cave_gallery` NE, `berserk_echo_cave_passage` SW, `berserk_echo_cave_relic_chamber` SE |

The Count's special has zero natural occurrences: the post-Eclipse hunt
locator creates or finds it within a bounded search. The hall's execution
record is verified before the location is marked. Both the Skull Knight and
journal use the same saved location on later requests, rather than creating
another residence. The dungeon's Count is behind a rock/wall screen from
the arrival stairs; he can move during combat.

Count stairs: NE hall and dungeon local **(12,20)**.
Count breach: dungeon **(12,5)**.
Cave stairs: NW underground **(12,12)**.
Cave relic: SE underground local **(12,5)**, combined-map **(36,29)**.
Cave chimes: SW local **(9,9)** and **(12,13)**.
The keeper starts at combined-map **(36,34)**, over 20 tiles from arrival.

Place full specials through the **overmap editor**, not the local mapgen menu.
Use a previously ungenerated area. Updating definitions does not replace
already-generated cave maps or move their saved monsters. The old cave ID,
claim handler and (12,5) relic update coordinates remain usable in old caves.
On a previously generated one-OMT cave, the new corridors will not appear.
Avoid placing `OVERMAP_UNIQUE` cave specials twice in one overmap.

## Проверка в игре

1. После первой охоты спросить Рыцаря-Черепа о Графе. Либо закрыть первый
   прорыв и выбрать охоту через дневник. Повторный запрос показывает то же место.
2. Найти «зал казней Графа» / `the Count's execution hall` на карте. Проверить
   главный южный вход, западный пролом, оба крыла и боковую кладовую.
3. Открыть дверь камеры в западном крыле, поговорить с узником. Диалог не
   должен быть обязательным условием победы или запечатывания.
4. Спуститься под северо-восточный зал. Проверить совпадение лестниц,
   отсутствие немедленного обзора босса, пути слева и справа от перегородки.
5. Проверить подготовку удара Графа, бой с обычным подготовленным героем
   и с Гатсом. Восемь слуг не должны заменяться новыми после убийства.
6. До убийства осмотреть прорыв: завершения нет. После убийства забрать
   печать, осмотреть прорыв и убедиться, что он закрыт. Повторный осмотр,
   уход и загрузка не должны выдавать новую награду или сбрасывать прогресс.
7. Закрыть первый и графский прорывы в разных местах. Сравнить новые
   появления рядом с каждым и в далёком городе, включая вход с внешнего
   соседнего района. Уже существующие демоны остаются; ночные появления
   Клейма возле прорыва ослаблены, но не исключены полностью.
8. Создать свежую пещеру целиком. У лестницы не должен сразу находиться
   хранитель. Найти оба каменных колокола в юго-западной части: встать рядом,
   нажать осмотр `e` и выбрать клетку колокола. Скрыться за камнем до шума.
   Демон не обязан отвлекаться, если уже видит игрока; это надо проверить.
9. Проверить английский/русский/китайский, UltiCa, старое сохранение,
   сохранение после каждой стадии и новые сообщения в `debug.log`.

## Static validation and upstream references

Passed: asset validator, 45 Python tests, gettext `msgfmt --check`,
`git diff --check`, and validation before packaging.
Tests cover connected seams, alternate paths, stairs, finite spawns,
independent regions, foreign killers, failed updates, repeated examination,
legacy migration and translations. The small data interpreter does **not**
prove CDDA loading or saved-game persistence.

Not checked in game: AI distraction, dialogue availability, monster movement,
windup timing, battle balance, actual map generation, UltiCa rendering and
real save/load. No game binary was launched.

All upstream references are pinned to **0.I-1**:

- [EOC documentation](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/EFFECT_ON_CONDITION.md)
- [Math functions and variables](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/NPCs.md)
- [Melee attack fields](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/MONSTER_SPECIAL_ATTACKS.md)
- [EOC source](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp): location offsets are in map squares; `overmap_tile` scales offsets but does not round to an OMT origin.
- [Furniture examine actor](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/iexamine_actors.cpp): provides the furniture's `pos` but has no automatic time cost.
- [Math source](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/math_parser_diag.cpp): `distance` accepts location variables and uses `rl_dist`.
- [Condition source](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/condition.cpp): position values use talker absolute coordinates; conditions short-circuit.

## Installation

Extract into `<CDDA>/mods/`, beside `cataclysm-tiles.exe`. Replace the old
`mods/Berserk` directory instead of layering a second installation. Remove
any duplicate `data/mods/Berserk`; keep saves. The optional graphics package
is included. No PR, merge, 2.0 ref update or release publication accompanies
this test build.
