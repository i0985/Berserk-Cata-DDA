# New Horizon 3.0: encounter registry (step 1)

The pre-Eclipse routes distinguish physical projections from the established
monsters. Keep all established IDs intact so monsters already present in saves
and scenario encounters remain loadable.

| Role | ID | Source | Outcome |
| --- | --- | --- | --- |
| Zodd projection | `mon_berserk_projection_zodd` | Rare `GROUP_NETHER` roll in vanilla microlab rooms | No corpse; one Behelit |
| Griffith reflection | `mon_berserk_projection_griffith` | `GROUP_NETHER`; also the once-per-day armor EOC's 1/100 attempt | No corpse; one Behelit |
| Void reflection | `mon_berserk_projection_void` | Rare `GROUP_NETHER` roll in vanilla microlab rooms | No corpse; one Behelit |
| Original Zodd | `mon_nosferatu_zodd` | `berserk_pursuer` scenario; existing saves | Original drops and behavior |
| Original Griffith | `mon_griffith_reborn` | `berserk_griffith_confrontation` scenario; existing saves | Original drops and behavior |
| Original Void | `mon_void_apostle` | `void_apostle_confrontation` scenario; existing `EOC_SPAWN_NETHER`; existing saves | Original drops and behavior |
| Eclipse Griffith | `mon_berserk_eclipse_griffith` | Final Eclipse map | Existing rescue/victory handling |
| Eclipse demons | `mon_berserk_eclipse_*` | Eclipse map and post-Eclipse era groups | Physical monsters; world era gated by event |
| Armor shadows | `mon_beast_of_darkness_1` through `6` | Armor curse EOCs | Separate real/hallucinated encounters |
| Skull Knight | `mon_skull_knight` / `mon_skull_knight_rescuer` | Existing scenario / rescue scene | Hostile old form / friendly story form |

`GROUP_NETHER` also appears in CDDA 0.I-1 microlab mapgen. Its weights are
relative selection weights, not probabilities per laboratory. The pre-existing
mod group also includes zombie brutes and armor shadows. The three old bosses
were removed from this group's future rolls; their distinct scenario IDs and
the Eclipse boss remain unchanged. Previously spawned originals in a saved
world are not replaced retroactively.

All three projections reuse the original sprites in UltiCa and the optional
Chibi tileset. Their smaller HP and zero regeneration are provisional for
these new IDs only; later combat tuning must assess their inherited attacks.
CDDA 0.I-1 supports `death_function.corpse_type: NO_CORPSE` separately from
`death_drops`, allowing their single Behelit drop without a physical corpse.
No ordinary-location Behelit cache is included in step 1.

## Step 2: Behelit encounter sites (planned, not yet implemented)

Build several small, recognizable locations. Examples: an expedition's last
camp among demons; a cursed great oak; a distinctive demon's lair. Give the
player a map note or other in-world clue pointing to the specific location.
After its encounter is cleared, a Behelit can be recovered from a fixed cache
or named adversary. Define what "cleared" means per site and make rewards
one-time, including across save/reload; do not rely on a global nearby-monster
count that unrelated zombies can change. Preserve a path to a Behelit for
players unable to defeat a high-level projection.

## Verification still needed in game

- Locate a vanilla microlab using `GROUP_NETHER`; inspect names, sprites,
  drops, no corpse, and whether the original bosses stopped appearing there.
- Try the three old scenarios, plus a pre-existing save with an original boss.
- Check the armor's recurring Griffith encounter and Brand warnings.
- Measure how often projection encounters actually occur; neither group
  weights nor the 1/100 daily armor attempt guarantee a find in a single lab.

Static JSON and asset validation do not replace those game checks.
