#!/usr/bin/env python3
"""Verify prediction coverage and score with upstream English compound merging."""
import argparse
import json
import math
from pathlib import Path

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer

ROOT = Path(__file__).resolve().parents[1]


def score(predictions, manifest):
    expected = {r['id']: r for r in manifest}
    if len(expected) != len(manifest) or not expected:
        raise ValueError('Expected manifest must be nonempty and have unique IDs')
    normalize = EnglishTextNormalizer()
    seen, counts = set(), dict(ins=0, del_=0, sub=0, reference_words=0)
    seconds, elapsed = 0.0, 0.0
    for prediction in predictions:
        example_id = prediction['audio_filepath']
        if example_id not in expected or example_id in seen:
            raise ValueError(f'Unexpected or duplicate prediction ID: {example_id}')
        seen.add(example_id)
        reference = expected[example_id]
        if prediction['text'] != reference['text']:
            raise ValueError(f'Raw reference differs: {example_id}')
        duration = prediction['duration']
        time = prediction['time']
        if not all(isinstance(x, (float, int)) and math.isfinite(x) and x > 0 for x in [duration, time]):
            raise ValueError(f'Invalid duration/timing: {example_id}')
        if abs(duration - reference['duration_seconds']) > 1/16000 + 1e-8:
            raise ValueError(f'Audio duration differs: {example_id}')
        alignment = edit_distance(tuple(normalize(reference['text']).split()),
                                  tuple(normalize(prediction['pred_text']).split()),
                                  merge_compounds=True)
        counts['ins'] += alignment['ins']
        counts['del_'] += alignment['del']
        counts['sub'] += alignment['sub']
        counts['reference_words'] += alignment['ref_len']
        seconds += duration
        elapsed += time
    if seen != set(expected):
        raise ValueError(f'Missing predictions: {sorted(set(expected)-seen)}')
    return dict(
        examples=len(seen), insertions=counts['ins'], deletions=counts['del_'],
        substitutions=counts['sub'], reference_words=counts['reference_words'],
        wer_percent=100*(counts['ins']+counts['del_']+counts['sub'])/counts['reference_words'],
        audio_seconds=seconds, recorded_inference_seconds=elapsed, rtfx=seconds/elapsed,
        scoring='EnglishTextNormalizer + kaldialign merge_compounds=True; pooled edit counts',
        timing_note='Uses backend-reported timings, which differ by backend; excludes setup/export. Subset throughput is not a guaranteed full-dataset rate.',
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('predictions', type=Path)
    parser.add_argument('--manifest', type=Path,
                        default=ROOT/'data/leaderboard/ami_cleaned/manifest_smoke.jsonl')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    read = lambda path: [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    result = score(read(args.predictions), read(args.manifest))
    output = json.dumps(result, indent=2)+'\n'
    if args.output:
        args.output.write_text(output)
    print(output, end='')


if __name__ == '__main__':
    main()
