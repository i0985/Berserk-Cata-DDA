# First-hunt mission prototype — CDDA 0.I-1

This is the first playable prototype of native missions for New Horizon.
Do not merge it into main or extend it to the other hunts until the native
mission UI, map marker and save/load behavior have been checked in the game.
No CDDA executable was run while preparing this change.

## Changed behavior

- After the rescue aftermath, or the post-Eclipse profession's initialization,
  request the first hunt immediately. The one-minute handler is a fallback.
- The hunt creates a native `MISSION_BERSERK_FIRST_HUNT`, shown in the mission
  list as **First hunt: the apostle's hollow** (Russian: **Первая охота: логово
  апостола**). Native assignment selects it as the active mission.
- Its start reads the existing `u_berserk_first_hunt_location` with
  `assign_mission_target.var`. It does not search for or generate a second site.
- Recalling the notes or asking the Skull Knight reveals that same location.
  It does not change the player's currently selected different mission. Use
  the game's mission menu to select this mission again.
- The existing apostle's death handler completes the mission and explains:
  search the remains, take the burned scrap, activate it to locate the breach.
- There is no deadline, generic reward or dependency on a surviving guide.
  Independent named-hunt coordinates and progression remain unchanged.

## Location distance and failure handling

For a new first-hunt target, the locator uses `min_distance: 8` and
`search_range: 16` in **overmap terrain tiles**, at surface level. The native
search uses square distance. On immediate issuance, the origin is the player's
return position. If an initial search fails and a later search is performed
after travelling, the ring is relative to that later position.

The target is a single OMT without road connections or adjacent map sections.
It can therefore use the native `om_terrain_replace: forest` path rather than
the special placement path. This keeps the ring constraints for the actual
replacement. `cant_see: true` restricts replacements to unseen forest; visible
or previously visited terrain is not selected. The existing special ID is
retained for compatibility and debug placement.

Why not merely add `min_distance` to `om_special`? In exact-tag
`mission_util.cpp`, the filter applies to searches, but `place_special` is
called with the maximum radius alone. A special can be placed too close,
then rejected by the filtered lookup. That is unsafe for a no-duplicate scheme.

There are at most three locator calls before automatic retries stop. After
moving at least 24 local map tiles from the last failed attempt, activating
the first-hunt notes permits a new bounded cycle. There is no recursive or
unbounded search and no silent expansion of the radius. Each native locator
call can itself perform the engine's two bounded search passes.

Exact-tag `get_om_terrain_pos` can return the player's origin when lookup
fails. Consequently, the returned point is checked with `overmap_at_point`
before saving coordinates, setting the marked flag or assigning a mission.
The engine may still emit its own unsuccessful-search debug message when no
matching terrain exists. This JSON-only prototype cannot suppress that message.

If the ring contains no unseen forest (including a map revealed entirely
through debug), lookup can fail. The notes and explanatory message are still
issued. To test a marker on a fully revealed map, first find the target and
then reveal the map; an existing saved target also works on a revealed map.

## Old saves

- A valid already marked lair is reused at its old coordinates, even if it is
  closer than the new distance range. It is not relocated or regenerated.
- An unfinished old hunt receives one native mission through the recovery
  handler or the notes/Skull Knight interaction.
- An already completed hunt is not reopened and grants no second reward.
- If saved coordinates do not actually identify the lair, they are preserved
  and a specific warning is shown. No replacement is generated automatically.

## User playtest

1. Back up the save. Close the game. Replace the complete `mods/Berserk`
   directory beside `cataclysm-tiles.exe`; avoid keeping another Berserk copy
   in `data/mods`. Install the accompanying graphics mod if normally used.
2. In a new pre-Eclipse story run, finish the rescue. The first-hunt mission
   should appear immediately if a valid forest location is found. Check its
   title, description and map pointer, not just a revealed terrain tile.
3. Check the target distance in OMT. Existing old targets are exempt.
4. Reveal the whole map after assignment and select the mission again. Its
   pointer should remain visible. Switch to another mission, activate the
   notes, then reselect the hunt through the mission menu.
5. Save, quit and load. The mission and its exact target should persist.
   Let the Skull Knight leave; the mission must remain accessible.
6. Defeat the hollow apostle. Verify that the mission enters the completed
   list once, loot is unchanged and the burned-scrap instruction appears.
   Activate the scrap and check the existing breach progression.
7. Load an old save with a marked unfinished first hunt. Check one mission
   pointing to the original lair, with no additional lair or apostle.
8. Load an old save where the first hunt is already completed. Check that no
   unfinished first-hunt mission is assigned and no progression resets.
9. Test a forest-less or fully revealed search area. No mission should point
   falsely to the player. After three failures, automatic retries stop. Move
   at least 24 local tiles and activate the notes to retry.
10. Check English, Russian and Simplified Chinese text and report any new
    debug messages, including the exact mission/coordinate state if possible.

## Static validation

The unit tests exercise data-level assignment, idempotence, completion,
legacy-state migration, failed lookup and bounded retries. Their mission
objects and persisted state are test models, not native game execution.
They do not establish that the native marker renders, the mission survives
real save/load, or the destination is playable. JSON/asset validation and
compiled translation checks are also run before packaging.

## After the prototype passes

| Target | Next work | Proposed distance |
|---|---|---|
| First breach | Mission bound to the stored breach; complete on seal | 6–12 OMT from the first lair |
| Flora | Mission after the first hunt; complete through the agreed dialogue state | 15–30 OMT from the prior story site |
| Count, Wyald, Rosine | Independent native missions using each existing site's coordinates/state | 15–35 OMT; separate lairs |
| Grunbeld | Unlock after the other three breaches are sealed | 25–45 OMT |

Those missions and distance settings are deliberately not added in this
prototype. Several targets span multiple OMTs or have underground sections;
the single-forest-cell replacement must not be copied to them. Exact
placement distance from a saved prior site, minimum separation between
multi-OMT lairs, and a bounded placement scheme require a separate iteration.
Existing direction items and hunting progression remain available meanwhile.

## Exact-tag references

- [Mission format](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/MISSIONS_JSON.md)
- [Target variable, search/replacement and special-placement behavior](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/mission_util.cpp)
- [Direct assignment and completion effects](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp)
- [Mission conditions and completion without an NPC giver](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/mission.cpp)
- [Assignment selects the active mission](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/avatar.cpp)
- [Native mission pointer rendering](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/overmap_ui.cpp)
