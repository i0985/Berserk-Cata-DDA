# Native furniture frames

`mods/Berserk/tileset/flora_native_furniture.png` contains unpainted frames
copied from the UltiCa tileset shipped with CleverRaven/Cataclysm-DDA 0.I.
Credit: UltiCa contributors, as credited in the upstream tileset.
License: [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

Sources:

- [normal.png](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I/gfx/UltimateCataclysm/normal.png)
- [tall.png](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I/gfx/UltimateCataclysm/tall.png)
- [Upstream tileset and attribution](https://github.com/CleverRaven/Cataclysm-DDA/tree/0.I/gfx/UltimateCataclysm)

The frames were extracted and repacked to pin their intended facing in Flora's
house. No pixels were repainted. Short frames are bottom-aligned in 32x64 cells.
The atlas remains under CC-BY-SA-3.0. Source hashes, source rectangles, original
sprite indices and the output SHA-256 are recorded in the adjacent JSON manifest.
Reproduce with `tools/tileset/extract_flora_furniture_33.py --native-dir DIR`.

These are ordinary native furniture images, not a replacement for the owner's
drawn enemies, objects, weapons or transformation overlays.
