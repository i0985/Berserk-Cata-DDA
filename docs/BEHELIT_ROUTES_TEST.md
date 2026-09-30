# New Horizon 3.0: four Behelit routes

Target: **CDDA 0.I-1**. This build was checked statically; CDDA was not run.
This document describes the earlier Behelit-routes milestone. The later
[Count hunt test build](COUNT_HUNT_TEST.md) adds the Count and expands the
cave. Flora and the other named-apostle hunts remain follow-up work.

## Places to test

| Location | Overmap special ID | OMT IDs | Cache / diversion |
| --- | --- | --- | --- |
| Cursed oak | `berserk_cursed_oak_special` | `berserk_cursed_oak` | Roots at (12,12); bone chimes |
| Echo cave | `berserk_echo_cave_special` | Entrance plus four underground OMTs; see the Count test notes | Hollow at (12,5) in the southeastern relic chamber; western stone chimes |
| Desecrated chapel | `berserk_desecrated_chapel_special` | `berserk_desecrated_chapel_reliquary`, `berserk_desecrated_chapel_nave` | Northern reliquary at (12,6); bell in the southern nave |
| Lost expedition camp | `berserk_lost_expedition_special` | `berserk_lost_expedition` | Specimen case at (18,6); southern hand-cranked siren |

Use **the overmap editor's special-placement menu**, not the local-map
mapgen-template menu, to place an entire site. The chapel contains two OMTs
aligned north/south; the cave contains a surface entrance and a 2 × 2 underground area. The special is not a local
mapgen template. Enter the placed site to generate its local map. Test on a
fresh, ungenerated area: overwriting an OMT marker does not regenerate a local
map that already exists in the save. `OVERMAP_UNIQUE` specials should only be
placed once per overmap, including manual debug placement.

The chapel contains a slow Eclipse butcher (450 HP, speed 80), three wretches,
cover and gaps in its west wall. The expedition contains one half-demon
(180 HP, speed 100), two wretches, separate shelters and gaps between them.
These reuse existing enemy definitions and sprites. The inscription and field
log provide local directions. Noise is an attempted distraction, not a
guarantee of a particular monster AI response.

New specials use forest placement and the same occurrence settings as the
existing sites. They have overmap names and symbols when discovered. This
does not add automatic notes for undiscovered sites or repopulate already
generated overmaps. Explore a new overmap for natural placement tests.

## Shared eligibility and compatibility

`EOC_BERSERK_BEHELIT_AVAILABLE` requires all four values to be zero:

- World state `berserk_eclipse_era`.
- Avatar state `u_berserk_eclipse_behelit_spent`.
- Avatar state `u_berserk_eclipse_trial_active`.
- Avatar state `u_berserk_eclipse_rescue_state`.

Missing variables in a pre-event old save retain the existing numeric zero
semantics. Used entry blocks further rewards immediately, before the final
rescue. The world-era check also blocks rewards for another avatar in a world
where the Eclipse has already completed. Existing inventory and ground
Behelits are preserved. This does not retroactively remove earlier loot or
change the existing Behelit's activation handler.

The four cache claims use this condition. Before entry, the corresponding
guardian must be outside an eight-tile radius of the avatar or dead. The
cache's furniture is changed to its empty version on its own OMT, using the
examined object's `pos`; the empty furniture is checked before awarding an
item. An unsuccessful update gives no reward and leaves a retry possible.
Each actual cache stores its own one-time state in furniture; taking one does
not disable the other routes before entry. After entry or completion,
examining an unclaimed cache empties it without awarding a Behelit.

The three projections and three original boss IDs now call a death EOC.
It captures **beta's** position (the dying monster), then selects the avatar
as alpha for the eligibility check. This handles other killers and deaths
without a killer. The Behelit is placed on the ground at the victim's location,
not in the killer's or avatar's inventory. Other drop entries are unchanged.
The two formerly Behelit-only groups remain defined as empty collections to
preserve IDs. The Eclipse Griffith variants keep their rescue/victory EOC and
do not award a new Behelit. Projection death messages no longer promise a drop
when the event has already been used. Hallucinations skip death EOCs in the
0.I-1 `monster::die` implementation.

Relevant upstream references, all at tag **0.I-1**:

- `src/monster.cpp`, `monster::die`: killer is alpha; victim is beta; hallucinations return before death effects.
- `doc/JSON/EFFECT_ON_CONDITION.md`: `test_eoc`, `run_eocs`, `map_furniture_id`, `map_spawn_item`, `mapgen_update`.
- `src/npctalk.cpp`: variable monster-ID filters, preserved context in nested EOCs, and absolute-coordinate mapgen targets.
- `src/item_factory.cpp`: empty collection item groups are loadable.

## In-game acceptance checklist

1. Before the Eclipse, examine each cache with the guardian nearby: no item.
2. Move or lure the guardian beyond eight tiles, or kill it; claim exactly one.
3. Examine again, save/reload and revisit: no second reward at that cache.
4. Visit a different site before entry: it can still provide one Behelit.
5. Check the chapel's shared north/south edge, west-wall route and both camp approaches.
6. Destroy a projection or original boss before entry: one ground Behelit.
7. Have an NPC or another monster kill a boss; also test an unattributed environmental death.
8. Complete the Eclipse, then examine an old unclaimed site and a newly generated one: neither awards a Behelit.
9. Kill each boss/projection after completion: no new Behelit; other loot remains.
10. Check old-save completion flags, translations in English/Russian/Chinese,
    UltiCa and the optional graphics package, and debug.log.

The Python reward-graph tests model these states and data transitions. They
cannot establish engine loading, actual save persistence, AI or gameplay.

## Installation

Extract the archive into `<CDDA>/mods/`, beside `cataclysm-tiles.exe`. Replace
the previous `mods/Berserk` directory rather than overlaying a second copy.
Remove a duplicate `data/mods/Berserk` installation if present; keep saves.

## Planned story order

Behelit routes -> Eclipse -> refuge, Brand, prosthesis and first lesser-apostle
hunt -> Skull Knight's directions to Flora -> peaceful meeting -> armor and
siege/escape -> Count, Wyald and Rosine hunts -> late Grunbeld confrontation.
The latter locations, dialogue and artifact rewards are not implemented here.
