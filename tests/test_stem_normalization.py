"""Search policy boundaries, including intentional loss of morphological distinctions."""
import unittest
from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer
from scripts.stem_normalization import stem_tokens


class StemNormalizationTests(unittest.TestCase):
    def test_inflection_equivalence(self):
        self.assertEqual(stem_tokens(['button','buttons']), ['button','button'])
        self.assertEqual(stem_tokens(['design','designing','designed']), ['design']*3)

    def test_numbers_identifiers_and_token_count_preserved(self):
        tokens=['20','£20','3.5','usb2','l','c','d','buttons']
        result=stem_tokens(tokens)
        self.assertEqual(result[:-1],tokens[:-1])
        self.assertEqual(len(result),len(tokens))
        self.assertEqual(tokens[-1],'buttons')

    def test_independent_normalization_and_remaining_errors(self):
        normalize=EnglishTextNormalizer()
        ref=normalize('The buttons are red.').split()
        hyp=normalize('The button is red.').split()
        before=edit_distance(ref,hyp,merge_compounds=False)
        after=edit_distance(stem_tokens(ref),stem_tokens(hyp),merge_compounds=False)
        self.assertEqual(before['total'],2)
        self.assertEqual(after['total'],1)
        self.assertEqual(after['ref_len'],before['ref_len'])

    def test_semantic_conflation_is_explicit(self):
        # Derivational stemming is deliberately broader than inflection matching.
        self.assertEqual(stem_tokens(['design','designer']),['design','design'])
        self.assertNotEqual(stem_tokens(['not','now']), ['not','not'])


if __name__=='__main__':
    unittest.main()
