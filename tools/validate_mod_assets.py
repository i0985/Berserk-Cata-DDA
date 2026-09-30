#!/usr/bin/env python3
"""Validate Berserk JSON packages and their mod_tileset sprite references."""

from __future__ import annotations

import argparse
import gettext
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
MODS_DIR = ROOT / "mods"
CONTENT_MOD_ID = "Berserk"
GRAPHICS_MOD_ID = "Berserk_chibi_tileset"
BASE_TILESET_IDS = ["UltimateCataclysm"]
LOCALES = ("ru", "zh_CN")


class ValidationError(Exception):
    pass


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"{path.relative_to(ROOT)}: invalid JSON: {error}") from error


def top_level_objects(path: Path) -> list[dict[str, Any]]:
    data = read_json(path)
    objects = data if isinstance(data, list) else [data]
    if not objects or not all(isinstance(entry, dict) for entry in objects):
        raise ValidationError(
            f"{path.relative_to(ROOT)}: top level must be an object or a non-empty array of objects"
        )
    return objects


def validate_mapgen_update_effects(path: Path, objects: list[dict[str, Any]]) -> None:
    """CDDA 0.I-1 only reads mapgen_update as a string or an array, not an object."""
    def visit(value: Any) -> None:
        if isinstance(value, list):
            for element in value:
                visit(element)
        elif isinstance(value, dict):
            for key, element in value.items():
                if key == "mapgen_update" and not (
                    isinstance(element, str) or isinstance(element, list)
                ):
                    raise ValidationError(
                        f"{path.relative_to(ROOT)}: mapgen_update must be a string or array in CDDA 0.I-1"
                    )
                visit(element)

    for entry in objects:
        if entry.get("type") == "effect_on_condition":
            visit(entry)


def validate_furniture_required_fields(path: Path, objects: list[dict[str, Any]]) -> None:
    """CDDA 0.I-1 requires both movement fields on standalone furniture."""
    for entry in objects:
        if entry.get("type") != "furniture" or "copy-from" in entry:
            continue
        for field in ("move_cost_mod", "required_str"):
            value = entry.get(field)
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValidationError(
                    f"{path.relative_to(ROOT)}: furniture {entry.get('id')!r} "
                    f"requires integer {field} in CDDA 0.I-1"
                )


def validate_monster_attacks(path: Path, objects: list[dict[str, Any]]) -> None:
    """The standalone monster_attack loader in 0.I-1 requires cooldown."""
    for entry in objects:
        if entry.get("type") != "monster_attack" or "copy-from" in entry:
            continue
        value = entry.get("cooldown")
        if not isinstance(value, (int, float, dict)) or isinstance(value, bool):
            raise ValidationError(
                f"{path.relative_to(ROOT)}: monster_attack {entry.get('id')!r} "
                "requires cooldown in CDDA 0.I-1"
            )


def validate_dynamic_lines(path: Path, objects: list[dict[str, Any]]) -> None:
    """Reject unsupported conditional wrappers in 0.I-1 talk-topic lines.

    dynamic_line_t(JsonObject) in src/npctalk.cpp accepts a dialogue condition
    directly, with yes/no branches. EOC's if wrapper and logical combinators
    are not line conditions. This checks that known incompatibility only;
    it does not implement the full native dialogue loader.
    """
    def visit(line: Any) -> None:
        if isinstance(line, list):
            for part in line:
                visit(part)
        elif isinstance(line, dict):
            unsupported = {"if", "and", "or", "not"}.intersection(line)
            if unsupported:
                raise ValidationError(
                    f"{path.relative_to(ROOT)}: dynamic_line does not support "
                    f"{', '.join(sorted(unsupported))} in CDDA 0.I-1; "
                    "put a single dialogue condition directly beside yes/no"
                )
            for field in ("yes", "no", "concatenate"):
                if field in line:
                    visit(line[field])

    for entry in objects:
        if entry.get("type") == "talk_topic":
            visit(entry.get("dynamic_line"))


