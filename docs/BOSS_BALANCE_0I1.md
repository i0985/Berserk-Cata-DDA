# Apostle combat balance: CDDA 0.I-1 draft

This is a **static tuning pass**, not a claim of combat balance after playtesting.
Reference: CleverRaven/Cataclysm-DDA tag `0.I-1` (`7b2efa5c`), especially
`data/json/monsters/zed_misc.json`, `jabberwock.json`, `nether.json`, and
`src/monster.cpp` (`monster::process_effects`, `monster::on_load`).

| Vanilla enemy | HP | Speed | Dodge | Active regeneration | Relevant threat |
| --- | ---: | ---: | ---: | ---: | --- |
| Zombie brute | 120 | 105 | inherited | 0 | Smash, armor |
| Mi-go | 210 | 120 | 4 | 0 | Cut, poison, mobility |
| Jabberwock | 400 | 140 | 3 | 0 | High melee, armor, poison |
| Zombie hulk | 480 | 130 | inherited | 0 | Heavy smash, armor, destruction |
| Shoggoth | 400 | 90 | inherited | 50 | Exception: regeneration plus splitting and item absorption |

In 0.I-1, `regenerates` feeds `heal` in `monster::process_effects`; it is not
simply an extra HP pool. The engine also has slower healing while a monster is
unloaded. Setting `regenerates: 0` removes the active combat regeneration
without claiming that the monster will never heal by other means. The old
Zodd value was **45**, not 100.

| Mod encounter | Old HP / speed / dodge / active regen | Draft HP / speed / dodge / active regen | Combat identity |
| --- | --- | --- | --- |
| Zodd projection | 380 / 90 / 3 / 0 | 250 / 90 / 1 / 0 | Heavy blow; no smash or sustained healing |
| Griffith reflection | 330 / 115 / 4 / 0 | 220 / 105 / 2 / 0 | Short wing strike; no stun aura |
| Void reflection | 300 / 105 / 3 / 0 | 200 / 95 / 2 / 0 | Rare, smaller psychic blast; no reality shift |
| Original Zodd | 1000 / 100 / 5 / 45 | 600 / 110 / 2 / 0 | Durable pursuer; leap and slower heavy smash |
| Original Griffith | 850 / 180 / 10 / 35 | 440 / 135 / 5 / 0 | Mobile, brief despair aura, short wing strike |
| Original Void | 600 / 150 / 8 / 20 | 400 / 110 / 3 / 0 | Psychic pressure and a short-range pure-damage shift |
| Eclipse Griffith | 650 / 125 / 5 / 0 | 440 / 120 / 4 / 0 | Survival and rescue remain the story objectives; victory remains possible |

The originals retain their old IDs, drops and scenario hooks. Projections have
their own reduced melee skill/damage and explicitly replace inherited attack
lists. Zodd's leap now tops out at 12 bash + 8 cut; his smash at 35 bash with
a 30% knockdown chance, every 18 turns for the original. Griffith's wing
strike is capped at range 2, and the despair aura lasts 2 turns in radius 3.
Void's psychic blast deals 8–12 pure damage in radius 3 with 1–2 turns of
stun; the original's reality shift deals 10 pure damage. The reflection's
psychic attempt is less frequent than the original's. These are attack
configuration values, **not measured damage after armor or player actions**.

## Game checks when available

Use three saves or debug-created characters on CDDA 0.I-1, preferably with
comparable weapon/armor quality before adding the armor's bonuses:

1. A prepared ordinary survivor with good armor, a solid melee weapon or
   firearm, spare ammunition, and a way to retreat. Each laboratory projection
   should be dangerous but beatable without 20/20 attributes. Check that
   obstacles and retreat actually matter.
2. A character with the prosthetic arm/cannon but without Berserker armor.
   Check whether ammunition and reload windows make a difference against an
   original apostle; fighting a projection must not require the cannon.
3. Guts in Berserker armor with high attributes. Original Zodd should still
   pressure him with movement and smash, while Eclipse Griffith should not
   require draining an endlessly replenished HP bar. Verify rescue and the
   victory path separately.

Log fight length, number of hits taken, maximum damage to one body part,
retreat opportunities and whether any attack chain prevents acting. Then tune
one variable at a time. No game binary was run for this pass. Previously
spawned monsters in old saves retain their IDs; check actual stat refresh on
load rather than assuming it.
