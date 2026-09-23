# Berserk translations

English is the base language used by the mod's JSON source files. Runtime translations are provided for:

- Russian (`ru`)
- Simplified Chinese (`zh_CN`)

## Files

- `lang/po/Berserk.pot` — English translation template
- `lang/po/ru.po` — Russian translation source
- `lang/po/zh_CN.po` — Simplified Chinese translation source
- `lang/mo/<locale>/LC_MESSAGES/Berserk.mo` — compiled catalogs loaded by the game

The compiled catalog is named `Berserk.mo` by convention. CDDA 0.I-1 scans all
`.mo` files in the user mod directory; it does not use the mod ID to select a
catalog. In a portable Windows build, install the mod beside
`cataclysm-tiles.exe` as `<CDDA>/mods/Berserk/`. Installing it in
`<CDDA>/data/mods/Berserk/` loads the JSON but leaves the translations invisible.
If both locations contain a mod with the same ID, CDDA uses the `data/mods/`
copy first and ignores the newer mod in the user `mods/` directory. Remove the
old copy before reinstalling; leave saves and configuration untouched.
Restart the game after adding or replacing translation catalogs.

## Updating a translation

1. Open the locale's `.po` file in Poedit.
2. Review or update the translations.
3. Save and compile it to the matching `.mo` path.
4. Test the mod with that language selected in CDDA.

CDDA translation lookup uses contexts for professions, scenarios, and start locations. Preserve every `msgctxt` entry when editing or regenerating catalogs.
