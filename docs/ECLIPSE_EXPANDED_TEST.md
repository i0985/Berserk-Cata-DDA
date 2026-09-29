# Expanded Eclipse field: 3 × 4 OMT test build

The Behelit now targets `berserk_eclipse_expanded_special`, a new 72 × 96 tile
field at z=-7. The old six-OMT special and all its terrain and monster IDs
remain in the mod for saved characters already inside that layout. Existing
generated local maps are never rebuilt by installing the new version.

| Row | West | Center | East |
| --- | --- | --- | --- |
| 1 | Arrival, no initial enemies | Judeau and weak demons | Optional medical cache and hunter |
| 2 | Pippin and a torn field | Crossroads and pursuit | Corkus, feast and a heavier group |
| 3 | Optional hunting ground | Scarred ravine | Gaston and the last approach |
| 4 | Last stand | Warning and ceremony threshold | Griffith, escape rift and ending |

The main route is **east, south, south, south, east**, indicated by a broad
ash path (`t_berserk_eclipse_ashen_flesh`) and faint veins. Side routes use
subtler trampled flesh. The entry popup gives the first direction. Edges
between sections connect through nine-tile gaps; ridges and dangerous pits
break long sightlines and leave room for both fights and detours. There are
41 placed enemies, including the active Griffith variant. He has the same
combat values and death EOC as the earlier stationary version, but can move
and pursue once he finds the player. The previous stationary version remains
for an old generated Eclipse.

The first entry is free of placed enemies. Later density is intentionally
uneven: the optional feast is crowded, while the ceremony is comparatively
quiet until Griffith engages. These are placed monsters, not timed waves;
hearing and movement may still pull enemies between adjacent sections.

When the player first enters the expanded ceremony, an event records the
start of the final confrontation. If Griffith chases the player backward,
the low-HP and lethal-hit rescue rules continue to operate across all 12 OMTs.
They cannot accidentally apply in the new field before the final scene.
The rescue/victory return check, old-world return seal, and era flag recognize
both old and new OMTs. The original old-save monsters and victory hooks remain.

## Check in the game

1. Make a backup. Activate a Behelit in a save that has **not generated this
   Eclipse destination yet**. Confirm that exactly one Behelit disappears and
   the entry popup mentions the eastern ash trail. An existing save already
   inside the old six-OMT Eclipse should keep its layout and ending.
2. Follow the broad ash route east, then south three times, then east. Visit
   the western and eastern branches separately. Check signs and opening gaps
   in UltiCa, and note where monsters first spot/hear the character.
3. Check that Judeau, Pippin, Corkus and Gaston each have a body and their
   scene marker, and that the knife hilt and clasp still affect Skull Knight
   dialogue. Compare enemy density for a 9/9 survivor with Guts's sword and
   for a stronger character.
4. Enter the ceremony, retreat one section, and confirm that Griffith follows.
   Test his defeat, the low-HP rescue, and a lethal blow *after* the final
   scene has started. Confirm that all endings return safely, including after
   saving and reloading during the confrontation.
5. Report the exact game version, first error in `debug.log`, dark or missing
   terrain, unexpected dead ends, and which sections still feel empty or
   overcrowded. The JSON and static tests do not replace these checks.

The map is underground for technical placement. Distinct sky and colored
illumination remain separate experiments; `light_emitted` in 0.I-1 is a
brightness value, not a color. Custom floor, ridge and landmark sprites can
replace existing `looks_like` art later without changing the route IDs.
