# P1/P2: Flora route and readiness repair

Branch: `codex/3.0-new-horizon`. This package extends the tested P0/R01 build.
It addresses Flora's missing route and missing preparation response; it does
not claim to complete every task in P1/P2. The game binary was not run.

## Confirmed cause in the reference engine

CDDA tag 0.I-1, `src/condition.cpp`, `f_at_om_location`,
`f_overmap_at_point` and `f_near_om_location`, compare
`oter_no_dir_or_connections(terrain)` with the requested string.
`src/overmap.cpp`, `oter_no_dir`, removes `_north`, `_west`, `_south` and
`_east` even when the terrain has `NO_ROTATE`.

Flora's four existing terrain IDs end in `_west` or `_east`. Conditions such
as `npc_at_om_location: berserk_flora_manor_west` and candidate validation
against that same name therefore never matched. These checks could reject
a successfully placed special and hide readiness while the separate armor
gift conditions still allowed the gift.

Mission target lookup uses its own matching mechanism. Its actual terrain
IDs remain unchanged; replacing those with normalized names would introduce
a different error.

## Changes

- Flora's actor/point/nearby conditions compare `berserk_flora_manor` and
  `berserk_flora_garden`. The four terrain IDs, special ID, maps and saved
  coordinates are retained.
- The route search keeps the existing bounded 48/80 OMT searches and global
  uniqueness. A v3 migration gives previously exhausted Flora searches a
  fresh attempt, including saves where the house was placed but rejected by
  the old validation. Other sites' placement and distances are untouched.
- A confirmed saved Flora location is reused. An unconfirmed field coordinate
  no longer counts as a valid house. A later siege stage is not reset by a
  route lookup.
- A manually discovered complete house can register before the main dialogue.
  Neighboring manor/garden tiles determine its northwest origin from any
  quadrant, including negative coordinates. The full 2×2 composition is
  required before manual registration. A Flora monster spawned in an ordinary
  field does not create a house or allow map updates there.
- Readiness checks the player and Flora at the registered home. An unrelated
  second debug-spawned Flora cannot prepare an attack on the original house.
- The main conversation includes a preparation branch that remains available
  after receiving the armor. A refusal explains whether the Eclipse is still
  ahead, the meeting is outside the home, the armor is missing, readiness is
  already confirmed, or the scene is over. No additional apostle kills are
  required for armor or readiness.
- Armor ownership/gift, preparation, activation and completed escape remain
  separate. Existing full/packed armor is accepted; missing pieces are gifted
  once. Preparation gives the charm but starts no fire or attack.
- Eight new strings have Russian and Simplified Chinese translations in the
  source catalogs and compiled catalogs.

## Checks completed without CDDA

- Repository asset validation: 264 JSON files, two mod packages, four compiled
  translation catalogs, tileset references.
- 20 focused definition/state checks: native-style directional normalization,
  candidate acceptance, exhausted-search recovery, mission coordinates,
  registration from all quadrants, invalid/manual placement, existing armor,
  repeated preparation, activation/cancellation and completed escape.
- The old dialogue fixture compared raw terrain IDs and missed this defect.
  It now models the directional normalization in the reference engine.
- The validator rejects directional mod terrain names in these condition
  fields while allowing actual directional IDs in mission target parameters.
- `msgfmt --check` and compiled lookup for all eight new strings.

These checks do not simulate native world generation, AI, UI, or actual
save/load. The player's build is `cdda-0.I-2026-09-19-2324`, not the exact
reference tag. Runtime placement and dialogue remain player verification.

## Focused player check

1. In the existing save, activate the directions to Flora again, or ask the
   Skull Knight. After the first hunt this should register the already placed
   or newly found home and assign its mission to the same coordinates.
2. Reach the home normally. If placing it through debug, place the complete
   special, not only the Flora creature in a field.
3. On the first conversation, inspect the armor and preparation responses.
   Receiving missing armor must not begin an attack.
4. With gifted or previously owned full/packed armor, confirm readiness. Take
   the charm, close the dialogue, and check that the grove is still peaceful.
5. Save/load before activating the charm. Activate it inside the registered
   grove, then verify the existing escape sequence and its one-time outcome.

## Remaining work

Continue the wider P1/P2 audit of old mission bindings, the Skull Knight's
availability and the information/dialogue flow. This repair does not relocate
existing destinations, rebuild visited maps, or change other hunts, the
Eclipse, loot balance or night spawning.
