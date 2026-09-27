# Eclipse entry and return prototype (CDDA 0.I-1)

This is a six-OMT layout prototype, arranged as two columns and three rows with a connected path from the entry chamber to an empty final altar. The flesh-covered floor and walls reuse base-game 0.I-1 terrain from the meat microlab. One stronger light source per area replaces the patchy nine-light pattern. It has no monsters, boss, Behelit drop source, Skull Knight NPC, or world-wide demon spawns yet. The final area has a technical rescue trigger and one-time consequences for testing.

## In-game check

1. Install `Berserk` from this branch under `<CDDA>/mods/Berserk` and remove any older `Berserk` copy from `<CDDA>/data/mods`.
2. In an existing or a new world, use the debug item-spawn menu to give yourself `berserk_behelit` (`Behelit`). Its acquisition from bosses comes in a later phase.
3. Note your coordinates and items. Activate the Behelit and choose **No** once; verify you stay put. Activate it again and choose **Yes**. You should arrive on flesh-covered ground beside a return seal. Check the outer walls and light in your tileset.
4. Walk east, south, west, south, and east through all six connected areas to reach the empty altar. Check each passage and ensure there is no opening into raw rock. Activate the Behelit from the altar to return. Re-enter and test the return seal at the entrance.
5. Repeat after saving and loading inside the area. Verify the return location is the same, and the Behelit is still in your inventory. Leave a harmless item on the floor and confirm it stays behind.
6. Try entering from a character standing indoors, on another Z level, and on an old save. Inspect `debug.log` for new warnings or errors.

Only the player and carried/worn equipment travel. Nearby NPCs, pets, and vehicles remain behind. Both teleports use `force_safe`: if the destination is blocked, the player remains in place and can try again. The exit seal remains on the map if the Behelit is dropped there.

Already visited glass, first flesh, and rotated dungeon test rooms are part of the save and remain intact, including items dropped there. The corrected six-room dungeon uses a new overmap special ID with `"rotate": false`; its terrain IDs remain the same, and the Behelit looks specifically for the corrected special. On an existing save, leave the old dungeon with the Behelit or entry seal before entering again. The Behelit and old return seals still work in legacy rooms. This keeps saved characters from being trapped during the layout change.

The dungeon is placed on demand at Z level -7, within 24 overmap tiles of the activation point. If there is no suitable unexplored space for all six rooms in that area, the attempt fails with a message and the player stays put. Returning to its entrance location and clearing the saved origin are not coupled: the stored origin is overwritten on the next entry, while a failed return keeps the origin for another attempt. Keep both legacy room definitions for old saves.

## Technical rescue check

Use a disposable copy of a save. The final altar has no enemies yet, so a normal visit does not trigger rescue. While standing in the **final** overmap tile, use the debug menu to lower head or torso HP to 30 or below. Within one turn, the rescue should stabilize head and torso at no less than 35 HP (or their maximum), stop bleeding, bring blood and red-cell deficits up to at least -5000, and move you back near the recorded Behelit activation point. A popup describes the Skull Knight's intervention; no friendly Skull Knight NPC or dialogue tree exists yet. The lost-left-hand CBM is installed only if neither it nor the arm cannon is present; both cannon and charge recipes are learned. `g_berserk_eclipse_era` is saved in the world as 1, but does not yet change world spawns. Rescue state 2 prevents duplicate consequences.

For a lethal hit test, enter with head and torso above 30, then cause a single hit to one of them that passes directly through zero; `PREVENT_DEATH` should use the same rescue. Repeat separately for head, torso, blood loss, and an active Berserk rush near its 150-second end. A rescue during the rush applies its exhaustion and three-day recovery **once**, without charging the additional Berserk blood loss; this still needs an in-game check. Test repeated hits, save/load before and after rescue, and a character who already has the arm cannon. Confirm no second hand CBM or popup appears after returning. If the original return tile is obstructed, the rescue attempts the nearest passable tile within five squares, then retries six tiles east and six tiles west; if all three areas are blocked, it leaves you in the altar alive with the Behelit as the manual exit. Check `debug.log` for errors.

The rescue is limited to the final area of a new run started after installing this update; it does not protect the rest of the dungeon. An old save currently inside the final area must exit and enter again to set the run-active flag. Griffith is not spawned and a victory ending is not wired yet; add and test that separate completion with the boss stage. Do not treat passing JSON checks as proof of successful gameplay.
