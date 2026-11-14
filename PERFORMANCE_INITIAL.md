Pilot performance characterization
===================================

Parakeet remains the strongest overall model in this pilot across the normalization and weighting policies tested. That conclusion holds for each meeting series, meeting type, duration bin and annotated role group. Smaller speaker-level comparisons can change the ordering; Whisper large-v3 versus turbo also varies across groups. These are descriptive subgroup results, not independent significance tests or evidence of a causal metadata effect.

The analysis uses all 800 frozen test clips, 8,584 normalized reference words and 49.92 audio minutes. It recomputes eight metrics from the original saved predictions: official WER, stem-normalized compound-aware WER, ordinary token WER, stemmed token WER, domain-weighted WER, stemmed domain-weighted WER, and the two custom-compound variants. All pooled results reproduce their earlier analyses.

[Complete tables](results/pilot/20261114T195638016516Z/performance_characterization.md) cover 47 groups across six fields, including every meeting and speaker. The accompanying [CSV](results/pilot/20261114T195638016516Z/performance_characterization.csv) and JSON contain all eight metrics, edit-cost components, group support and denominators.

Meeting type and series
------------------------

Official WER, pooled within each group:

| Meeting type | Clips | Words | Minutes | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Scenario | 477 | 5,423 | 33.17 | 11.12% | 11.54% | 6.80% |
| Non-scenario | 323 | 3,161 | 16.75 | 19.84% | 20.53% | 13.35% |

Every model scores worse on the non-scenario subset. But this subset consists entirely of EN2002, one series with four recurring speakers; scenario data come from three other series and twelve speakers. Meeting type is inseparable from these series, speaker and topic differences here. It would be misleading to conclude that non-scenario meetings generally cause this much extra error.

| Series | Clips | Words | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: |
| EN2002 | 323 | 3,161 | 19.84% | 20.53% | 13.35% |
| ES2004 | 170 | 2,280 | 10.39% | 10.83% | 5.96% |
| IS1009 | 127 | 1,602 | 12.11% | 12.42% | 7.18% |
| TS3003 | 180 | 1,541 | 11.16% | 11.68% | 7.66% |

The ordering Parakeet, large-v3, turbo holds within each series for all eight metrics. Per-meeting scores provide more variation: Parakeet remains lowest in all sixteen meetings, while the Whisper ordering changes and sometimes ties. Meetings contain only 17–97 sampled clips and 153–1,073 words, so small differences should not drive strong conclusions.

Normalization and weighting within meeting type
------------------------------------------------

To isolate weighting, compare the ordinary-token control to domain-weighted WER under the same normalization and without compound alignment:

| Group | Model | Token WER | Domain-weighted WER | Stemmed token WER | Stemmed domain-weighted WER |
| --- | --- | ---: | ---: | ---: | ---: |
| Scenario | large-v3 | 11.60% | 11.23% | 11.34% | 10.90% |
| Scenario | turbo | 11.95% | 11.60% | 11.71% | 11.29% |
| Scenario | Parakeet | 7.32% | 7.15% | 7.04% | 6.80% |
| Non-scenario | large-v3 | 20.12% | 20.07% | 19.90% | 19.86% |
| Non-scenario | turbo | 20.91% | 20.87% | 20.53% | 20.51% |
| Non-scenario | Parakeet | 13.63% | 13.61% | 13.35% | 13.33% |

Weighting has a larger effect in scenario data, consistent with its scenario-only development source. The boosts add 6.27% to scenario reference mass but just 1.09% to non-scenario mass without stemming (6.53% versus 0.97% with stemming). This is a tangible limitation of our current domain vocabulary: it emphasizes product-design terms much more than the non-scenario discussion. It should not be advertised as uniformly prioritizing the important vocabulary of every meeting.

Stemming reduces pooled WER in both meeting types, with no change in their model ranking. It is not uniformly beneficial in every smaller subgroup: for example Parakeet's compound-aware WER changes from 7.78% to 7.82% in duration Q3. Text policy and alignment can interact. The custom compound rules affect only the previously identified TS3003a reference, so they do not materially change these broad conclusions.

Duration
---------

Bins reuse the full eligible split's duration quartiles fixed before inference; no thresholds were chosen to maximize observed performance differences. Scores below are official WER.

| Bin | Clip duration | Clips | Words | large-v3 | turbo | Parakeet |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Q1 | <1.74 s | 197 | 828 | 23.79% | 22.83% | 20.17% |
| Q2 | 1.74–<2.90 s | 200 | 1,394 | 18.29% | 20.30% | 14.28% |
| Q3 | 2.90–<4.93 s | 203 | 2,237 | 12.11% | 12.65% | 7.78% |
| Q4 | >=4.93 s | 200 | 4,125 | 12.29% | 12.61% | 6.08% |

