"""Result-integrity checks; fixtures are synthetic, not model predictions."""
import unittest

from scripts.score_predictions import score


def example(key, reference, prediction):
    return (
        dict(id=key, text=reference, duration_seconds=2.0),
        dict(audio_filepath=key, text=reference, pred_text=prediction, duration=2.0, time=0.5),
    )


class SmokeScoringTests(unittest.TestCase):
    def test_compound_merging(self):
        ref, pred = example('one', 'the white board is blue', 'the whiteboard is blue')
        self.assertEqual(score([pred], [ref])['wer_percent'], 0)

    def test_pool_counts_instead_of_averaging_utterance_wer(self):
        ref1, pred1 = example('one', 'red green', 'red blue')
        ref2, pred2 = example('two', 'blue', 'blue extra')
        result = score([pred2, pred1], [ref1, ref2])
        self.assertEqual(result['substitutions'], 1)
        self.assertEqual(result['insertions'], 1)
        self.assertEqual(result['reference_words'], 3)
        self.assertAlmostEqual(result['wer_percent'], 200/3)

    def test_missing_or_duplicate_predictions_fail(self):
        ref, pred = example('one', 'hello', 'hello')
        for predictions in ([], [pred, pred]):
            with self.assertRaises(ValueError):
                score(predictions, [ref])

    def test_wrong_id_or_reference_fails(self):
        ref, pred = example('one', 'hello', 'hello')
        for changes in (dict(audio_filepath='other'), dict(text='different')):
            with self.assertRaises(ValueError):
                score([dict(pred, **changes)], [ref])

    def test_bad_duration_or_timing_fails(self):
        ref, pred = example('one', 'hello', 'hello')
        for changes in (dict(duration=1.0), dict(time=0), dict(time=float('nan'))):
            with self.assertRaises(ValueError):
                score([dict(pred, **changes)], [ref])


if __name__ == '__main__':
    unittest.main()
