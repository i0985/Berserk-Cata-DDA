"""Update every extended mod_tileset definition from the shared ID list."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_TARGET = SCRIPT_DIR.parents[1] / "mods" / "Berserk_chibi_tileset"
COMPATIBILITY_FILE = SCRIPT_DIR / "tileset_compatibility.txt"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="directory containing the extended mod_tileset JSON files",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    compatibility = json.loads(COMPATIBILITY_FILE.read_text(encoding="utf-8"))

    for path in sorted(args.target.glob("*.json")):
        if path.name == "modinfo.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        changed = False
        for entry in data:
            if entry.get("type") != "mod_tileset":
                continue
            if entry.get("compatibility") != compatibility:
                entry["compatibility"] = compatibility
                changed = True
        if changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print("updated", path)


if __name__ == "__main__":
    main()
