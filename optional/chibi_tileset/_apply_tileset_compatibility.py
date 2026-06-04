"""Patch all mod_tileset JSON files with shared compatibility list."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
COMPAT = json.loads((ROOT / "_tileset_compatibility.json").read_text(encoding="utf-8"))


def main() -> None:
    for path in sorted(ROOT.glob("*.json")):
        if path.name.startswith("_") or path.name == "modinfo.json":
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        changed = False
        for entry in data:
            if entry.get("type") != "mod_tileset":
                continue
            if entry.get("compatibility") != COMPAT:
                entry["compatibility"] = COMPAT
                changed = True
        if changed:
            path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            print("updated", path.name)


if __name__ == "__main__":
    main()
