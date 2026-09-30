# Wyald and Rosine: independent hunt test build

Target: CDDA **0.I-1**. Branch: `codex/3.0-new-horizon`.
This milestone has **not been run in the game**. Static checks below do not establish combat balance, native save persistence, map generation or successful loading.

The following milestone adds Grunbeld's late hunt and the assembled four-hunt chapter. See [GRUNBELD_HUNT_TEST.md](GRUNBELD_HUNT_TEST.md) for its phase handling, old-save behavior, current validation totals and full-flow checklist.

## Access and progression

After the Eclipse and completion of the first small-apostle hunt, ask the Skull Knight or peaceful Flora to mark either trail. The first-breach journal also offers the independent trails. Sealing the Count's breach gives the new journal, including in an existing world when that interaction is performed again.

The `journal of the named apostle hunts` (`berserk_apostle_hunt_journal`) remains usable when the Knight is absent. It does not require literacy. Activate it on the surface to seek or mark Wyald, Rosine or the Count. Locations are generated on request in suitable forest terrain, not placed randomly in every overmap. If the search finds no suitable site within 40 OMT, travel farther and retry; no encounter or reward is consumed. Previously found coordinates are reused.

Wyald and Rosine can be hunted in either order. Every lair has four 24×24 chunks forming a 48×48 area, two routes, stone cover, a record to examine and a final southeast arena. The guardian is spawned only on entering its final OMT, not in the approach. Six finite minion placements are defined per site; native population settings may affect the resulting count. There are no continuous reinforcements.

| Hunt | Overmap special | Final OMT | Original guardian | Reward |
|---|---|---|---|---|
| Wyald | `berserk_wyald_camp_special` | `berserk_wyald_ring` | `mon_berserk_apostle_wyald` | `berserk_wyald_beast_knot` |
| Rosine | `berserk_rosine_valley_special` | `berserk_rosine_nest` | `mon_berserk_apostle_rosine` | `berserk_rosine_mistvale_veil` |

These forest encounters are our adaptation of the Black Dogs and Mistvale; they do not reconstruct manga scenes literally. Existing sprites are used through `looks_like` until custom artwork is available.

## Encounters and rewards

| Creature | HP | Speed | Ordinary melee | Dodge | Bash / cut armor | Feature |
|---|---:|---:|---|---:|---|---|
| Wyald | 640 | 110 | 3d8 + 16 bash | 1 | 6 / 10 | Short leap; prepared ranged melee strike |
| Black Dog thrall | 150 | 95 | 1d6 + 10 cut | inherited | 2 / 3 | Finite camp support |
| Rosine | 420 | 135 | 2d6 + 14 cut | 4 | 3 / 5 | Flight; prepared piercing strike |
| Cocoon-born ravager | 85 | 125 | 1d6 + 6 cut | 2 | 1 / 1 | Fast, fragile flying support |

Neither guardian regenerates. Ordinary attack expressions describe pre-armor damage definitions, not guaranteed damage to the player. Wyald's special has a maximum bash amount of 40 and range 3; Rosine's has a maximum stab amount of 30 and range 4. Native melee-special damage scales between 0.5 and 1.0 before armor/dodging/blocking.

Both specials first apply a visible five-second preparation effect and consume 220 / 240 moves. The damaging actor requires that effect and clears it after its attempt, including a miss. At unmodified base speeds the preparation costs roughly two seconds of action time; exact observed timing must be checked in combat. Leave the attack's reach or break its line with stone or trunks. Rosine's prototype uses the native ranged-melee actor for the piercing dive: it is not a new physical flight animation.

Wear the **Beast Knot before activating Berserk** to snapshot a 210-second duration instead of 150 seconds. Equipping/removing it mid-activation does not rescale the current timer. The existing blood/stamina aftermath and three-day recovery are preserved. Wear the **Mistvale Veil** for **+1 dodge**; it does not confer invulnerability.

No stamina bonus was enabled for the Veil. In `Character::update_stamina` at 0.I-1, adding 0.05 to `STAMINA_REGEN_MOD` changes the winded multiplier from 0.1 to 0.15, a 50% increase while winded rather than a uniform 5%. `REGEN_STAMINA` applies later but follows a branch that excludes synthetic lungs. A future stamina property needs explicit interaction checks with Berserk exhaustion and stamina bionics before inclusion.

## Independent world records

| State | Meaning |
|---:|---|
| 0 / absent | Unknown |
| 1 | Site found |
| 2 | Encounter started |
| 3 | Original guardian defeated |
| 4 | Breach sealed |
| 5 | Relic received |

Each hunt keeps `berserk_hunt_<kind>_state`, its own `..._location` (surface final-OMT origin in absolute map-square coordinates), successful-spawn marker, bounded attempt count and reward claim. Original-death flags are separate. Any killer can complete the guardian death record. A guardian that leaves its arena does not move the recorded breach location.

