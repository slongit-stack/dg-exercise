Meeting transcription performance for search
==============================================

Parakeet TDT v3 has the lowest overall error rate under all four scoring policies tested. Its advantage holds across meeting types, meeting series, clip-duration bins and role groups. Whisper large-v3 and turbo change order in some subgroups, and turbo leads for one speaker. Stemming and vocabulary weighting change the scores without changing the overall model ranking.

The evaluation covers 800 AMI-Cleaned test clips: 49.92 minutes of audio, 8,584 normalized reference words, sixteen meetings, sixteen speakers and four meeting series. The same saved predictions are used for every comparison. The application question is which model best preserves the words a meeting-search system would match and prioritize.

Four scoring policies
----------------------

Every policy starts with the **Hugging Face English normalizer** used in our pinned leaderboard checkout. It standardizes text features such as casing, punctuation, contractions, numbers and spelling before references and predictions are compared.

| Score | Text normalization | Error costs | What it examines |
| --- | --- | --- | --- |
| **WER** | Hugging Face English normalizer | Ordinary token edit counts | Overall word accuracy after HF normalization |
| **Stem WER** | HF normalization, then English stemming | Ordinary token edit counts | Accuracy when morphological variants can match |
| **Domain WER** | HF normalization | Domain-weighted token edit costs | Accuracy with extra emphasis on recurring domain vocabulary |
| **Stem + domain WER** | HF normalization, then English stemming | Domain-weighted token edit costs | The combined search-oriented matching and weighting policy |

All four use token-level alignment, with no compound merging, to keep the comparison consistent. Our leaderboard reproduction separately used compound-aware alignment; the WER values here consequently differ slightly from those reproduction scores. “HF normalization” describes the particular leaderboard implementation, rather than a universal standard for English transcription.

Ordinary WER divides pooled insertions, deletions and substitutions by the reference-token count. Domain WER divides pooled weighted edit cost by reference-token weight. Lower is better; a more forgiving score does not mean that the underlying transcription has improved.

Stemming
---------

We apply the fixed Snowball English stemmer after HF normalization, independently to each transcript. It makes forms such as “button”/“buttons” and “design”/“designed”/“designing” match, approximating a search index that uses stems. It preserves token count and leaves numbers and mixed alphanumeric identifiers unchanged.

Stemming also merges some meaningful distinctions: “design” and “designer,” for example. It is therefore a deliberate search-matching policy rather than a claim that the words are interchangeable in every context.

Domain weighting
-----------------

Weights come from 98 separate AMI development meetings, excluding evaluation meeting series and speakers. The background is Brown, a public 500-document corpus of general written English. We combine AMI term frequency with the difference between background and AMI document-frequency measures: terms recurring across AMI meetings but less prevalent in Brown can receive higher weights.

Eligible terms must occur at least five times, across at least three meetings and two series. Weights range from 1 to 4; unsupported and unseen terms retain weight 1. Missing a reference term costs its weight, inserting a predicted term costs its weight, and substituting one term for another costs the larger weight. Alignment minimizes this weighted cost directly.

The development review exposed a genre mismatch: “yeah” initially received weight 4.00 and “okay” 2.05, ahead of “remote” at 1.47. Conversational style was dominating the top of the weight ranking. We consequently excluded 117 conversational/function-word forms from receiving boosts. **This list was curated by the LLM, not sourced from a published stopword list.** Those words still count at weight 1; they are not removed. We did not measure whether they dominated total error cost without exclusions.

The final weights emphasize terms such as “remote,” “buttons,” “LCD,” “interface” and “battery.” We fit separate weights to unstemmed and stemmed development text. Thus a comparison between the two weighted scores changes both token equivalence and the learned weights; WER versus Stem WER isolates stemming without that additional change. The complete formula, curated exclusions and provenance are in [DOMAIN_METRIC.md](DOMAIN_METRIC.md).

An empirically derived compound list was also tested, but its effect was practically unnoticeable in this pilot, so it is omitted from the comparisons below. Limited discovery coverage, including the lexicon used, or a low incidence of matching ambiguous forms could explain the small effect; this experiment does not distinguish those explanations.

Overall results
----------------

| Model | WER | Stem WER | Domain WER | Stem + domain WER |
| --- | ---: | ---: | ---: | ---: |
| Whisper large-v3 | 14.737% | 14.492% | 14.379% | 14.090% |
| Whisper large-v3-turbo | 15.249% | 14.958% | 14.905% | 14.573% |
| Parakeet TDT v3 | 9.646% | 9.366% | 9.457% | 9.125% |

Stemming lowers WER for every model. Domain weighting also produces lower scores than the corresponding ordinary-token score. Under these particular weights, the relative error burden is somewhat lower when recurring domain vocabulary is emphasized. This does not establish better retrieval performance or explain a model's training history.

Only about 22% of reference tokens receive a boost, adding roughly 4.4–4.5% to total reference weight. This is a modest vocabulary emphasis, not a metric exclusively of keywords. Actual search quality would require queries and relevance judgments.

Meeting type and series
------------------------

WER by meeting type:

| Group | Clips | Words | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: |
| Non-scenario | 323 | 3,161 | 20.12% | 20.91% | 13.63% |
| Scenario | 477 | 5,423 | 11.60% | 11.95% | 7.32% |

Every model scores worse on the non-scenario subset. However, this subset consists entirely of EN2002, one series with four speakers. Scenario data come from three different series and twelve speakers. Meeting type, speakers and topic are confounded; the results do not show that non-scenario meetings generally cause higher errors.

