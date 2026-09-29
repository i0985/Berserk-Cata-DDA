# Eclipse field: test build for CDDA 0.I-1

This branch changes the six-OMT Eclipse from connected flesh-walled rooms into
an open sacrificial field. The positions and overmap terrain IDs are unchanged
for saved worlds; **already generated tiles in an old save will keep their old
map**, while a newly placed Eclipse uses this field layout. The older one-OMT
test terrains and their return seals remain for save compatibility.

## Entry and completion

- Confirming Behelit activation records the origin and searches for a safe new
  six-OMT destination. Declining or failing placement/teleportation leaves the
  Behelit in inventory.
- Only after the character is confirmed in the entry OMT does the EOC mark the
  run active, set a spent flag, and consume one Behelit. Further Behelits do not
  start another run for this character. Check the exact inventory count in game.
- The entry has a sealed scar, not a usable return seal. Old saves with the
  previous seal and no spent flag can still use it to escape. The original
  return-point logic remains available to the Skull Knight rescue and the
  victory ending. If all return attempts fail, his rift in the final OMT lets
  the player retry after intervention, even without a Behelit.
- The final-area low-HP rescue, lethal-hit protection, Griffith victory EOC,
  one-time aftermath, lost hand/eye and new world era are preserved. There is
  no overall exploration timer and no new timed final scene yet.
- Griffith's Eclipse manifestation is fixed at the ceremony site, so it cannot
  chase the player across an OMT boundary before the fight. Victory no longer
  depends on the player's exact OMT; all six dungeon OMTs are checked before
  the return is committed. The temporary Skull Knight may appear on the open
  field rather than requiring an indoor tile. The Brand and eye records are
  standalone bionics, so old saves no longer seek nonexistent parent CBMs.
- An old save already made **after** Griffith died without his victory EOC has
  no reliable completion flag. Reload a save from before his defeat for this
  test; do not assume the fixed death hook can replay a past kill.

## Field layout

| OMT | Scene | Optional discovery |
| --- | --- | --- |
| Entry (northwest) | Open landing on living ground | Passage seals behind the player |
| Traces (northeast) | Judeau, exposed supplies and hunter | Knife hilt; guarded bandages and painkillers |
| Torn field (midwest) | Pits, ridges and Pippin | Broken clasp and a trail suggesting two routes |
| Feast (mideast) | Demons gathered around the fallen | Corkus and a scene that can be bypassed |
| Approach (southwest) | Pits, stronger enemies and quiet scars | Gaston; warning before Griffith |
| Ceremony (southeast) | Griffith on an open field | Two endings; rift for retrying a blocked rescue |

All four bodies remain item objects with their gear; examinable markers now
add a short individual popup. Judeau's hilt and Pippin's clasp are optional
items. Carrying either enables extra conditional Skull Knight responses during
rescue, victory or a later conversation. Neither gates the finale. The cache
and the feast are also optional. The pit tiles use vanilla `t_pit`: stepping in
is dangerous. The open ground uses the flesh floor's existing UltiCa art as a
fallback, without an indoor roof. Glowing flesh supplies fixed light points;
colored-light behavior and the exact atmosphere need visual testing in game.

The eastern and western middle OMTs both provide a safe route from entry to
finale even if the other middle OMT is excluded. A static flood-fill checks
these routes and the four bodies, memory items and Griffith's position. It
cannot prove monster movement, line of sight, loot drops or the visual result.

## In-game checks when available

1. Use a disposable world and one Behelit. Decline entry, then try from an
   area where no destination can be placed; item count must stay unchanged.
   Successfully enter and verify exactly one item disappears. Save/reload
   inside; a second Behelit must not reopen the Eclipse after completion.
2. Inspect the landing scar, both middle paths, the four bodies and the pits.
   Collect neither, one, then both memory items on separate test runs. Talk
   to the Skull Knight and confirm only matching extra lines are offered.
3. Visit the cache and feast or bypass them. Check that the cache contains
   bandages and aspirin, with a hunter close enough to pose a real risk.
4. In the final OMT, test rescue via low head/torso HP, a fatal blow and
   Griffith's defeat. Check the return, one-time aftermath, old save with a
   usable return seal, and the rescue rift if return is deliberately blocked.
5. Check UltiCa and the optional graphics mod, three languages, save/reload,
   and `debug.log`. No CDDA game binary was run for this change.
