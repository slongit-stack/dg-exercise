By **token alignment**, I mean the process of lining up the reference words and the model’s predicted words to determine which words match and which are substitutions, deletions, or insertions.

After normalization, we split each transcript at spaces. Each resulting word is one token. For example:

```text
Reference:  the  buttons  are  red
Prediction: the  button   —   red
```

Under ordinary WER, this alignment contains:

- One substitution: `buttons → button`
- One deletion: `are`
- Two matches: `the`, `red`

That gives **2 errors / 4 reference tokens = 50% WER**. The algorithm searches for the alignment with the lowest total edit cost.

**Normalization happens before alignment.** With stemming enabled, `buttons` and `button` both become `button`, so that substitution disappears. The deletion remains, giving **25% Stem WER**.

The distinction from our leaderboard reproduction concerns **compound merging**:

```text
Reference:  the  tool  bar
Prediction: the  toolbar
```

Ordinary token alignment treats `tool`, `bar`, and `toolbar` as different tokens. It counts one substitution and one deletion: **2 errors**.

The leaderboard’s compound-aware alignment can recognize that joining `tool` and `bar` produces `toolbar`, and count **zero errors**. That forgiveness happens while comparing the transcripts; it does not require an explicit compound-normalization rule.

In the revised report, **all four scores disable compound merging**:

| Score | How alignment chooses its lowest-cost path |
|---|---|
| WER / Stem WER | Each insertion, deletion, or substitution costs 1 |
| Domain WER / Stem + domain WER | Costs depend on the affected words’ weights |

For weighted alignment, deleting a word costs its reference weight, inserting a word costs its predicted weight, and substituting costs the larger of the two weights. Those costs can change which alignment is optimal.

So “consistent token alignment” means that all four compare individual space-separated tokens, without special compound forgiveness. **The weighted scores still use different edit costs.** This lets us compare stemming and weighting without also switching compound handling.
