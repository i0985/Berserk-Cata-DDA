# Eclipse: loss of hand and eye before the final fight

Target: CDDA **0.I-1**. This change is in `codex/3.0-new-horizon` only.
The game executable was not run. The checks below still require a playtest.

## Encounter

1. Enter the expanded ceremony area. The existing mobile Griffith ID is
   spawned near the original local position `(15, 17)`, with a one-cell
   fallback if that exact cell is occupied.
2. Immediately apply permanent `berserk_eclipse_griffith_waiting`. Its flags
   `CANNOT_MOVE` and `CANNOT_ATTACK` prevent walking, melee and special attacks.
   This is an effect on the actual creature; it persists during waiting and
   does not require replacing the boss or resetting his HP.
3. Approach within three map squares on the same level, where Griffith can
   see the player. Movement events check this immediately; a one-turn handler
   supplies a fallback after loading or waiting.
4. A one-time handler attempts to populate each of the eight adjacent cells:
   six Eclipse wretches and two Eclipse half-demons. Each attempt targets one
   exact cell with radius zero. These are real creatures with normal behavior
   and drops. Walls, pits without a floor, vehicles and occupied cells are
   subject to native placement rules; the handler never overwrites them or
   moves the new creatures farther away to make space. On unobstructed ground
   this produces a full ring. Existing occupants can leave a gap in the ring.
5. Show a modal story message about Griffith, rage, the demons' grip and the
   wounds incurred while breaking free. The game does not advance turns as
   part of these scripted effects. This is a text scene and real surrounding
   creatures, rather than a new grabbing AI or animation system.
6. After dismissal, install missing-hand and lost-eye bionics immediately,
   then apply the existing missing-hand body effects before releasing Griffith.
   Perception is halved by the existing lost-eye enchantment. No scripted HP
   loss, bleeding or additional blood withdrawal is added by this scene.
7. Remove only the custom waiting effect from Griffith. Resume normal combat
   using his existing stats, HP and death handler.
8. Existing low-health and death prevention rescue handlers become applicable
   once this final fight begins. The Skull Knight's stabilization, return,
   Brand, recipe unlocks and world-era transition retain their existing flow.

## State and compatibility

| State | Meaning |
|---|---|
| `u_berserk_eclipse_final_spawned = 1` | Griffith is present and waiting |
| `u_berserk_eclipse_grasp_state = 0` | Approach scene not performed |
| `u_berserk_eclipse_grasp_state = 1` | Ring/message sequence in progress |
| `u_berserk_eclipse_grasp_state = 2` | Wounds committed; scene cannot repeat |
| `u_berserk_eclipse_final_started = 1` | Final combat/rescue zone active |
| Existing rescue state 1 / 2 | Rescue underway / completed |

The scene marks itself in progress before spawning the ring. A recovery
handler for state 1 applies wounds and releases Griffith without making a
second ring or repeating the popup. Normal saves cannot be made inside the
modal message, but this makes the intermediate state safe to resume.

The shared wound handler checks for each bionic before adding it. An existing
missing hand, lost eye or arm cannon is preserved. Four message variants
avoid narrating the same limb loss twice. The aftermath also calls the shared
handler, so it does not duplicate these wounds and remains a fallback for
legacy maps, an earlier rescue or victory without the approach scene.

All existing monster, bionic and mapgen IDs are retained. The old
`berserk_eclipse_griffith_on_entry` update remains defined for compatibility;
the new entry path spawns directly so its immediate callback can pause the
actual creature. Already active fights in old saves are not frozen or
restarted. The new scene is for the expanded ceremony map, not the retained
legacy six-OMT map.

Spawning Griffith can retry at most three times before a warning. Leaving
and re-entering the ceremony resets that bounded placement cycle. A failed
placement never marks the fight as started or applies the player's wounds.

Griffith can still be attacked from outside the three-cell trigger distance;
this change does not give him invulnerability. A ranged early kill keeps the
existing victory-and-rescue fallback, with wounds applied in the aftermath.
This exception should be considered separately if mandatory scene activation
is later desired for every combat approach.

## Playtest

Back up the save and replace the whole `Berserk` folder under `mods` beside
`cataclysm-tiles.exe`. Keep one copy of the mod; remove an older duplicate in
`data/mods` if present. Use a new Eclipse encounter or a save from before
entering the final area. An old already active Griffith fight intentionally
keeps its old behavior.

1. Enter the ceremony and wait away from Griffith. Verify he neither walks
   nor uses an aura/special attack, and the player has no new wounds yet.
2. Save and reload while he waits. Confirm one Griffith and the same position.
3. Approach on open ground. Verify one popup, eight neighboring creatures,
   lost hand and lost eye in the bionics menu, immediate hand/grip limitations
   and reduced Perception after dismissal.
4. Verify that he walks and attacks after the popup. Check that his sprite
   and HP have not been replaced/reset as part of release.
5. Save and reload during combat, leave/re-enter the ceremony and approach
   again. No second ring, popup or duplicate bionics should appear.
6. Try the scene with an existing missing hand, existing eye injury and an
   installed arm cannon. Verify the appropriate message and retained cannon.
7. Try an occupied neighboring cell, obstacle and narrow passage. No ally
   should be deleted, no demon should spawn inside a wall, and failed ring
   placements should not be retried on subsequent turns.
8. Check a normal rescue, critical head/torso health, a lethal blow and victory
   over Griffith. After return, check one set of wounds, Brand and recipes,
   the existing first-hunt mission and no new startup/debug errors.
9. Check English, Russian and Simplified Chinese messages and the waiting
   creature's effect description.

## Checks performed without the game

Data-level regressions exercise waiting, actor scopes, the full ring,
occupied-cell handling, popup/wound/release ordering, duplicate guards,
intermediate-state recovery, legacy combat and bounded boss-placement failure.
The test model uses a copied state to check persistence logic; it does not
read/write a native save or prove native AI, rendering or survival behavior.
JSON/assets, EOC references, compiled translations and the release archive
are checked separately.

## Exact-tag implementation references

- [Monster movement and attack guards](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monmove.cpp): effect flags `CANNOT_MOVE` and `CANNOT_ATTACK`.
- [Monster flags and effects](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monster.cpp): generic JSON flags can be supplied by active effects.
- [Dialogue effects](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp): permanent effects, spawn `target_var`, callbacks and monster EOC actor scope.
- [Spawn legality and movement events](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/game.cpp): `avatar_moves` and bounded `find_nearby_spawn_point`.
