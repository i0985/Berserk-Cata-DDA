"""Static turn_cost regressions based on CDDA 0.I-1's duration parser."""

import unittest

from validate_mod_assets import ROOT, ValidationError, validate_turn_cost_durations


class TurnCostDurationTests(unittest.TestCase):
    def check(self, value):
        validate_turn_cost_durations(ROOT / "example.json", [{
            "type": "effect_on_condition",
            "effect": [{"if": {"math": ["1 == 1"]}, "then": {"turn_cost": value}}],
        }])

    def test_accepts_native_unit_strings_and_other_value_forms(self):
        for value in (
            "1 second", "3 seconds", "1 s", "1 turn", "2 turns", "1 t",
            "2 minutes", "1 minute", "1 m", "1 hour", "2 hours", "1 h",
            "1 day", "2 days", "1 d", "1 hour 30 minutes", "infinite",
            1, {"u_val": "action_duration"}, ["1 second", "3 seconds"],
        ):
            with self.subTest(value=value):
                self.check(value)

    def test_rejects_invalid_unit_suffixes_and_noninteger_literal_quantities(self):
        for value in ("1 sec", "3 secs", "1 secondx", "0.5 seconds", "", "seconds"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.check(value)

    def test_rejects_bad_unit_inside_duration_range(self):
        with self.assertRaises(ValidationError):
            self.check(["1 second", "3 sec"])


if __name__ == "__main__":
    unittest.main()
