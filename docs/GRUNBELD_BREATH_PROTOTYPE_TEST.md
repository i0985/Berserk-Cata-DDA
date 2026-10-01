# Grunbeld: fixed-target dragonfire prototype

Target: **CDDA 0.I-1**. Branch: `codex/3.0-new-horizon`.
No game binary was run. This is the first attack prototype, awaiting native
playtesting before its approach is extended to other bosses.

## Behavior

| Stage | Behavior |
|---|---|
| Select | Dragon chooses a hostile creature on its own floor, within six squares |
| Prepare | Stores that creature's absolute cell and its own origin; marks the narrow line; cannot move or attack |
| Release | After three seconds, casts one heat attack toward the stored cell; aim does not follow the victim |
| Recover | Three seconds without movement or attacks, then normal AI resumes |

The line goes from the dragon to the originally selected cell, **up to six
squares**, rather than automatically extending six squares past a nearby
target. Source cell is excluded. Native line spells stop at impassable
obstacles. Walking sideways off the marked line, beyond its endpoint, or
behind suitable cover should avoid the jet. Moving nearer the dragon while
remaining on the marked line can still be hit.

Damage is **36 heat before native defenses**, with spell accuracy 10, rather
than a guaranteed 36 HP loss. Every creature occupying the affected line
can be hit, including incidental bystanders. The strike does not target the
victim object again after preparation.

The native special-attack cooldown remains 24 seconds from a successful
preparation. The saved per-dragon cooldown also forbids preparation for
18 seconds after release/cancellation. Whichever restriction still applies
blocks another preparation. Waiting/saving does not reroll a saved aim.

## Visual prototype

- A harmless custom field marks the threatened line, with `fd_laser` tile
  fallback and a red `*` in ASCII. The dragon's inspected effect also explains
  its fixed aim. The warning is more than a combat-log line.
- The released line produces the native heat-colored spell animation and a
  short custom flash using `fd_fire` tile fallback. One combat sound comes
  from the dragon.
- Both custom fields decay and have no field damage, spread, movement penalty
  or fire processor. All heat damage is applied once by the release spell.
  A fading flash is **not** a persistent fire or a second damage source.
- No `fd_flame_burst` is spawned: its 0.I-1 native processor changes it into
  `fd_fire_vent`, which would create an unintended ongoing hazard.
- Normal completion/cancellation clears only the warning field, within six
  squares of the recorded origin. Other fires and terrain are not removed.
  If the dragon dies and its actor is no longer processed, the warning
  decays automatically after its protected lifetime (approximately five
  seconds from placement in the loaded area).

Tiles, contrast, spell animation and real player readability still need to
be checked in UltiCa and with the chibi addon. The laser fallback is a
temporary marker, not a newly drawn final breath sprite.

## Implementation and exact-tag findings

The attack uses `attack_type: "spell"` in
`monster_special_attacks/grunbeld_attacks.json`, selecting a zero-damage
control spell. `"spellcasting"` is not an accepted actor name in the
[0.I-1 monster attack factory](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monstergenerator.cpp).
The old heat-melee strike ID remains defined but is disabled and removed
from the dragon's active attack list. Knight/other bosses' attacks are
unchanged.

The control spell runs `EOC_BERSERK_GRUNBELD_BREATH_BEGIN`. In
[spell effect EOCs](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/magic_spell_effect.cpp),
**alpha is the victim and beta is the caster**. Preparation therefore saves
state on `npc_val`/the beta actor. Math uses `n_*` for this actor, whereas
JSON effect/variable keys use `npc_*`. During a monster tick that same
dragon is alpha and its stored values are read as `u_*`.

Persistent per-monster values store phase, origin, target, due time and
cooldown. Monster/Creature save code serializes values and effects in
[savegame_json.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/savegame_json.cpp).
Native save/reload has not been exercised here.

