AMI-Cleaned pilot results
=========================

The frozen pilot contains 800 eligible test clips (49.92 audio minutes), 8,584 normalized reference words, all 16 meetings, and all 16 speaker IDs. Selection was fixed before inference, proportional across meeting × global duration-quartile strata, using largest-remainder allocation and a deterministic ID hash. Every stratum is represented. One example overlaps the earlier smoke set.

All models ran sequentially on the same NVIDIA A10G with driver 580.196.07, batch size 2, five warm-up steps, and the pinned checkpoints and scoring revision used by the smoke test. Parakeet used one worker, FP16, modified beam search with beam 6, and cached TensorRT engines. Whisper used BF16/SDPA and upstream generation settings.

| Model | Pilot WER | Published full AMI-Cleaned WER | Pilot inference | Pilot wall time | Projected full inference | Sampled device peak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| whisper-large-v3 | 14.33% | 13.63% | 200.88 s | 241.1 s | 32.11 min | 4.10 GiB |
| whisper-large-v3-turbo | 14.85% | 13.88% | 70.51 s | 87.1 s | 11.27 min | 2.08 GiB |
| parakeet | 9.21% | 9.01% | 6.77 s | 17.0 s | 1.08 min | 2.08 GiB |

All 800 predictions per model passed ID coverage, raw-reference equality, and duration checks. Common scoring applies the upstream English normalizer and compound-aware alignment, pooling edit counts. Subgroup error counts reconcile to the pooled scores. The raw references and audio bytes were preserved.

Interpretation
--------------

The subsequent [paired uncertainty analysis](UNCERTAINTY.md) supports using this pilot for exploratory normalization comparisons. Parakeet's advantage persists across clip resampling and every leave-one-series-out check; the smaller difference between Whisper models remains unresolved by the conditional clip-selection interval.

Parakeet has the lowest observed WER in the pilot and in each of the four meeting series. Large-v3 has slightly lower observed WER than turbo. These are descriptive findings; no significance or population-generalization claim is made. Only four meeting series are represented, with repeated speakers. The pilot is not the full-split leaderboard reproduction, and the revisions behind the supplied published values remain unconfirmed.

| Meeting series | large-v3 WER | turbo WER | Parakeet WER |
| --- | ---: | ---: | ---: |
| EN2002 | 19.84% | 20.53% | 13.35% |
| ES2004 | 10.39% | 10.83% | 5.96% |
| IS1009 | 12.11% | 12.42% | 7.18% |
| TS3003 | 11.16% | 11.68% | 7.66% |

EN2002 is substantially harder for every model. Meeting, series, and speaker breakdowns are saved in the machine-readable summary; these group labels are from the verified manifest metadata.

The pilot and full eligible split have similar duration distributions: median 2.93 versus 2.90 seconds; 95th percentile 9.23 versus 8.97 seconds. The pilot maximum is 17.48 seconds versus 26.17 seconds in the full split; that full-split maximum was covered by the smoke test. Allocation rounding gives slightly different inclusion probabilities, so pilot WER is not claimed as an unbiased estimate. No normalization rules or vocabulary weights were fitted on this evaluation data.

Runtime and memory
------------------

Duration-scaled projections total about 44.5 minutes of full-split inference at batch size 2, plus preparation, loading, warmup, and scoring. Scaling by example count or reference-word count gives similar values; these are sensitivity checks, not confidence intervals. Actual full-run time may differ. Backend timing protocols differ, so raw RTFx values should not be treated as a controlled architecture comparison.

The sampled memory figures are device-wide readings taken once per second over setup and inference, not exact per-process peaks. They indicate substantial headroom at batch size 2. A short fixed batch-size comparison for Whisper would be useful if full-run settings are needed; keep the checkpoint, data, normalization, and decoding policy fixed and check transcript changes. The pilot is the agreed evaluation scope; no full-run tuning is required now. Parakeet does not need another engine build for a full run at batch size 2.

Reproduction and artifacts
--------------------------

```bash
normExpEnv/bin/python scripts/select_pilot.py
normExpEnv/bin/python scripts/export_hf_subset.py --manifest data/leaderboard/ami_cleaned/manifest_pilot.jsonl --output data/leaderboard/ami_cleaned/hf_pilot --purpose "Frozen stratified evaluation pilot"
normExpEnv/bin/python scripts/run_smoke.py --stage pilot --warmup-steps 5
normExpEnv/bin/python scripts/summarize_pilot.py path/to/pilot/run
```

- Manifest and selection audit: `data/leaderboard/ami_cleaned/manifest_pilot.jsonl` and `pilot_selection.json`.
- This run: `results/pilot/20261114T195638016516Z`.
- Summary: `results/pilot/20261114T195638016516Z/summary.json`.
- Each model directory contains raw predictions, verified score, command, package versions, inference log, wall time, and GPU samples.

Pilot selection was rerun to verify determinism; all 800 exported IDs/references/audio checksums were checked through the Hugging Face loader. Seven existing integrity tests passed, and the completed pilot verified the extended launcher against all three real backends.
