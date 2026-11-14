Search-oriented stem normalization
===================================

The fixed Snowball English experiment changes scores for all three models, without changing their ranking. It asks how much error remains after morphological distinctions tolerated by a stem-based search index are removed. It does not measure actual retrieval success.

Policy and development audit
-----------------------------

`configs/normalization/stemming_v1.json` freezes `snowballstemmer==3.0.1`, English, with no fitted parameters or exceptions. Apply the pinned upstream English normalizer first, then stem each lowercase ASCII alphabetic token independently. Preserve numeric, currency, mixed alphanumeric, and other tokens. Stemming preserves token count. Apply exactly the same function independently to references and predictions. This experiment does not layer on the custom compound rules or remove stopwords.

The policy was agreed and saved before rescoring. Development inputs are the same separate 98 AMI training-labelled meetings used for compound discovery, with evaluation series and speakers excluded. The script generates a development collision audit before test rescoring. No development-driven exceptions were added, and no rules were tuned after observing pilot scores. These remain exploratory experiments on an already inspected test pilot.

Development text contains 467,272 normalized tokens and 8,960 distinct tokens. Stemming changes 73,053 token occurrences (15.63%) and produces 1,640 groups containing multiple original vocabulary forms. The complete groups and occurrence counts are in `data/development/compounds/stemming_audit.json`.

An LLM inspection of selected development groups confirms useful matches such as `button/buttons` and `design/designed/designing`. It also exposes broader conflations: `design` merges with `designer`, `operate` with `operator`, and `relate` with `relative`. These are not always semantically interchangeable. This audit is illustrative, not an independently measured semantic error rate. We retain the fixed algorithm rather than hand-tune exceptions to this benchmark.

Pilot results
--------------

All scores below pool edits over the same frozen 800 clips and 8,584 reference tokens. The official baseline is reproduced exactly before rescoring. Reference token count stays fixed, so these changes are changes in edit counts rather than denominator effects.

| Model | Official baseline WER | Stem-normalized WER, same compound alignment | Change (percentage points) | Net fewer edits |
| --- | ---: | ---: | ---: | ---: |
| Whisper large-v3 | 14.3290% | 14.1542% | −0.1747 | 15 |
| Whisper large-v3-turbo | 14.8532% | 14.6086% | −0.2446 | 21 |
| Parakeet TDT v3 | 9.2148% | 9.0284% | −0.1864 | 16 |

Stemming changes 547 reference clips and 550, 551, and 556 prediction clips, respectively. Many text changes do not alter errors because both sides already agree. With compound-aware alignment, errors decrease in 18/23/21 clips and increase in 3/2/4 clips, respectively; the remaining clips have unchanged totals. Stemming is not guaranteed to preserve concatenation equivalence under compound alignment, so individual clips can get worse even though ordinary token matches are preserved.

For a search index that matches individual stems, ordinary token alignment is the more direct diagnostic. Holding that alignment fixed gives:

| Model | Upstream normalization + token alignment | Stem normalization + token alignment | Change (percentage points) |
| --- | ---: | ---: | ---: |
| Whisper large-v3 | 14.7367% | 14.4921% | −0.2446 |
| Whisper large-v3-turbo | 15.2493% | 14.9581% | −0.2912 |
| Parakeet TDT v3 | 9.6459% | 9.3663% | −0.2796 |

These two controlled comparisons keep alignment settings constant within each table. Stem-normalized WER is an alternative score, not the published leaderboard metric. Smaller values reflect more forgiving equivalence rules; they do not mean the raw transcripts improved. Ranking remains Parakeet, large-v3, turbo. Differences in the size of the reductions are descriptive: no new paired uncertainty analysis or claim of statistically resolved model differences is made here.

Potential additions (not implemented)
--------------------------------------

- **Stopword removal:** test a fixed, versioned search stopword list, independently from stemming before testing their combination. Preserve negation and application-critical words. Document the treatment of phrase queries and the policy for references that become empty; do not silently change the eligible clip set. Stopword removal changes the reference denominator, so report counts and coverage alongside scores. Its relevance depends on whether the intended search index drops the same words.
- **Acronym canonicalization:** audit upstream handling of `LCD`, `L C D`, and punctuation variants. Discover and review mappings using development text, then freeze them before evaluation. Preserve distinctions between letter sequences, ordinary words, and product identifiers. This may be especially relevant to technical meeting search; do not assume an acronym and its full expansion are always interchangeable. Compare independently before combining with other policies.

Both would be exploratory extensions. Neither is necessary to obtain a changed score now that stemming has a measurable effect. A downstream retrieval test would be needed to establish whether any normalization policy improves search outcomes.

Reproduction and artifacts
---------------------------

```bash
normExpEnv/bin/python -m pip install -r requirements-normalization.txt
normExpEnv/bin/python scripts/evaluate_stemming.py results/pilot/20261114T195638016516Z
normExpEnv/bin/python -m unittest discover -s tests -v
```

The script verifies development transcript provenance, prediction coverage, reference equality, durations, and official edit counts. Outputs include policy/input/source hashes and dependency versions. In the pilot run directory, `stemming_analysis.json` contains all four normalization/alignment combinations; each model's `stemming_clip_audit.jsonl` contains before/after tokens and per-clip counts. Raw references and predictions are unchanged. Code is in `scripts/stem_normalization.py` and `scripts/evaluate_stemming.py`.

All 17 unit tests pass; `pip check` passes. Added tests cover inflection equivalence, retained residual errors, number/identifier preservation, token-count preservation, and known semantic conflation. No new GPU inference was needed.
