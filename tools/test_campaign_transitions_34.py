"""Exercise seal commits against the furniture result, including retry and payout."""

from collections import Counter
import unittest

from test_reference_journal_33 import Book, EOCS


PREFIX = "EOC_BERSERK_"
SITE = (1, 0, 0)


class SealSite(Book):
    def __init__(self):
        super().__init__()
        self.values["_pos"] = SITE
        self.calls = Counter()

    def run(self, name):
        self.calls[name] += 1
        if name in EOCS and any(name.endswith(suffix) for suffix in ("_SEAL_COMMIT", "_REGISTER_SEAL", "_CLAIM",
                                                                    "_BREACH_CLOSE_COMMIT")):
            event = EOCS[name]
            if self.condition(event["condition"]):
                self.effect(event["effect"])
            elif "false_effect" in event:
                self.effect(event["false_effect"])


class CampaignSeals(unittest.TestCase):
    def test_ashen_commit_waits_for_replacement_and_issues_journal_once(self):
        world = SealSite()
        world.furniture[SITE] = "f_berserk_open_breach"
        commit = PREFIX + "BREACH_CLOSE_COMMIT"
        world.run(commit)
        self.assertEqual(world.values.get("u_berserk_breach_sealed", 0), 0)
        self.assertIn("запечатать", world.messages[-1]["u_message"].lower())
        self.assertFalse(world.calls[PREFIX + "CAMPAIGN_GIVE_JOURNAL"])
        world.furniture[SITE] = "f_berserk_sealed_breach"
        world.run(commit)
        self.assertEqual(world.values["u_berserk_breach_sealed"], 1)
        self.assertEqual(world.values["berserk_hunt_first_breach_state"], 4)
        self.assertEqual(world.calls[PREFIX + "CAMPAIGN_GIVE_JOURNAL"], 1)
        world.run(commit)
        self.assertEqual(world.calls[PREFIX + "CAMPAIGN_GIVE_JOURNAL"], 1)
        self.assertEqual(len(world.messages), 2)

    def test_named_seals_block_reward_until_success_and_pay_once(self):
        cases = (
            ("count", "berserk_count_dungeon", None),
            ("wyald", "berserk_wyald_ring", "berserk_wyald_beast_knot"),
            ("rosine", "berserk_rosine_nest", "berserk_rosine_mistvale_veil"),
            ("grunbeld", "berserk_grunbeld_crucible", "berserk_grunbeld_carapace_shard"),
        )
        for boss, terrain, relic in cases:
            with self.subTest(boss=boss):
                world = SealSite()
                world.om = terrain
                stage = f"berserk_hunt_{boss}_state"
                world.values.update(dict(berserk_eclipse_era=1, u_berserk_eclipse_rescue_state=2))
                world.values[stage] = 3
                world.furniture[SITE] = f"f_berserk_{boss}_breach"
                commit = PREFIX + boss.upper() + "_SEAL_COMMIT"
                reward = PREFIX + (boss.upper() + "_CLAIM" if relic else "COUNT_REGISTER_SEAL")
                world.run(commit)
                world.run(reward)
                self.assertEqual(world.values[stage], 3)
                self.assertFalse(world.inventory)
                self.assertFalse(world.calls[PREFIX + "COUNT_REWARD_REGISTER"])
                world.furniture[SITE] += "_sealed"
                world.run(commit)
                self.assertEqual(world.values[stage], 4)
                world.run(reward)
                world.run(reward)
                if relic:
                    self.assertEqual(world.values[stage], 5)
                    self.assertEqual(world.inventory[relic], 1)
                else:
                    self.assertEqual(world.calls[PREFIX + "COUNT_REWARD_REGISTER"], 1)
