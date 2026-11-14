"""Weighted alignment correctness and development-support guardrails."""
import itertools
import unittest
from kaldialign import edit_distance
from scripts.domain_metric import fit_weights, weighted_distance


class DomainMetricTests(unittest.TestCase):
    def test_uniform_weights_recover_token_wer(self):
        strings=[list(s) for n in range(4) for s in itertools.product('ab',repeat=n)]
        for ref in strings:
            for hyp in strings:
                got=weighted_distance(ref,hyp,{})
                self.assertEqual(got['weighted_errors'],edit_distance(ref,hyp,merge_compounds=False)['total'])
                self.assertEqual(got['reference_weight'],len(ref))

    def test_costs_hallucination_and_missing_term(self):
        weights={'remote':4.,'the':1.}
        self.assertEqual(weighted_distance(['remote'],[],weights)['weighted_errors'],4.)
        self.assertEqual(weighted_distance([],['remote'],weights)['weighted_errors'],4.)
        self.assertEqual(weighted_distance(['the'],['remote'],weights)['weighted_errors'],4.)
        self.assertEqual(weighted_distance(['remote'],['remote'],weights)['weighted_errors'],0.)

    def test_optimal_cost_matches_exhaustive_paths(self):
        weights={'a':1.,'b':4.}
        def oracle(ref,hyp):
            if not ref: return sum(weights[t] for t in hyp)
            if not hyp: return sum(weights[t] for t in ref)
            return min((0 if ref[0]==hyp[0] else max(weights[ref[0]],weights[hyp[0]]))+oracle(ref[1:],hyp[1:]),
                       weights[ref[0]]+oracle(ref[1:],hyp),weights[hyp[0]]+oracle(ref,hyp[1:]))
        strings=[list(s) for n in range(3) for s in itertools.product('ab',repeat=n)]
        for ref in strings:
            for hyp in strings:
                got=weighted_distance(ref,hyp,weights)
                self.assertEqual(got['weighted_errors'],oracle(ref,hyp))
                self.assertEqual(got['weighted_errors'],sum(got[k] for k in ['substitution_cost','deletion_cost','insertion_cost']))

    def test_support_and_background_contrast(self):
        docs={'Aa':['remote']*2+['the']*5+['single']*8,'Ab':['remote']*2+['the']*5,
              'Ba':['remote']*2+['the']*5}
        fit=fit_weights(docs,[['the'],['the'],['the']],{'Aa':'A','Ab':'A','Ba':'B'})
        self.assertEqual(fit['weights'],{'remote':4.})
        # A term seen in only one series cannot acquire a domain boost.
        fit=fit_weights(docs,[['the']],dict.fromkeys(docs,'A'))
        self.assertEqual(fit['weights'],{})

    def test_invalid_weights_fail(self):
        for bad in [0,-1,float('inf'),float('nan')]:
            with self.assertRaises(ValueError):
                weighted_distance(['a'],[],{'a':bad})

    def test_boost_exclusions_do_not_remove_tokens(self):
        docs={'Aa':['yeah']*8+['remote']*2,'Ab':['yeah']*8+['remote']*2,
              'Ba':['yeah']*8+['remote']*2}
        fit=fit_weights(docs,[['other']],{'Aa':'A','Ab':'A','Ba':'B'}, {'yeah'})
        self.assertNotIn('yeah',fit['weights'])
        self.assertEqual(fit['domain_tokens'],30)
        got=weighted_distance(['yeah'],[],fit['weights'])
        self.assertEqual(got['reference_weight'],1)
        self.assertEqual(got['weighted_errors'],1)


if __name__=='__main__':
    unittest.main()
