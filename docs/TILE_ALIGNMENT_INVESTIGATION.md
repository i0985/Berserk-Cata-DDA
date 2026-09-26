# UltiCa armor alignment (CDDA 0.I-1)

The armor sheet uses 32 × 32 frames. On the tested game tag, `src/cata_tiles.cpp`
reads `sprite_offset_y` with `get_int` when loading a `tiles-new` entry, and
positions the sprite with `divide_round_down(tile_offset.y * tile_width,
tileset_tile_width)`. UltiCa's tile width is 32. Therefore one offset unit
moves the image by one source pixel, which becomes several display pixels at
the player's chosen zoom. A value between -16 and -15 cannot be expressed by
this JSON field.

Feedback from in-game inspection: the worn helmet looks right at -17, while
the chestplate and gloves appear slightly high at -16 and slightly low at -15.
The current trial separates only the worn helmet at -17; other upper sprites
retain -15, and lower sprites retain -4. This is not a tested final correction
for the chestplate or gloves.

An intermediate position at the same zoom requires a finer-resolution sprite
sheet: double the source to 64 × 64 cells, use `sprite_width` and
`sprite_height` of 64 with `pixelscale: 0.5`, and shift the intended frame's
opaque pixels by one high-resolution pixel. Check the result in-game at several
zoom levels. Keep each ID and foreground index stable. Avoid changing the
shapes or colors of the existing pixel art.

The `Stale game data detected` message is caused by a saved FlexBuffer for a
JSON file whose modification time changed. With the game closed, remove the
generated `cache/mods/Berserk/` directory before testing another edit.
