"""Regressions for the native 0.I GENERIC dispatch failure (29 October).

These verify exported data and the repository guard, not a running game.
"""
import copy
import unittest
from unittest.mock import patch

import validate_mod_assets as validator


class ItemLoaderSchemaTests(unittest.TestCase):
    path = validator.ROOT / "mods/Berserk/items/forge_woodland_leads.json"

    def test_legacy_dispatch_is_rejected_but_item_and_other_types_are_allowed(self):
        with self.assertRaisesRegex(validator.ValidationError, "type GENERIC"):
            validator.validate_legacy_item_types(
                self.path, [{"type": "GENERIC", "id": "old_sketch"}]
            )
        validator.validate_legacy_item_types(
            self.path,
            [{"type": "ITEM", "subtypes": ["TOOL"]}, {"type": "item_group"}],
        )

    def test_repository_guard_catches_original_broken_export(self):
        original = validator.top_level_objects

        def broken_sketch(path):
            objects = original(path)
            if path == self.path:
                objects = copy.deepcopy(objects)
                objects[0]["type"] = "GENERIC"
                objects[0].pop("subtypes", None)
            return objects

        with patch.object(validator, "top_level_objects", side_effect=broken_sketch):
            with self.assertRaisesRegex(
                validator.ValidationError, "forge_woodland_leads.json.*GENERIC"
            ):
                validator.validate_repository()

    def test_exported_sketch_can_read_without_wielding_or_charges(self):
        item, = validator.top_level_objects(self.path)
        self.assertEqual(item["id"], "berserk_forge_woodland_sketch")
        self.assertEqual(item["type"], "ITEM")
        self.assertIn("TOOL", item["subtypes"])
        self.assertEqual(item["charges_per_use"], 0)
        self.assertIn("ALLOWS_REMOTE_USE", item["flags"])
        self.assertFalse(item["use_action"]["need_wielding"])
        self.assertEqual(
            item["use_action"]["effect_on_conditions"],
            ["EOC_BERSERK_FIX28_BEHELIT_LEAD_READ"],
        )


if __name__ == "__main__":
    unittest.main()
