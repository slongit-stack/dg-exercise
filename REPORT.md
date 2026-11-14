# Choosing ASR for meeting search

Parakeet TDT 0.6B v3 is the strongest first candidate for an AMI-style meeting-search prototype amongst the three models in this experiment. It has substantially lower word error than Whisper large-v3 and large-v3-turbo, and retains that overall advantage after stemming and domain weighting. Actual search performance has not been measured, so this is a model-selection recommendation for a prototype rather than a validated retrieval-system decision.

## Reproducing the leaderboard foundation

We evaluated three open-weight systems using the Hugging Face Open ASR Leaderboard's AMI-Cleaned **test** split. The data revision, upstream code and checkpoints are pinned in `configs/`. Audio and raw references are preserved. We reuse upstream inference implementations, with local orchestration, revision/cache adapters, coverage checks and scoring wrappers. This is an approximate reproduction on a meaningful subset, not a claim to have recovered every setting behind a published historical result.

The prepared split contains 7,715 eligible clips after applying the upstream reference filter; 90 additional rows normalize to empty and remain in the audit. Evaluation uses a frozen proportional sample of 800 clips across meeting × duration-quartile strata: 49.92 audio minutes and 8,584 normalized reference words. It covers all sixteen meetings and sixteen speakers in four series.

| Model | Pilot HF compound-aware WER | Published AMI-Cleaned WER supplied by user | Difference |
| --- | ---: | ---: | ---: |
| Whisper large-v3 | 14.33% | 13.63% | +0.70 pp |
| Whisper large-v3-turbo | 14.85% | 13.88% | +0.97 pp |
| Parakeet TDT v3, fast-gpu-asr | 9.21% | 9.01% | +0.20 pp |

The published figures were supplied from the leaderboard, not independently tied to historical model/data/code revisions. Subsampling, series composition, dataset/reference processing and decoding/backend differences are plausible explanations for the gaps. We cannot attribute them precisely. Random seeds alone are not a sufficient explanation. Matching the HF normalizer does not establish complete pipeline equivalence.

All models ran sequentially on one A10G with batch size two. Backend-reported pilot inference times were about 201 seconds, 71 seconds and 6.8 seconds, respectively; their timing protocols differ and omit setup. These are observations on this run, not reproductions of published throughput rankings. Checkpoint loading, export and TensorRT engine building can materially affect first-use latency.

## Why this sample is useful

Similarity to published scores alone is not a sample-size justification. Paired stratified resampling of the saved pilot predictions gives a design-weighted large-v3-minus-Parakeet gap of 5.10 percentage points, with an approximate conditional 95% interval of 4.04–6.13 points. The turbo-minus-large-v3 gap is 0.53 points with an interval of −0.10–1.16, so that smaller overall difference remains unresolved. These weighted point estimates differ slightly from the unweighted table above.

The ranking survives omission of any one series. However, four series with recurring speakers cannot establish broad new-meeting or new-speaker generalization. The 800 clips are a useful exploratory working set for the large observed difference; they cannot guarantee detection of small normalization effects. See [UNCERTAINTY.md](UNCERTAINTY.md) for methods and interpretation.

## Normalization and a complementary metric

The four-score analysis holds token-level alignment constant and crosses two choices: HF English normalization with or without Snowball stemming, and ordinary versus domain-weighted error costs. Its WER control differs from the compound-aware leaderboard score above. The [performance report](PERFORMANCE.md) explains the four scores and their denominators.

| Model | Token WER | Stem WER | Domain WER | Stem + domain WER |
| --- | ---: | ---: | ---: | ---: |
| Whisper large-v3 | 14.737% | 14.492% | 14.379% | 14.090% |
| Whisper large-v3-turbo | 15.249% | 14.958% | 14.905% | 14.573% |
| Parakeet TDT v3 | 9.646% | 9.366% | 9.457% | 9.125% |