def validate_turn_cost_durations(path: Path, objects: list[dict[str, Any]]) -> None:
    """Check literal turn_cost strings against 0.I-1's time_duration units.

    The '1 sec' documentation example is not accepted by calendar.cpp's unit
    list. units.h consumes its 's', then rejects the leftover 'ec'. Integers,
    variable objects and ranges remain the native loader's responsibility.
    """
    quantity = re.compile(
        r"(?: *[+-]?[0-9]+ *(?:turns|turn|t|seconds|second|s|"
        r"minutes|minute|m|hours|hour|h|days|day|d))+ *"
    )

    def check(value: Any) -> None:
        if isinstance(value, str) and value != "infinite" and not quantity.fullmatch(value):
            raise ValidationError(
                f"{path.relative_to(ROOT)}: invalid turn_cost duration {value!r} "
                "in CDDA 0.I-1; use e.g. '1 second', not '1 sec'"
            )
        if isinstance(value, list):
            for part in value:
                check(part)

    def visit(value: Any) -> None:
        if isinstance(value, list):
            for part in value:
                visit(part)
        elif isinstance(value, dict):
            for key, part in value.items():
                if key == "turn_cost":
                    check(part)
                visit(part)

    visit(objects)


def png_size(path: Path) -> tuple[int, int]:
    try:
        with path.open("rb") as image:
            header = image.read(24)
    except OSError as error:
        raise ValidationError(f"{path.relative_to(ROOT)}: cannot read PNG: {error}") from error
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValidationError(f"{path.relative_to(ROOT)}: not a valid PNG header")
    return struct.unpack(">II", header[16:24])


def sprite_indexes(value: Any) -> Iterable[int]:
    if isinstance(value, int) and not isinstance(value, bool):
        yield value
    elif isinstance(value, list):
        for entry in value:
            if isinstance(entry, int) and not isinstance(entry, bool):
                yield entry


