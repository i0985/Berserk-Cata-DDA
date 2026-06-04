# Berserk — Extended optional tileset

The main **Berserk** mod ships tile definitions for **UltimateCataclysm (UltiCA)** only. This optional mod adds the same tile IDs for other popular tilesets (same approach as 锈蚀黎明 / Rusty Dawn).

## Supported tilesets

| Internal ID | Common name |
|-------------|-------------|
| `Chibi_Ultica` | ChibiUltica |
| `MshockXottoplus` | MshockXotto+ |
| `MshockXottoplus12` | MSX++ 12 |
| `MSXotto+` | MSXotto+ |
| `MXplus12_for_cosmetics` | MSX++ cosmetics |
| `MSX++DEAD_PEOPLE` | MSX++ Dead People |
| `UNDEAD_PEOPLE` | Undead People |
| `UNDEAD_PEOPLE_BASE` | Undead People (base) |
| `UNDEAD_PEOPLE_LEGACY` | Undead People (legacy) |

Equipment and swords use custom **Ber_Suit** 32×32 art (no per-tileset offset). Monster sprites are still i0985 Ultica baseline copies.

## Install

1. Install the main **Berserk** mod.
2. Copy this folder to `mods/Berserk-chibi_tileset/` (folder name may differ).
3. Enable **both** mods in the launcher.
4. Select **Chibi_Ultica**, **MshockXottoplus**, or **Undead People** (or a compatible variant above) in game options.

## 简体中文

主 mod 只注册 **UltiCA**。使用 **ChibiUltica / MshockXotto+ / Undead People** 等图块集时，须额外启用本可选 mod，否则装备和怪物会没有贴图。

贴图支持表与锈蚀黎明 `mod_tileset_RD.json` 的 `compatibility` 写法一致：同一张 PNG + 多个图块集 ID。

## Rebuild Ber_Suit PNGs

After editing `Picture/Ber_Suit/*_Eq.png` or `*_Drop.png`, run (from repo):

`python optional/chibi_tileset/_build_ber_suit_eq_sheets.py`

After editing `_tileset_compatibility.json`, run:

`python _apply_tileset_compatibility.py`