WER by meeting series:

| Group | Clips | Words | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: |
| EN2002 | 323 | 3,161 | 20.12% | 20.91% | 13.63% |
| ES2004 | 170 | 2,280 | 10.75% | 11.18% | 6.49% |
| IS1009 | 127 | 1,602 | 12.61% | 12.92% | 7.55% |
| TS3003 | 180 | 1,541 | 11.81% | 12.07% | 8.31% |

Parakeet, large-v3 and turbo retain that order within each series under all four scores. Parakeet also leads in each of the sixteen individual meetings, although the Whisper models sometimes reverse order or tie. Individual meeting groups contain only 17–97 clips and 153–1,073 words.

The normalization and weighting comparisons within each meeting type are:

| Group | Model | WER | Stem WER | Domain WER | Stem + domain WER |
| --- | ---: | ---: | ---: | ---: | ---: |
| Scenario | large-v3 | 11.60% | 11.34% | 11.23% | 10.90% |
| Scenario | turbo | 11.95% | 11.71% | 11.60% | 11.29% |
| Scenario | Parakeet | 7.32% | 7.04% | 7.15% | 6.80% |
| Non-scenario | large-v3 | 20.12% | 19.90% | 20.07% | 19.86% |
| Non-scenario | turbo | 20.91% | 20.53% | 20.87% | 20.51% |
| Non-scenario | Parakeet | 13.63% | 13.35% | 13.61% | 13.33% |

Weighting changes scenario scores more than non-scenario scores. All development meetings were scenario meetings, so the vocabulary emphasizes product-design discussion. Without stemming, boosts add 6.27% to scenario reference weight but only 1.09% to non-scenario reference weight. This limits how broadly we can interpret “domain vocabulary” in this experiment.

Clip duration
--------------

Duration bins use full-test-split quartiles fixed before inference. The table shows WER.

| Group | Clips | Words | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q1: <1.74 s | 197 | 828 | 24.03% | 22.83% | 20.41% |
| Q2: 1.74–<2.90 s | 200 | 1,394 | 18.58% | 20.73% | 14.56% |
| Q3: 2.90–<4.93 s | 203 | 2,237 | 12.83% | 13.28% | 8.49% |
| Q4: ≥4.93 s | 200 | 4,125 | 12.61% | 12.95% | 6.45% |

The shortest clips have the highest WER for every model. They make up almost a quarter of clips but less than a tenth of reference words. Individual errors have a larger proportional effect on short references; differences in context, content and reference quality may also contribute. These results do not establish that changing segmentation alone would improve recognition.

Parakeet leads in every bin. Turbo beats large-v3 in Q1, while large-v3 leads in Q2–Q4. Both patterns hold under all four scores.

Meeting roles
--------------

Roles are the assigned AMI scenario-task roles: industrial designer (ID), marketing expert (ME), project manager (PM) and user-interface designer (UI). The table shows WER.

| Group | Clips | Words | Speakers | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Industrial designer | 90 | 1,310 | 3 | 13.66% | 14.66% | 5.73% |
| Marketing expert | 122 | 1,464 | 3 | 10.18% | 9.36% | 7.72% |
| Project manager | 192 | 1,936 | 3 | 9.35% | 10.18% | 6.40% |
| User-interface designer | 73 | 713 | 3 | 16.83% | 17.11% | 11.92% |
| Unannotated | 323 | 3,161 | 4 | 20.12% | 20.91% | 13.63% |

Turbo beats large-v3 in the marketing-expert group; large-v3 leads in the other groups. Parakeet leads throughout. These orderings hold under all four scores.

Each annotated role has just three speakers across the three scenario series. Speaker and role effects cannot be separated reliably. All 323 non-scenario clips lack a role annotation and remain in the explicit unannotated group.

Speaker differences
--------------------

Speaker groups contain 18–118 clips and 167–1,155 words. Parakeet leads for fifteen of the sixteen speakers under all four scores. Turbo leads for FEE016, whose group contains 42 clips and 572 words:

| Score | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: |
| WER | 9.44% | 8.22% | 8.74% |
| Stem WER | 8.92% | 7.69% | 8.22% |
| Domain WER | 9.31% | 8.10% | 8.69% |
| Stem + domain WER | 8.80% | 7.59% | 8.21% |

Turbo already leads under ordinary WER, so stemming and weighting do not cause this exception. It is a small exploratory subgroup, rather than an established reason to choose a different model for this speaker. Speaker IDs do not establish accent, gender or other demographic effects.

Metadata and interpretation
-----------------------------

Meeting type, speaker/channel identity and role labels were checked against the AMI meeting annotations for all 800 clips. Series IDs agree with meeting IDs, and durations agree with stored frame counts and sample rate. Role is the only missing field among the selected annotations. These checks establish consistency of the metadata joins, not independent correctness of the original annotations.

All subgroup scores pool error costs and reference mass; they do not average clip percentages. Group totals reconcile with overall scores. Groups overlap across metadata fields, and speakers recur within series. With only four series and many exploratory comparisons, small differences should not be treated as statistically established or causal. The [earlier uncertainty analysis](UNCERTAINTY.md) provides context for overall model comparisons, rather than confidence intervals for these alternative scores or subgroups.

[Complete four-score tables](results/pilot/20261114T195638016516Z/performance_four_metrics.md) include every meeting and speaker. The [CSV](results/pilot/20261114T195638016516Z/performance_four_metrics.csv) records group sizes, metric-specific denominators and edit-cost components.
