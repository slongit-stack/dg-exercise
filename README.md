# Meeting ASR evaluation for search

A three-model reproduction of the Hugging Face Open ASR Leaderboard on an AMI-Cleaned test subset, followed by search-oriented normalization, domain-weighted WER, and metadata characterization.

**Main result:** Parakeet TDT 0.6B v3 has the lowest overall error rate under all four report scoring policies amongst the three models tested. This is evidence for selecting it as the first candidate for an AMI-style meeting-search prototype, not a demonstration of downstream retrieval quality. Exact historical leaderboard settings remain unconfirmed.

Read [REPORT.md](REPORT.md) for the integrated findings, [PERFORMANCE.md](PERFORMANCE.md) for the four-score analysis, with the student-project assessment retained locally in `STUDENT_EXERCISE.md` (excluded from Git). [REPRODUCIBILITY.md](REPRODUCIBILITY.md) records what has and has not been verified. The exclusion-list sensitivity experiment and a clean reproduction run are deferred.

**Brief Description:** We investigated how to choose a speech-to-text model for searching recorded meetings, using a public Hugging Face leaderboard (https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) as our starting point. We tested three openly available models—Whisper large-v3, Whisper large-v3-turbo, and NVIDIA Parakeet—on the same 800 meeting-audio clips, totaling about 50 minutes. Parakeet made substantially fewer transcription errors in this sample; the smaller difference between the two Whisper models was less conclusive.

With the application of enabling search and information retrieval in mind, we then experimented with a modified normalization method which aggressively stems words to reduce penalties related to morphological mismatches. We also developed a domain-specific variation of WER to weigh mistakes on terms particularly relevant to this dataset higher than those on common terms using a form of Wikipedia as a backdrop.

Finally, we conduct some basic analysis of results on various subsets of the data, split on metadata categories. Results are provided in the "PERFORMANCE.md" file.

See the "REPORT.md" file for a final discussion and reporting of results.

## Contents

| Location | Purpose |
| --- | --- |
| `configs/` | Pinned dataset/model revisions and frozen normalization/metric policies |
| `scripts/` | Data preparation, upstream inference orchestration, scoring and report tables |
| `tests/` | Scoring, provenance-related and environment guardrails |
| `artifacts/` | Checksummed CPU replay bundle of public text inputs, predictions and fitted weights |
| `results/pilot/20261114T195638016516Z/` | Versioned compact summaries and tables from the completed pilot |
| `requirements-*.txt` | CPU requirements and separate GPU environment snapshots |

Local audio, model weights, caches, environments, upstream checkouts, credentials and application settings are ignored by Git. The replay archive contains licensed reference/development text and public annotation metadata, but no audio or model weights. See [THIRD_PARTY.md](THIRD_PARTY.md) for attribution and rights notices.

## CPU setup

Use Python 3.10 for scoring/analysis. From this repository's root:

```bash
python3.10 -m venv normExpEnv
normExpEnv/bin/python -m pip install -r requirements-data.txt
git clone https://github.com/huggingface/open_asr_leaderboard.git open_asr_leaderboard
git -C open_asr_leaderboard checkout c21a412f2dd7cbe3af658d69fbf3d0dd536a264e
export PYTHONPATH="$PWD/open_asr_leaderboard"
```

The upstream checkout supplies `normalizer`; it is not installed as a PyPI package. `requirements-data.txt` includes the normalization requirements. On Linux, audio operations may need system `libsndfile`; inference additionally needs FFmpeg. Setup downloads dependencies and upstream code; no GPU is needed for the CPU path. Use the absolute checkout path in `PYTHONPATH` again in a new shell, or use the Make targets, which set it automatically.

## Inspect and restore the saved experiment

```bash
normExpEnv/bin/python scripts/project.py inspect
normExpEnv/bin/python scripts/project.py restore
make test
make replay-plan
```

`inspect` checks the archive and every member hash without changing files. `restore` writes missing replay inputs into their original project-relative locations and refuses to overwrite differing files. This supplies the pilot manifest, selection audit, metadata XML, development text, Brown archive, lexicon, learned weights, saved predictions and baseline analyses. It does not require downloading AMI audio.

The replay bundle is intentionally small enough to version in Git. Its exact members, sizes and hashes are in `artifacts/pilot_replay_manifest.json`. Most run internals live only in that archive; the compact summaries and four-score tables are also directly readable in `results/`.

