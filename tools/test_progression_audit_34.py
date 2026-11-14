"""Exercise real progression conditions with fixtures for native map placement."""
import unittest

from test_reference_journal_33 import Book, EOCS


P = "EOC_BERSERK_"


class Field(Book):
    def value(self, expression):
        expression = expression.replace("u_val('pos_x')", str(self.pos[0]))
        expression = expression.replace("u_val('pos_y')", str(self.pos[1]))
        expression = expression.replace("time('30 minutes')", "1800")
        return super().value(expression)

    def run(self, id_):
        if id_ == P + "GODO_SEEK":
            self.calls.append(id_)
            return  # Simulate a failed native placement.
        return super().run(id_)

    def effect(self, action):
        if isinstance(action, dict) and "remove_active_mission" in action:
            self.missions.pop(action["remove_active_mission"], None)
            return
        if isinstance(action, dict) and "reveal_map" in action:
            return
        if isinstance(action, dict) and action.get("assign_mission") == "MISSION_BERSERK_GRUNBELD":
            assert "MISSION_BERSERK_GRUNBELD" not in self.missions
            self.missions["MISSION_BERSERK_GRUNBELD"] = self.values["berserk_hunt_grunbeld_location"]
            return
        return super().effect(action)


class ProgressionAudit(unittest.TestCase):
    def test_completed_refusal_survives_every_later_transformation(self):
        f = Field()
        f.values.update(berserk_eclipse_era=1, u_berserk_eclipse_route=2,
                        u_berserk_apostol_return_state=2, u_berserk_apostol_outcome=2)
        for path, lineage in [(0, 0), (2, 6), (3, 10), (4, 14)]:
            with self.subTest(path=path):
                f.values.update(u_berserk_apostol_path=path, u_berserk_apostol_lineage=lineage,
                                u_berserk_apostol_schema=1, u_berserk_apostol_stage=bool(path))
                for event in ("APOSTOL_CONTINUATION_READY", "JOURNAL_BREACH_LOCATE"):
                    self.assertTrue(f.condition(EOCS[P + event]["condition"]), event)
                self.assertFalse(f.condition({"test_eoc": P + "APOSTOL_GIFT_LINE"}))
        f.values["u_berserk_apostol_return_state"] = 1
        self.assertFalse(f.condition({"test_eoc": P + "APOSTOL_CONTINUATION_READY"}))

    def test_any_early_pact_unlocks_both_stronghold_route_and_boss_retry(self):
        f = Field()
        f.values.update(berserk_eclipse_era=1, u_berserk_eclipse_rescue_state=2,
                        u_berserk_flora_escaped=1, berserk_flora_stage=3)
        f.om = "berserk_grunbeld_crucible"
        f.pos = (12, 12, 0)
        for boss in ("count", "wyald", "rosine"):
            with self.subTest(boss=boss):
                f.values.update({f"berserk_hunt_{name}_state": (2 if name == boss else 4)
                                 for name in ("count", "wyald", "rosine")})
                events = ["GRUNBELD_SEEK", "NEXT_STRONGHOLD_GUIDE", "GRUNBELD_RETRY"]
                for resolution in (0, 1):
                    flag = f"u_berserk_pact_resolved_{boss}"
                    f.values[flag] = resolution
                    for event in events:
                        self.assertEqual(f.condition(EOCS[P + event]["condition"]),
                                         bool(resolution), event)
                f.values[flag] = 0
        f.values["u_berserk_pact_resolved_rosine"] = 1
        f.values["berserk_apostle_grunbeld_dead"] = 1
        self.assertTrue(f.condition({"test_eoc": P + "GRUNBELD_SEEK"}))
        self.assertFalse(f.condition({"test_eoc": P + "GRUNBELD_RETRY"}))

    def test_flora_referral_recovers_only_after_a_real_forge_is_found(self):
        f = Field()
        f.values.update(berserk_eclipse_era=1, u_berserk_apostol_return_state=2,
                        berserk_hunt_count_state=4, berserk_hunt_wyald_state=4,
                        u_berserk_pact_resolved_rosine=1, u_berserk_flora_referral_issued=1,
                        berserk_godo_location=(0, 0, 0))  # Old unverified target.
        definition = EOCS[P + "GODO_KNOWN"]["condition"]
        f.overrides[P + "GODO_KNOWN"] = False
        f.missions["MISSION_BERSERK_FLORA_REFERRAL"] = (0, 0, 0)
        check, seek = (P + "LATE_FLORA_CHECK", P + "GODO_SEEK")
        f.run(check)
        f.now += 60
        f.run(check)
        self.assertEqual(f.calls.count(seek), 1)
        self.assertFalse(f.missions)
        f.now += 1800
        f.run(check)
        self.assertEqual(f.calls.count(seek), 2)
        forge = (1920, -960, 0)
        f.values["berserk_godo_location"] = forge
        f.terrain[forge] = "berserk_godo_workshop"
        f.overrides[P + "GODO_KNOWN"] = f.condition(definition)
        f.run(check)
        f.run(check)
        self.assertEqual(f.missions, {"MISSION_BERSERK_FLORA_REFERRAL": forge})
        self.assertEqual(len(f.messages), 1)

    def test_already_met_flora_does_not_send_player_back_to_forge(self):
        f = Field()
        f.values.update(berserk_eclipse_era=1, u_berserk_eclipse_rescue_state=2,
                        berserk_hunt_count_state=4, berserk_hunt_wyald_state=4,
                        berserk_hunt_rosine_state=4, u_berserk_flora_met=1)
        f.run(P + "LATE_FLORA_CHECK")
        self.assertFalse(f.missions)
        self.assertNotIn(P + "GODO_SEEK", f.calls)

    def test_legacy_stronghold_coordinates_recover_without_generating_a_duplicate(self):
        f = Field()
        location = (600, -1200, 0)
        f.values.update(berserk_eclipse_era=1, u_berserk_eclipse_rescue_state=2,
                        berserk_flora_stage=3, berserk_hunt_count_state=4,
                        berserk_hunt_wyald_state=4, berserk_hunt_rosine_state=4,
                        berserk_hunt_grunbeld_location=location, u_berserk_road_journal_issued=1)
        f.terrain[location] = "berserk_grunbeld_crucible"
        f.run(P + "GRUNBELD_SEEK")
        f.run(P + "GRUNBELD_SEEK")
        self.assertEqual(f.values["berserk_hunt_grunbeld_location"], location)
        self.assertEqual(f.missions, {"MISSION_BERSERK_GRUNBELD": location})
        self.assertNotIn(P + "GRUNBELD_FIND", f.calls)


if __name__ == "__main__":
    unittest.main()
