# New Horizon: location scenery test build

Target: **CDDA 0.I-1**. Branch: `codex/3.0-new-horizon`.

No CDDA executable was run. These are JSON, data-level transaction and geometry
checks. Native appearance, monster AI, sound, bashing, save/reload and loot
generation still need a player test. The previous Grunbeld breath prototype
is included and still awaits its first native test.

## Changed locations

| Location | New content | Reason to explore |
|---|---|---|
| Lost expedition | Canvas tents with sleeping bags, a survey station, crates, folding chairs, supplies, rubble and blood traces | Read the interrupted journal, take camping supplies, approach the specimen case from more than one direction |
| Desecrated chapel | Pew rows, altar furniture, western bell chamber, side aisle, books and a defaced memorial | Read the memorial, find small supplies, go around the nave |
| First apostle's hollow | Rock-floored depression, irregular shallow pits, victim traces, rubble and a side cache | Approach behind the preserved stone screens or inspect the stripped camp |
| First local breach | Broken foundation, changed soil, shallow fissures, debris and a boundary stone | Find the wound and identify why closing it only affects nearby new manifestations |
| Wyald's Black Dogs camp | Canvas mess tent, tables, food stores, a cage with an open gate, trophies and a training area | Inspect the prisoners' route and camp stores before entering the existing fighting ground |
| Rosine's valley | Flowers, tree screens, toys, dormant, inhabited, empty and destroyed cocoons | Choose routes between cover and cocoons; deliberately open two inhabited shells or smash them |
| Flora's manor | Room partitions and doors, dining area, bedroom/workshop furniture, books, supplies, flower beds, benches and a work journal | Prepare in a lived-in sanctuary; see the west road and southern garden before the siege |
| Grunbeld's stronghold | Breached ramparts, charred standard, rubble, beds and stores in the barracks, tools in the quarry | Use the siege works as cover and find small recovery supplies before the crucible |

Layout dimensions are unchanged. Existing quest furniture, relic and seal
coordinates, arena entrance conditions, stone sight screens and hidden boss
arrival cells are preserved. Boss stats, rewards, hunt registry and eclipse
progression are unchanged. New cover and supplies can change practical
difficulty and must be judged in play.

The expedition already used vanilla canvas furniture in its palette. This
build adds visibly relevant camping equipment and occupation traces; it does
not introduce stone walls or a new roof level. The chapel takes inspiration
from vanilla rural church organization, but keeps this mod's two-tile footprint
and existing distraction/relic locations.

## Cocoon behavior

- `f_berserk_rosine_cocoon_sealed`: dormant shell. Can be bashed; no creature.
- `f_berserk_rosine_cocoon_inhabited`: examine and explicitly confirm opening.
  One `mon_berserk_cocoon_ravager` attempts to appear 1–2 squares from that
  cocoon, not from the avatar. Successful placement changes only that shell
  to the existing empty ID. If no valid cell exists, it remains inhabited.
- `f_berserk_rosine_cocoon`: existing empty ID retained for old saves. No
  release on subsequent examinations. New fallback is a ruptured egg sac.
- `f_berserk_rosine_cocoon_destroyed`: inert torn remains. Bashing a dormant,
  inhabited or empty shell changes it to this state. Bashing is an alternative
  to releasing the creature in this prototype.

There are exactly two inhabited cocoons in the cocoon grove. Their two former
preplaced ravagers are removed there; other valley ravagers remain. There is
no recurring cocoon spawner and no automatic proximity hatch in this version.
Furniture state is the per-cell record, so independent cocoons do not share a
world flag. The test model covers copied state; native save/reload is untested.

## Exact-tag references

Vanilla composition and IDs were checked against:

- [Rural church](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/mapgen/church_rural.json): altar, nave/side spaces, books.
- [Campsites](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/mapgen/campsite.json): deployed tents and camp equipment.
- [Forest camp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/mapgen/survivor_forest_camp.json): working areas, scattered supplies and tools.
- [Mansion](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/mapgen/mansion.json): room functions, storage and tool groups.
- [Tent furniture](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/furniture_and_terrain/furniture-terrains.json), [egg sacs](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/furniture_and_terrain/furniture-eggs.json), and furniture storage/seats/flora definitions.
- [EOC implementation](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp): `f_spawn_monster` runs success/failure callbacks with the same dialogue context; `target_var` selects the source. A radius-zero furniture transform updates the examined cell.

These are references for an original adapted layout, not full copies of vanilla
maps. No dependency on master or a newer lighting mechanism is introduced.

## Verification

**188 tests passed; 222 JSON files validated.** Both translation catalogs
compiled with `msgfmt --check`; `git diff --check` passed. New tests
check mapped 24×24 rows, original creature placements, approach-connected story
features, canvas camp access, all four Flora siege states with new furniture,
finite cocoon transactions, and compiled RU/zh_CN text. Ordinary doors are
treated as openable in the walk model; vehicles, destruction, fields, native
pathfinding and visibility are not simulated.

## Installation and player checklist

Back up the save. Replace the whole `mods/Berserk` folder beside
`cataclysm-tiles.exe`; keep one installed copy and remove an old
`data/mods/Berserk` duplicate if present.

**Mapgen changes affect newly generated maps.** Previously visited camps,
manors and lairs are not forcibly rebuilt; overwriting them could remove
player items or alter a saved battle. Use a test world or place a new special
on an ungenerated part of the overmap. Old cocoons receive their new definition
but are still empty; new inhabited ones are generated only in the new grove.

1. Inspect expedition tents, sleeping bags, crates, case and delayed alarm.
   Confirm there is no inaccessible equipment or crate on a story cell.
2. Walk chapel main and side approaches; inspect the memorial, altar and
   western bell device. Check the delayed distraction in actual combat.
3. Enter the first hollow and breach from several approaches. Confirm each
   boss appears once at the existing inner trigger and remains the same boss
   when retreating and returning.
4. Explore Wyald's cage, mess tent and fighting yard; check both routes remain
   usable and the trophy text opens without changing hunt state.
5. In Rosine's grove, compare intact, moving, empty and shredded cocoons in
   UltiCa and with the optional chibi pack. Open one twice: exactly one creature
   must emerge. Block its nearby cells and retry; bash a different shell. Save
   and reload after opening and verify it stays empty. Check melee attacks can
   actually bash these custom furniture definitions.
6. Speak with Flora, prepare the siege, and flee by the western road once and
   the southern garden on a separate test. Check added furniture and doors do
   not strand the player or prevent the preexisting armor/scenario logic.
7. Explore Grunbeld's siege works and barracks; test both forms, fixed breath,
   relic and breach completion. This build does not validate the breath's native
   rendering merely because the scenery tests pass.
8. Check English/Russian/Chinese names, inspect `debug.log`, and send the exact
   message and screenshot for any blocked route or misplaced furniture.

## Sprites to draw

See [LOCATION_SPRITES_RU.md](LOCATION_SPRITES_RU.md). No new PNG placeholders
were generated and existing armor/CBM sprite offsets are untouched. Vanilla
furniture fallbacks are temporary; they do not constitute custom final art.
