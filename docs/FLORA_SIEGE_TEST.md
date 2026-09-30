# Flora's siege and escape — 3.0 test milestone

Target: **CDDA 0.I-1**. Branch: `codex/3.0-new-horizon`.
Parent checkpoint: `a929dbabcf646aa380ecd36fcb17812ea4be9894` (peaceful Flora).

This is an untested-in-game continuation of the peaceful manor. Static checks
are not native JSON loading, AI combat, rendering or game save/load tests.
No game executable was launched.

## Player sequence

1. Find Flora after the Eclipse/first hunt and finish any peaceful questions.
2. Choose **“I am ready to accept the armor and face the attack.”** Read the
   warning and explicitly accept the armor and escape charm.
3. Missing armor pieces are issued through the existing one-time gift handler.
   Existing complete/packed suits are retained without duplication. The manor
   remains peaceful during equipment and inventory preparation.
4. Activate **Flora's escape charm** while standing on one of the four manor
   OMTs. A separate confirmation starts the attack. Cancelling does nothing.
5. Two stationary friendly root guardians appear at the north/east approaches.
   Smoke appears at two northern room points. Western and southern house doors
   are opened by targeted updates; pale path markings lead out of the grove.
6. After 30 game seconds, Zodd arrives from the north and Grunbeld from the east.
   They can move and fight; they are not invulnerable or required kills.
7. After 90 game seconds, ward-bound embers appear and one eastern wall tile
   opens. Both intended exit routes remain structurally passable.
8. Move beyond the grove and its eight-tile margin. The world records escape,
   replaces the registered manor with charred floor/walls and a broken ward,
   and ends the sanctuary's protection. Re-entry cannot restart the attack.

Normal inventory/dialogue UI pauses do not themselves constitute a timed scene.
Before charm activation, **no siege clock runs at all**, even if inventory
actions consume time. After activation, actions that consume game time advance
the siege. Flora then offers an urgent escape line instead of further lore.

Fast escape before the 30-second wave is allowed: later waves do not spawn at
the escaped player's position. There is no overall timeout, forced teleport,
automatic victory, or additional death prevention in this encounter.

## Deliberate scope of the first version

The ember furniture emits ordinary light and smoke uses vanilla `fd_smoke`.
There is **no spreading `fd_fire`**. The charring/collapse is scripted; it does
not burn loose gear, detonate ammunition or randomly seal exits. This is an
intentional controlled visual representation of the fire, not CDDA combustion.
Smoke can still reduce visibility and be hazardous; it is placed away from the
initial armor handover point and exit doors.

Zodd uses his existing art/stats/special attacks (600 HP, speed 110, no regen).
Grunbeld is the armored siege variant (850 HP, speed 80, 3d8 + 24 bash base
attack, bash/cut/heat armor 16/24/12, no regen). It temporarily uses the Eclipse
butcher's sprite through `looks_like`. His dragon phase and separate late hunt
are outside this milestone. Root guardians use the existing oak guardian art,
280 HP, stationary movement, and no special attacks. Faction hostility is set
both ways between the attackers and guardians; friendly spawns do not target
the player or player companions. Actual AI targeting needs game verification.

Flora and temporary guardians are removed from the ruined scene when loaded;
the cleanup never deletes surviving apostles. A distant teleport is handled
by cleanup on return, rather than assuming all actors were loaded at escape.
Survivors may pursue the player and remain in the world. Leaving by another
edge or teleporting away also resolves the abandoned manor. This is not a
scripted protection from pursuit, damage or death.

## Original deaths and compatibility

Persistent world facts:

- `berserk_apostle_zodd_dead = 1` for the original Zodd or siege Zodd's death.
- `berserk_apostle_grunbeld_dead = 1` for the siege Grunbeld's death.
- `berserk_hunt_grunbeld_state >= 3` and the death OMT are registered for a future
  hunt/breach resolution. This does not silently seal a breach (`state 4`).
- Grunbeld's optional kill yields the existing Flaming Carapace Shard group.

The death handlers do not depend on the killing actor: player, companion,
monster and environmental/no-killer death all record the same original death.
The old Zodd's Behelit callback is retained through a wrapper; it still checks
global Behelit availability. Projections explicitly keep their original
callback and **do not** mark the originals dead.

The siege and old Zodd challenge check the death registry before spawning an
original. A nearby old Zodd is reused instead of spawning a second siege copy.
Already instantiated originals in old saves are not retroactively erased.
Any future Grunbeld/Zodd location or hunt must honor these world death facts;
this milestone does not implement a new complete dragon hunt.

Separate persistent scene states:

