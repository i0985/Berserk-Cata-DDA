"""One-off: compose Chibi tileset sheets from Ber_Suit *_Eq.png (phase 1)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

SRC = Path(r"D:\09 Code\Picture\Ber_Suit")
OUT = Path(__file__).resolve().parent
DEPLOY = Path(r"D:\09 Code\0.i2026-05-11-1531\mods\Berserk-chibi_tileset")

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


def load(name: str) -> Image.Image:
    im = Image.open(SRC / name).convert("RGBA")
    if im.size != (32, 32):
        raise SystemExit(f"{name}: expected 32x32, got {im.size}")
    return im


def compose_sword(eq_name: str, drop_name: str) -> Image.Image:
    sheet = Image.new("RGBA", (32, 64), (0, 0, 0, 0))
    sheet.paste(load(eq_name), (0, 0))
    sheet.paste(load(drop_name), (0, 32))
    return sheet


def main() -> None:
    upper = Image.new("RGBA", (128, 32), (0, 0, 0, 0))
    for i, fn in enumerate(UPPER_FILES):
        upper.paste(load(fn), (i * 32, 0))

    lower = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    for i, fn in enumerate(LOWER_FILES):
        lower.paste(load(fn), (i * 32, 0))

    upper_path = OUT / "tileset" / "berserk_armor_upper.png"
    lower_path = OUT / "tileset" / "berserk_armor_lower.png"

    upper.save(upper_path)
    lower.save(lower_path)

    sword_paths: list[Path] = []
    for out_name, (eq_name, drop_name) in SWORD_SHEETS.items():
        out_path = OUT / out_name
        compose_sword(eq_name, drop_name).save(out_path)
        sword_paths.append(out_path)

    if DEPLOY.is_dir():
        (DEPLOY / "tileset").mkdir(parents=True, exist_ok=True)
        upper.save(DEPLOY / "tileset" / "berserk_armor_upper.png")
        lower.save(DEPLOY / "tileset" / "berserk_armor_lower.png")
        for out_name, pair in SWORD_SHEETS.items():
            compose_sword(*pair).save(DEPLOY / out_name)

    print("Wrote:", upper_path, upper.size)
    print("Wrote:", lower_path, lower.size)
    for p in sword_paths:
        print("Wrote:", p, (32, 64))
    if DEPLOY.is_dir():
        print("Deployed to", DEPLOY)


if __name__ == "__main__":
    main()
