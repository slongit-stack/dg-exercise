Compound-normalization experiment v1
=====================================

The first experiment is complete. A conservative development-derived compound normalizer changes only one of 800 pilot references and no model outputs. The official compound-aware scorer already forgives that boundary difference. This is a limited effect on this sample, not evidence that compound normalization is universally unimportant.

Development material and discovery
----------------------------------

`scripts/discover_compounds.py` uses the locally downloaded AMI manual word XML annotations. It selects the 98 meetings labelled `seen_type="training"` in `meetings.xml`, excluding evaluation meeting series and any evaluation speakers. Disjointness was checked using global speaker IDs. These annotations are development inputs for our experiment; we do not claim they reproduce a Hugging Face training split or its reference-cleaning procedure. No additional audio or inference is needed.

The resulting 65,852 text segments contain 467,272 upstream-normalized words. Segments stay within speaker files and break at sentence punctuation, non-word events, or pauses exceeding one second. This reduces spurious adjacency across turns; these are discovery units, not verified linguistic sentences.

Candidates require both an observed open bigram and its concatenated token somewhere in development text, with the closed form also present in the system's CMU pronunciation lexicon. There is no minimum frequency beyond one occurrence of each form. The lexicon snapshot, package copyright, source annotation hashes, selection policy, and transcript hash are saved under `data/development/compounds/`. AMI attribution remains in `data/CCBY4.0.txt` and related source documentation.

Discovery produced 407 candidates. The candidate list, examples, counts, and provenance are preserved. A pronunciation dictionary is only a candidate filter, not proof of semantic equivalence. It also limits recall: this snapshot lacks `whiteboard`, `touchscreen`, and `touchpad`. Absence from our rules therefore does not establish that a variant is invalid or unimportant. Prefix and hyphenation variants are included in the candidate scope alongside conventional compounds.

Review and frozen rules
-----------------------

`configs/normalization/compounds_v1.json` contains all 407 decisions, rejection reasons, review method, development hashes, and the 42 accepted rules. Review was performed by the Codex LLM, not a human. All candidate forms were screened; up to two development contexts for each form were inspected for shortlisted pairs. This is a conservative linguistic screen, not exhaustive validation or an independent accuracy assessment.

Accepted examples include `infra red → infrared`, `key pad → keypad`, `web site → website`, and `tool bar → toolbar`. Meaning-changing candidates were excluded: the development example for `point less` means one fewer point, `feed back` is a verb phrase, and `power point` refers to an electrical power point rather than presentation software. Letter names, detached suffixes, fragments, and uncertain pairs were excluded.

Rules were frozen before pilot rescoring. No pilot references or predictions were used to select rules. Later inspection of the changed test clip is a result audit, not a rule-discovery input. Do not silently add rules based on it.

The text-only normalizer applies the pinned upstream English normalizer, then greedily joins accepted adjacent token pairs to a closed form. The exact same function runs independently on references and hypotheses; it never sees the other side. Rules cannot cascade, and canonicalization was verified idempotent on all development segments. It changes 167 development segments. Raw text, eligibility, and saved model predictions remain intact.

Normalization versus alignment
-------------------------------

The official `kaldialign(..., merge_compounds=True)` forgives concatenation differences without a lexical or semantic check. Synthetic checks confirm that it assigns zero errors to `white board` versus `whiteboard`, but also `a part` versus `apart`. Our normalizer intentionally keeps the latter texts distinct, although the official alignment will still forgive that distinction when enabled.

We therefore score a two-by-two experiment: upstream/custom normalization × ordinary token/compound-aware alignment. The token-only score exposes the effect of our independent text policy; the compound-aware score preserves the official comparison. Token-only variants are alternative metrics, not leaderboard WER.

| Model | Upstream + token alignment | Custom + token alignment | Official baseline | Custom + compound alignment |
| --- | ---: | ---: | ---: | ---: |
| Whisper large-v3 | 14.7367% | 14.7151% | 14.3290% | 14.3307% |
| Whisper large-v3-turbo | 15.2493% | 15.2278% | 14.8532% | 14.8549% |
| Parakeet v3 | 9.6459% | 9.6237% | 9.2148% | 9.2159% |

For each model, custom normalization removes two ordinary token errors (one substitution and one deletion) by joining a reference `tool bar`; predictions already contain `toolbar`. The reference denominator changes from 8,584 to 8,583 words. Official compound-aware error counts do not change at all; its tiny WER increase comes entirely from that denominator change. Model ranking is unchanged. These scores pool counts across the fixed pilot; they are not the design-weighted estimates in UNCERTAINTY.md.

The existing compound-aware alignment lowers baseline WER by roughly 0.40–0.43 percentage points relative to ordinary token alignment. Our 42 rules add little beyond that. Only one test clip is affected, so we make no general claim about a normalization benefit, ranking change, or downstream search quality. Dictionary coverage and the cleaned reference source constrain this experiment; no attempt was made to tune v1 until it produced a larger effect.

Reproduction and checks
------------------------

```bash
normExpEnv/bin/python scripts/discover_compounds.py
normExpEnv/bin/python scripts/evaluate_compounds.py results/pilot/20261114T195638016516Z
normExpEnv/bin/python -m unittest discover -s tests -v
```

Discovery uses the saved lexicon snapshot after its first run. If development candidates or provenance change, rescoring rejects the frozen review hashes. For a fresh machine, preserve the development artifacts or supply the same local annotations and lexicon snapshot. The upstream normalizer revision is pinned in NORMALIZATION.md.

Results are in `results/pilot/20261114T195638016516Z/compound_analysis.json`, with per-model `compound_changed_clips.json` showing the complete before/after audit. Before rescoring, prediction coverage, reference equality, durations, and baseline edit counts are checked against the verified pilot. All 13 unit tests pass, including semantic exclusions, token boundaries, idempotence, segmentation boundaries, and existing scoring integrity checks. No additional GPU inference was performed.

Next is the complementary domain-sensitive metric, with weights learned from separate development material. Metadata characterization follows those metric developments, as agreed in AGENDA.md.
