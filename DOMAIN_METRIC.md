Domain-weighted WER v1
=======================

We added an experimental domain-contrast weighted WER to complement ordinary WER. It gives extra cost to errors involving vocabulary recurring in AMI development meetings and relatively distinctive against general English. It informs a model-selection decision for a meeting-search prototype that prioritizes that vocabulary. It does not establish retrieval quality, semantic correctness, model training provenance, or fine-tuning potential.

All three models were rescored from saved predictions. Parakeet remains lowest, followed by Whisper large-v3 and turbo. No new inference was performed.

Development weights
--------------------

Weights use the separate 98 AMI training-labelled meetings already prepared for normalization experiments. Evaluation meeting series and recurring speakers were excluded in that preparation. All 98 development meetings are scenario meetings: the resulting vocabulary emphasizes product-design discussion and is not a neutral vocabulary for every meeting type. The test pilot includes non-scenario meetings too; subsequent metadata characterization should expose this mismatch.

The background is the public Brown corpus distributed by NLTK: 500 documents of edited American English, from Francis and Kucera (1964), revised 1971/1979. This is a small, reproducible alternative to the originally suggested Wikipedia background. The 3.3 MB archive, SHA-256, source URL, README, and attribution are retained in `data/background/brown/`. Its README permits redistribution. The download URL names a mutable branch; the retained archive hash identifies the exact input actually used. Brown is old and differs in genre from conversational meetings.

For each normalization policy, normalize both corpora with the upstream English normalizer, optionally followed by our fixed Snowball stemmer. An AMI document is a whole meeting, assembled from its discovery segments; a Brown document is one original corpus file. Speaker fragments are not treated as independent documents. Strip Brown's POS tags before normalization. Compute:

```
IDF(t) = ln((number_of_documents + 1) / (document_frequency(t) + 1))
salience(t) = AMI_relative_token_frequency(t)
              * max(0, Brown_IDF(t) - AMI_meeting_IDF(t))
weight(t) = 1 + 3 * salience(t) / maximum_development_salience
```

This is a TF-IDF-informed contrast heuristic, not standard textbook TF-IDF. The IDF difference favors terms appearing in a larger fraction of AMI meetings than Brown documents. Token frequency favors recurring terms rather than isolated rare names. Document sizes and genres differ, so this is not a calibrated statistical measure of domain specificity.

Only lowercase ASCII alphabetic tokens of length at least three, observed at least five times in at least three meetings and two meeting series, can receive a boost. Other terms—including unseen terms, numbers, unsupported rare names and letter tokens—receive weight 1. Eligible boosts lie in (1, 4]. The support thresholds and maximum boost are explicit heuristic choices, fixed before weighted pilot scoring; they were not optimized for retrieval outcomes or a preferred model ranking.

The 117 conversational/function-word exclusions were **curated by Codex as the LLM**, using the development-weight output and general linguistic judgments. They were not taken from a published stopword list, and no human or independent assessor reviewed them. “Documented” means the actual forms and their treatment are recorded in `configs/domain_metric_v1.json`, not that they have an external authoritative source. This is a subjective design choice that should be reviewed; a comparison with and without exclusions remains a useful sensitivity experiment.

The motivating anecdote came from the initial development-only weighting pass: without exclusions, `yeah` received the maximum weight of 4.000 and `okay` about 2.051, ahead of `remote` (1.472), `buttons` (1.415), and `button` (1.266). Thus “yeah” and “okay” dominated the **top of the weight ranking**, reflecting conversational style relative to edited prose. We did not compute a no-exclusion pilot score, so we cannot claim they dominated the total evaluation error cost. The observed token was `okay`, rather than literally `ok`; both forms are in the curated list. These initial values were observed in the development tool output before the prototype weights were replaced; the frozen final weights are the retained artifacts.

Before any pilot weighted scores were computed, we froze those 117 forms as exclusions from boosting. They still count at weight 1: no words are removed from transcripts. The stemmed policy excludes their stem forms too. This metric-specific boost eligibility is distinct from the deferred stopword-removal normalization experiment.

The final LLM review of top development weights found plausible search terms:

| Upstream-normalized term | Weight |
| --- | ---: |
| remote | 4.000 |
| buttons | 3.638 |
| button | 2.692 |
| lcd | 2.476 |
| user | 2.162 |
| design | 1.978 |
| scroll | 1.961 |
| control | 1.931 |
| interface | 1.889 |

There are 1,944 boosted upstream terms and 1,269 boosted stems. Under stemming, `button` has weight 4.000 and `remot` 3.424. We recompute weights from equivalently normalized development/background text rather than transferring unstemmed weights to stems. This keeps vocabulary definitions consistent, but cross-normalization comparisons change both token equivalence and fitted weighting; they do not isolate stemming alone. The stemming-only experiment remains in STEMMING.md.

