#!/usr/bin/env python3
"""Run scripted campaign transitions or a timed 100-turn sample in CDDA 0.I-1."""

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
import time

import pexpect
import pyte

ROOT = Path(__file__).resolve().parents[1]
WORLD = "BerserkCI"
SEED = "EarlyGuts34"
ENGINE = "7b2efa5cea38e4d4d97dd0e63b28b9148623da59"
PACKAGES = ("Berserk", "Berserk_chibi_tileset")
TESTS = {
    "suite": (
        ("early-start", "new world, early Guts, base STR/DEX 10/10"),
        ("rescue-pending", "normal rescue pending, safe arrival unconfirmed"),
        ("rescue-complete", "normal rescue pending, safe arrival confirmed"),
        ("flora-escaped", "active siege, outside boundary at 29 seconds"),
        ("flora-ruins", "escape complete, fire timer aged to 600 seconds"),
        ("breach-retry", "ashen seal commit on a tile without closed furniture"),
        ("breach-confirmed", "native map update installed the closed furniture"),
    ),
    "alternate": (
        ("alternate-pending", "ordinary survivor, route 2 refusal, landing unconfirmed"),
        ("alternate-complete", "ordinary survivor, route 2 refusal, safe surface landing confirmed"),
    ),
}
LOCATION_FALLBACKS = ("berserk_godo_workshop", "berserk_first_hunt_lair")


def math(expression):
    return {"math": [expression]}


def invoke(stem):
    return {"run_eocs": "EOC_BERSERK_" + stem}


def marker(label):
    return {"u_message": label, "popup": True}


def probe(label, *conditions):
    return {
        "if": {"and": [math(c) if isinstance(c, str) else c for c in conditions]},
        "then": marker("PASS " + label),
        "else": marker("FAIL " + label),
    }


def location(name):
    return {"global_val": name}


def target(name, terrain, special):
    return {"u_location_variable": location(name), "target_params": {
        "om_terrain": terrain, "om_special": special, "random": True, "search_range": 140, "min_distance": 0, "z": 0,
    }}


def suite():
    breach = {"context_val": "pos"}
    return [
        probe("early-start", {"u_profession": "berserk_before_eclipse"},
              {"u_has_item": "true_guts_early_sword"}, "u_val('strength') == 10",
              "u_val('dexterity') == 10", "berserk_eclipse_era == 0"),
        math("u_berserk_eclipse_rescue_state = 1"), math("u_berserk_rescue_safety_schema = 1"),
        math("u_berserk_eclipse_trial_active = 1"),
        math("u_berserk_rescue_safe_arrival = 0"), invoke("ECLIPSE_RESCUE_COMMIT_IF_RETURNED"),
        probe("rescue-pending", "u_berserk_eclipse_rescue_state == 1",
              "u_berserk_hand_recipes_learned == 0"),
        math("u_berserk_rescue_safe_arrival = 1"), invoke("ECLIPSE_RESCUE_COMMIT_IF_RETURNED"),
        probe("rescue-complete", "u_berserk_eclipse_rescue_state == 2",
              "u_berserk_eclipse_trial_active == 0", "u_berserk_hand_recipes_learned == 1",
              {"u_has_bionics": "bio_berserk_brand_of_sacrifice"}),
        {"u_location_variable": location("berserk_flora_location")},
        {"u_location_variable": location("berserk_flora_center"), "x_adjust": -40},
        math("berserk_flora_treehouse_layout = 4"), math("berserk_flora_siege_state = 2"),
        math("berserk_flora_siege_v2 = 1"), math("berserk_flora_fire_phase = 1"),
        math("berserk_flora_siege_started = time('now') - 29"), invoke("FLORA_SIEGE_TICK"),
        probe("flora-escaped", "berserk_flora_siege_state == 5", "u_berserk_flora_escaped == 1"),
        math("berserk_flora_siege_started = time('now') - 600"), invoke("FLORA_SIEGE_TICK"),
        probe("flora-ruins", "berserk_flora_siege_state == 5", "berserk_flora_fire_phase == 4",
              "berserk_flora_escort_started == 0", "berserk_flora_zodd_attempts == 0",
              "berserk_flora_grunbeld_attempts == 0"),
        {"u_location_variable": breach},
        math("_pos.x = floor(_pos.x / 24) * 24 + 11"),
        math("_pos.y = floor(_pos.y / 24) * 24 + 11"),
        invoke("BREACH_CLOSE_COMMIT"),
        probe("breach-retry", "u_berserk_breach_sealed == 0", "berserk_hunt_first_breach_state != 4"),
        {"mapgen_update": "berserk_local_breach_seal", "target_var": breach},
        invoke("BREACH_CLOSE_COMMIT"),
        probe("breach-confirmed", "u_berserk_breach_sealed == 1", "berserk_hunt_first_breach_state == 4",
              {"map_furniture_id": "f_berserk_sealed_breach", "loc": breach}),
    ]


