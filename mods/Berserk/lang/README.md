# Berserk translations

English is the base language used by the mod's JSON source files. Runtime translations are provided for:

- Russian (`ru`)
- Simplified Chinese (`zh_CN`)

## Files

- `lang/po/Berserk.pot` — English translation template
- `lang/po/ru.po` — Russian translation source
- `lang/po/zh_CN.po` — Simplified Chinese translation source
- `lang/mo/<locale>/LC_MESSAGES/Berserk.mo` — compiled catalogs loaded by the game

The compiled catalog must be named `Berserk.mo` to match the mod ID in `modinfo.json`.

## Updating a translation

1. Open the locale's `.po` file in Poedit.
2. Review or update the translations.
3. Save and compile it to the matching `.mo` path.
4. Test the mod with that language selected in CDDA.

CDDA translation lookup uses contexts for professions, scenarios, and start locations. Preserve every `msgctxt` entry when editing or regenerating catalogs.
