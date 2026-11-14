Pilot uncertainty and sample-size decision
==========================================

Keep the frozen 800-clip pilot for exploratory normalization experiments. It distinguishes the large Parakeet advantage, but does not resolve the smaller Whisper difference. Similarity to published leaderboard scores alone does not establish that a sample is large enough. Detectability of normalization effects must be assessed after those effects are measured, using paired scores on the same clips.

This analysis uses saved predictions from `results/pilot/20261114T195638016516Z`: 800 test clips, 8,584 normalized reference words, 16 meetings, 16 speakers, and four meeting series. No additional GPU inference was performed.

Conditional clip-selection uncertainty
--------------------------------------

We drew 20,000 paired bootstrap samples (seed 20261114), resampling clips with replacement within each original meeting × duration-quartile stratum and keeping each stratum's sample size fixed. All models use identical resampled clips. We weight counts by population/sample stratum size before computing pooled error/word ratios. This corrects slight allocation-rounding differences; weighted point estimates therefore differ slightly from the original pilot scores. Intervals are percentile intervals without finite-population correction.

| Model | Weighted WER | Approximate 95% interval |
| --- | ---: | ---: |
| whisper-large-v3 | 14.31% | 13.18–15.46% |
| whisper-large-v3-turbo | 14.85% | 13.70–16.04% |
| parakeet-tdt-0.6b-v3 | 9.22% | 8.26–10.22% |

Paired differences directly assess comparisons; positive values mean the first model has higher WER. Units are percentage points (pp).

| Comparison | Difference | Approximate 95% interval |
| --- | ---: | ---: |
| large-v3 minus Parakeet | 5.10 pp | 4.04–6.13 pp |
| turbo minus Parakeet | 5.63 pp | 4.51–6.74 pp |
| turbo minus large-v3 | 0.53 pp | −0.10–1.16 pp |

These approximate intervals describe clip-selection uncertainty conditional on the represented benchmark meetings/speakers and sampling design. They do not establish performance on new speakers or meetings. Selection is reproducible through a fixed ID hash; the bootstrap approximates variation under the stratified sampling design. No bootstrap probability is interpreted as the probability that a model is better.

Meeting-series sensitivity
--------------------------

Speakers recur within series, so whole-series checks preserve their grouping. Leaving out each series gives these observed, unweighted pooled scores:

| Omitted series | large-v3 WER | turbo WER | Parakeet WER |
| --- | ---: | ---: | ---: |
| EN2002 | 11.12% | 11.54% | 6.80% |
| ES2004 | 15.75% | 16.31% | 10.39% |
| IS1009 | 14.84% | 15.41% | 9.68% |
| TS3003 | 15.02% | 15.55% | 9.56% |

The ranking survives every exclusion. Parakeet's advantage ranges from 4.31–5.47 pp over large-v3 and 4.74–5.99 pp over turbo. Absolute WER depends strongly on series composition, especially inclusion of the harder non-scenario EN2002 series.

We also enumerate all 256 ordered bootstrap draws of four whole series. The central 95% descriptive ranges for WER are 10.70–18.62% (large-v3), 11.13–19.29% (turbo), and 6.28–12.46% (Parakeet). Only four clusters are available: these ranges are sensitivity summaries, not reliable nominal confidence intervals or significance tests. This calculation holds within-series predictions fixed; its positive turbo-minus-large-v3 range does not resolve the clip-selection uncertainty shown above.

Recommendation and reproduction
-------------------------------

Proceed with the pilot for exploratory comparisons, preserving the original references and predictions. Use the same paired analysis when comparing normalization methods; expand evaluation if the relevant effects remain uncertain. Develop or tune rules on separate development data. Expanding this test split improves coverage within these same four series, but does not supply new independent meeting series or speakers.

```bash
normExpEnv/bin/python scripts/analyze_uncertainty.py results/pilot/20261114T195638016516Z
normExpEnv/bin/python -m unittest discover -s tests -v
```

The run directory contains `uncertainty.json` with complete results, input hashes and methods, and `utterance_error_counts.jsonl` with paired per-clip counts. Counts reconcile with all three verified pilot scores. Published leaderboard figures have no uncertainty estimate here, and their exact historical pipeline revisions remain unconfirmed.
