# Hunt bosses: inner arena entry

Target: **CDDA 0.I-1**. Branch: `codex/3.0-new-horizon`.
The game binary was not executed. Native AI, saved-game loading and actual
visibility still require the user's playtest.

## Implemented behavior

| Encounter | Final OMT | Entry EOC | Existing creature preserved |
|---|---|---|---|
| First hunt | `berserk_first_hunt_lair` | `EOC_BERSERK_FIRST_HUNT_ENTER` | `mon_berserk_hollow_apostle` |
| Local breach | `berserk_local_breach` | `EOC_BERSERK_BREACH_ENTER` | `mon_berserk_breach_warden` |
| Wyald | `berserk_wyald_ring` | `EOC_BERSERK_WYALD_ENTER` | `mon_berserk_apostle_wyald` |
| Rosine | `berserk_rosine_nest` | `EOC_BERSERK_ROSINE_ENTER` | `mon_berserk_apostle_rosine` |
| Grunbeld | `berserk_grunbeld_crucible` | `EOC_BERSERK_GRUNBELD_ENTER` | Knight or existing dragon |

All five maps use a specific central area: local X and Y **8 through 15**,
inclusive. Crossing an OMT boundary or walking around its outside does not
start a fresh encounter. Every movement checks the region. A one-turn
recurring handler covers waiting, loading and movement methods which do not
produce an ordinary walking event. Existing story prerequisites still apply;
Grunbeld still requires the three named breaches to be closed.

First-hunt and local-breach mapgen no longer place the boss in advance.
Support creatures remain. New arena layouts have four walkable recesses,
each screened from the center by opaque rock. Candidate local coordinates
are `(6,6)`, `(17,6)`, `(6,17)` and `(17,17)`.

Before creating a creature, the handler:

1. Checks that this is the registered lair, the hunt is not finished and no
   successful arrival has already been recorded.
2. Searches for the original living boss within 60 local squares in the
   loaded neighborhood. Grunbeld checks the dragon first, then the knight.
   Adoption records the encounter without healing, relocating or replacing
   the creature. A pending dragon transformation cannot start a new knight.
3. Calculates candidate absolute positions from the current OMT origin.
   `overmap_tile: true` only scales offsets in 0.I-1; it does **not** snap a
   position to an OMT origin. Discovery anchors found at the breach furniture
   are normalized by its known `(12,7)` offset. Current-position anchors use
   `floor(pos / 24) * 24`, including negative coordinates.
4. Skips candidates the player can see. Each actual spawn targets one exact
   hidden cell, with `min_radius = max_radius = 0`. Occupied or impassable
   cells are left intact; the next hidden candidate is tried.
5. Commits the successful-arrival flag only in the native success callback.
   Named hunts advance to encounter state 2 only upon success or adoption.

Once present, the boss uses normal AI and can pursue the player out of the
arena. No immobilizing effect, recurring teleport, map reset or HP reset is
used. Leaving and returning never spawns a replacement when an arrival flag
already exists, even if the wounded boss has left the loaded neighborhood.

## Bounded failures and manual retry

There are at most four candidate checks per pass and at most six **placement
attempts** per encounter cycle. Visible candidates do not consume placement
attempts. If all points are visible on an initial approach, a message asks
the player to move behind cover; no visible materialization is forced.

If six placements fail, automatic placement stops and a warning is shown.
Clear a recess and examine **battle-scarred ground** at local `(12,12)` to
reset the failed-placement counter and retry. Existing Wyald/Rosine/Grunbeld
breach interactions retain their retry aliases and pass through the same
inner-area checks. Manual retry does not restart a completed/spawned boss.

The new ground marker has no movement penalty. It also identifies freshly
generated first-hunt/breach maps whose guardians have not existed yet.

## Saved-game compatibility and limits

- All monster IDs, death handlers, progression/reward IDs and existing
  successful-arrival flags are retained. Combat stats are unchanged.
- Already-generated terrain is **not** overwritten to add new screens or
  markers. Test new maps to see the updated recesses. Old named arenas can
  use the new trigger, but their original open layout may leave every
  candidate visible until the player finds cover or darkness.
- Old first-hunt/breach maps previously placed their guardian at generation
  and had no arrival flag. A found living guardian is adopted with its
  existing damage and position, including when it has moved into a nearby
  loaded area.
- If such an old map has neither a new mapgen marker nor a loaded guardian,
  the handler reports that the original must be located and refuses to
  invent a replacement. JSON cannot reliably prove that an unrecorded old
  guardian has not wandered into an unloaded area. This conservative case
  may need save-specific inspection; it deliberately avoids duplication.
- A copied model state tests persistent flags, not native save serialization.
  Searching the loaded neighborhood does not constitute a world-wide scan.
- Bosses may still see/hear and move normally immediately after spawning.
  The guard prevents appearing on a currently visible cell, rather than
  preventing later pursuit or discovery.

## Playtest

Back up the save. Replace the whole `Berserk` folder in `mods` beside
`cataclysm-tiles.exe`; keep one copy and remove an older duplicate from
`data/mods` if present.

For each encounter:

1. Use a new/unvisited arena. Approach from each available side, cross the
   outer OMT boundary and circle outside. The boss must not yet be present.
2. Enter the center along each path in separate tests. Verify one arrival,
   behind cover, and the expected encounter message. Grunbeld first appears
   as a knight when his story prerequisites are fulfilled.
3. Damage the boss, retreat outside the arena, save/reload and return. Check
   the same damaged creature, free pursuit and no new copy.
4. Occupy one recess with another creature/vehicle and retry. Confirm it is
   not overwritten and another hidden point is used. Block all four, check
   the bounded warning, then clear one and examine the central tracks.
5. Test fully exposed candidate points: no boss should materialize in view.
   Move behind cover and confirm the encounter can resume.
6. Kill the boss. Check the original drops/reward, breach closure and
   progression; return/reload/examine tracks and confirm no new boss.
7. For Grunbeld, save during the dragon phase and return. No second knight
   should appear, and dragon HP/progression should persist.
8. Test a legacy map with a living guardian already nearby. Confirm adoption
   without changing its HP. Also test an old first-hunt/breach map whose
   guardian is not loaded: the handler must warn, rather than create a copy.
9. Check English, Russian and Simplified Chinese messages and `debug.log`.

## Automated checks

`tools/test_hunt_arenas.py` exercises all four approaches, absolute/negative
coordinates, saved-target matching, hidden exact-cell placement, occupied
recesses, six-attempt limits, manual retry, legacy adoption, unloaded-old-map
refusal, completed hunts and both Grunbeld states. Connectivity and basic
rock occlusion are checked against the actual map rows. The wider suite also
checks existing hunt progression, rewards, form transitions and translations.

These checks do not replace native vision, combat or save/load tests.

## Exact-version references

- [Movement events](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/game.cpp): `avatar_moves`.
- [Dialogue conditions](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/condition.cpp): `u_can_see_location`, furniture/OMT checks.
- [Dialogue effects](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp): location searches, absolute offsets, exact-cell spawn and success callbacks.
- [Tripoint expressions](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/math_parser.cpp): location `.x`, `.y`, `.z` members.
