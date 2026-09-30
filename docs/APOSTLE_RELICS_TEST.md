# Apostle relic prototype — New Horizon 3.0

Target: **CDDA 0.I-1**. Base revision: `851b0a052d5ad4608ec871d4f9207e1cb1d56ffc`.
This is an untested-in-game development build. No CDDA binary was run.

## Rewards and availability

| Reward | Item ID | Prototype effect | Availability |
| --- | --- | --- | --- |
| Seal of Severed Flesh | `berserk_count_iron_seal` | Adds `floor(actual hit damage × 0.20)` against the explicit mod demon whitelist | Existing guaranteed Count trophy drop; the old trophy ID is retained |
| Beast Knot | `berserk_wyald_beast_knot` | Berserk lasts 210 rather than 150 seconds | Debug prototype; reserved Wyald drop group |
| Mistvale Veil | `berserk_rosine_mistvale_veil` | +1 dodge bonus, not +1 dodge skill or guaranteed avoidance | Debug prototype; reserved Rosine drop group |
| Flaming Carapace Shard | `berserk_grunbeld_carapace_shard` | −20% incoming heat damage before clothing absorption; cooling strength +10 | Debug prototype; reserved Grunbeld drop group |

**Wear the items.** Backpack possession, wielding and dropping do not grant
their benefits. Each has `max_worn: 1`; duplicate copies cannot normally stack
the same reward. Different relics may be worn together. They use the AURA layer
as magical accessories, with zero coverage, encumbrance and warmth; this does
not alter any Berserker armor definition or allow stacking heavy armor.
There are no new relic sprites in this build; ASCII/item fallback art needs a
separate visual check. Existing armor/cannon tilesets are untouched.

Wyald, Rosine and Grunbeld's hunts are **not implemented by this prototype**.
Their reserved collection groups are not attached to unrelated bosses or
random loot. Add the three items through debug to test them now; attach the
groups when their own encounters exist. Do not publish them as obtainable
normal-play rewards yet.

The Veil deliberately has no stamina property in this build. Native
`STAMINA_REGEN_MOD` exists, but its interaction with winded/Berserk recovery
and condition cache refresh must be checked before enabling it. The existing
exhaustion mechanics must not be silently weakened.

## Seal: damage event and explicit targets

`EOC_BERSERK_COUNT_RELIC_DAMAGE` listens for `monster_takes_damage`.
The damaged monster is **alpha**, the attacker **beta**. It requires an avatar
attacker wearing the seal, positive actual damage and a living target. A
radius-zero `u_monsters_nearby` query at alpha checks the exact type ID. A demon
standing near an ordinary zombie does not qualify that zombie.

The native event occurs after mitigation/base HP subtraction. The event adds
20%, rounded down, by assigning **ALL** HP; it does not issue a second damage
event, reapply armor or substitute a different killer. Examples:

| Original mitigated hit | Extra HP loss |
| ---: | ---: |
| 0–4 | 0 |
| 5 | 1 |
| 17 | 3 |
| 50 | 10 |

If the original hit already killed the target, the bonus does nothing. A
bonus-only kill clamps HP at zero and the original native hit continues its
normal death handling. The usual displayed damage amount and statistics may
exclude this supplemental HP loss: confirm that behavior in-game. This is a
prototype tradeoff; it is not a separate slash or a critical-hit multiplier.
Player-attributed ranged hits also qualify. NPC attacks do not.

The whitelist contains:

- Darkness beasts `mon_beast_of_darkness_1` through `6`;
- the five Eclipse demon types: wretch, halfbreed, hunter, butcher, elite;
- the hollow apostle and breach warden;
- the cursed-oak and echo-cave guardians;
- the Count and his servants;
- existing Zodd, Griffith and Void IDs;
- the three projection IDs;
- both final Eclipse Griffith IDs.

It excludes zombies, vanilla nether creatures, people, the Count's prisoner
and both Skull Knight variants. The query uses the default hostile filter;
friendly copies are not boosted. Hallucinations with a listed ID are not
specifically excluded by this native query; their ordinary hallucination
behavior and lack of normal loot are unchanged. The whitelist is explicit
in `effects/apostle_relic_eocs.json` and must be reviewed when adding enemies.

## Knot: fixed activation, existing costs

At `EOC_BERSERK_MODE_START`, wearing the Knot selects **210 seconds**;
otherwise the mode remains **150 seconds**. The selected duration is saved
in `u_berserk_mode_duration`, then passed to the rush effect. Changing equipment
after activation does not change the running effect or restart the countdown.

Warnings are emitted every 30 seconds, then every second for the final ten.
The two extra 180/150-second warning thresholds do not generate a false
150-second warning at the start of the ordinary mode. Old active saves can
continue counting down without the new duration variable. Native save/load
compatibility still needs the user's game test.

The mode controller and finish handler are unchanged: the existing armor
removal rule, stamina floor while raging, final exhaustion, blood formula,
three-day recovery and Eclipse rescue sequencing remain in force. An extended
mode postpones these costs; it does not reduce them.

