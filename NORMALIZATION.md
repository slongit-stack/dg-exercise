English normalization setup
===========================

The local `open_asr_leaderboard/` checkout is from
https://github.com/huggingface/open_asr_leaderboard at commit
`c21a412f2dd7cbe3af658d69fbf3d0dd536a264e`.
Keep this revision when reproducing results: normalization and scoring can change.

`normExpEnv` uses Python 3.10.12. Activate it with:

```bash
source normExpEnv/bin/activate
```

The environment's `open_asr_leaderboard.pth` adds the absolute path of the
checkout to Python's import path. If the project moves or the environment is
recreated, recreate this file in the environment's site-packages directory.
The upstream repository has no pip installation metadata.

```python
from normalizer import EnglishTextNormalizer
from kaldialign import edit_distance

normalize = EnglishTextNormalizer()
reference = normalize("I've got twenty pounds.")
prediction = normalize("I have got £20.")
counts = edit_distance(
    tuple(reference.split()), tuple(prediction.split()), merge_compounds=True
)
print(counts)
```

This example was verified to yield zero errors. `pip check` also passed.
Dependency versions are recorded in `requirements-normalization.txt`.

The current upstream English scoring uses this normalizer on both reference
and prediction, then `kaldialign` with `merge_compounds=True`. Corpus WER
should sum edit counts and reference word counts across examples before
division, rather than averaging utterance WERs.

This installs the English normalization and alignment components only. Running
the full upstream evaluation entry points additionally requires their dataset,
inference, and other dependencies. Model evaluation is now complete at pilot
scope; see PILOT.md. The first custom compound-normalization experiment is
documented in COMPOUNDS.md, with the agreed project sequence in AGENDA.md.
Matching the normalizer alone does not reproduce a leaderboard score.

Search-oriented Snowball English stemming is now implemented as a separate
experiment; see STEMMING.md for its frozen policy, development audit, results,
and potential stopword/acronym extensions. Its dependency is pinned above in
requirements-normalization.txt; the baseline scorer remains unchanged.
