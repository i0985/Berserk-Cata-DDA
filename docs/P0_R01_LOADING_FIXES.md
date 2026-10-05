# New Horizon 3.0 — P0 / R01, 3 October 2026

## Scope

Fix the reported startup failure and audit the existing loot migrations. This
iteration does not redesign placement, move saved sites, change quests, balance
bosses, alter maps, or change the agreed lore. It does not run a CDDA binary.

## Confirmed startup failure

CDDA 0.I-1 `src/mission_util.cpp`, `parse_mission_om_target`, rejects an explicit
`search_range` when `random` is false. `mission_target_params::random` defaults
to false in `src/mission.h`, so omitting `random` does not solve that error.

All 12 conflicting searches now use `random: true` while retaining their
bounded search radii, terrain/special IDs, coordinate variables and success
validation:

| Search | First / fallback range, OMT | File |
| --- | --- | --- |
| Count | 48 / 80 | `effects/apostle_hunt_eocs.json` |
| Flora | 48 / 80 | `effects/flora_eocs.json` |
| Local breach | 48 / 80 | `effects/local_breach_eocs.json` |
| Wyald | 48 / 80 | `effects/wyald_rosine_hunt_eocs.json` |
| Rosine | 48 / 80 | `effects/wyald_rosine_hunt_eocs.json` |
| Grunbeld | 64 / 96 | `effects/grunbeld_hunt_eocs.json` |

Here `random` selects among matching targets in the allowed search area. It is
not a monster-spawn setting or a chance to grant the quest. The existing checks
for previously saved sites and actual target terrain remain in place.

Removing `search_range` would be another syntactically valid option for a
nearest-target search, but would discard the intended explicit search bounds.
This patch keeps those bounds. It does not guarantee placement in every save or
implement strict minimum placement distances.

The packaging validator now checks this native constraint both on location
lookups and on mission target assignment. It also catches unsupported target
fields and the confirmed bread/jerky/aspirin/rag loot mistakes.

## R01 loot audit

The baseline already uses `count` for bread, jerky and aspirin and
`scrap_cotton` instead of `rag`, including Rosine's opened cocoon. These working
changes were retained, not replaced again.

The remaining charges entries belong to water, liquid treatments, an oil lamp,
batteries and candles. They were retained: charges are not globally invalid.

An audit of 1,474 mod objects checked 117 distinct explicit item references, 13
referenced loot groups and mod-prefixed terrain/furniture/monster/bionic/EOC/talk
IDs. Inline EOCs were counted as definitions, and mapgen `place_items.item` was
checked as an item-group reference rather than a literal item.

No unresolved references were found in those checked fields against the
available native 0.I JSON data supplemented by previously cached 0.I-1
extracts and mod definitions. This is not a full native loader or a complete
September 19 experimental data snapshot. It cannot certify every JSON field,
inheritance rule or runtime interaction.

Modern supplies remain restricted to the expedition and the chapel's modern
refugee aid context. Count, Wyald, Flora and the stronghold retain their
medieval supply groups. No loot substitution or reward/stat change was needed
in this iteration.

## Vanilla examples for P1

The available local native examples distinguish target assignment from local
map updates:

- **Refugee center:** 0.I-1 `src/mission_start.cpp`,
  `mission_start::reveal_refugee_center`, targets `refctr_S3e` in the
  `evac_center` special, assigns the mission target and separately reveals the
  location/road route. Its explicit C++ search parameters bypass the JSON parser;
  copying that C++ parameter combination into JSON is not automatically valid.
- **Hub-01 delivery:** cached 0.I
  `data/json/npcs/refugee_center/surface_staff/Smokes/free_merchant_shopkeep_missions.json`,
  `MISSION_FREE_MERCHANTS_HUB_DELIVERY_1`, uses `assign_mission_target` with
  `robofachq_surface_entrance`, special `hub_01`, and a reveal radius. It does
  not combine an explicit search range with a nearest-target JSON search.
- **Farm/Tacoma commune:** the same cached file,
  `MISSION_FREE_MERCHANTS_EVAC_3`, targets `ranch_camp_67` in `ranch_camp`, then
  applies the mission's mapgen update for its initial NPC setup. A map update is
  not a substitute for placing a whole special or rewriting a visited map.

These are the basis for the next placement/mission stage, not a claim that P1
has already been implemented. Exact quest JSON must be checked against the
chosen game version before copying it.

## Validation and handoff

- The added search rule reproduced the reported failure before the JSON fix.
- 16 targeted cases checked accepted/rejected target parameters and the known
  loot regressions; valid liquid/battery/candle charges remained accepted.
- Repository asset validation passed: 2 mod packages, 264 JSON files,
  31 mod_tileset definitions, 33 sprite sheets, 78 tile IDs, 4 translation catalogs.
- Packaging uses the existing mtime-preserving release writer.
- No game executable was launched. Actual world placement and combat still
  require the user's playtest.

## User checks

1. Install the new mod folders cleanly, replacing the old `Berserk` folder
   rather than mixing JSON files from different builds. Preserve your saves.
2. Open the new-character screen and then the existing save. The reported
   `search_range` / `random` loader error should no longer occur.
3. Check for bread/jerky/aspirin quantity warnings and missing `rag` errors
   during loot consistency checks and cocoon examination.
4. If startup succeeds, continue with P1: first hunt, breach and Flora target
   registration. A later target-search failure is a separate placement issue;
   this iteration does not claim to resolve it.