## Reproduce scoring later

After the exclusion-list sensitivity work, run:

```bash
make replay
```

Or choose an explicit **new** output directory:

```bash
normExpEnv/bin/python scripts/project.py replay --output results/replay/my-check
```

Replay copies the frozen pilot to a fresh directory, then runs summary, paired uncertainty, compound audit, stem scoring, domain scoring, metadata characterization and four-score table rendering. It uses frozen weights and rules; it does not refit them or run inference. The historical compound audit remains an internal validation step; the main report presents four scores. Existing saved predictions and the frozen pilot are preserved. A failed replay leaves its partial output for inspection; retry using another new directory.

The command sequence is prepared but has **not** been run end-to-end during packaging. Commands and lightweight checks are distinguished in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Rebuild data and development inputs

This path is separate from replay and requires more disk space and network access:

1. Obtain AMI manual annotations release 1.7 from the [AMI download page](https://groups.inf.ed.ac.uk/ami/download/). Place `words/`, `corpusResources/`, the release README and license under `data/`. The original word XML is needed to derive development text; it is not needed for replay.
2. Download and prepare the pinned HF data, then select the pilot:

   ```bash
   normExpEnv/bin/python scripts/download_ami_cleaned.py
   normExpEnv/bin/python scripts/prepare_ami_cleaned.py
   normExpEnv/bin/python scripts/select_pilot.py
   ```

3. Derive development candidates and text using the retained lexicon snapshot:

   ```bash
   normExpEnv/bin/python scripts/discover_compounds.py
   ```

4. The Brown archive is supplied by `restore`. To fetch it independently, use the URL in `data/background/brown/provenance.json` and verify its recorded SHA-256. The pinned hash, not the mutable download branch, identifies the input.
5. `scripts/fit_domain_weights.py` rebuilds the current weights. Do not overwrite the frozen v1 artifacts to conduct sensitivity experiments; create a versioned policy/output workflow first. Development candidates and provenance are bound to the frozen compound review by hashes. If your annotations or lexicon differ, investigate the mismatch rather than bypassing it.

See [DATASET.md](DATASET.md), [COMPOUNDS.md](COMPOUNDS.md), and [DOMAIN_METRIC.md](DOMAIN_METRIC.md) for provenance and limitations. No clean annotation-to-result rebuild is claimed yet.

## Reproduce inference

The completed run used an NVIDIA A10G on G5.xlarge and driver 580.196.07. Whisper and Parakeet require separate Python 3.12.16 environments. See [INFERENCE.md](INFERENCE.md) for environment installation, system requirements and backend details. The `*-lock.txt` files are snapshots of the successful installations, not a promise of compatibility with every future platform or package index.

After preparing all evaluation audio and installing both inference environments:

```bash
normExpEnv/bin/python scripts/export_hf_subset.py --manifest data/leaderboard/ami_cleaned/manifest_pilot.jsonl --output data/leaderboard/ami_cleaned/hf_pilot --purpose "Frozen stratified evaluation pilot"
make inference-plan
normExpEnv/bin/python scripts/run_smoke.py --stage pilot --warmup-steps 5
```

Inference creates a new timestamped run directory. Batch size is two; Parakeet uses beam six and one worker. Engines are hardware-specific and are built on first use. Warmup, model loading, export and setup costs differ from backend-reported inference time. Check `nvidia-smi` before running; the original application sandbox needed separate GPU access permission. No driver changes are performed by these commands.

## Navigation

- [PILOT.md](PILOT.md): inference results, selection and published-score comparison.
- [UNCERTAINTY.md](UNCERTAINTY.md): sample-size justification and four-series limitations.
- [STEMMING.md](STEMMING.md): fixed Snowball policy and semantic tradeoffs.
- [DOMAIN_METRIC.md](DOMAIN_METRIC.md): formula, weighted alignment and LLM-curated exclusions.
- [TOKEN_ALIGNMENT_NOTE.md](TOKEN_ALIGNMENT_NOTE.md): the verbatim explanatory note.
- [PERFORMANCE_INITIAL.md](PERFORMANCE_INITIAL.md): retained earlier eight-score report.
- [AI_USAGE.md](AI_USAGE.md): roles of AI, user decisions and verification limits.
