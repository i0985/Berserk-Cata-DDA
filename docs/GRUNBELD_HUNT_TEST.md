# Grunbeld and the assembled four-hunt chapter

Target **CDDA 0.I-1**, test branch **`codex/3.0-new-horizon`**. No game executable has been run. This is a test build for the user's native checks, not a claim that the complete game flow already passed.

## Encounter

Seal the Count, Wyald and Rosine's independent breaches. On the surface, activate the hunt journal and select Grunbeld, or ask the Skull Knight/peaceful Flora for his trail. The last preceding hunt also seeks this site automatically. The locator searches suitable forest within 40 OMT; failure leaves progress and rewards intact and can be retried elsewhere. An already-dead Grunbeld is an exception to the late unlock: his remaining wound can be located without resurrecting him.

Special **`berserk_grunbeld_stronghold_special`**, a **2×3 OMT / 48×72 map-square** surface stronghold. Follow the north-south stone track. The western quarry and eastern ramparts/barracks provide two routes; the final **`berserk_grunbeld_crucible`** lies in the southeast. Six finite vanilla-mod demon placements support the encounter. No boss is inserted into random world groups. The guardian spawns only when the avatar enters the final OMT.

| Form | ID | HP | Speed | Basic attack | Bash / cut / heat armor | Prepared attack |
|---|---|---:|---:|---|---|---|
| Armored apostle | `mon_berserk_grunbeld_knight` | 720 | 90 | 3d8 + 18 bash | 14 / 20 / 8 | Hammer: maximum 48 bash, reach 3 |
| Flaming dragon | `mon_berserk_grunbeld_dragon` | 950 | 85 | 3d10 + 18 cut | 12 / 18 / 28 | Focused flame: maximum 36 heat, reach 6 |

Both forms have melee skill 7, dodge 0 and regeneration 0. Attack amounts describe data before defense, not guaranteed player damage. Native melee-special scaling is 0.5–1.0 before defenses. The flame is a single-target heat attack using the native ranged-melee actor; solid cover can interrupt its line. It cannot be blocked with a weapon, but dodging remains possible. This prototype does not implement a wide flame cone or a spreading fire field.

Preparing the hammer consumes 260 moves, the flame 300 moves, and applies visible effects for six/seven seconds. At base speeds the preparation provides approximately 2.9/3.5 seconds of action delay; actual timing requires game testing. Leave the reach or take stone cover. The dragon's post-transition pause costs three turns in addition to native polymorph setting its moves to zero.

The existing Eclipse executioner/butcher sprites serve as `looks_like` placeholders. No new hand-drawn Grunbeld sprite, multi-cell body or colored-light feature is claimed.

## Phase transition and death handling

1. Successful first spawn reserves the encounter and adds a permanent armored-form marker.
2. At **≤50% of the armored form's HP**, a damage-event handler casts a self-targeted `targeted_polymorph` spell. It checks the marker and the world phase rather than a living-only nearby-ID query, so a normal lethal hit can still enter the handler.
3. Before casting, a nonpositive first-form HP value is stabilized to one. The cast callback confirms the resulting dragon ID before committing phase 2. The native spell's successful-call callback alone is insufficient proof of transformation.
4. The dragon begins with 950 HP once. Native polymorph preserves the HP ratio, so explicitly initializing the final phase avoids a nearly dead dragon immediately after the transition. No recurring heal or subsequent regeneration is added. Armored readiness is removed; a dragon marker and short move delay are applied.
5. A one-second world watcher handles a loaded living armored form that crosses the threshold outside a source-bearing damage event. It does not heal or reset a dragon.
6. Source-less lethal damage or direct engine death uses the first form's death callback as a fallback. The ruined armor leaves no corpse/relic, records the dying creature's exact location and requests one dragon nearby. Six bounded attempts, followed by a manual retry at the crucible mark, handle blocked spawn space. While pending, the hunt remains in state 2: no victory, quiet region or relic.
7. Only the final dragon's death marks the original dead and advances the hunt to state 3. Killer identity is irrelevant. An already registered lair coordinate is preserved if the creature wandered away.

Primary-source review used the exact tag: [monster damage, polymorph and death](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monster.cpp), [targeted polymorph](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/magic_spell_effect.cpp), [spell/effect dispatch and tracker removal](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp), [monster talker](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/talker_monster.cpp), [HP math](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/math_parser_diag.cpp).

Important source details: `monster_takes_damage` is sent after HP subtraction, before the subsequent dead-state handling for source-bearing damage. `monster::poly` preserves the creature and its HP ratio, resets moves/special cooldowns and updates faction. The math HP-maximum call uses valid bodypart `torso`; monster talkers ignore that bodypart. Death EOC **source** gives the killer as alpha (possibly null) and the dying creature as beta; the monster documentation's example says otherwise. The implementation follows the source and requests the avatar only for player messages/spawning.

## Flora and older saves

