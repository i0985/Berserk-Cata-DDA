"""Regression checks for conditional dialogue syntax in CDDA 0.I-1.

These are static schema checks, not a native game-loading test.
"""

import json
from pathlib import Path
import unittest

from validate_mod_assets import ROOT, ValidationError, validate_dynamic_lines


class DynamicLineCompatibility(unittest.TestCase):
    def check(self, line):
        validate_dynamic_lines(ROOT / "example.json", [
            {"type": "talk_topic", "dynamic_line": line}
        ])

    def test_rejects_eoc_if_wrapper_and_logical_line_wrappers(self):
        for condition in (
            {"if": {"math": ["berserk_flora_stage == 2"]}},
            {"and": [{"u_has_item": "test"}]},
            {"or": [{"u_has_item": "test"}]},
            {"not": {"u_has_item": "test"}},
        ):
            with self.subTest(condition=condition), self.assertRaises(ValidationError):
                self.check({**condition, "yes": "yes", "no": "no"})

    def test_rejects_wrapper_in_nested_branches_and_concatenation(self):
        invalid = {"if": {"math": ["1 == 1"]}, "yes": "wrong"}
        for line in (
            ["hello", invalid],
            {"math": ["1 == 1"], "yes": invalid},
            {"math": ["1 == 1"], "no": invalid},
            {"concatenate": ["hello", invalid]},
        ):
            with self.subTest(line=line), self.assertRaises(ValidationError):
                self.check(line)

    def test_supported_lines_and_response_conditions_remain_allowed(self):
        for line in (
            "hello", {"str": "translated"}, ["hello", "goodbye"],
            {"math": ["berserk_flora_stage == 2"], "yes": "leave", "no": "welcome"},
            {"concatenate": ["hello", {"u_has_item": "test", "yes": "found it"}]},
        ):
            self.check(line)
        validate_dynamic_lines(ROOT / "example.json", [{
            "type": "talk_topic", "dynamic_line": "hello",
            "responses": [{"condition": {"and": [{"math": ["1 == 1"]}]}}],
        }])

    def test_all_mod_dialogues_use_compatible_wrappers(self):
        for path in (ROOT / "mods").glob("*/dialogue/*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            validate_dynamic_lines(path, data if isinstance(data, list) else [data])


if __name__ == "__main__":
    unittest.main()
