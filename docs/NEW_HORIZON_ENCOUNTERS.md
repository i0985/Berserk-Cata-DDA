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

## Step 2: Behelit encounter sites (unverified in game)

Two rare `OVERMAP_UNIQUE` specials can appear while generating previously
unexplored overmaps. `occurrences: [25, 100]` is the chance for each special to
join an overmap's placement pool, not a guarantee of placement. The cursed oak
occupies one forest OMT. The echo cave has a forest entrance at z=0 and a
separate chamber at z=-1; the stair coordinates match.

Both sites have distinct named overmap symbols **once discovered**. Automatic
notes on distant, still-hidden locations are not implemented; neither is a
map or journal clue directing the player to them. Existing overmaps already
generated in an old save are not retroactively repopulated. Explore new
overmaps to find the sites.

The oak guardian is a slow, heavy root attacker (360 HP, speed 85); the cave
guardian is a faster, lighter hunter (240 HP, speed 115). Their IDs occur only
in their respective site mapgen and local guardian checks, never in random
monster groups. Each has a dedicated temporary UltiCa-compatible sprite in
both graphics packages. Their two melee special attacks and balance need game
checks. The oak clearing and cave chamber also contain two weaker demons each.

Each Behelit is represented by **examinable furniture at the center**, not a
ground item. The player can claim it only while the corresponding living
guardian is more than eight tiles away from the player: defeat it or draw it
away and slip past it. The bone chimes at the oak's edge and stone chime deep
in the cave make a loud noise to support a diversion, but monster AI response
still needs in-game testing. Only the exact guardian ID is counted; unrelated
zombies and the lesser demons do not block claiming. Taking the relic runs an
update on the player's current OMT that replaces that particular cache with
an inert version, then grants one Behelit. The changed furniture holds the
one-time state at the site through save/reload; visiting a different site
does not share a character-wide reward flag. Check that map update and item
delivery order in game before treating one-time rewards as proven.

Further sites, such as an expedition's final camp, and map clues can follow
after the oak and cave are tested.

## Verification still needed in game

- Locate a vanilla microlab using `GROUP_NETHER`; inspect names, sprites,
  drops, no corpse, and whether the original bosses stopped appearing there.
- Try the three old scenarios, plus a pre-existing save with an original boss.
- Check the armor's recurring Griffith encounter and Brand warnings.
- Measure how often projection encounters actually occur; neither group
  weights nor the 1/100 daily armor attempt guarantee a find in a single lab.
- In a newly generated forest area, confirm both specials can appear. Enter
  the cave and climb back up; check oak and cave sprites, lighting, combat and
  map symbols. Try sprinting to each cache with the guardian nearby, luring it
  past eight tiles, killing it, and reloading after taking the Behelit.

Static JSON and asset validation do not replace those game checks.