Stemming permits matches such as “button”/“buttons,” as a stem-based index might. It also erases distinctions such as “design”/“designer.” Lower scores under this policy do not mean that the original transcripts improved.

Domain weights use TF-IDF-informed frequency contrast between 98 separate AMI development meetings and 500 Brown documents. Terms must recur across meetings and series; weights range from one to four. Weighted alignment charges reference weight for deletions, hypothesis weight for insertions, and the larger weight for substitutions. It directly minimizes weighted cost and pools that cost over reference weight.

The background comparison initially ranked “yeah” and “okay” above technical terms. An LLM-curated list of 117 conversational/function-word forms was excluded from receiving boosts, while all those words remain counted at weight one. The list is not externally sourced or independently validated. A comparison without these exclusions is explicitly deferred. Parameters and exclusions were fixed before weighted pilot scoring, but the overall experiment remains exploratory on an already inspected pilot.

All development meetings are scenario meetings. The resulting vocabulary emphasizes product design, and its weighting affects scenario scores more than non-scenario scores. The heuristic does not establish general meeting-term importance. It also underemphasizes unsupported names, numbers and unseen terms. A different target query distribution could justify different priorities.

Also tried an empirically derived compound list. Its effect was practically negligible in this pilot and is omitted from the four-score comparisons. The historical audit remains available in [COMPOUNDS.md](COMPOUNDS.md).

## What the data breakdown reveals

Parakeet leads in every meeting, series, meeting type, duration bin and role group under the four-score analysis. Turbo beats large-v3 on the shortest clips and for the marketing-expert role. Turbo leads for one speaker under all four token-based scores, illustrating why the overall winner is not universal.

Non-scenario data have higher errors, but consist of a single series with four speakers; meeting type cannot be separated from series, topic and speaker differences. Short clips have the highest WER. Roles are assigned scenario-task roles, not demographic labels. All 323 non-scenario clips lack a role annotation and remain in an explicit unannotated group.

Metadata checks verify identity/channel joins, type/role/agent consistency, series labels and frame-derived durations for all clips. They do not independently establish that the source annotations are correct. We do not infer accent, gender, overlap, SNR or active-speech speaking rate. Grouped scores are exploratory, with small groups, repeated speakers and no subgroup significance claims. Full support counts and tables are linked from [PERFORMANCE.md](PERFORMANCE.md).

## Decision and limitations

For an initial meeting-search prototype on this material, choose Parakeet as the baseline candidate, retain raw transcripts, and align evaluation normalization with the intended index. Choose between the Whisper models based on actual application constraints rather than treating their small overall pilot difference as established.

Before a deployment decision, obtain held-out queries and relevance judgments, test important names/numbers and phrase matching, and check latency and cost under production settings. Weighted WER is an inspectable proxy for vocabulary priorities, not retrieval precision/recall or semantic adequacy. Neither the metric nor these outcomes establishes what any model was trained on.

Known limits include undocumented aspects of AMI-Cleaned processing, unknown historical leaderboard revisions, only four evaluation series, exploratory reuse of the pilot, subjective boost exclusions, genre mismatch with Brown, and no independent clean reproduction of the final packaged pipeline yet. Additional experiments should be versioned instead of silently revising policies against test errors.

## Automation and provenance

A future evaluation job can validate input hashes, pin software/checkpoints, verify prediction coverage and raw references, compute all score variants, reconcile subgroup totals and publish versioned reports. Inference should be a separate, explicitly requested stage so rescoring does not spend GPU time. The provided replay plan copies a saved run to a new directory and regenerates CPU analyses from frozen parameters; it does not overwrite the original run or refit weights.

[README.md](README.md) documents setup and entry points. [REPRODUCIBILITY.md](REPRODUCIBILITY.md) distinguishes completed checks from deferred replay. [AI_USAGE.md](AI_USAGE.md) documents AI involvement, including implementation, candidate review, metric implementation and report drafting.