def tile_ids(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        yield from (entry for entry in value if isinstance(entry, str))


def underlying_object_id(tile_id: str) -> str:
    # CDDA 0.I-1 checks the empty-variant ID before the active-bionic base ID.
    if tile_id.startswith("overlay_mutation_active_") and tile_id.endswith("_var_"):
        tile_id = tile_id[:-5]
    for prefix in (
        "overlay_worn_", "overlay_wielded_", "overlay_mutation_active_", "overlay_mutation_"
    ):
        if tile_id.startswith(prefix):
            return tile_id.removeprefix(prefix)
    return tile_id


def load_expected_extra_compatibility() -> list[str]:
    path = ROOT / "tools" / "tileset" / "tileset_compatibility.txt"
    data = read_json(path)
    if not isinstance(data, list) or not data or not all(isinstance(entry, str) for entry in data):
        raise ValidationError(
            "tools/tileset/tileset_compatibility.txt: expected a non-empty JSON array of strings"
        )
    if len(data) != len(set(data)):
        raise ValidationError("tools/tileset/tileset_compatibility.txt: duplicate tileset IDs")
    return data


def validate_modinfo(package: Path, objects_by_file: dict[Path, list[dict[str, Any]]]) -> str:
    modinfo_path = package / "modinfo.json"
    if modinfo_path not in objects_by_file:
        raise ValidationError(f"{package.relative_to(ROOT)}: missing modinfo.json")
    entries = [entry for entry in objects_by_file[modinfo_path] if entry.get("type") == "MOD_INFO"]
    if len(entries) != 1 or not isinstance(entries[0].get("id"), str):
        raise ValidationError(f"{modinfo_path.relative_to(ROOT)}: expected exactly one MOD_INFO with an id")
    return entries[0]["id"]


def validate_translation_catalogs(package: Path) -> int:
    """Ensure the release contains usable catalogs for both non-English locales."""
    mod_id = package.name
    example = (
        ("profession_male", "Berserker after the Eclipse")
        if mod_id == CONTENT_MOD_ID
        else (None, "Berserk: Extended tileset (Chibi / MSX+ / Undead)")
    )
    for locale in LOCALES:
        path = package / "lang" / "mo" / locale / "LC_MESSAGES" / f"{mod_id}.mo"
        try:
            with path.open("rb") as catalog_file:
                catalog = gettext.GNUTranslations(catalog_file)
        except (OSError, ValueError) as error:
            raise ValidationError(f"{path.relative_to(ROOT)}: missing or invalid catalog: {error}") from error
        if catalog.info().get("language") != locale:
            raise ValidationError(f"{path.relative_to(ROOT)}: expected language {locale!r}")
        context, source = example
        translation = catalog.pgettext(context, source) if context else catalog.gettext(source)
        if translation == source:
            raise ValidationError(f"{path.relative_to(ROOT)}: missing translation for {source!r}")
    return len(LOCALES)


def validate_tileset(
    package: Path,
    path: Path,
    definition: dict[str, Any],
    expected_compatibility: list[str],
    known_ids: set[str],
) -> tuple[int, int]:
    errors: list[str] = []
    compatibility = definition.get("compatibility")
    if compatibility != expected_compatibility:
        errors.append(
            f"compatibility is {compatibility!r}; expected {expected_compatibility!r}"
        )

    sheets = definition.get("tiles-new")
    if not isinstance(sheets, list) or not sheets:
        errors.append("tiles-new must be a non-empty array")
        sheets = []
    elif len({sheet.get("file") for sheet in sheets if isinstance(sheet, dict)
              and isinstance(sheet.get("file"), str)}) > 1:
        # In CDDA 0.I-1, fg indexes in one mod_tileset share an atlas offset.
        # A second PNG with fg: 0 would silently display the first PNG instead.
        errors.append("split distinct sprite files into separate mod_tileset definitions")

    checked_sheets = 0
    checked_tiles = 0
    for sheet_number, sheet in enumerate(sheets, start=1):
        if not isinstance(sheet, dict):
            errors.append(f"tiles-new[{sheet_number - 1}] is not an object")
            continue
        relative_image = sheet.get("file")
        sprite_width = sheet.get("sprite_width")
        sprite_height = sheet.get("sprite_height")
        if not isinstance(relative_image, str):
            errors.append(f"sheet {sheet_number}: file must be a string")
            continue
        if not isinstance(sprite_width, int) or sprite_width <= 0:
            errors.append(f"sheet {sheet_number}: sprite_width must be a positive integer")
            continue
        if not isinstance(sprite_height, int) or sprite_height <= 0:
            errors.append(f"sheet {sheet_number}: sprite_height must be a positive integer")
            continue

        image_path = package / relative_image
        if not image_path.is_file():
            errors.append(f"sheet {sheet_number}: missing image {relative_image}")
            continue
        try:
            width, height = png_size(image_path)
        except ValidationError as error:
            errors.append(str(error))
            continue
        if width % sprite_width or height % sprite_height:
            errors.append(
                f"sheet {sheet_number}: {relative_image} is {width}x{height}, not divisible by "
                f"{sprite_width}x{sprite_height}"
            )
            continue
        frame_count = (width // sprite_width) * (height // sprite_height)
        checked_sheets += 1

        tiles = sheet.get("tiles")
        if not isinstance(tiles, list) or not tiles:
            errors.append(f"sheet {sheet_number}: tiles must be a non-empty array")
            continue
        for tile_number, tile in enumerate(tiles, start=1):
            if not isinstance(tile, dict):
                errors.append(f"sheet {sheet_number}, tile {tile_number}: entry is not an object")
                continue
            ids = list(tile_ids(tile.get("id")))
            if not ids:
                errors.append(f"sheet {sheet_number}, tile {tile_number}: id is missing")
            for tile_id in ids:
                if underlying_object_id(tile_id) not in known_ids:
                    errors.append(
                        f"sheet {sheet_number}, tile {tile_number}: unknown game object id {tile_id!r}"
                    )
            for key in ("fg", "bg"):
                for index in sprite_indexes(tile.get(key)):
                    if index < 0 or index >= frame_count:
                        errors.append(
                            f"sheet {sheet_number}, tile {tile_number}: {key} index {index} outside "
                            f"0..{frame_count - 1} for {relative_image}"
                        )
            checked_tiles += len(ids)

    if errors:
        details = "\n  - ".join(errors)
        raise ValidationError(f"{path.relative_to(ROOT)}:\n  - {details}")
    return checked_sheets, checked_tiles


def validate_repository(root: Path = ROOT) -> dict[str, int]:
    global ROOT, MODS_DIR
    ROOT = root.resolve()
    MODS_DIR = ROOT / "mods"
    if not MODS_DIR.is_dir():
        raise ValidationError(f"{MODS_DIR}: mods directory does not exist")

    packages = sorted(path.parent for path in MODS_DIR.glob("*/modinfo.json"))
    if not packages:
        raise ValidationError("no mod packages found under mods/")

    objects_by_package: dict[Path, dict[Path, list[dict[str, Any]]]] = {}
    json_count = 0
    for package in packages:
        package_objects: dict[Path, list[dict[str, Any]]] = {}
        for path in sorted(package.rglob("*.json")):
            objects = top_level_objects(path)
            validate_mapgen_update_effects(path, objects)
            validate_furniture_required_fields(path, objects)
            validate_monster_attacks(path, objects)
            validate_dynamic_lines(path, objects)
            validate_turn_cost_durations(path, objects)
            if sum(entry.get("type") == "mod_tileset" for entry in objects) > 1:
                raise ValidationError(
                    f"{path.relative_to(ROOT)}: CDDA 0.I-1 requires one mod_tileset per file"
                )
            package_objects[path] = objects
            json_count += 1
        objects_by_package[package] = package_objects

    packages_by_id: dict[str, Path] = {}
    for package, objects_by_file in objects_by_package.items():
        mod_id = validate_modinfo(package, objects_by_file)
        if mod_id in packages_by_id:
            raise ValidationError(
                f"duplicate MOD_INFO id {mod_id!r}: {packages_by_id[mod_id]} and {package}"
            )
        packages_by_id[mod_id] = package
    if set(packages_by_id) != {CONTENT_MOD_ID, GRAPHICS_MOD_ID}:
        raise ValidationError(
            f"expected mod IDs {CONTENT_MOD_ID!r} and {GRAPHICS_MOD_ID!r}; found {sorted(packages_by_id)}"
        )

    catalog_count = sum(validate_translation_catalogs(package) for package in packages)

    content_package = packages_by_id[CONTENT_MOD_ID]
    known_ids: set[str] = set()
    id_locations: dict[tuple[str, str], list[Path]] = defaultdict(list)
    for path, objects in objects_by_package[content_package].items():
        for entry in objects:
            object_type = entry.get("type")
            object_id = entry.get("id")
            if object_type != "mod_tileset" and isinstance(object_id, str):
                known_ids.add(object_id)
                if isinstance(object_type, str):
                    id_locations[(object_type, object_id)].append(path)
    duplicates = {
        key: locations for key, locations in id_locations.items() if len(locations) > 1
    }
    if duplicates:
        details = "; ".join(
            f"{object_type} {object_id!r} in {', '.join(str(p.relative_to(ROOT)) for p in paths)}"
            for (object_type, object_id), paths in sorted(duplicates.items())
        )
        raise ValidationError(f"duplicate typed object IDs: {details}")

    # CDDA 0.I-1 does not finalize deferred profession definitions. A mod-local
    # copy-from must be loaded after its base profession or the ID disappears.
    local_professions = {
        object_id for (object_type, object_id) in id_locations if object_type == "profession"
    }
    loaded_professions: set[str] = set()
    for path, objects in objects_by_package[content_package].items():
        for entry in objects:
            if entry.get("type") != "profession":
                continue
            parent = entry.get("copy-from")
            if parent in local_professions and parent not in loaded_professions:
                raise ValidationError(
                    f"{path.relative_to(ROOT)}: profession {entry.get('id')!r} "
                    f"copies {parent!r} before the base is loaded"
                )
            if isinstance(entry.get("id"), str):
                loaded_professions.add(entry["id"])

    expected_extra = load_expected_extra_compatibility()
    sheet_count = 0
    tile_count = 0
    tileset_count = 0
    for package, objects_by_file in objects_by_package.items():
        mod_id = next(key for key, value in packages_by_id.items() if value == package)
        expected = BASE_TILESET_IDS if mod_id == CONTENT_MOD_ID else expected_extra
        for path, objects in objects_by_file.items():
            for entry in objects:
                if entry.get("type") == "mod_tileset":
                    sheets, tiles = validate_tileset(
                        package, path, entry, expected, known_ids
                    )
                    tileset_count += 1
                    sheet_count += sheets
                    tile_count += tiles

    return {
        "packages": len(packages),
        "translation_catalogs": catalog_count,
        "json_files": json_count,
        "tileset_definitions": tileset_count,
        "sprite_sheets": sheet_count,
        "tile_ids": tile_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root (defaults to the parent of tools/)",
    )
    args = parser.parse_args()
    try:
        counts = validate_repository(args.root)
    except ValidationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        "OK: {packages} packages, {json_files} JSON files, "
        "{tileset_definitions} mod_tileset definitions, {sprite_sheets} sprite sheets, "
        "{tile_ids} tile IDs, {translation_catalogs} translation catalogs".format(**counts)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
