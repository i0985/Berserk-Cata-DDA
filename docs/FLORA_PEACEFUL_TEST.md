# Flora: peaceful manor and split starts — New Horizon 3.0

Base revision: `c8765e81140fc28b28406ed495a3d40b2815dc14`.
Target: **CDDA 0.I-1**. Development branch: `codex/3.0-new-horizon`.
**No game binary was run.** This iteration implements the peaceful encounter;
the burning-house attack remains a separate next iteration.

## Two story starts

Choose scenario **(BERSERK) Before or after the Eclipse**
(`berserk_story_start`), then one of its two professions:

| Start | Profession ID | Equipment | Implanted bionics / story |
| --- | --- | --- | --- |
| Berserker before the Eclipse | `berserk_before_eclipse` | Early true sword, leather-padded shirt/sleeves/pants, leather gloves, barbute helm, boots and underwear | No starting Brand, lost eye, hand stump, cannon or cursed armor |
| Berserker after the Eclipse | `berserk` (original ID) | Existing true sword and all six existing Berserker armor pieces | Hand stump and cannon, lost eye, Brand; Eclipse completed, new era active |

The early sword (`true_guts_early_sword`) is based on the exact-tag vanilla
`mc_zweihander`: **16 bash + 52 cut**, compared with the base's 10 + 36 and
the unchanged later true sword's 40 + 100. Its game weight is **1800 g**, using
the existing true-sword convention; no `ALWAYS_TWOHAND` flag is imposed.
Native strength and wielding checks still apply. It is not a reward from a
blacksmith: that acquisition story is future work. It temporarily uses the
vanilla zweihander appearance.

New after-Eclipse characters start with the four CBMs in parent-before-child
order. Their profession queues `EOC_BERSERK_POST_ECLIPSE_START` once. This sets
the era, rescue-completed and spent-Behelit states, teaches the cannon/charge
recipes and brings the friendly Skull Knight. The existing retry handler
handles lack of a placement tile. It does not apply rescue wounds, take blood,
regrant armor, or replay the rescue cutscene. Repeat initialization is guarded.

The original `berserk`, `berserk_prosthesis` and `berserk_fan` IDs remain.
Existing saves retain their equipment and installed bionics: profession EOCs
are queued for new characters, not retroactively for loaded old characters.
The old lost-hand profession is now an explicit standalone definition rather
than inheriting new after-Eclipse initialization. It is scenario-only and
remains selected by the old **The Lost Hand** scenario. The Zodd challenge also
allows the new before-Eclipse profession. The fan is unchanged.

A new before-Eclipse character **does not rewind an existing world's era or
global quest history**. Use a fresh world to test the full before-Eclipse path.

## Finding the manor

After surviving the Eclipse and finishing the first hunt, ask the Skull Knight
**The first hunt is over. Where can I find Flora?** He provides a reusable
directions item (`berserk_flora_directions`), which uses a TOOL activation and
does not require literacy. Activate it on the surface to locate/reveal the
manor. If the Knight has gone, the journal earned by sealing the first local
breach offers the same route before its existing refuge/Count choices.

The locator searches a bounded 40-OMT area, finds or creates
`berserk_flora_manor_special`, and records a shared world location. Subsequent
requests reveal that same location, including from farther away. A failed
search shows a retry instruction and grants no armor.

The special has **GLOBALLY_UNIQUE** and **occurrences [0,100]**: no random
instances are seeded in every overmap; the quest locator places it. The layout
contains four fixed, nonrotating OMTs:

| Northwest | Northeast |
| --- | --- |
| `berserk_flora_manor_west` | `berserk_flora_manor_east` |
| `berserk_flora_garden_west` | `berserk_flora_garden_east` |

The house/gardens form a **48 × 48** area. Flora stands in the western study,
with benches, bookcases, a bed and a sanctuary ward. Unlocked western and
southern exits lead to distinct paths. Ordinary vanilla terrain/furniture
already have base tileset support; there are no new custom sprite sheets.
Flora temporarily uses a vanilla civilian appearance. Her custom art can be
added later.

