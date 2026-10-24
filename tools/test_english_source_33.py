"""English runtime sources and genuine Russian gettext coverage."""
import gettext
import json
import unittest

from apply_english_source_33 import MOD, CYRILLIC, convert, fields, translations


def leaves(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values(): yield from leaves(v)
    elif isinstance(x, list):
        for v in x: yield from leaves(v)


class EnglishSource(unittest.TestCase):
    def test_every_runtime_json_value_has_an_english_base(self):
        for path in MOD.rglob('*.json'):
            for s in leaves(json.loads(path.read_text())):
                self.assertFalse(CYRILLIC.search(s), (str(path), s))

    def test_all_manuscript_translations_resolve_to_the_exact_russian(self):
        with open(MOD / 'lang/mo/ru/LC_MESSAGES/Berserk.mo', 'rb') as stream:
            ru = gettext.GNUTranslations(stream)
        for source, en in translations().items():
            self.assertEqual(ru.gettext(en), source, en)

    def test_a_new_untranslated_sentence_stops_the_build(self):
        with self.assertRaisesRegex(ValueError, 'Missing English at'):
            convert({'dynamic_line': 'Совсем новая непереведённая реплика.'}, translations(), 'test')

    def test_identifiers_conditions_numbers_and_existing_english_are_unchanged(self):
        obj = {'id': 'EOC_BERSERK_EXAMPLE', 'condition': {'math': ['u_berserk_stage == 1']},
               'effect': {'u_message': 'Already English.', 'popup': True, 'count': 2}}
        self.assertEqual(convert(obj, translations()), obj)

    def test_translation_is_idempotent(self):
        mapping = translations()
        for ru, en in mapping.items():
            self.assertEqual(convert(convert(ru, mapping), mapping), en)

    def test_template_and_runtime_catalogs_have_no_russian_source_keys(self):
        for p in (MOD / 'lang/po').glob('*'):
            for block in p.read_text().split('\n\n'):
                self.assertFalse(CYRILLIC.search(fields(block).get('msgid', '')), str(p))


if __name__ == '__main__': unittest.main()
