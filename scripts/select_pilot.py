#!/usr/bin/env python3
"""Freeze a proportional, meeting/duration-stratified AMI-Cleaned pilot."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/leaderboard/ami_cleaned'
SIZE = 800
SEED = 'normExp-pilot-v1'


def main():
    source = DATA/'manifest_test.jsonl'
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    boundaries = np.quantile([r['duration_seconds'] for r in rows], [.25, .5, .75])
    strata = defaultdict(list)
    for row in rows:
        bucket = int(np.searchsorted(boundaries, row['duration_seconds'], side='right'))
        strata[(row['meeting_id'], bucket)].append(row)
    # Largest-remainder allocation keeps total size fixed and represents each
    # stratum in proportion to its population, up to integer rounding.
    quotas = {k: SIZE*len(v)//len(rows) for k,v in strata.items()}
    remaining = SIZE-sum(quotas.values())
    order = sorted(strata, key=lambda k: (-(SIZE*len(strata[k]) % len(rows)), k))
    for key in order[:remaining]:
        quotas[key] += 1
    selected = set()
    for key, candidates in strata.items():
        ranked = sorted(candidates, key=lambda r: hashlib.sha256(
            (SEED+':'+r['id']).encode()).hexdigest())
        selected.update(r['id'] for r in ranked[:quotas[key]])
    pilot = [r for r in rows if r['id'] in selected]
    assert len(pilot) == SIZE
    assert {r['speaker_id'] for r in pilot} == {r['speaker_id'] for r in rows}
    assert {r['meeting_id'] for r in pilot} == {r['meeting_id'] for r in rows}
    manifest = ''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in pilot)
    target = DATA/'manifest_pilot.jsonl'
    if target.exists() and target.read_text() != manifest:
        raise ValueError('Existing pilot differs; use a new version rather than changing it')
    target.write_text(manifest)
    smoke = {json.loads(line)['id'] for line in (DATA/'manifest_smoke.jsonl').read_text().splitlines()}
    def describe(items):
        durations = [r['duration_seconds'] for r in items]
        return dict(examples=len(items), audio_seconds=sum(durations),
                    duration_percentiles_seconds=np.percentile(durations,[0,25,50,75,95,100]).tolist(),
                    reference_words=sum(r['normalized_reference_words'] for r in items),
                    meetings=dict(sorted(Counter(r['meeting_id'] for r in items).items())),
                    speakers=dict(sorted(Counter(r['speaker_id'] for r in items).items())))
    report = dict(seed=SEED, source_manifest_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  pilot_manifest_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  selection='Proportional meeting x global duration-quartile strata; largest-remainder allocation; SHA-256 ranking within strata; original row order retained.',
                  duration_boundaries_seconds=boundaries.tolist(),
                  strata=[dict(meeting=k[0],duration_bin=k[1],population=len(strata[k]),selected=quotas[k])
                          for k in sorted(strata)],
                  smoke_overlap_ids=sorted(selected & smoke), pilot=describe(pilot), full=describe(rows),
                  limitations=['Only four meeting series; repeated speakers limit independence.',
                              'Pilot is evaluation data: do not fit normalization or term weights on it.',
                              'Integer allocation gives slightly unequal inclusion probabilities; pilot WER is descriptive, not an unbiased full-split estimate.'])
    (DATA/'pilot_selection.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['pilot'],indent=2))


if __name__ == '__main__':
    main()
