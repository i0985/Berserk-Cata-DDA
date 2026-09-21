#!/usr/bin/env python3
"""Build deterministic release archives for the Berserk CDDA mods."""

from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

from validate_mod_assets import ValidationError, validate_repository


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ("Berserk", "Berserk_chibi_tileset")
ZIP_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def files_for(package: Path):
    yield from sorted(
        path
        for path in package.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )


def write_archive(output: Path, package_names: tuple[str, ...]) -> None:
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for package_name in package_names:
            package = ROOT / "mods" / package_name
            for path in files_for(package):
                relative = path.relative_to(package.parent).as_posix()
                info = zipfile.ZipInfo(relative, ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        counts = validate_repository(ROOT)
    except ValidationError as error:
        print(f"ERROR: release not built: {error}", file=sys.stderr)
        return 1

    output = args.output.resolve()
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    archives = [
        ("Berserk.zip", ("Berserk",)),
        ("Berserk_chibi_tileset.zip", ("Berserk_chibi_tileset",)),
        ("Berserk-CDDA-0.I-1.zip", PACKAGES),
    ]
    for filename, package_names in archives:
        path = output / filename
        write_archive(path, package_names)
        print(f"Wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    print(f"Validated {counts['json_files']} JSON files before packaging")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