## Shard limits

The native `incoming_damage_mod` heat multiplier is **0.8**, applied before
clothing absorption. `CLIMATE_CONTROL_CHILL: +10` moderates overheating rather
than granting a temperature immunity; it is not a literal 10°C reduction.
There is no `HEAT_IMMUNE`, smoke protection, equipment fire protection or
protection against other damage types. Some direct HP loss paths may bypass
ordinary incoming damage processing. Never test lethal fire on the only copy
of a save.

## Files changed

- New: `mods/Berserk/items/apostle_relics.json`.
- Removed: `mods/Berserk/items/apostle_count_trophy.json`; its ID has moved to
  the new file, not been deleted from game definitions.
- New: `mods/Berserk/effects/apostle_relic_eocs.json`.
- New: `mods/Berserk/enchantments/apostle_relics.json`.
- New: `mods/Berserk/monsterdrops/apostle_relic_drops.json` (future groups only).
- Updated: `mods/Berserk/effects/berserk_mode_eocs.json` (start/countdown only).
- Updated: `mods/Berserk/effects/apostle_hunt_eocs.json` (seal instructions only).
- Updated: `mods/Berserk/lang/po/Berserk.pot`, `ru.po`, `zh_CN.po` and both
  compiled `mods/Berserk/lang/mo/*/LC_MESSAGES/Berserk.mo` catalogs.
- Updated: `docs/COUNT_HUNT_TEST.md`; added this checklist and
  `tools/test_apostle_relics.py`.

## Verification performed

- Asset/JSON/catalog validator: **170 JSON files**, two packages.
- **54 Python regression tests** including nine new relic tests.
- Both PO catalogs compiled with `msgfmt --check`; new descriptions, names,
  messages and three Russian plural forms checked in compiled catalogs.
- Whole package built with `tools/package_release.py`.
- Changed JSON parsed, whitespace checked and mode controller/finish compared
  directly with the base revision.

The Python harness exercises the EOC definitions and event talker assumptions.
It is **not** CDDA's loader, combat engine, enchantment cache or native save
serializer. AI, actual kills/drop attribution, worn-item restrictions,
enchantment updates, display, native saves and the full Eclipse flow have not
been tested in-game.

## User test checklist

Install into `mods` alongside `cataclysm-tiles.exe`. Replace the old **Berserk
folder as a whole** so the retired `apostle_count_trophy.json` cannot leave a
duplicate definition. Keep only one Berserk copy: remove another copy from
`data/mods` if present. Back up the save before testing.

1. Start a fresh test world and load a backed-up old save. Check debug.log.
   An existing Count trophy should retain its ID and display the new name.
2. Kill the Count normally: verify one seal drops and the hunt/breach still
   completes. Wear the seal, also test it carried and removed.
3. Compare damage against a mod half-demon and a zombie with the same weapon.
   Test a zombie beside a demon, a ranged hit, an NPC attacker, armor-blocked
   damage and a kill caused by the extra HP loss. Check loot/kill attribution.
4. Obtain the other three items via debug using the IDs in the table. Wear
   them together with the full Berserker set; verify a second same relic is
   refused and bonuses vanish when taken off.
5. Trigger a normal 150-second mode, then a 210-second mode with the Knot.
   Remove/re-equip it mid-mode: no restart or duration change. Save/reload
   while raging; check warnings and the normal costs/three-day lockout.
6. Verify the Veil's dodge bonus and removal in the character screen. It
   should not provide stamina or suppress winded/recovery.
7. In a disposable test save, compare moderate heat/fire damage and hot
   ambient conditions with/without the Shard. Other damage and smoke must
   remain dangerous.
8. Test Eclipse rescue while an extended mode is running: one rescue,
   no duplicate aftermath/blood loss and normal progression afterward.
9. Switch English/Russian/Chinese; check all four items and the new warnings.

Stop for this game check before expanding the artifacts or attaching future
rewards to new hunts.

## Exact-version technical references

- [0.I-1 EOC documentation](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/doc/JSON/EFFECT_ON_CONDITION.md)
  (`monster_takes_damage`, effect duration expressions).
- [0.I-1 monster damage handling](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/monster.cpp)
  (`monster::apply_damage`).
- [0.I-1 monster talker](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/talker_monster.cpp)
  (`set_all_parts_hp_cur`).
- [0.I-1 dialogue math](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/math_parser_diag.cpp)
  (`hp_ass`, `_monsters_nearby_eval`).
- [0.I-1 enchantment loading](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/magic_enchantment.cpp)
  (`DODGE_CHANCE`, `incoming_damage_mod`, WORN conditions).
- [0.I-1 character processing](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/character.cpp)
  (dodge bonus, climate control, stamina regeneration).
- [0.I-1 clothing restrictions](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/character_attire.cpp)
  (`can_wear`, `max_worn`).
- [0.I-1 item loading](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/item_factory.cpp)
  (`max_worn`, ARMOR/ARTIFACT/TOOL subtypes).