For debug placement use the **overmap special** menu, not the mapgen-update
menu. Place the globally unique special only once, then enter its actual map.
First conversation can register a manually placed manor if the locator has
not done so; it never resets later attack/ruin stages or relocates an already
registered manor. Debug force-placement of multiple unique copies is outside
normal quest behavior and can produce native duplicate-special warnings.

## Conversations and armor ownership

Flora is a friendly, immobile, pacifist **MONSTER** with `CONVERSATION` and
`chat_topics`, following the current Skull Knight story-actor approach. She
does not expire or wander off. She is not a full trading/equipment NPC.

Questions cover:

- the Brand, night summons and the limits of wards;
- tension, shadows, the armor and ordinary clothes beneath it;
- the 150/210-second mode, exhaustion, blood loss and three-day recovery;
- apostles, projections and the God Hand;
- the Count's seal and limits of relics;
- preparing a refuge/cannon, and the existing Count hunt as a next goal.

Receiving armor is an **explicit confirmation**, not a speaker-effect reward.
It requires the post-Eclipse state, a real Flora as dialogue beta, the peaceful
stage, and an unclaimed gift. It gives only missing items, with no forced
equip, removal of old gear, consumable requirements or repeated replacements.

| Current ownership | Behavior |
| --- | --- |
| No armor | Receive each of the six parts once |
| Some parts, including a lab-found part | Keep them; receive only missing parts |
| All six across worn equipment, inventory and nested carried contents | Owner conversation, no duplicate suit |
| A carried packed armor bundle | Owner conversation, no duplicate suit |
| Gift already accepted, then pieces lost/dropped | No replacement reward |
| Gift claimed by another character in this world | Advice still available; no second world gift |

The full-set test uses `u_has_item`, so the pieces need not all be worn together.
It explicitly recognizes `berserk_armor_bundle`. It does **not** search nearby
ground, vehicles or distant stashes: bring the existing complete set/bundle
when requesting armor. If the new pieces overflow carrying capacity, native
`u_spawn_item` can leave them on the ground; check around the speaker.

Acknowledging an already-owned suit resolves only that character's armor
conversation; it does not consume Flora's unused world gift. Possessing all
armor does **not** block directions, lore or subsequent hunt advice. The
after-Eclipse start therefore skips redundant acquisition but can visit Flora
as an optional adviser.

## Peaceful sanctuary / future attack boundary

`berserk_flora_stage = 1` is the peaceful world state. Saved manor coordinates
participate in the existing quiet-region predicate, preventing new era patches
targeting the grove even when the source is a neighboring visited tile. The
protected radius is 48 map tiles from the saved northwest OMT origin. The
Brand's hourly night handler also checks the nearby manor OMTs while peaceful.

These guards do not delete existing monsters, prevent them walking in, erase
the Brand or stop the armor's separate shadow mechanics. Flora is mortal.
The first meeting is intended to have no scripted enemies/fire, not guaranteed
invulnerability against enemies the player brings.

The accepted gift leaves the grove peaceful. This build has **no attack,
fire/smoke spawning, Zodd/Grunbeld assault, combat timer or burned-map update**.
The later attack can use stage 2, and ruins stage 3; neither stage is reset by
meeting/locating Flora. A later explicit readiness choice must start that
separate scene. Do not attach fire to the dialogue's passive reading effects.

## Changed files

New:

- `mods/Berserk/dialogue/flora.json`
- `mods/Berserk/effects/flora_eocs.json`
- `mods/Berserk/monsters/flora.json`
- `mods/Berserk/furniture/flora.json`
- `mods/Berserk/overmap/flora_manor.json`
- `mods/Berserk/mapgen/flora_manor.json`
- `mods/Berserk/mapgen/flora_palettes.json`
- `mods/Berserk/items/flora_directions.json`
- `mods/Berserk/items/true_guts_early_sword.json`
- `mods/Berserk/scenarios/berserk_story_starts.json`
- `tools/test_flora.py` and this document.

Updated:

