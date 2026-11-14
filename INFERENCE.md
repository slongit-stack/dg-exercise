Three-model smoke test
======================

The subsequent 800-example pilot is complete; see `PILOT.md` for its selection,
results, memory measurements, runtime projections, and rerun commands. The same
launcher supports it with `--stage pilot --warmup-steps 5`.

The smoke launcher reuses the pinned leaderboard's Transformers and Fast GPU
ASR runners on the same local 18-example dataset.

Status: all three models passed the 18-example smoke test on an A10G with
driver **580.196.07**, after the upgrade and reboot.

| Model | Compound-aware WER | Measured inference seconds |
| --- | --- | --- |
| Whisper large-v3 | 12.7946% | 6.884 |
| Whisper large-v3-turbo | 12.7946% | 1.977 |
| Parakeet TDT 0.6B v3 (fast-gpu-asr) | 6.0606% | 0.221 |

The set has 95.12 seconds of audio and 297 normalized reference words.
Every model produced all 18 predictions with matching raw references and
durations. Both Whisper models produced exactly the same raw predictions as
before the driver upgrade. Parakeet's first run took about 225 seconds including
checkpoint download, model export, engine building, warmup, and inference;
its engines are cached under `data/cache/parakeet_engines/`.

These coverage-test results are not estimates of full-dataset accuracy or
throughput. Backend timing protocols differ and exclude setup/warmup from the
inference column. Machine-readable results are in `results/smoke/summary.json`;
raw outputs, package versions, configuration, logs, and timing are under
`results/smoke/20261114T194623575187Z/`.

GPU execution requires access outside the application sandbox. The earlier
570-driver failure is preserved under `results/smoke/20261114T191844273014Z/`.
The completed driver upgrade and verification are recorded in
`results/smoke/driver_upgrade_status.json` and `driver_upgrade_install.log`.

Environments
------------

| Environment | Purpose |
| --- | --- |
| `normExpEnv` | Data preparation, orchestration, result validation and scoring; Python 3.10 |
| `normExpWhisperEnv` | Both Whisper checkpoints; Python 3.12.16, CUDA-enabled PyTorch |
| `normExpParakeetEnv` | Parakeet Fast GPU ASR; Python 3.12.16, CPU-only PyTorch for export, separate CUDA/TensorRT runtime |

Python 3.12.16 is installed locally under `.python/`. The Parakeet backend's
documented requirements are Python 3.12–3.14, an SM75-or-newer NVIDIA GPU, driver
580 or newer, and a compatible C++ compiler. G5's A10G and G6's L4 meet the GPU
architecture requirement. Driver compatibility, TensorRT export, and decoding
are verified on the A10G at batch size two with one Parakeet worker. Larger
batch sizes and G6 hardware have not been tested. The export log reports a
TensorRT allocator peak of 2,692 MiB GPU memory; this is not total process VRAM.

Recreate the two inference environments with Python 3.12 and:

```bash
python3.12 -m venv normExpWhisperEnv
normExpWhisperEnv/bin/python -m pip install --no-cache-dir -r requirements-whisper-lock.txt
python3.12 -m venv normExpParakeetEnv
normExpParakeetEnv/bin/python -m pip install --no-cache-dir -r requirements-parakeet-lock.txt
```

The lock files record the installations used for the successful GPU tests.
Whisper uses CPU TorchCodec for audio decoding alongside CUDA PyTorch for
inference. The default PyPI TorchCodec build required a different CUDA runtime;
the explicit CPU build resolves that mismatch. System FFmpeg is also available.

Running
-------

Run from the project root once `nvidia-smi` works:

```bash
normExpEnv/bin/python scripts/export_hf_subset.py
normExpEnv/bin/python scripts/run_smoke.py --dry-run
normExpEnv/bin/python scripts/run_smoke.py
```

For one model at a time:

```bash
normExpEnv/bin/python scripts/run_smoke.py --models whisper-large-v3-turbo
normExpEnv/bin/python scripts/run_smoke.py --models whisper-large-v3
normExpEnv/bin/python scripts/run_smoke.py --models parakeet
```

The launcher uses GPU zero, runs models sequentially, and starts with batch
size two, one warm-up step, and one Parakeet worker. Override `--batch-size`
or `--warmup-steps` explicitly. These are smoke settings, not the published
H200 throughput settings. Whisper uses upstream BF16/SDPA generation defaults;
Parakeet uses FP16, modified beam search with beam six, and the upstream
0.1/10/40-second TensorRT duration profile.

Exact checkpoint revisions are in `configs/inference_smoke.json`. Whisper
accepts revisions directly. `scripts/run_parakeet_upstream.py` supplies the
missing revision option by wrapping the upstream checkpoint downloader. It
also preserves the parent's cache environment when upstream launches its
export subprocess, while retaining the exporter's device/config overrides.
This prevents child imports from trying to create caches in the read-only
home directory. No upstream audio or decoding code is changed.

The local Hugging Face export preserves original Parquet features, raw
references, IDs, and embedded audio bytes, with a checksum/provenance sidecar.
The launcher checks it against the source smoke manifest before execution.
All caches are directed under `data/cache/`; model weights and target-specific
TensorRT engines will be downloaded/built on the first actual GPU run.

Results and interpretation
--------------------------

Each invocation creates a fresh `results/smoke/<timestamp>/` directory, with a
separate subdirectory for each model. Existing run directories are rejected.
Outputs include configuration, commands, installed-package versions, logs,
exit status and setup-inclusive wall time, upstream raw prediction manifests,
and a common verified score after successful inference.

The common scorer checks every expected ID occurs exactly once, the raw
reference is unchanged, and audio duration matches. It then applies the
upstream English normalizer and `kaldialign` with `merge_compounds=True`, pooling
edit counts and reference words. This avoids relying on the Whisper runner's
printed `jiwer` WER, whose alignment differs from final leaderboard scoring.

The raw predictions can be checked/scored again without inference:

```bash
normExpEnv/bin/python scripts/score_predictions.py path/to/predictions.jsonl
```

Backend-reported inference timing and full subprocess wall time are recorded
separately. Timing protocols differ between upstream backends. The smoke set
is a coverage test, not a representative accuracy or throughput sample; do
not extrapolate its RTFx directly to the full split or compare its WER with
the published full AMI-Cleaned WER. The completed representative pilot and its
runtime measurements are documented in PILOT.md. A full-split run is not required
for the agreed project scope.

Checks completed without a GPU
------------------------------

- Hugging Face loads all 18 exported examples with exact IDs, references, and
  audio SHA-256s, including with the upstream `token=True` argument.
- Both inference environments reproduce cached normalization for all 7,805
  references.
- Whisper's upstream preparation decodes the local smoke audio successfully;
  Parakeet's upstream preparation preserves all 18 float32 waveforms exactly.
- Both upstream CLIs import successfully; the Whisper WER module is cached.
- All three environments pass `pip check`.
- Seven unit tests pass for scoring integrity, compound merging, pooled WER,
  and propagation of cache/device settings into the export subprocess.
- The launcher exits before inference when GPU preflight fails.

Run the unit checks with:

```bash
normExpEnv/bin/python -m unittest discover -s tests -v
```
