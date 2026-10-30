# Native UltiCa mutation overlays

`mods/Berserk/tileset/apostol_native_overlays.png` contains copied and assembled
layers from the UltiCa contributors' human-body sheet distributed with
[Cataclysm-DDA 0.I](https://github.com/CleverRaven/Cataclysm-DDA/tree/0.I/gfx/UltimateCataclysm).

Original image: [human_body.png](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I/gfx/UltimateCataclysm/human_body.png).
Original definitions: [tile_config.json](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I/gfx/UltimateCataclysm/tile_config.json).
Artists and upstream project: [UltiCa contributors](https://github.com/I-am-Erk/CDDA-Tilesets).
License: [Creative Commons Attribution-ShareAlike 3.0](https://creativecommons.org/licenses/by-sa/3.0/),
as distributed in [CDDA's license](https://github.com/CleverRaven/Cataclysm-DDA/blob/0.I/LICENSE.txt).
The extracted/assembled sheet is distributed under the same license.

Changes: only extraction, placement in a new atlas and alpha composition of
the existing wing and chitin layers, plus the native muzzle and ear layers for Wyald. No individual layer is repainted.
`apostol-native-sprite-sources-33.json` records the original Git object hash,
SHA-256, overlay names, original sprite indices, pixel rectangles and outputs.
The extraction script accepts only the reviewed source image.

Mappings: patchy skin for the Count; fur, muzzle and canine ears for Wyald; thin/thick chitin for
Rosine; chitin/scales for Grunbeld. The 0.I UltiCa configuration has no insect
wing overlay, so Rosine uses its closest existing membranous-wing layer.
This is an interim visual fallback, not a claim that the original bat-wing
mutation has been granted. The native utility traits use their ordinary
base-tileset overlays (antennae, fangs, shell) as well.

All eight bodies have distinct male/female overlay IDs. Only UltiCa is included
in this atlas's compatibility list. Existing Berserk artwork is unchanged.

Owner amendment 31 October: Wyald pawns use the short muzzle and canine ears;
independent Wyald bodies use the long muzzle and lupine ears. These four
compositions reuse untouched native pixels. Other twelve frames are identical.
