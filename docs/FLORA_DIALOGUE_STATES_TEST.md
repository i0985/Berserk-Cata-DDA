# Flora: first conversation and siege readiness (CDDA 0.I-1)

This changes dialogue initialization, readiness checks and refusal explanations.
It retains the armor gift, attack timing, two exits, boss spawns and old state IDs.
No CDDA executable was run; native UI, map updates and save loading await playtests.

## Confirmed dialogue ordering

At exact tag [0.I-1, src/npctalk.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/npctalk.cpp),
`dialogue::opt` calls `dynamic_line`, `gen_responses`, then `apply_speaker_effects`.
Registering the manor in the main topic's speaker effect could not unlock the
responses already generated for the first meeting.

Flora now begins at `TALK_BERSERK_FLORA_ENTER`. Its unconditional greeting
responses do not require registration. Its speaker effect registers the manor
before **Let us speak** opens `TALK_BERSERK_FLORA` and evaluates the real choices.
Closing the greeting does not give armor, prepare an attack or start a timer.
Existing topic IDs are kept.

Both story discovery and the greeting calculate the same northwest OMT origin.
Flora placed by debug in any of the manor's four quadrants resolves to that
origin. An isolated Flora placed in an ordinary field does not designate it a
manor. An existing registered location is preserved, and later siege/ruin states
are never reset. The center is reconstructed from that location for old saves.

Native `npc_at_om_location` is supported in
[src/condition.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/condition.cpp).
Native `distance('u', variable)` and `distance('npc', variable)` are supported in
[src/math_parser_diag.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/math_parser_diag.cpp).
Activation checks both one of the four manor OMTs and proximity to the recorded
center, preventing a distant debug copy from starting updates at the old manor.

## Persistent states

| Player-visible stage | Saved state |
| --- | --- |
| Met Flora | `u_berserk_flora_met = 1`; peaceful `berserk_flora_stage = 1` |
| Received or acknowledged armor | `u_berserk_flora_armor_resolved = 1`; the gift remains world-limited |
| Explicit readiness confirmed | `berserk_flora_siege_state = 1`; no attack clock |
| Attack started | Existing states 2–4; `berserk_flora_stage = 2` |
| Escape complete | Existing state 5, `berserk_flora_stage = 3`, `u_berserk_flora_escaped = 1` |

Receiving armor alone does not confirm readiness. Armor owners, including a
carried packed suit, get their own confirmation topic and retain their equipment.
Only activating the escape charm and accepting its confirmation starts combat.
Cancelling preserves readiness and explains that the attack is still postponed.

The charm explains different refusals: Eclipse not completed, readiness not
confirmed, manor registration missing, player outside the registered manor,
attack already underway, or escape already completed. It uses no charges and
can be activated in place from the inventory.

Escape also gives the existing apostle hunt journal once and reports the next
goal. The directions/status report and surviving Flora's dialogue reflect the
completed event. This uses the existing journal progression; it does not add a
new native mission system or change which hunts are unlocked.

## Static checks

Regression scenarios model the native dialogue ordering and exercise:

- the first manual meeting, before and after story discovery;
- canonical registration from each quadrant, and rejection of unrelated actors;
- separate owner readiness for six pieces, a packed suit, and a previously claimed gift;
- gift/wearing armor without readiness; cancel then confirm; first activation;
- old missing-center/location state repair without resetting later stages;
- specific refusals, distant copied manors, preserved items and no combat side effects;
- escape, abstract state copy/reload, journal issuance and no repeated reward.

Translations are provided in English, Russian and Simplified Chinese, including
compiled catalogs. Python tests do not substitute for native game verification.

## Short user playtest

Install the fresh archive into `mods` next to the executable, replacing the old
Berserk folder; remove a duplicate Berserk from `data/mods` if present. Back up
the save before testing the one-time attack.

1. After the Eclipse, visit a newly discovered or debug-placed manor. On the
   first conversation choose **Let us speak**; armor questions and the relevant
   readiness option should work immediately, without closing and reopening.
2. Receive armor, exit dialogue and wait briefly: there should be no attack.
   Activating a debug-created charm now should explain that readiness is missing.
3. Agree to prepare through dialogue. Test again with an existing six-piece or
   packed set: no duplicate armor. Save/reload before starting the attack.
4. Activate the charm outside the manor, then inside. Cancel once, then confirm.
   Cancellation must leave preparation intact; confirmation must start the siege.
5. Escape beyond either exit. Check the journal and next-goal message, then
   save/reload. The charm must explain that the event is complete, and a new
   conversation/directions query must not reset the manor or grant another suit.
6. Check a pre-Eclipse character, an old prepared save, and English/Russian/Chinese.
   Record any new debug.log errors and the exact refusal if a valid step fails.