Monster actors cannot queue delayed EOCs through `run_eocs` in this tag.
A global one-second watcher scans only loaded dragons within 48 squares of
the player. Before firing it checks positive HP, complete saved coordinates,
the preparation effect, unchanged origin, and a due-time window. It cancels
an expired or displaced preparation rather than redirecting it. A dragon
which left the loaded neighborhood cannot release a stale shot on return.
An old save's preparation effect without the new state is cleared harmlessly.
A pending state cannot be overwritten by a new preparation before cleanup.

The nominal preparation is three seconds; scheduler/effect-processing order
can defer resolution to the next one-second check. An effect expires after
four seconds, and anything later than the allowed window cancels. Stage 0
is committed **before** casting, preventing damage callbacks from releasing
the same shot again.

Movement/attack locks use `CANNOT_MOVE` and `CANNOT_ATTACK`, checked by
[monmove.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monmove.cpp).
External displacement can still interrupt the preparation. Recovery has
the same bounded locks, making the counterattack window meaningful.

Preview and release spells share line shape, zero extra width, range and
ground targets. Neither ignores walls. The target is a saved cell passed to
`u_cast_spell`/`npc_cast_spell` with `targeted: false`, not a new UI selection
or current creature location. The control spell uses `NO_PROJECTILE` so a
visible target behind glass does not substitute a ground cell for the
victim EOC; the actual preview/release line still respects obstacles.

## Verification and limits

- **180 tests passed; 218 JSON files validated.** New cases cover fixed aim,
  delay, single release, displacement/death, late reentry, expired effect,
  legacy/missing state, independent dragon state, saved negative coordinates,
  a cardinal-line wall model, cooldown, finite visual fields and actor order.
- EN originals and compiled RU/zh_CN translations are updated. `msgfmt
  --check`, translation coverage and `git diff --check` pass.
- The repository validator now rejects unsupported attack actor names,
  missing spell_data IDs and common math actor-scope mistakes. It remains
  a static validator, not a replacement for the game's JSON loader.
- Geometry tests model cardinal lines. Native diagonal rasterization, glass,
  vehicles, all defenses and actual player/NPC damage need live testing.
- The prototype is for one named dragon encounter. Monster state is separate
  per actor, but warning fields have no owner. If debug-spawned dragons charge
  nearby simultaneously, one cleanup can remove another's overlapping
  markers. Do not extrapolate this visual-marker system to a crowd of bosses
  without addressing that limit.
- HP, armor, normal melee, form changes, rewards and hunt progression retain
  their existing definitions. A new attack's timing/geometry still changes
  practical difficulty; damage and timing may need tuning after playtesting.

## Home playtest

Back up the save and replace the whole `Berserk` folder in `mods` beside
`cataclysm-tiles.exe`. Keep a single copy; remove an old `data/mods/Berserk`
duplicate if present. Existing locations can use the updated dragon attack;
no fresh map generation is required for this prototype.

1. Debug-spawn **Grunbeld, flaming dragon** (`mon_berserk_grunbeld_dragon`)
   in an open test area, separately from the full hunt. Start 4–6 squares away.
2. Confirm a warning line appears before any damage. Inspect the dragon's
   preparation effect. It should pause instead of chasing or using melee.
3. Remain on the line once to confirm heat damage and visible flame. Repeat
   with a one-square sideways step: the beam must remain aimed at the old cell
   and miss your new cell. Test a diagonal line as well.
4. Put an intact impassable wall/glass/vehicle obstacle between you and the
   dragon. Check which obstacles the native line blocks; report exceptions.
5. During recovery confirm a short opening to move/attack, then ordinary
   pursuit and attacks resume. Verify no early second breath.
6. Save during preparation, reload, and check original aim and one release.
   Kill or displace the dragon during preparation: no delayed heat shot.
   Leave the neighborhood and return later: no stale surprise strike.
7. Check warning disappearance, no fire vents or endlessly spreading fire,
   UltiCa/chibi, English/Russian/Chinese strings, and `debug.log`.
8. Finally repeat in the real stronghold and check knight-to-dragon conversion,
   relic reward and breach completion still behave as before.

Acceptance: the player can identify the threatened cells, move out in time,
and actually avoid the attack. Only after that check should Count/Wyald/
Rosine/knight attacks adopt this pattern.