Review was performed by the LLM on development outputs, not a human or independent relevance assessor. The complete weights, counts, document frequencies and salience values are saved in `data/development/domain_metric/{upstream,stemmed}_weights.json`. Fitting used no test references or model predictions; the pilot itself is already inspected, so results remain exploratory.

Alignment and aggregation
--------------------------

We directly minimize weighted token Levenshtein cost:

- Exact match: 0.
- Deletion: weight of the reference token.
- Insertion: weight of the predicted token.
- Substitution: maximum of the reference and predicted token weights.

Using the maximum charges for hallucinated boosted terms as well as missed boosted terms. An unknown hallucinated term still costs at least 1; it does not automatically receive maximum weight. This conservative fallback can underemphasize unseen important terms. Ties prefer match/substitution, then deletion, then insertion. Positive weights ensure insertions and deletions are never free.

Weighted WER is `100 * pooled weighted edit cost / pooled reference weight`. We pool costs and reference masses across clips rather than average clip percentages. Empty hypotheses and insertions into empty references have defined costs; the fixed pilot has positive pooled reference mass. Like ordinary WER, insertions can make the result exceed 100%.

The algorithm selects a minimum weighted-cost alignment, rather than adding weights along an arbitrary ordinary-WER alignment. Compound merging is disabled for both the ordinary-token control and weighted metric. Our compound rules, stopword removal, and acronym rules are not applied. This gives an explicit, testable metric definition; weighted scores must not be compared directly against compound-aware leaderboard WER as though weighting were the only change.

Pilot results
--------------

All values are pooled scores on the frozen 800 clips, not design-weighted full-split estimates. The ordinary controls use the same normalization as their corresponding weighted columns and ordinary token alignment.

| Model | Ordinary token WER | Domain-weighted WER | Stemmed token WER | Stemmed domain-weighted WER |
| --- | ---: | ---: | ---: | ---: |
| Whisper large-v3 | 14.737% | 14.379% | 14.492% | 14.090% |
| Whisper large-v3-turbo | 15.249% | 14.905% | 14.958% | 14.573% |
| Parakeet TDT v3 | 9.646% | 9.457% | 9.366% | 9.125% |

Official compound-aware baseline WER remains 14.329%, 14.853%, and 9.215%, respectively; these values are retained separately in the result artifact.

The weighted score is lower than its ordinary-token control for each model. Under these particular weights, relative error burden is slightly lower when recurring domain vocabulary is emphasized. This is descriptive evidence under our scoring choices, not proof that domain terms are always recognized correctly, that retrieval improves, or that the small differences between score reductions are meaningful. No new uncertainty estimates are claimed for these weighted comparisons.

Of 8,584 reference tokens, 1,919 receive a boost without stemming (22.36%); 1,844 receive a boost with stemming (21.48%). Weighted reference mass is 8,958.104 and 8,968.938, respectively. The boosts add only about 4.4–4.5% to total reference mass, so this policy is a modest reweighting, not an evaluation exclusively of keywords. There are 121 development-OOV reference tokens without stemming and 75 with stemming; these retain weight 1. Per-model predicted-token coverage and OOV counts are also recorded.

The decision supported so far is that this additional vocabulary emphasis does not overturn Parakeet's advantage in the pilot. A search system with different query terms, phrase constraints, or requirements for names and numbers could prefer a different policy. Actual search validation would require held-out queries and relevance judgments, which are not part of this metric implementation.

Reproduction and validation
----------------------------

With the retained Brown archive and development transcripts:

```bash
normExpEnv/bin/python scripts/fit_domain_weights.py
normExpEnv/bin/python scripts/evaluate_domain_metric.py results/pilot/20261114T195638016516Z
normExpEnv/bin/python -m unittest discover -s tests -v
```

Do not refit weights after inspecting test errors to favor a ranking; preserve versioned policy and weight artifacts for evaluation. The evaluator checks policy/development/background hashes against the fitted artifacts, validates weight bounds, and reproduces verified baseline edit counts after coverage/reference/duration checks. Outputs include input, policy, fitted-weight, and source hashes. Existing raw data and predictions are unchanged.

`results/pilot/20261114T195638016516Z/domain_metric_analysis.json` contains pooled costs, ordinary controls, coverage, OOV counts, and provenance. Each model's `domain_metric_clip_counts.jsonl` stores weighted components and denominator mass for later paired uncertainty and metadata characterization. Brown preprocessing and fitting are in `scripts/fit_domain_weights.py`; the metric is in `scripts/domain_metric.py`.

All 23 tests pass. Six new tests verify uniform-weight equivalence to ordinary token edit distance, explicit term/hallucination costs, optimal weighted alignment against exhaustive small examples, development-support constraints, boost exclusions without token removal, and invalid-weight rejection. No additional dependencies or GPU inference were needed for this phase.

Next: characterize ordinary and alternative scores using the available meeting, series, speaker, scenario and duration metadata. Stopword removal, acronym canonicalization, keyword precision/recall, and a downstream retrieval test remain optional extensions.
