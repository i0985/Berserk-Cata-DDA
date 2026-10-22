"""Regression for the mandatory recipe member reported by native CDDA 0.I."""
import copy
import unittest
from unittest.mock import patch

import validate_mod_assets as validator


class RecipeActivityLevelTests(unittest.TestCase):
    path = validator.ROOT / "mods/Berserk/recipes/reference_journal.json"

    def test_standalone_recipe_types_require_activity_level(self):
        for kind in ("recipe", "uncraft", "practice", "nested_category"):
            with self.subTest(kind=kind), self.assertRaisesRegex(
                validator.ValidationError, "activity_level"
            ):
                validator.validate_recipe_activity_level(
                    self.path, [{"type": kind, "result": "notebook"}]
                )

    def test_copy_from_can_inherit_the_member(self):
        validator.validate_recipe_activity_level(
            self.path, [{"type": "recipe", "copy-from": "notebook", "result": "journal"}]
        )

    def test_explicit_activity_level_must_be_a_nonempty_string(self):
        for value in (None, True, 0, [], {}, "", " "):
            with self.subTest(value=value), self.assertRaisesRegex(
                validator.ValidationError, "activity_level"
            ):
                validator.validate_recipe_activity_level(
                    self.path,
                    [{"type": "recipe", "copy-from": "notebook", "activity_level": value}],
                )

    def test_real_journal_recipe_has_light_exertion(self):
        objects = validator.top_level_objects(self.path)
        self.assertEqual(objects[0]["activity_level"], "LIGHT_EXERCISE")
        validator.validate_recipe_activity_level(self.path, objects)

    def test_repository_validation_rejects_original_broken_recipe(self):
        original = validator.top_level_objects

        def without_activity_level(path):
            objects = original(path)
            if path == self.path:
                objects = copy.deepcopy(objects)
                objects[0].pop("activity_level", None)
            return objects

        with patch.object(validator, "top_level_objects", side_effect=without_activity_level):
            with self.assertRaisesRegex(
                validator.ValidationError, "reference_journal.json.*activity_level"
            ):
                validator.validate_repository()


if __name__ == "__main__":
    unittest.main()