- `mods/Berserk/professions/professions.json`
- `mods/Berserk/scenarios/berserk_lost_hand_start.json`
- `mods/Berserk/scenarios/berserk_pursuer.json`
- `mods/Berserk/dialogue/skull_knight.json`
- `mods/Berserk/items/post_eclipse_journal.json`
- `mods/Berserk/effects/local_breach_eocs.json`
- `mods/Berserk/effects/apostle_progression_eocs.json`
- `mods/Berserk/effects/eclipse_brand_eocs.json`
- `mods/Berserk/lang/po/Berserk.pot`, `ru.po`, `zh_CN.po`, and both compiled MO catalogs.
- `tools/validate_mod_assets.py`: checks the current after-Eclipse profession
  name instead of an obsolete translated label.

All six armor item files, existing swords, bionic definitions, curse/Berserk
mode, combat monsters, relics and sprite sheets are unchanged.

## Static checks completed

- Asset validator: **180 JSON files**, two packages, four translation catalogs.
- **65 Python tests**, including eleven Flora state/layout/localization tests.
- Both PO catalogs compiled with `msgfmt --check`; profession/scenario names
  and descriptions use their exact male/female translation contexts.
- 24-character rows, connected exits and cross-tile house/garden routes.
- Partial/full/packed/worn/nested ownership, one-time gift, missing/wrong beta,
  pre-Eclipse denial, failed locator/reuse, legacy profession separation,
  one-time after-Eclipse initialization and sanctuary target filtering.
- Release packaging, JSON parsing and whitespace checks.

The harness models EOC definitions and expected native operation order. It
does not execute native AI, combat, map placement, save loading or rendering.
No new or old world was launched. Native wielding with one hand, item overflow,
NPC dialogue, world uniqueness and full progression still need game checks.

## User playtest

Back up your save. Replace `mods/Berserk` beside `cataclysm-tiles.exe` as a
whole, and remove any second Berserk copy in `data/mods`. The combined archive
also contains the optional `Berserk_chibi_tileset` package.

1. **New world, before start:** leather gear/early sword, no cursed armor/CBMs;
   normal Behelit → Eclipse → rescue still available.
2. **New world, after start:** true sword, six armor pieces, all four CBMs,
   no second Eclipse, active new era, one Knight and working first-hunt route.
3. **Old save:** no automatic new bionics, armor deletion, weapon replacement,
   replayed rescue or reset hunt progress. Test the old lost-hand scenario too.
4. After the first hunt, ask the Knight for Flora; activate directions again
   from farther away. After sealing the first breach, repeat via the journal
   with the Knight gone. Every request should point to the same manor.
5. Walk in through both house exits, meet Flora and read every topic. Check
   English/Russian/Chinese and save/reload before/after conversation.
6. Accept with no armor, one lab-found part, all six split between worn/carried
   gear, and a packed bundle. Only missing pieces should be awarded once.
   Test low carrying capacity; inspect the floor for overflow.
7. Drop the granted pieces, save/reload and ask again: no new gift. Start a
   second character in the same test world if testing the shared gift limit.
8. Wait after dark in the peaceful manor; test entry from neighboring OMTs.
   No new era patch/Brand night summon should populate the protected grove.
   Bring an existing monster separately: it must not vanish. Armor shadows
   remain independent and can still appear.
9. Confirm no surprise assault/fire while talking or accepting. Stop here
   before adding the next attack iteration. Inspect debug.log throughout.

## Exact-version references

- [0.I-1 overmap uniqueness](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/OVERMAP.md)
- [0.I-1 professions/scenarios](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/JSON_INFO.md)
- [0.I-1 profession loader](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/profession.cpp)
- [0.I-1 new-character EOCs](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/effect_on_condition.cpp)
- [0.I-1 inventory conditions](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/condition.cpp)
- [0.I-1 worn/nested inventory traversal](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/visitable.cpp)
- [0.I-1 monster dialogue/map placement](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/MAPGEN.md)
- [0.I-1 vanilla sword baseline](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/items/melee/swords_and_blades.json)
- [0.I-1 civilian actor baseline](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/data/json/monsters/civilians.json)
