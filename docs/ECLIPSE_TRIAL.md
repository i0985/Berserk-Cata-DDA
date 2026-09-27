# Eclipse entry and return prototype (CDDA 0.I-1)

This is a six-OMT layout prototype, arranged as two columns and three rows with a connected path from the entry chamber to an empty final altar. The flesh-covered floor and walls reuse base-game 0.I-1 terrain from the meat microlab. One stronger light source per area replaces the patchy nine-light pattern. It has no monsters, boss, rewards, Behelit drop source, hand loss, or world-era progression yet.

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
