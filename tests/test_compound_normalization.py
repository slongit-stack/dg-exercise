"""Semantic boundaries and alignment distinctions for the frozen experiment."""
import tempfile
from pathlib import Path
import unittest

from kaldialign import edit_distance
from scripts.compound_normalization import canonicalize, load_rules, normalize_compounds
from scripts.discover_compounds import segments


class CompoundNormalizationTests(unittest.TestCase):
    def test_variants_match_without_reference_conditioning(self):
        rules = load_rules()
        for text in ['infra red', 'infra-red', 'infrared']:
            self.assertEqual(normalize_compounds(text, rules), ['infrared'])
        self.assertEqual(normalize_compounds('a water-proof handset', rules),
                         ['a', 'waterproof', 'handset'])

    def test_rejected_meaning_differences_stay_distinct(self):
        rules = load_rules()
        for a,b in [('a part','apart'),('may be','maybe'),('point less','pointless'),
                    ('power point','powerpoint'),('feed back','feedback')]:
            self.assertNotEqual(normalize_compounds(a,rules), normalize_compounds(b,rules))
        # Official compound-aware alignment itself forgives a meaning distinction.
        self.assertEqual(edit_distance('a part'.split(), ['apart'], merge_compounds=True)['total'],0)
        self.assertGreater(edit_distance('a part'.split(), ['apart'], merge_compounds=False)['total'],0)

    def test_token_boundaries_and_idempotence(self):
        rules = load_rules()
        for pair,closed in rules.items():
            got = canonicalize(['before',*pair,'after'],rules)
            self.assertEqual(got,['before',closed,'after'])
            self.assertEqual(canonicalize(got,rules),got)
        self.assertEqual(canonicalize(['web','pages'],rules),['web','pages'])

    def test_discovery_does_not_bridge_pause_punctuation_or_event(self):
        xml = '''<root><w starttime="0" endtime="1">web</w>
        <w starttime="3" endtime="4">site</w><w punc="true">.</w>
        <w starttime="4" endtime="5">hand</w><gap/>
        <w starttime="5" endtime="6">set</w></root>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'words.xml'
            path.write_text(xml)
            self.assertEqual(list(segments(path)),['web','site','hand','set'])


if __name__ == '__main__':
    unittest.main()