def alternate():
    landing = {"u_val": "berserk_apostol_landing"}
    return [
        math("u_berserk_eclipse_rescue_state = 0"), math("u_berserk_eclipse_trial_active = 1"),
        math("u_berserk_eclipse_route = 2"), math("u_berserk_apostol_outcome = 2"),
        math("u_berserk_apostol_return_state = 1"), math("u_berserk_apostol_origin_z = u_val('pos_z')"),
        {"u_location_variable": landing}, math("u_berserk_apostol_landing_ok = 0"),
        invoke("APOSTOL_RETURN_COMMIT"),
        probe("alternate-pending", "u_berserk_apostol_return_state == 1",
              "u_berserk_apostol_continuation_started == 0"),
        math("u_berserk_apostol_landing_ok = 1"), invoke("APOSTOL_RETURN_COMMIT"),
        probe("alternate-complete", "u_berserk_apostol_return_state == 2",
              "u_berserk_eclipse_trial_active == 0", "u_berserk_apostol_continuation_started == 1"),
    ]


def benchmark(scene):
    position = location("probe_bench_position")
    effects = []
    if scene == "eclipse":
        effects += [
            target("probe_bench_position", "berserk_eclipse_expanded_arrival", "berserk_eclipse_expanded_special"),
            {"u_teleport": position, "force_safe": True},
            probe("benchmark-eclipse-site", {"u_at_om_location": "berserk_eclipse_expanded_arrival"}),
            math("u_berserk_eclipse_trial_active = 1"),
        ]
    elif scene == "siege":
        effects += [
            target("probe_bench_position", "berserk_flora_manor_west", "berserk_flora_manor_special"),
            {"u_teleport": position, "force_safe": True},
            probe("benchmark-siege-site", {"u_at_om_location": "berserk_flora_manor"}),
            {"u_location_variable": location("berserk_flora_location")},
            {"u_location_variable": location("berserk_flora_center")},
            math("berserk_flora_treehouse_layout = 4"), math("berserk_flora_siege_state = 2"),
            math("berserk_flora_siege_v2 = 1"), math("berserk_flora_fire_phase = 1"),
            math("berserk_flora_siege_started = time('now')"),
            # Keep the avatar stationary for a repeatable sample of the active handlers.
            math("berserk_flora_zodd_spawned = 1"), math("berserk_flora_grunbeld_spawned = 1"),
            math("berserk_flora_escort_started = 1"),
        ]
    return effects + [math("u_probe_bench_start = time('now')"), math("u_probe_bench_pending = 1"),
                      marker("BENCH READY"), {"u_assign_activity": "ACT_WAIT", "duration": "2 minutes"}]


def prepare(user, mode):
    config = user / "config"
    config.mkdir()
    (config / "options.json").write_text(json.dumps([{"name": "USE_LANG", "value": "en"}]))
    for name in PACKAGES:
        shutil.copytree(ROOT / "mods" / name, user / "mods" / name)
    world = user / "save" / WORLD
    world.mkdir(parents=True)
    (world / "mods.json").write_text(json.dumps(["dda", *PACKAGES, "BerserkCIProbe"]))
    (world / "worldoptions.json").write_text(json.dumps([
        {"name": "CHARACTER_POINT_POOLS", "value": "story_teller"},
        {"name": "WANDER_SPAWNS", "value": "false"},
    ]))
    probe_dir = user / "mods" / "BerserkCIProbe"
    probe_dir.mkdir()
    records = [
        {"type": "MOD_INFO", "id": "BerserkCIProbe", "name": "Berserk CI Probe",
         "description": "Isolated native test fixture", "category": "content", "dependencies": ["Berserk"]},
        {"type": "effect_on_condition", "id": "EOC_BERSERK_CI_GIVE_PROBE", "eoc_type": "EVENT",
         "required_event": "game_start", "condition": "u_is_avatar", "effect": {"u_spawn_item": "berserk_ci_probe"}},
        {"type": "ITEM", "id": "berserk_ci_probe", "copy-from": "paper", "name": {"str": "campaign probe"},
         "volume": "1 ml", "use_action": {"type": "effect_on_conditions", "description": "Run campaign test",
                                         "effect_on_conditions": ["EOC_BERSERK_CI_PROBE"]}},
        {"type": "effect_on_condition", "id": "EOC_BERSERK_CI_PROBE",
         "effect": {"suite": suite, "alternate": alternate}[mode]() if mode in TESTS else benchmark(mode)},
    ]
    if mode not in TESTS:
        records.append({"type": "effect_on_condition", "id": "EOC_BERSERK_CI_BENCH_END",
                        "recurrence": "1 second", "global": True, "condition": {"and": [
                            math("u_probe_bench_pending == 1"),
                            math("time('now') - u_probe_bench_start >= 100"),
                        ]}, "effect": [math("u_probe_bench_pending = 0"), marker("BENCH 100")]})
    (probe_dir / "modinfo.json").write_text(json.dumps([records[0]]))
    (probe_dir / "probe.json").write_text(json.dumps(records[1:]))