| `berserk_flora_siege_state` | Meaning |
| --- | --- |
| 0 / missing | No readiness decision |
| 1 | Prepared; no attack clock |
| 2 | Warning/guardians; clock started |
| 3 | Apostles attempted; spawn callbacks mark actual success |
| 4 | Charring and eastern breach |
| 5 | Escape committed; cannot restart |

`berserk_flora_stage` keeps its established 1=peaceful, 2=siege, 3=ruins meaning.
Existing gift/profession/equipment IDs remain. Neither curse nor armor defensive
stats, Berserk duration/cost/cooldown, weapon stats, or bionic definitions change.
The sanctuary suppresses unrelated era/Brand additions during its own siege,
then stops suppressing them after escape. Armor shadows remain separate.

Failed boss placement retries at ten-second intervals, at most six attempts per
boss, with a warning on final failure; escape never requires a successful spawn.
Successful spawns and recorded deaths cannot be retried into duplicate bosses.
The charm can be replaced by Flora during preparation if the player loses it;
replacement does not issue armor again.

## Source checks at the exact tag

Read alongside `doc/JSON/EFFECT_ON_CONDITION.md`, `doc/JSON/MAPGEN.md`, and
`doc/JSON/MONSTERS.md` in `CleverRaven/Cataclysm-DDA` **0.I-1**:

- `src/npctalk.cpp`: spawn target variables, friendly flag, success/failure
  EOCs; mapgen update target coordinates; monster EOC actor switching.
- `src/monster.cpp`: death EOC alpha is the killer or null, beta the victim;
  friendly/faction attitudes.
- `src/mapgen.cpp`: fields use **integer age in turns**, not a duration string;
  point/square terrain setters and item-preserving mapgen flags.
- `src/mapdata.cpp`: furniture `required_str`, `move_cost_mod`, light emission.
- `src/monfaction.cpp`: inheritance and bilateral hate/friendly definitions.

Updates are anchored to the stored manor coordinates, never to the current
player OMT. They preserve items/traps/furniture except for explicitly replaced
ward/ember tiles. CDDA mapgen update can cancel on vehicle collision and offers
no success callback here; native vehicle/appliance collision and partial updates
remain an explicit game-test risk. Do not park vehicles on the handover, smoke,
collapse or marked path tiles during the first test.

## Static verification

Run:

```sh
python tools/validate_mod_assets.py
python -m unittest discover -s tools -p 'test_*.py'
python tools/package_release.py
```

The new data interpreter tests guarded readiness, inventory preparation delay,
cancelled activation, missing charm replacement, phase timing, duplicate/retry
limits, escape from both sides and distant teleport, absolute update targets,
state persistence by object copy, original vs projection deaths, inherited
Behelit reward and compiled English/Russian/Chinese strings. Layout checks
apply each patch and verify both routes from the armor handover point. These
checks do not simulate native saves, smoke spread, damage, pursuit or rendering.

## Game checklist for the user

Install by replacing the entire `mods/Berserk` beside `cataclysm-tiles.exe`.
Remove any second `Berserk` in `data/mods`. Keep a backup of your test save.

1. Load an existing post-Eclipse save. Recall Flora's directions. At a peaceful
   manor, verify all old questions still work and readiness has a warning.
2. Test a partial suit and a full/packed suit. Only missing parts should be
   handed over; existing gear must stay in place. Prepare equipment and wait
   several minutes: there must be no attack before charm activation.
3. Activate the charm, first cancel, then confirm. Watch the popup, guardians,
   northern/eastern approaches, smoke, doors and path markings.
4. Stay for 30 and 90 seconds in separate tests. Confirm moving apostles and
   staged charring; verify neither exit was replaced with an obstacle.
5. Escape once through each route on separate backup saves. After the popup,
   return: the manor should be charred, Flora unavailable, the ward inactive,
   and the charm unable to restart. Survivor pursuit is allowed.
6. Save/load while prepared, during warning, after boss arrivals and after
   escape. Check that clocks, rewards, bosses and aftermath do not duplicate.
7. On a disposable debug test, kill each apostle. Confirm Grunbeld drops the
   shard, remains dead after load, and no replacement appears. Separately kill
   a projection: it must not count as original death.
8. Check UltiCa/chibi fallback art, both languages, companions/guard hostility,
   smoke visibility and any new `debug.log` errors. Report the first error and
   the phase where it happened.

## Not verified in native play

Game JSON load; actual actor count/placement; smoke duration/spread; guardian
AI delay; difficulty and pursuit; vehicle collision cancellation; native
save/load transition behavior; off-bubble map updates and actor cleanup;
UltiCa/chibi rendering and glyph/light appearance. No PR or main merge.
