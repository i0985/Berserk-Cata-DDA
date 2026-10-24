# English base text for 3.3

Owner decision, 24 October: every new dialogue, description and message must
have an English version at minimum. English is the runtime JSON source;
Russian remains a gettext translation. Existing Chinese translations stay in
place, with English fallback for missing entries.

## Coverage

- Converted 1,517 distinct Russian-source strings across 51 JSON files.
- Those strings appear in 10,120 runtime text positions, including conditional
  branches, reference-book fragments and repeated menu labels.
- Covered Flora, the captive, named apostles, the God Hand, shared NPC
  reactions, the reference book, scene messages, quests, items and traits.
- All 381 runtime JSON files now contain no Cyrillic string values.
- All 1,517 English keys resolve to their complete approved Russian text in
  the compiled Russian catalog. English needs no separate catalog.
- Names, story facts, map directions, material quantities, time requirements,
  narrative markers, paragraph breaks and runtime variable tags are retained.

`tools/translations/english_33.json` holds the real English text alongside its
Russian source. Documentation and owner manuscripts remain in their original
language. Existing English text outside this inventory is retained.

## Build rules

Use `python tools/build_story_33.py`. After the eleven story builders and the
visual policy, `tools/apply_english_source_33.py` converts manuscript drafts,
updates the template and Russian catalog, retains Chinese translations and
compiles both catalogs with `msgfmt --check`. A Russian draft without an English
entry is an error. Do not publish intermediate individual-builder output.

The common-scene builder compares translated message bodies when checking
for an existing callback. Rebuilding over English output therefore cannot add
a second Russian draft of the same Behelit notification.

## Validation

296 current checks pass: 284 checks for 3.3 (including six new English-source
checks), five recipe checks and seven dynamic-dialogue checks. Tests execute
the actual conditions and transactions. Presentation fixtures now resolve
the compiled Russian catalog, with an explicit English rendering mode.

A structural comparison with parent `5137ce962a1aba95b019314e977d3ec7fa484533`
shows that the runtime JSON changes consist only of the mapped text values.
IDs, conditions, effects, rewards, numbers and geometry are unchanged.
The canonical rebuild is deterministic. This does not replace testing native
CDDA loading, dialogue formatting and language switching in the game.
