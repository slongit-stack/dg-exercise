import unittest

import numpy as np

from scripts.analyze_uncertainty import series_draws, stratified_draws


class UncertaintyTests(unittest.TestCase):
    def test_pairing_weights_and_determinism(self):
        words = np.array([1, 2, 1, 2])
        baseline = np.array([0, 2, 2, 1])
        errors = np.column_stack([baseline, baseline+words, np.zeros(4)])
        strata = {'a': [0, 1], 'b': [2, 3]}
        population = {'a': 4, 'b': 6}
        draws, point = stratified_draws(errors, words, strata, population, 1000, 19)
        again, _ = stratified_draws(errors, words, strata, population, 1000, 19)
        np.testing.assert_array_equal(draws, again)
        self.assertGreater(np.std(draws[:, 0]), 0)
        # Resampling the same examples for both models preserves their exact
        # one-error-per-reference-word difference in every replicate.
        np.testing.assert_allclose(draws[:, 1]-draws[:, 0], 100)
        np.testing.assert_allclose(point, [100*13/15, 100*28/15, 0])

    def test_exact_whole_series_enumeration(self):
        errors = np.array([[1, 0, 0], [0, 1, 0]])
        words = np.array([1, 3])
        rates = series_draws(errors, words, ['a', 'b'])
        np.testing.assert_allclose(rates, [[100, 0, 0], [25, 25, 0],
                                          [25, 25, 0], [0, 100/3, 0]])


if __name__ == '__main__':
    unittest.main()