The shortest clips have the highest WER for every model. They contribute nearly a quarter of clips but under a tenth of reference words. Short references make individual insertions or deletions proportionally expensive; clip context, content and reference quality may also matter. This does not establish that simply changing segment length would improve recognition.

Parakeet stays lowest in every duration bin under all eight metrics. Turbo beats large-v3 in Q1, while large-v3 is lower in Q2–Q4. That pattern survives stemming and weighting. Thus the overall Whisper ordering is not universal across clip lengths.

Roles
------

These are AMI scenario-task roles: ID = industrial designer, ME = marketing expert, PM = project manager, UI = user-interface designer. They are not inferred occupations, demographics or acoustic traits. Official WER:

| Role | Clips | Words | Speakers | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ID | 90 | 1,310 | 3 | 12.90% | 14.20% | 5.27% |
| ME | 122 | 1,464 | 3 | 9.90% | 9.22% | 7.17% |
| PM | 192 | 1,936 | 3 | 8.83% | 9.56% | 5.89% |
| UI | 73 | 713 | 3 | 16.55% | 16.83% | 11.36% |
| Unannotated | 323 | 3,161 | 4 | 19.84% | 20.53% | 13.35% |

Turbo beats large-v3 in the ME group; large-v3 is lower in the other groups. Parakeet is lowest throughout. This ordering survives all eight policies. Roles have only three speakers each across the three scenario series, so speaker and role effects cannot be separated reliably. All non-scenario clips lack a role annotation and remain in the explicit unannotated group; they are not discarded or treated as having an unknown scenario role.

Speakers and exceptions
-------------------------

The sixteen speaker groups contain 18–118 clips and 167–1,155 words. They are repeated across sessions within their series. They are not independent observations for a broad population claim, and the tables should not be interpreted as evidence of accent, gender or demographic effects.

Parakeet is lowest for all sixteen speakers under official WER. One subgroup illustrates policy-dependent ordering:

| FEE016 (42 clips, 572 words) | large-v3 | turbo | Parakeet |
| --- | ---: | ---: | ---: |
| Official WER | 9.44% | 8.22% | 8.04% |
| Stem-normalized, compound-aware WER | 8.92% | 7.69% | 7.87% |
| Ordinary token WER | 9.44% | 8.22% | 8.74% |
| Stemmed domain-weighted WER | 8.80% | 7.59% | 8.21% |

Turbo leads for this speaker under the latter three policies. The official-to-stemmed-compound comparison reverses the order by one net error; token alignment already gives turbo the lead before weighting. Therefore the weighted comparison is not evidence that weighting alone caused the reversal. This is a small exploratory exception, not a statistically established preference for this speaker.

Metadata reliability and limits
--------------------------------

All 800 rows were checked against the existing AMI `meetings.xml` for meeting type, global speaker/channel identity, annotation agent and role. Series IDs were checked against meeting IDs; durations agree with stored frame counts and sample rate. The only missing field among the selected annotations is role, missing in 323 clips as described above. The annotation source hash and checks are recorded in the output.

These checks establish consistency of our joins and field interpretation, not independent correctness of the original annotations. Earlier dataset preparation decoded and verified every audio file. This phase does not repeat waveform validation or listening review, and does not infer speaking rate, active-speech duration, SNR, overlap, accent or demographics. The headset label is used to verify identity, not interpreted as proof of upstream microphone processing.

Every field partitions the fixed sample; all subgroup numerators and denominators reconcile to pooled scores. Metrics use ratios of pooled counts or costs, never average clip WERs. Each CSV row reports its metric-specific reference mass, so compound token-count changes and weighted denominators remain visible. Missing roles are retained. Exact/near-floating-point ties are explicitly labelled in machine-readable ranking summaries rather than assigned a strict order.

Groups overlap across fields and are confounded with each other. Only four independent series are available; there are many exploratory subgroup comparisons and no new significance tests, subgroup confidence intervals, causal claims or correction for multiple comparisons. The earlier paired uncertainty analysis remains the appropriate context for overall model differences. No metric parameters, weights or normalization rules were changed in response to this characterization.

Reproduction
-------------

```bash
normExpEnv/bin/python scripts/characterize_performance.py results/pilot/20261114T195638016516Z
normExpEnv/bin/python -m unittest discover -s tests -v
```

The script verifies manifests and saved prediction/weight/rule hashes against earlier analyses, recomputes all eight scores and reconciles subgroup totals. It saves `performance_characterization.json`, CSV, generated Markdown tables, and per-model `characterization_clip_counts.jsonl` with metric costs and labels. The run stays CPU-only and uses no new inference.

All 27 tests pass, including pooled-versus-averaged scoring, duration boundaries, missing-role retention, undefined zero-mass groups and correct tie labelling.

The core performance-characterization step is complete. Remaining core work is report/repository consolidation; stopword normalization, acronym rules, no-exclusion metric sensitivity, keyword precision/recall, and embedding-based selection remain optional extensions.
