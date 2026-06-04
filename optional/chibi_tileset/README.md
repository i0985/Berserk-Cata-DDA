# Berserk — ChibiUltica optional tileset

The main **Berserk** mod ships tile definitions for **UltimateCataclysm (UltiCA)** only. This folder is an **optional patch** for players who use the **ChibiUltica** tileset.

## What it does

- Copies i0985's original Ultica PNG sprites (baseline art, not yet resized for chibi style).
- Registers the same tile IDs with `compatibility: ["Chibi_Ultica"]` so equipment and monsters show up instead of being invisible.

Per author permission: this patch does **not** modify the main mod's UltiCA files.

## Install

1. Install the main mod: copy or symlink `Berserk-Cata-DDA` into your game's `mods/` folder.
2. Copy **this entire folder** (`optional/chibi_tileset`) into `mods/` as its own mod, for example:

   `mods/Berserk-chibi_tileset/`

   (The folder name can differ; `modinfo.json` must stay inside it.)

3. In the launcher, enable **both** mods:
   - **Berserk** (main mod)
   - **Berserk: ChibiUltica tiles (optional)** ← required when using Chibi_Ultica tileset
4. Select the **Chibi_Ultica** tileset in game options.
5. For an **existing save**, use Main Menu → Manage Worlds → Modify Mods → add the optional tileset mod, then reload.

## 简体中文

主 mod 的贴图只注册给 **UltiCA**。用 **Chibi_Ultica** 时，必须**额外启用**本可选 mod，否则装备和怪物会没有贴图（不是 PNG 没复制，而是游戏不会加载 UltiCA 专用定义）。

## Notes

- Sprites are still Ultica-sized offsets for now; they may look slightly misaligned on chibi bodies until custom chibi art is drawn.
- A future **MshockXotto+** optional patch may be added separately.
