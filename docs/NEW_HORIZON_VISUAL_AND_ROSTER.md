# New Horizon: Eclipse art and encounter roster

Target: CDDA `0.I-1` (`7b2efa5cea38e4d4d97dd0e63b28b9148623da59`). This is a design register, not a claim that the artwork or attacks below are already implemented.

## Roster before adding more bosses

| Category | Characters and existing content | Intended role |
| --- | --- | --- |
| Manga story, present or represented at the Eclipse | Guts, Griffith/Femto, Skull Knight, Judeau, Pippin, Corkus, Gaston, sacrificial crowd; God Hand as distant presences | Dialogue, remains, ritual staging. God Hand are separate from apostles and are not ordinary enemies. |
| Adaptation for this mod | The six-area trial, pre-Eclipse projections of Zodd/Griffith/Void, flesh terrain, named remains and memories | Establish a playable path without claiming that killing a projection kills the original. Existing `mon_void_apostle` ID stays for saved games despite its misleading historical name. |
| Ordinary dungeon creatures | `mon_berserk_eclipse_wretch`, `halfbreed`, `hunter`, `butcher`, `elite` | Scalable encounters and navigation pressure. They are not named manga apostles. |
| Potential later named encounters | Any additional manga apostle, one at a time after checking their appearance and role in the source | Separate design, art, weakness, drop and balance pass. Zodd is not automatically placed in this Eclipse. |

The prototype roles can use the existing wretch/halfbreed for a **pack devourer**, hunter for a **herder**, and butcher/elite for a **heavy executioner**. These are encounter roles, not a decision to rename existing IDs. First test one visible warning and a real player turn before a heavy strike. `0.I-1` documents targeting warnings and `targeting_cost` for *gun* monster attacks; that does not prove a generic melee windup. A log message alone is insufficient. Confirm the chosen special attack and effect timing in source and in a small encounter before extending it to all three roles. Evaluate zombies, NPCs, doorways, and whether the warning remains visible in UltiCa.

## Visual work in two stages

1. Paint individual 32 px terrain sprites and multi-cell arrangements for living ground, boundaries, pits, distant silhouettes and sacrificial debris. Introduce several surface variants and deliberate light source positions, then check all six OMT joins and route readability at several zoom levels. Current `mapgen/eclipse_palettes.json` uses ordinary `light_emitted: 80` on `t_berserk_eclipse_luminous_flesh`; its `color: red` is an ASCII/tile appearance setting, not a colored light source.
2. Isolate a colored-light experiment in a tiny test map. In the `0.I-1` tag, field types visibly separate `color` from `light_emitted`, and the inspected renderer's lighting tint code does not demonstrate a JSON-defined RGB source. Do not add an unverified light-color field to the release. Pin the exact game build with support, test UltiCa and save/load, and only then consider migrating a proven technique to the Eclipse. The 0.I-1 layout can still achieve contrast with ordinary illumination and sprites.

Suggested order: layout readability → sprite sheet previews → six-area playthrough → single telegraphed enemy → colored-light experiment. Keep art and combat prototypes in a separate test build until visual checks are possible.
