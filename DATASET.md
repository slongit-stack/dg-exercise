AMI-Cleaned preparation and verification
=======================================

The reproduction dataset is `hf-audio/open-asr-leaderboard`, configuration
`ami_cleaned`, split `test`, pinned to revision
`de79e57adf9983993bcc72586d7313460825f5eb`.
See `configs/ami_cleaned.json` for manifest locations and the scoring revision.
The published comparison values remain in `configs/leaderboard_reference.json`.
We have not verified that the current pinned dataset and scoring revisions are
the historical revisions used for those published values.

Prepared data
-------------

| Item | Result |
| --- | --- |
| Download | Three Parquet shards, 1,848,264,937 bytes; SHA-256s match Hugging Face LFS metadata |
| Raw test split | 7,805 examples, 8.01575 audio hours |
| Eligible evaluation split | 7,715 examples, 7.97989 audio hours |
| Excluded by upstream reference filter | 90 examples; retained in audit manifest |
| Normalized evaluation reference words | 82,348 |
| Audio | Mono, 16 kHz, 32-bit float WAV |
| Duration range | 1.0–26.1699375 seconds; median 2.88 seconds |
| Coverage | 16 meetings, 16 speaker IDs, four meeting series |
| Smoke test | 18 clips, 95.12 seconds; covers all meetings and both duration extremes |

All clips were decoded and checked for finite samples, expected channel count
and sample rate, and duration agreement within one sample. No duplicate audio,
all-zero audio, or peaks above unit amplitude were found. This is a technical
validation, not a listening audit of intelligibility or reference correctness.

`data/leaderboard/ami_cleaned/` contains:

- `manifest_all.jsonl`: every original row in original shard order, including
  excluded references, with eligibility flags and audit metadata.
- `manifest_test.jsonl`: all eligible rows; the primary evaluation manifest.
- `manifest_smoke.jsonl`: deterministic coverage sample for debugging inference.
- `audio/`: original embedded WAV bytes, extracted without resampling,
  renormalization, or quantization.
- `verification.json`: counts, duration distribution, meeting breakdowns,
  dependency versions, annotation checksum, and limitations.
- `download_provenance.json`: pinned revision and verified shard checksums.
- `dataset_info.json` and `upstream_README.md`: pinned source metadata.
- `shards/`: original downloaded Parquet files.

Every manifest row preserves the unmodified reference as `text`. Use this field
as the raw reference when rescoring. `normalized_text` is a cached result of the
pinned upstream English normalizer, useful for auditing and filtering; it must
not replace the raw text in normalization experiments. Paths are relative to
the project root. Original IDs, source shard/row, embedded filename, audio
checksum, frame count, and dataset revision are retained.

The eligibility predicate matches upstream `is_target_text_in_range` applied
to normalized text: exclude empty strings and `ignore time segment in scoring`.
The 90 observed exclusions normalize to empty text, including fillers such as
`Mm.` and `Um um.`. Keep the eligible example set fixed when comparing scoring
variants unless an explicitly separate experiment changes that policy.

Scope and metadata interpretation
---------------------------------

The full eligible split is prepared rather than choosing an arbitrary smaller
evaluation sample. Use the smoke manifest to establish inference compatibility
and estimate cost before deciding whether to run the full split. The smoke set
is selected by a fixed ID hash from typical-length clips in each meeting, plus
the shortest and longest eligible clips. It is not a representative score
estimate and must not be used to tune the normalizer.

The meetings are the a–d sessions of EN2002, ES2004, IS1009, and TS3003. Repeated
speakers mean these 16 meetings are not independent speaker samples. Preserve
`meeting_series_id` when analyzing uncertainty; only four series are present.

Every example's meeting, speaker ID, and headset channel number matches the
local AMI `data/corpusResources/meetings.xml`. Meeting type, annotation agent,
and role (where available) are joined from that file. This corroborates the
ID interpretation; it does not establish all upstream audio processing.
The downloaded card does not clearly document how `ami_cleaned` was produced,
so exact microphone processing and reference-cleaning provenance remain open.

Start/end numbers are retained as `encoded_start`/`encoded_end`; their scale
and alignment to original recordings have not been independently verified.
`words_per_segment_second` measures normalized reference-word density over the
whole clip, not active-speech speaking rate. Overlap, SNR, and active-speech
duration are not estimated in this preparation step.

Earlier raw room recordings (EN2001a, EN2001b, ES2002a, ES2002b) and beamformed
EN2001a audio belonged to a separate experiment. They were removed during
workspace cleanup; none overlapped these test meetings or supplied evaluation
audio. AMI source annotations are retained for development-data reconstruction.
Development text has since been prepared from 98 separate, training-labelled AMI
meetings, excluding evaluation series and speakers; see COMPOUNDS.md and
DOMAIN_METRIC.md. Rules and weights are developed outside these test references.

Rerunning
---------

From the project root:

```bash
source normExpEnv/bin/activate
python -m pip install -r requirements-data.txt
python scripts/download_ami_cleaned.py
PYTHONPATH="$PWD/open_asr_leaderboard" python scripts/prepare_ami_cleaned.py
```

The preparation script also needs the local AMI `meetings.xml` annotation file.
The checkout must be at scoring commit
`c21a412f2dd7cbe3af658d69fbf3d0dd536a264e` to reproduce these normalized values.
The existing virtual environment already adds that checkout to its import path;
the explicit `PYTHONPATH` above also supports a freshly recreated environment.

Downloads are verified before use. Existing extracted audio with a different
checksum causes preparation to stop. A repeated preparation run produced
identical manifests and verification output. Additional checks confirmed exact
raw-reference preservation, parity with the actual upstream filtering function
on all rows, and smoke-set membership, coverage, checksums, and decoding.

The upstream card identifies AMI as CC-BY-4.0; retain the source attribution and
consult its citation when distributing results. Three-model pilot inference is
complete; see PILOT.md. The agreed evaluation scope is the frozen 800-clip pilot,
with the full eligible split retained for provenance and selection auditing.
