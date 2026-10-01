# 3.0 test build: committed attacks and hunt missions

Target: CDDA **0.I-1**. This work was checked against that tag's sources.
**The game binary was not launched.** All gameplay, rendering, native mission UI,
AI, native map placement and save/load behavior still require a player test.

## Attacks

| Opponent | Preparation | Fixed attack | Base damage before armor | Recovery |
| --- | --- | --- | --- | --- |
| Count | 3 seconds | 75-degree forward sector, range 2 | 36 bash | 2 seconds |
| Wyald | 3 seconds | Up to 3 marked cells along the saved direction | 40 bash per occupied cell | 2 seconds |
| Rosine | 3 seconds | Up to 4 marked cells along the saved direction | 30 stab per occupied cell | 2 seconds |
| Grunbeld knight | 3 seconds | 90-degree forward sector, range 3 | 48 bash | 3 seconds |
| Grunbeld dragon | Existing prototype retained | Fixed marked breath line | Existing values retained | Existing recovery retained |

The caster stores the target/origin before preparation. Later movement by the
player does not retarget that special attack. Harmless, temporary field markers
show the threat area. Preparation and recovery block ordinary movement and attacks.
Displacing/killing the caster, losing its preparation effect or returning after
an expired preparation cancels the pending strike. Monster variables carry the
saved state; no delayed EOC is queued on a temporary monster dialogue.

Wyald/Rosine advance cell by cell through safe native creature teleportation,
never forced placement. The release occurs in one event, not an animated sequence
of movement turns. A still-occupied cell, wall or other failed destination stops
further steps. A nearby target does not cause overshooting. Cover prevents native
spell propagation; warning visibility, creature collision and spell armor behavior
must be checked in game. These are basic prototypes, not proven boss balance.

Retired melee special-attack IDs remain defined but disabled, and are removed from
the four monsters' active lists. Ordinary melee stats, HP, armor, regeneration,
rewards and the dragon breath definitions were preserved.

## Real objectives

Six mission definitions extend the existing first-hunt mission:

- Close the ashen breach: defeat the guardian and seal the wound.
- Flora: sanctuary and escape: meet, prepare explicitly, then escape the siege.
- Count, Wyald, Rosine and Grunbeld: defeat the guardian, seal that site's breach,
  and claim its relic.

Each mission's native start uses `assign_mission_target` with the **registered
coordinate variable**. It does not search for or create another site. Objectives
are assigned on discovery/recall and finished from their own persistent progress.
Completed legacy objectives are not issued as new jobs. A one-minute recovery
handler repairs missing mission assignment; it does not move known sites.

The existing immediate first-hunt request after the rescue is retained. Winning
that hunt now also seeks Flora immediately. Existing burned-scrap/breach and journal
interactions remain. After all three named breaches reach the sealed state,
the stronghold guide runs immediately during synchronization, with bounded retries.
Manual journal recall remains available after the Skull Knight leaves.

Use the game's mission menu to select the tracked objective. Changing that
selection does not reset other hunts. The journal recalls site objectives;
it does not programmatically select a native active-mission pointer.

## Site spacing and engine limitation

| Target | Preferred search ring (OMT) |
| --- | --- |
| First hunt | 8–16 (existing prototype) |
| First breach | 6–12 |
| Flora | 15–30 |
| Count, Wyald, Rosine | 15–35 |
| Grunbeld | 25–45 |

Native search starts around the current player. Candidate validation also checks
against the registered first-hunt location (breach/Flora/named hunts), or Flora
(Grunbeld). When that story anchor is absent, the player is the fallback anchor.
Named candidates are additionally checked against other registered named lairs,
with a preferred minimum of 8 OMT. Stored positions are explicitly rounded with
tripoint component math; `overmap_tile` in coordinate adjustment only scales
an offset and does **not** round the existing position.

**These rings are preferences, not a guarantee for every generated world.**
In 0.I-1 `min_distance` constrains terrain lookup, but `place_special` receives only
origin and maximum radius. A unique site can therefore already exist outside the
requested ring. Three attempts are allowed from one position, followed by at most
one non-creating lookup. If a valid existing unique site is found outside preferred
spacing, its position is kept, the objective is registered there and a warning
explains the deviation. No second special is created to replace it. Further
automatic searches stop until the player moves at least 24 local tiles.
Failure keeps existing registrations unchanged and gives a retry instruction.

## Automated verification

- 205 Python data-level tests passed, including 17 additional attack/mission tests.
- Validator: 229 JSON files, 31 mod tileset definitions, 33 sprite sheets,
  78 tile IDs and 4 translation catalogs.
- English originals and 30 new Russian/Chinese translations; catalogs compiled
  with `msgfmt --check`.
- JSON syntax/references, EOC actor state, fixed targets, cancellation, modeled
  collision, independent mission completion, bounded lookup and stored-coordinate
  reuse checked. Python actor fixtures are not the native game engine.

## Player test checklist

1. Install a fresh `Berserk` folder from the archive into `mods` beside the game
   executable. Remove a duplicate in `data/mods` if present. Back up the test save.
2. First hunt after rescue: inspect the mission menu immediately; select the target
   on an already revealed overmap. Reopen the save and recall from the journal.
3. Discover each of the six sites. Confirm its objective points to that same site,
   not a second generated copy. Confirm old saved sites remain at their old positions.
4. Complete Count while Wyald/Rosine remain active. Seal and claim each reward;
   confirm only that hunt finishes. Check the Grunbeld guide after the third seal.
5. For each attack, stand on the warning once, then try sidestepping and retreating.
   Test a wall, a closed door and another creature along a rush path; no traversal
   through obstacles or multiple hits on the same cell should occur.
6. Save during preparation and after the hit; reload or leave the area. An expired
   windup must not fire later. Check recovery before the next special attack.
7. Check markers in UltiCa and ASCII. Compare the dragon breath with the prior build.
   Inspect debug.log for loader, spell, teleport, mission or tripoint-math errors.
8. Record actual preferred-ring deviations and whether any search is slow. Do not
   infer native performance or successful gameplay from the Python results above.
