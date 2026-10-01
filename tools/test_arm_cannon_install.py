"""Check installation transaction and activation configuration without CDDA.

The small interpreter exercises the shipped EOC, including an injected failed
bionic addition. It does not test CDDA's inventory UI or native JSON loader.
"""

import json
from pathlib import Path
import unittest


MOD = Path(__file__).resolve().parents[1] / "mods" / "Berserk"
CANNON = "bio_berserk_arm_cannon"
STUMP = "bio_berserk_hand_stump"


class InstallTransaction:
    def __init__(self, bionics=(), copies=1, fail_add=False):
        self.bionics = list(bionics)
        self.copies = copies
        self.fail_add = fail_add
        self.operations = []
        self.messages = []

    def condition(self, value):
        if "and" in value:
            return all(self.condition(part) for part in value["and"])
        if "not" in value:
            return not self.condition(value["not"])
        if "u_has_bionics" in value:
            return value["u_has_bionics"] in self.bionics
        if "u_has_items" in value:
            item = value["u_has_items"]
            assert item["item"] == CANNON
            return self.copies >= item["count"]
        raise AssertionError(value)

    def effect(self, value):
        if isinstance(value, list):
            for part in value:
                self.effect(part)
        elif "if" in value:
            key = "then" if self.condition(value["if"]) else "else"
            if key in value:
                self.effect(value[key])
        elif "u_add_bionic" in value:
            self.operations.append("add")
            if not self.fail_add:
                self.bionics.append(value["u_add_bionic"])
        elif "u_consume_item" in value:
            assert value["u_consume_item"] == CANNON
            assert CANNON in self.bionics, "item consumed before installed"
            self.operations.append("consume")
            self.copies -= value["count"]
        elif "u_message" in value:
            self.messages.append(value["u_message"])
        else:
            raise AssertionError(value)

    def activate(self):
        eoc = json.loads((MOD / "effects/arm_cannon_install_eocs.json").read_text())[0]
        key = "effect" if self.condition(eoc["condition"]) else "false_effect"
        self.effect(eoc[key])


class ArmCannonInstallTests(unittest.TestCase):
    def test_success_consumes_one_after_add_and_repeat_preserves_spare(self):
        transaction = InstallTransaction((STUMP,), copies=2)
        transaction.activate()
        self.assertEqual(transaction.operations, ["add", "consume"])
        self.assertEqual(transaction.copies, 1)
        self.assertEqual(transaction.bionics.count(CANNON), 1)
        transaction.activate()
        self.assertEqual(transaction.operations, ["add", "consume"])
        self.assertEqual(transaction.copies, 1)
        self.assertEqual(transaction.bionics.count(CANNON), 1)

    def test_refusals_preserve_item_and_installed_bionics(self):
        for bionics, copies in (((), 1), ((STUMP, CANNON), 1), ((STUMP,), 0)):
            with self.subTest(bionics=bionics, copies=copies):
                transaction = InstallTransaction(bionics, copies)
                transaction.activate()
                self.assertEqual(transaction.copies, copies)
                self.assertEqual(transaction.bionics, list(bionics))
                self.assertFalse(transaction.operations)

    def test_failed_add_preserves_item_and_can_be_retried(self):
        transaction = InstallTransaction((STUMP,), fail_add=True)
        transaction.activate()
        self.assertEqual(transaction.copies, 1)
        self.assertNotIn(CANNON, transaction.bionics)
        self.assertEqual(transaction.operations, ["add"])
        self.assertIn("could not be installed", transaction.messages[-1])
        transaction.fail_add = False
        transaction.activate()
        self.assertEqual(transaction.copies, 0)
        self.assertEqual(transaction.bionics.count(CANNON), 1)

    def test_activation_bypasses_obtain_and_generic_cbm_auto_consumption(self):
        items = json.loads((MOD / "items/bionics/arm_cannon_cbms.json").read_text())
        item = next(obj for obj in items if obj["id"] == CANNON)
        # ALLOWS_REMOTE_USE skips loc.obtain() in avatar_action::use_item.
        self.assertIn("ALLOWS_REMOTE_USE", item["flags"])
        self.assertFalse(item["use_action"]["need_wielding"])
        # BIONIC_ITEM and SINGLE_USE would be consumed even after EOC refusal.
        self.assertEqual(item["subtypes"], ["TOOL"])
        self.assertNotIn("copy-from", item)
        self.assertNotIn("SINGLE_USE", item["flags"])
        self.assertEqual(item["charges_per_use"], 0)
        self.assertEqual((item["weight"], item["volume"]), ("3500 g", "3000 ml"))
        self.assertNotIn("difficulty", item)

    def test_same_recipe_and_installed_bionic_dependency(self):
        recipes = json.loads((MOD / "recipes/arm_cannon_recipes.json").read_text())
        self.assertTrue(any(obj.get("result") == CANNON for obj in recipes))
        bionics = json.loads((MOD / "bionics/arm_cannon.json").read_text())
        bionic = next(obj for obj in bionics if obj["id"] == CANNON)
        self.assertEqual(bionic["required_bionic"], STUMP)
        self.assertEqual(bionic["fake_weapon"], "berserk_arm_cannon_gun")
        guns = json.loads((MOD / "items/guns/arm_cannon.json").read_text())
        self.assertFalse(any("use_action" in obj for obj in guns))


if __name__ == "__main__":
    unittest.main()
