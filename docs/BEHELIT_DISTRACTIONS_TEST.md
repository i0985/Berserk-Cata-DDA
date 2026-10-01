# Behelit sites: delayed distractions

Target: **CDDA 0.I-1**, branch `codex/3.0-new-horizon`.
The game binary was **not executed**. This is a build for native playtesting,
not a claim that all four guardians have followed the devices in game.

## Source findings

The existing `u_make_sound` calls already used the examined device's absolute
cell, not the avatar's cell. Furniture examination sets context `pos` in
[iexamine_actors.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/iexamine_actors.cpp).
`f_make_sound` reads it through `target_var` and calls the real game sound
system in [npctalk.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp).
There is no soundpack sample ID in this call. An absent speaker sound does
not establish that no monster-hearable noise occurred.

All four original guardians have `HEARS`. However, the oak/cave guardians
and the original butcher/half-demon lacked intelligent sound pathfinding.
In [monmove.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monmove.cpp),
the pathfinding sound branch requires `has_intelligence()`; otherwise the
sound fallback uses simpler movement. `has_intelligence()` in
[monster.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monster.cpp)
includes `path_settings.avoid_traps`. The previous hanging-chime furniture
was also impassable, although sound seeking uses the source cell as its
destination. These are confirmed constraints of the old definitions, not
a reproduced diagnosis of the user's exact encounter.

Monster sound distance in [sounds.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/sounds.cpp)
uses XY distance and vertical attenuation, rather than tracing a route
through walls. Weather, other noises, hostility/morale and visible enemies
also affect the result. Solid cover blocks sight and can obstruct movement;
it does not automatically mute sound for monsters.

## Implemented

| Site | Sound volume | Placement and cover |
|---|---:|---|
| Cursed oak | 45 | Chimes at local `(1,22)`, away from the root cache; rock screen and open routes around it |
| Echo cave | 65 | Two independent western chimes at `(4,10)` and `(9,19)` in the southwest OMT; rock screens before the eastern chamber |
| Desecrated chapel | 65 | Bell remains at `(6,15)` in the southern nave; partial screen and an additional west-wall breach |
| Lost expedition | 45 | Siren remains at `(4,20)`; four canvas tents with open flaps replace houses; tent cover between guardian and siren |

Each device now:

1. Transforms only its own cell from idle furniture into its armed variant.
2. Captures the examination cell and activation floor in queued EOC context.
3. Queues exactly four activation pulses at **20, 35, 50 and 65 seconds**.
4. Produces a real, non-ambient `alarm` at that captured cell, provided the
   player remains on that floor and within 48 squares, and the armed device
   still exists there. Destroying the device suppresses subsequent pulses.
5. Rejects repeated winding while armed. The two cave devices are independent.
6. Returns to idle at 90 seconds through a native world `TRANSFORM_RADIUS`
   timed event. In this tag a delayed `u_transform_radius` adds one second;
   the JSON specifies 89 seconds to give a 90-second total. The timed event
   survives loss of the activating character and can update an offscreen
   submap. Only matching armed furniture is replaced: destroyed or replaced
   devices are not resurrected.

Pulse EOCs are finite, not recurring. If a pulse is skipped after leaving
the floor or neighborhood, it is not replayed upon return. Native queued
EOC context and world timed events are serialized by the game's save code.
Actual native save/reload still needs a playtest.

All four sound cells are walkable. The hanging bones and stones no longer
make an impassable destination. Guardians have `max_dist: 64`,
`max_length: 320`, and `avoid_traps: true`, enabling bounded native pathfinding
around cover. The chapel and expedition use **map-only inherited variants**:
`mon_berserk_chapel_guardian` and `mon_berserk_expedition_guardian`. Combat
stats and sprites come from their existing butcher/half-demon bases. The
roaming base monsters are unchanged.

No effect forces a guardian to abandon a visible enemy, teleports it to the
device, or immobilizes it. Once native sound-seeking memory expires, ordinary
AI continues; this does **not** promise a return to the relic or immediate
forgetting at the last pulse. Other combat noises can compete with the lure.

Descriptions and the chapel/camp records explain hiding and delayed sounds.
English originals, Russian and Simplified Chinese catalogs are included.
Behelit availability, post-Eclipse restrictions and relic coordinates stay
unchanged. Claim checks recognize both new variants and original saved
guardians, so an old living guardian cannot accidentally grant a free relic.

## Compatibility and limits

- Existing IDs and saves are retained. Oak/cave guardian definitions gain
  pathfinding in existing maps as well as new ones.
- Already-generated layouts are not rebuilt. Old chime positions, house
  walls and missing screens remain until a fresh site is generated.
- Original butcher/half-demon guardians in old chapel/camp maps are preserved;
  they do not automatically become the new pathfinding variants.
- Rock screens and tents are opaque in their normal definitions, but this
  test build has not verified native visibility, tent rendering, chase
  timings, hearing through every seam, or AI priorities in live combat.
- Initial line screens, walkable routes and timer persistence were checked
  geometrically or with a model. Such tests do not simulate native mapgen,
  sound clustering, AI, or loading the user's save.
- No guardian-specific forced response was added. First test native delayed
  sound plus pathfinding; introduce a special reaction only if needed.

## Verification performed

- **167 tests passed**, including finite timing, blocked repeat activation,
  independent cave devices, copied source coordinates, model reload,
  destruction, remote/floor pulse suppression, native reset contract,
  guardian inheritance and legacy relic protection.
- **215 JSON files** passed `tools/validate_mod_assets.py`.
- All maps remain 24 x 24. Stitched cave/chapel routes connect guardians,
  devices and cache approaches. Sources are outside the relic's eight-square
  guard radius in the geometric default-distance check; initial direct
  source-to-guardian lines cross a solid screen.
- `msgfmt --check` and compiled RU/zh_CN coverage passed.
- `git diff --check` passed. Package contents are checked against source bytes.

## Playtest at home

Back up the save. Replace the whole `Berserk` folder in `mods` beside
`cataclysm-tiles.exe`, keeping one copy. Remove an older duplicate from
`data/mods` if present. Use newly generated sites for changed layouts and
the new chapel/camp guardians; old maps intentionally retain their geometry.

For each site:

1. Find the device by examining furniture: hanging bone chimes, loose stone
   chime, cracked chapel bell, or wind-up emergency siren. They use furniture
   examination, not activation of an inventory item.
2. Wind it before the guardian sees you, then leave the device and hide behind
   the nearby rock, chapel wall, or tent. At 20 seconds confirm the sound
   belongs to the device's original cell, not your new location.
3. Without revealing yourself, watch whether the guardian follows it around
   cover. Try the alternate approach to the cache while it investigates.
4. Repeat while deliberately staying visible. The guardian should retain
   normal combat priorities, not magically forget you.
5. Try winding it twice: no overlapping sequence. Four sounds finish at
   65 seconds; winding becomes available again at 90 seconds. AI may keep
   investigating after the sound sequence ends.
6. Save after winding but before 20 seconds, reload, and check source/timing.
   Destroy another armed device: later pulses should stop and it must not
   reappear. Leave the area or use stairs: skipped pulses must not replay,
   and the device must become idle by the end of its cycle.
7. Check UltiCa/chibi appearance, all three languages, cache interaction,
   one-time Behelit pickup, post-Eclipse refusal, and `debug.log`.

If a hidden-player test fails, record site, guardian name, source coordinates,
cover, competing sounds and whether the creature moved toward the source,
got stuck, or pursued something else. Those observations determine whether
a special guardian response is necessary.
