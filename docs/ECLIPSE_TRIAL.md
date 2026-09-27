# Eclipse entry and return prototype (CDDA 0.I-1)

This is a one-OMT technical test area. It has no monsters, boss, rewards, Behelit drop source, hand loss, or world-era progression yet.

## In-game check

1. Install `Berserk` from this branch under `<CDDA>/mods/Berserk` and remove any older `Berserk` copy from `<CDDA>/data/mods`.
2. In an existing or a new world, use the debug item-spawn menu to give yourself `berserk_behelit` (`Behelit`). Its acquisition from bosses comes in a later phase.
3. Note your coordinates and items. Activate the Behelit and choose **No** once; verify you stay put. Activate it again and choose **Yes**. You should arrive on black glass beside a return seal.
4. Walk around the enclosed 24-by-24 test area. Examine the return seal to go back. Repeat, this time activating the Behelit in the test area to leave.
5. Repeat after saving and loading inside the area. Verify the return location is the same, and the Behelit is still in your inventory. Leave a harmless item on the floor and confirm it stays behind.
6. Try entering from a character standing indoors, on another Z level, and on an old save. Inspect `debug.log` for new warnings or errors.

Only the player and carried/worn equipment travel. Nearby NPCs, pets, and vehicles remain behind. Both teleports use `force_safe`: if the destination is blocked, the player remains in place and can try again. The exit seal remains on the map if the Behelit is dropped there.

The test map is placed on demand at Z level -7, within 24 overmap tiles of the activation point. If there is no suitable unexplored space in that area, the attempt fails with a message and the player stays put. Returning to its entrance location and clearing the saved origin are not coupled: the stored origin is overwritten on the next entry, while a failed return keeps the origin for another attempt. Avoid replacing this prototype with the full Eclipse map before testing old saves that contain this test location.