After killing the guardian, examine the exposed breach in the **north of the final clearing**. Only a confirmed furniture update commits state 4. Examine the sealed mark a second time to claim the relic and commit state 5. The reward is reserved before spawning its item; a repeated examination cannot issue another. An already carried/worn prototype relic is not duplicated. If the player cannot carry the new item, check the ground.

The seal suppresses new incursions within a distance of 48 map squares from that site's stored origin, roughly two OMT. State 5 retains the same protection as state 4. It does not remove existing demons, erase the Brand or disable armor shadows. The existing Brand and new-era handlers share the local-region query; other lairs and distant regions remain active.

The Count's existing loot is preserved. If his breach is sealed and his original seal is carried/worn, a one-minute watcher advances the Count's record from 4 to 5 without creating another item. Old IDs are retained. No four-site single completion flag is introduced.

Closing a site gives a journal and a concrete next location: the other named hunt, then the Count if unfinished. The subsequent Grunbeld milestone adds his late hunt after these three breaches are sealed. Once all four are sealed, the first closed breach is marked as a recovery destination.

## Checked without launching the game

- Repository validator: 197 JSON files, two mod packages, tile/sprite references and compiled catalogs.
- 87 Python tests, including 11 new independent-hunt tests. These use a small EOC interpreter and data inspection, not the game engine.
- Negative flows: pre-Eclipse access, failed location search, six failed spawn attempts and manual retry, premature sealing, failed map update, wrong-place reward, repeated reward and preexisting relic.
- Coordinate/state isolation, state 5 retaining local protection, any-killer death, modeled state copy/re-entry, no random boss-group insertion, stitched route connectivity and clear static spawn tiles.
- English source strings, Russian and Simplified Chinese compiled translations, including native plural forms for minions.
- Exact-tag source review: actor loading/cooldown, inline leap IDs, ranged-melee line checks, self effects, move costs, EOC attacker/target scopes, mapgen furniture/loot fields and stamina calculation.

Primary references: [0.I-1 monster actors](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/mattack_actors.cpp), [actor loading](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monstergenerator.cpp), [character stamina](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/character.cpp), [EOC documentation](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/EFFECT_ON_CONDITION.md), [mapgen source](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/mapgen.cpp).

## Native game checks still required

1. Back up the save. Replace `mods/Berserk` beside `cataclysm-tiles.exe` with the archive's folder; remove a second Berserk copy from `data/mods` if present. Keep the optional chibi package only if used. Do not overlay old and new JSON files.
2. Load an existing post-Eclipse world, finish the first hunt, activate its journal and choose the independent trails. Verify the Russian/English UI and marked locations. Also load a new world: both guardians must be absent from ordinary random groups and neither journal hunt should unlock before the event.
3. Visit Wyald first: examine the approach record, traverse both routes, enter the southeast arena. Verify one boss, a visible preparation effect, actual delay, cover interrupting the strike, leap behavior and ability to retreat. Re-enter and save/reload before and after the fight: no second boss.
4. Kill him, save/reload, examine the exposed breach and then the sealed mark. Receive exactly one Knot. Repeated interaction and save/reload after reward must not duplicate it. Wear it before Berserk and verify the 210-second timer plus unchanged recovery and costs.
5. Repeat for Rosine: check flying minions, piercing windup, cover, +1 dodge while wearing the Veil, no stamina bonus. Test Rosine-first order separately.
6. Check each transition with native save/reload, including found-but-unvisited sites. Closed Count/Wyald regions must not close Rosine's region; new-era appearances outside the quiet radius must remain possible. Existing creatures must remain. The Brand bionic and armor shadows must still function.
7. Kill a guardian using NPCs/zombies or draw it outside the arena. Its original lair must still be sealable and its registry independent. Keep an eye on eventual unload/reload of a living, escaped guardian.
8. Block the boss anchor: no completion on failure. After the six automatic attempts, clear space and examine the exposed mark to retry. Verify furniture sealing with the avatar/vehicle on the update point does not falsely commit completion.
9. Check the Count's old state-4 save while carrying its seal: state 5 without another seal, continued local protection. Check directions still work after the Skull Knight has departed and from the surviving first-hunt journal.
10. Inspect `debug.log`, UltiCa placeholder rendering, actual difficulty for an equipped 9/9 survivor and a high-stat armored Guts, native terrain/furniture loading and performance. No claim is made that these checks already passed.

New independent lairs are quest-created. For debugging, use the **global-map** special placement menu and the exact special IDs above; they are globally unique, so do not place duplicates in the same test world. A marker does not regenerate already generated local terrain: use a fresh ungenerated area or the normal quest locator.
