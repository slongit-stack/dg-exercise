# Reproducibility and validation status

The numerical experiment is frozen at the completed 800-clip pilot. The user deferred exclusion-list sensitivity and the full reproduction run. Packaging provides the inputs and commands for that later work; it does not establish that a fresh machine reproduces every result.

## Evidence already obtained

- Data preparation decoded all evaluation clips and checked format, finite samples, durations, duplicate/zero audio and reference/metadata joins. The pilot was selected before inference; selection determinism was checked.
- All three models completed smoke and pilot inference on the A10G. Saved prediction coverage, raw references and durations were verified; scoring and subgroup counts reconciled.
- Compound, stem and domain-metric analyses completed, and performance characterization recomputed all eight internal score variants. The reader-facing report presents four token-aligned variants.
- The CPU replay archive was built from an explicit allowlist. Its archive checksum and all 60 member checksums passed. It contains no audio, model weights or application credential directories.
- Thirty unit tests passed during packaging. New tests cover restore conflict handling, idempotent restore and rejection of archive path traversal. Earlier tests cover metric/alignment behavior and subgroup aggregation.
- The replay command sequence was inspected with `--dry-run`; it did not copy a run, rescore, refit or execute inference.
- The standalone four-score renderer was checked against the previously saved four-score tables using a temporary directory. Documentation links and the Git file set were checked as part of packaging.

## Prepared but deferred

- Full CPU replay through `make replay` after the exclusion-list sensitivity work.
- A clean Python environment installation followed by replay, without relying on this workspace's `.pth` file or preinstalled dependencies.
- Re-derivation from independently downloaded AMI manual annotations and Brown; replay instead retains their exact derived inputs and checksums.
- A repeat GPU inference run. Existing model/driver/backend evidence remains documented in INFERENCE.md; the current packaging work did not use the GPU.
- Exclusion-list sensitivity, human review of the exclusion list, and actual retrieval evaluation.

## Later reproduction procedure

1. Preserve v1 policy, weights and results. Implement any sensitivity variant under new identifiers and output paths.
2. Create a clean CPU environment using README.md; clone and check out the pinned upstream normalizer.
3. Verify and restore the bundle, then run tests.
4. Run `scripts/project.py replay --output results/replay/CHOSEN_NEW_NAME` using a nonexistent output directory. It copies the saved run and recomputes analyses there with frozen v1 parameters; it does not refit weights. Evaluate sensitivity variants separately.
5. Compare all pooled score numerators/denominators and subgroup partitions, not just rounded displayed percentages. Compare input/policy hashes and investigate rather than suppressing differences.
6. Record Python/dependency versions, command output, exit status and output checksums. Explicitly note any environment changes or expected descriptive-path differences in JSON.
7. If independent inference reproduction is needed, use a new timestamped run, preserve raw outputs and compare coverage, scores and transcript differences. Timing and GPU engine reproducibility are separate questions from score replay.

A local Git repository is prepared with an initial snapshot of the reviewed code, documentation, summaries and replay bundle. No remote repository is created or published by these steps. A code license has not been selected; third-party data/software attribution is in THIRD_PARTY.md. Publication and a broader license choice remain separate decisions.

## Workspace cleanup

The unrelated standalone transcription script, scratch test/checkpoint files,
BeamformIt checkout, four earlier room-array recording sets (EN2001a/b and
ES2002a/b), and beamformed EN2001a outputs were removed at the user's request.
This freed about 6.45 GB (6.01 GiB). Those recordings were never inputs to the
reported scores. The HF evaluation data, AMI annotation sources, environments,
model caches, saved inference, fitted policies and replay bundle are retained.
The original exercise/discussion and explicitly preserved initial report remain
as relevant project context and history.