- Grunbeld killed in the grove remains dead. His existing body drop is the single shard reward. The new mark does not mint another, even when the old trophy was left on the ground or lost. The new lair can still be sealed and advances to state 5 because its reward was already issued.
- Old saves recorded the grove death position in `berserk_hunt_grunbeld_location`. A separate `berserk_hunt_grunbeld_site_registered` flag distinguishes that position from an actual located stronghold. Finding the lair updates only this hunt's coordinate; it does not move other hunters' quiet regions. Direct final-room entry or sealing also registers the actual site, including a debug-placed lair when the original is already dead.
- A living grove scene actor represents the same original, not a second apostle. Once his stronghold is registered and the siege is no longer active, that scene actor is retired without running death/loot callbacks, representing departure for his lair. A ten-second watcher also catches a previously unloaded scene on later visits. Other creatures are not removed. Future siege spawns do not create a second Grunbeld after his lair is registered.
- The new lair's final death has its own marker, so later journal use does not misclassify a newly defeated dragon as an old grove trophy and skip its legitimate reward.
- Existing item/monster IDs and relic effects remain intact. No PR or main-branch merge is performed.

## Completion, reward and next destination

Each of the four named hunts retains separate world coordinates and progress: **0 unknown → 1 found → 2 encounter → 3 guardian defeated → 4 breach sealed → 5 relic received**. Grunbeld's phase/pending/retry/death and reward records are additional fields, not replacements for this shared sequence.

After final victory, examine the exposed breach in the north of the crucible. A confirmed furniture update commits state 4. Examine the sealed mark again to receive **Flaming Carapace Shard** (`berserk_grunbeld_carapace_shard`) once. Existing carried/worn prototypes are not duplicated. An item that cannot fit may be on the ground. A repeated examination cannot reissue a lost reward.

Wear the shard for **20% reduction of incoming heat damage before clothing protection** and modest hot-weather cooling. It does not grant smoke protection, protect equipment from burning or provide complete fire immunity. Existing enchantment definitions are unchanged.

The shared query suppresses new Brand/new-era incursions only within 48 map squares, roughly two OMT, of each **independently sealed** site's stored origin. State 5 retains the same protection as state 4. It does not clear existing demons, remove the Brand or turn off armor shadows. New forms are included in existing density counting, strong-demon detection and the Count seal's explicit damage whitelist.

Completion marks an unfinished named hunt if any remains. After all four, the first sealed breach is marked as a recovery destination and the journal can mark any completed lair. The closing objective is concrete: return, recover and fortify the refuge. No unimplemented fifth hunt is advertised.

## Static checks and limits

The assembled build passes **100 Python tests**, including 13 new Grunbeld tests, and validates **206 JSON files**, two packages and four compiled catalogs. English source text, Russian and Simplified Chinese catalogs include the new forms, map labels, dialogue, warnings and phase messages.

Tests exercise the JSON definitions with a small interpreter and inspect maps/data. They cover threshold/ordinary lethal transitions, one-time dragon initialization, failed polymorph confirmation, pending/blocked dragon spawn, manual retry, modeled re-entry/state copies, final death by different killers, failed seal confirmation, duplicate rewards, old grove deaths/coordinates, scene retirement, independent local suppression, route connectivity and localization. These are **not native loader, combat, savegame, mapgen or rendering tests**.

## Native checklist for the user

1. Back up the save. Replace the whole `mods/Berserk` folder beside `cataclysm-tiles.exe`; remove a second copy in `data/mods` if present. Keep the optional chibi package only if used. Do not overlay leftover JSON from older builds.
2. Load a new and an existing world without debug errors. Check before-Eclipse access stays blocked; after the first hunt, Count/Wyald/Rosine can be followed independently; Grunbeld unlocks after their breaches are sealed. Check a failed forest search can be retried and a found site is reused.
3. Enter both stronghold routes. Check the six chunk seams, stone cover, approach record, supplies and final spawn. Grunbeld must not spawn on the approach or respawn after a living escape/re-entry.
4. Reduce armored HP gradually through 50%, then separately test a lethal bullet/melee hit to the first body. Check one dragon at the same location, 950 initial HP once, short pause, distinct name/effect, no premature trophy or closed breach. Test explosive/direct/source-less first-form death separately: no corpse reward; the pending dragon must appear or remain retryable.
5. Test hammer/flame warning effects, real delay, moving out of reach, line interruption by stone, heat damage versus the worn shard, ongoing bleed/other status effects and balance for an ordinary equipped survivor, a prosthetic-arm character and high-stat armored Guts. Native timing/difficulty are unverified.
6. Save/reload in each hunt state and on both sides of transformation, including blocked pending dragon spawn. Verify no healing/reset of the already wounded dragon and no duplicate original. Draw the boss out of the arena: the original breach location must remain sealable after its defeat.
7. Kill the dragon, seal the breach, take the reward once. Block the furniture update and verify no false completion. Check inventory overflow, preowned trophy, repeated claim, native reload and independent quiet areas.
8. Load an old save where Grunbeld died at Flora's grove, with and without the old shard in inventory. No new Grunbeld or second shard; the located stronghold should still be sealable. Test a surviving grove actor and a later visit to the unloaded grove after his lair is found. Other demons must remain.
9. Finish all four hunts in the allowed orders; verify the journal/Skull Knight/Flora directions and concrete recovery destination. Check that the Brand, night danger outside the quiet radius, original armor appearances and Berserk costs remain active. Check Russian, English and Chinese text and UltiCa/chibi placeholder rendering.
10. Inspect `debug.log` through the full path: Behelit → Eclipse → rescue/biotics → first hunt/refuge → Flora/escape → independent hunts → Grunbeld → local closure/recovery. The archive contains the complete current test branch, but this complete native playthrough is still pending.

For debug placement, use the **global-map special** menu with `berserk_grunbeld_stronghold_special` in fresh ungenerated terrain. It is globally unique: do not place several copies in one world. The regular journal path is preferred for testing progression.