class Terminal:
    def __init__(self, game, user):
        self.screen = pyte.Screen(173, 75)
        self.stream = pyte.ByteStream(self.screen)
        env = dict(os.environ, TERM="xterm-256color", LC_ALL="C.UTF-8", LANGUAGE="en")
        self.child = pexpect.spawn(str(game / "cataclysm"),
            ["--userdir", str(user), "--seed", SEED, "--disable-ascii-art"], cwd=str(game),
            env=env, dimensions=(75, 173))

    def drain(self, seconds):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            try:
                self.stream.feed(self.child.read_nonblocking(65536, timeout=.08))
            except pexpect.TIMEOUT:
                pass

    def screen_text(self, width=None):
        return "\n".join(line[:width].rstrip() for line in self.screen.display)

    def wait(self, label, timeout=20, width=None, dismiss=()):
        until = time.monotonic() + timeout
        while label not in self.screen_text():
            full_view = self.screen_text()
            if time.monotonic() >= until:
                raise RuntimeError(f"Timed out waiting for {label!r}:\n{full_view}")
            fallback = next((target for target in LOCATION_FALLBACKS
                             if f"DEBUG : Unable to find and assign mission target {target}" in full_view), None)
            if fallback:
                print(f"CDDA fixture: {fallback} not found; continuing through the native fallback", flush=True)
                self.send(" ")
                continue
            if "DEBUG :" in full_view or "not found in mods folder" in full_view or "FAIL " in full_view:
                raise RuntimeError(f"Missing {label!r}:\n{self.screen_text()}")
            # Keep narrative popups distinct from their copies in the sidebar log.
            if any(note in self.screen_text(width) for note in dismiss):
                self.send(" ")
            else:
                self.drain(.10)

    def send(self, keys):
        self.child.send(keys.encode())
        self.drain(.30)

    def start(self, early):
        self.wait("Dark Days Ahead")
        self.send("n")
        self.wait("Custom Character")
        self.send("\r")
        self.wait("POINTS", 120)
        self.send("\t")
        self.wait("sort")
        if early:
            self.send("/")
            self.send("Guts\r")
            self.wait("Berserk: Guts")
            self.send("\r")
            self.send("\t")
            self.wait("Berserk: Guts before the Eclipse")
            self.send("\r")
            self.send("\t")
            self.send("\t")
            self.wait("Dexterity")
            for key in ("l", "l", "j", "l", "l"):
                self.send(key)
        else:
            self.send("\t")
            self.wait("Survivor")
            self.send("\t")
            self.send("\t")
            self.wait("Dexterity")
        for _ in range(4):
            self.send("\t")
        self.send("Y")
        self.wait("Wield:", 120)

    def use_probe(self):
        self.send("a")
        self.send("/")
        self.send("campaign probe\r")
        self.wait("campaign probe")
        self.send("\r")

    def cpu_seconds(self):
        fields = Path(f"/proc/{self.child.pid}/stat").read_text().rsplit(")", 1)[1].split()
        return (int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--mode", default="suite", choices=(*TESTS, "normal", "eclipse", "siege"))
    args = parser.parse_args()
    game = args.game.resolve()
    version = (game / "VERSION.txt").read_text()
    if f"commit sha: {ENGINE}\n" not in version:
        raise SystemExit("Wrong CDDA revision for the pinned native fixture")
    print(f"engine={ENGINE} seed={SEED} packages={','.join(PACKAGES)} mode={args.mode}", flush=True)
    with tempfile.TemporaryDirectory(prefix="berserk-native-") as folder:
        user = Path(folder)
        prepare(user, args.mode)
        terminal = Terminal(game, user)
        try:
            terminal.start(early=args.mode != "alternate")
            if args.mode not in TESTS and "Safe: On" in terminal.screen_text():
                terminal.send("!")  # Prevent safe mode from stopping the timed wait.
            terminal.use_probe()
            if args.mode in TESTS:
                for label, state in TESTS[args.mode]:
                    terminal.wait("PASS " + label, 45, width=125, dismiss=(
                        "You returned human.", "The Skull Knight waits nearby.",
                        "Smoke stings your eyes", "The seal did not take hold.",
                    ))
                    print(f"PASS {label}: {state}", flush=True)
                    terminal.send(" ")
            else:
                if args.mode != "normal":
                    terminal.wait("PASS benchmark-" + args.mode, 75, width=125)
                    terminal.send(" ")
                terminal.wait("BENCH READY", width=125)
                before_cpu = terminal.cpu_seconds()
                start = time.perf_counter()
                # Dismiss the probe to start the native waiting activity.
                terminal.child.send(b" ")
                terminal.wait("BENCH 100", 45, width=125, dismiss=("The smoke thickens.",))
                print(json.dumps({"scene": args.mode, "turns": 100,
                                  "wall_seconds": round(time.perf_counter() - start, 4),
                                  "engine_cpu_seconds": round(terminal.cpu_seconds() - before_cpu, 4)}), flush=True)
        finally:
            terminal.child.close()


if __name__ == "__main__":
    main()
