# Eclipse: arrival-field visual prototype (0.I-1)

The existing six-OMT destination, story IDs, monster groups, and completion
conditions are unchanged. Only the **northwestern arrival OMT** gets a test
composition. Its east side now has staggered ridges: the straight sightline
from the arrival scar to the eastern edge is blocked, while northern and
southern routes stay walkable. This does not guarantee that monsters elsewhere
will stay put: they can hear combat, wander around a ridge, or enter the loaded
area. The six OMTs together are only 48 by 72 map squares.

The arrival palette has ash, trampled flesh, and three faint veins instead of
the old 80-strength light tile at the landing. The old light tile elsewhere is
untouched so we can compare the look before changing every area. The ash uses
UltiCa's `t_dirt` art for now; the other new surfaces reuse existing flesh art.
Their final art can be supplied as mod tiles without changing mapgen IDs.
Walls now use a mod-specific terrain ID copied from the same flesh wall, which
allows a separate ridge sprite later without replacing the vanilla wall art.
Characters can walk across all new floor variants at the old movement cost.

## Sprite checklist for the artist

Draw **one 32 × 32 tile per map square** for the base set, matching the current
UltiCa perspective and anchor. A 64 × 64 image assigned to one 32 × 32 tile
will be scaled down. To depict a larger shape, draw adjoining 32 × 32 pieces
and place them across a 2 × 2 or 3 × 3 block of map squares.

| Priority | Subject and intended ID | Size and variants | Notes |
| --- | --- | --- | --- |
| 1 | Living ground `t_berserk_eclipse_open_flesh` | 32 × 32; 3 subtle variants | Base terrain, no sharp repeated seam. Currently uses vanilla flesh art. |
| 1 | Ash `t_berserk_eclipse_ashen_flesh` | 32 × 32; 2 variants | Walkable gray surface, visible against living ground. Currently uses vanilla dirt art. |
| 1 | Trampled path `t_berserk_eclipse_trampled_flesh` | 32 × 32; 2 variants | Worn route through the field; same movement cost as base. |
| 1 | Dim vein `t_berserk_eclipse_dim_vein` | 32 × 32; 2 variants | A faint visual pulse. The engine currently emits ordinary white light at strength 15. |
| 1 | Flesh ridge `t_berserk_eclipse_ridge` | 32 × 32 edges, corners and tips | Opaque obstacle. Draw adjoining pieces so the ridge reads as a single fold. |
| 2 | Pit `t_pit`, corpse pit `t_pit_corpsed` | 32 × 32 edges and center | These are dangerous tiles; distinguish their hazard from harmless ash. Dedicated mod IDs may follow when the art is ready. |
| 2 | Arrival scar `f_berserk_eclipse_arrival_scar` | 32 × 32 | The one-way entry landmark. Never obscure its examine target. |
| 3 | Distant altar silhouettes, wrecks, bodies and feast details | 2 × 2 or 3 × 3 compositions, each piece 32 × 32 | Plan after encounter layout; these are not yet assigned new terrain IDs. |

Do not paint a graphic into the underlying character sprite. Furniture,
terrain and creature sprites are separate overlays, and the ground should
remain readable under a creature.

## Light and size follow-up

In this game's 0.I-1 `lightmap.cpp`, terrain's `light_emitted` is passed as a
single luminance number to `add_light_source`. The terrain's `color` is the
appearance/ASCII color, not the emitted light color. This prototype tests
ordinary light only. Colored light needs a separate exact-version engine
prototype; do not imply a red light based on a red terrain sprite.

For a larger Eclipse, evaluate a **new, versioned 3 × 4 OMT special** rather
than stretching the current six-OMT special in place. That yields 72 × 96 map
squares and gives room for a landing, two routes through the fallen band, a
staged feast, a quiet approach and a ceremony. Keep the existing OMT IDs and
old special available for saves already inside the six-OMT field; add new IDs
for connecting sections and update every location check in the entry, rescue
and victory EOCs. First test line of sight, monster hearing and aggro boundaries
on one new section. Merely increasing area without sight breaks may still
produce a single pursuing mob.

## Player check

1. Back up the save. Enter a *newly generated* Eclipse with a Behelit; an
   already generated Eclipse keeps its old local maps.
2. At the arrival scar, compare the ash/path/flesh and the three small light
   pools against the brighter, old lighting in later OMTs. Check in UltiCa and
   in the optional graphic mod.
3. Walk both sides of the new ridges. Verify that a direct sightline east from
   the scar is broken and that the passage to the gallery and southern route
   are still open. Observe whether any monster can already see or hear the
   player on arrival.
4. Check that the original four bodies, Griffith, rescue and return still work
   during a complete run; report any debug messages. Static checks do not
   simulate these interactions.
