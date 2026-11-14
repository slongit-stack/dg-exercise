Project agenda
==============

Decision context: compare three open-weight ASR systems for meeting search, distinguishing transcription accuracy from normalization choices and domain-term preservation. Core models are Whisper large-v3, Whisper large-v3-turbo, and Parakeet TDT 0.6B v3.

1. **Dataset preparation — complete for evaluation.** Use the verified, frozen 800-clip AMI-Cleaned test pilot. Prepare separate AMI meetings for developing normalization and metric inputs. Speaker-seeded embedding expansion is a stretch goal.
2. **Leaderboard reproduction — complete at the agreed pilot scope.** Retain upstream inference, pinned inputs/configurations, raw predictions, common scoring, comparisons with published scores, and the uncertainty analysis. Document unknown historical revisions; no full-split inference is required.
3. **Compound normalization — v1 complete.** Audited existing compound-aware alignment, discovered candidates from separate meetings, recorded LLM review, froze 42 conservative rules, and rescored saved predictions in a normalization × alignment comparison. The additional effect is tiny; see COMPOUNDS.md. Preserve raw references and the fixed eligible clip set.
4. **Complementary metric — v1 complete.** Implemented TF-IDF-informed domain-contrast weighted WER with separate AMI development meetings and Brown background documents, under upstream and stem normalization. Recorded development review and explicit weighted alignment costs. See DOMAIN_METRIC.md for scores and limitations. Keyword precision/recall remains optional.
5. **Performance characterization — v1 complete.** Recomputed eight scores across meeting type, series, meeting, speaker, annotated role, and fixed duration quartiles. Verified metadata joins, retained missing roles, reconciled all subgroup counts, and documented confounding and policy-dependent exceptions. See PERFORMANCE.md and run-level JSON/CSV/tables. No new inferred metadata or subgroup significance claims.
6. **Report and repository — ongoing, final cleanup at the end.** Consolidate code, document methods and limitations, record AI assistance, prepare a clear README and rerun instructions, and initialize/publish a Git repository as appropriate. Keep large data, environments, weights, and caches out of version control.

Working rules
-------------

Normalization update: the fixed Snowball English stemming experiment is complete;
see STEMMING.md. It changes all three model scores without changing the ranking.
Stopword removal and acronym canonicalization are documented there as optional
future additions. Neither is enabled. The complementary metric is now complete
at v1 scope; performance characterization is also complete. Report/repository
consolidation remains. The metric boost-exclusion list was LLM-curated rather
than externally sourced; its provenance and the motivating `yeah`/`okay`
development-weight example are explicit in DOMAIN_METRIC.md. A no-exclusion
sensitivity comparison remains optional.

- Develop rules, candidate lists, and vocabulary weights on separate AMI meetings; exclude evaluation series and recurring evaluation speakers.
- Freeze parameters before applying them to the test predictions; label later changes as exploratory.
- Review proposed compound additions with development context and retain acceptance/rejection reasons.
- Use saved predictions for CPU-only rescoring. Additional inference or embedding selection is optional, not a prerequisite.
- Keep the 800-clip pilot unless measured effects justify expansion; closeness to published scores alone is not a sample-size argument.

Evidence: DATASET.md, INFERENCE.md, PILOT.md, UNCERTAINTY.md. The original exercise and candidate-solution discussion are in `solution`.

Consolidation milestone
------------------------

The integrated findings and recommendation are in REPORT.md; the reader-facing
four-score characterization remains in PERFORMANCE.md. README.md provides setup,
replay and inference entry points. AI_USAGE.md records AI involvement, assesses
the required scope and stretch goals. THIRD_PARTY.md
records attribution; new project code has no selected blanket license yet.

Packaging retains the frozen v1 evidence and a checksummed text-only replay
bundle, excludes local environments/audio/weights/settings from Git, and adds a
replay runner that writes a fresh output directory. The full replay and clean
installation are explicitly deferred until after the sensitivity work; see
REPRODUCIBILITY.md. Lightweight tests, archive validation and command planning
are completed separately. No exclusion-list sensitivity or new inference was
performed during consolidation. No remote publication is implied by local Git
initialization.
