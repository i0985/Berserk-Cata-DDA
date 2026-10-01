# Arm cannon: inventory attachment, CDDA 0.I-1

## Scope and source findings

This patch changes attachment of the crafted item, not the cannon's weight,
damage, ammunition, deployed weapon or missing-hand penalties.

The exact reported inventory UI interaction has not been reproduced in CDDA.
The following paths were checked against **tag 0.I-1**:

- [avatar_action.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/avatar_action.cpp):
  `avatar_action::use_item` normally obtains an item before invoking its action.
  `ALLOWS_REMOTE_USE` instead invokes it in place, bypassing extraction/pickup.
- [item.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/item.cpp)
  and [character.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/character.cpp):
  one-handed wielding has a weight/arm-strength check. A rejection when wielding
  the physical cannon must not be a prerequisite for attachment.
- [iuse_actor.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/iuse_actor.cpp):
  the `effect_on_conditions` actor defaults to not requiring wielding. It can
  return a successful invocation even when its EOC condition rejects attachment.
- `Character::invoke_item` then automatically removes `BIONIC_ITEM` objects.
  This removal can happen after a rejected EOC, independently of our explicit
  `u_consume_item` effect.
- [wish.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/wish.cpp):
  the debug installation menu lists item types with the native `install_bionic`
  action. The custom attachment action replaces it, so the cannon was already
  omitted from that menu. This is separate from `required_bionic`.
- [bionics.cpp](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I-1/src/bionics.cpp):
  direct bionic addition does not enforce the normal surgical prerequisite.
  The attachment EOC must continue checking for the missing-hand bionic itself.

## Change and compatibility

The physical item keeps ID **bio_berserk_arm_cannon**, its displayed name,
recipe, sprite, 3500 g weight and 3000 ml volume. It is now a standalone
zero-charge `TOOL` with `ALLOWS_REMOTE_USE`, rather than inheriting the surgical
`BIONIC_ITEM` slot from `bionic_general`. This avoids generic automatic CBM
consumption on refusal. The installed bionic remains unchanged and has the
same ID; installed cannons and the missing-hand dependency are preserved.

Attachment requires the missing-hand bionic, no existing cannon bionic, and
one cannon item in the character's inventory. It adds the bionic, verifies
its presence, and only then consumes one crafted item. Failure retains it.

The cannon is attached through its inventory action, rather than an autodoc
or the debug **install bionic** list. For debugging, use **spawn item**, search
for `prosthetic arm cannon CBM` / `КБМ руки-пушки` (ID above), and activate the
item after granting the missing-hand bionic. Do not add native `install_bionic`
to this TOOL: the debug menu assumes that action has a surgical bionic slot.

## Checks performed without the game

- EOC transaction tests: normal success, a spare copy, repeated activation,
  missing hand absent, already installed, no carried item, injected failed
  bionic addition and a successful retry.
- Activation flags, zero charge use, stable recipe ID, unchanged dependency,
  physical weight/volume and separate deployed weapon.
- Repository JSON/assets validator, translation catalogs, unit suite and ZIP
  integrity checks.

These checks do not execute the native inventory UI, JSON loader, debug menu,
bionic deployment or save loader. No CDDA executable was launched.

## User playtest

Install the archive into `mods` beside `cataclysm-tiles.exe`, replacing the old
Berserk folder. Remove a second copy from `data/mods` if present. Back up the save.

1. With the missing left-hand bionic, put one crafted cannon in a backpack.
   Leave the right hand empty. **Activate** the inventory item, not **wield** it.
   Expect one installed cannon and one consumed item.
2. Repeat on a separate test save with the right hand holding a sword, and
   with low strength. Inventory attachment must still work without wielding
   the 3.5 kg physical item. Check a container nested inside a backpack too.
3. Without the missing-hand bionic, activation must explain the refusal and
   retain the item. With a cannon already installed, a spare must also remain.
   Start with two copies: successful attachment consumes exactly one.
4. Load an old save with a previously crafted item; attach it and save/reload.
   Also reload a save with a previously installed cannon. Deploy, reload, fire
   and retract it. Check the open/closed sprites and new entries in debug.log.
5. Check the action, description and failure text in English, Russian and
   Simplified Chinese. Debug-spawn the physical item by its ID if required.

Actual UI behavior, old-save loading and bionic deployment await user testing.
