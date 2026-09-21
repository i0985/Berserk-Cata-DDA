"""Compose the extended tileset sheets from 32x32 Ber_Suit source images."""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = SCRIPT_DIR.parents[1] / "mods" / "Berserk_chibi_tileset"

UPPER_FILES = (
    "Ber_suit_Head_Eq.png",
    "Ber_suit_Body_Eq.png",
    "Ber_suit_Hand_Eq.png",
    "Ber_suit_Bracer_Eq.png",
)
LOWER_FILES = (
    "Ber_suit_Leg_Eq.png",
    "Ber_suit_shoe_Eq.png",
)
SWORD_SHEETS = {
    "true_guts_sword.png": ("Ber_suit_Sword_Eq.png", "Ber_suit_Sword_Drop.png"),
    "forged_guts_sword.png": ("Ber_suit_Sword(FK)_Eq.png", "Ber_suit_Sword(FK)_Drop.png"),
    "nosferatu_zodd_sword.png": ("Ber_suit_ZODSw_Eq.png", "Ber_suit_ZODSw_Drop.png"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path, help="directory containing *_Eq.png and *_Drop.png")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="extended tileset mod directory")
    return parser.parse_args()


def load(source: Path, name: str) -> Image.Image:
    image = Image.open(source / name).convert("RGBA")
    if image.size != (32, 32):
        raise SystemExit(f"{name}: expected 32x32, got {image.size}")
    return image


def compose_sword(source: Path, eq_name: str, drop_name: str) -> Image.Image:
    sheet = Image.new("RGBA", (32, 64), (0, 0, 0, 0))
    sheet.paste(load(source, eq_name), (0, 0))
    sheet.paste(load(source, drop_name), (0, 32))
    return sheet


def main() -> None:
    args = parse_args()
    (args.output / "tileset").mkdir(parents=True, exist_ok=True)

    upper = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for index, filename in enumerate(UPPER_FILES):
        upper.paste(load(args.source, filename), (index * 32, 0))

    lower = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    for index, filename in enumerate(LOWER_FILES):
        lower.paste(load(args.source, filename), (index * 32, 0))

    upper.save(args.output / "tileset" / "berserk_armor_upper.png")
    lower.save(args.output / "tileset" / "berserk_armor_lower.png")
    for output_name, source_names in SWORD_SHEETS.items():
        compose_sword(args.source, *source_names).save(args.output / output_name)

    print("updated", args.output)


if __name__ == "__main__":
    main()
