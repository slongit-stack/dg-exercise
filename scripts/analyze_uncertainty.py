#!/usr/bin/env python3
"""Paired pilot uncertainty conditional on the sample design, plus series sensitivity."""
import argparse
from collections import defaultdict
import hashlib
from itertools import product
import json
from pathlib import Path

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['whisper-large-v3', 'whisper-large-v3-turbo', 'parakeet']
PAIRS = [(0, 2), (1, 2), (1, 0)]


def describe(rates, point):
    result = dict(models={}, paired_differences_pp={})
    for i, model in enumerate(MODELS):
        result['models'][model] = dict(point_wer_percent=float(point[i]),
            percentile_95_interval=np.percentile(rates[:, i], [2.5, 97.5]).tolist())
    for a, b in PAIRS:
        result['paired_differences_pp'][MODELS[a]+' minus '+MODELS[b]] = dict(
            point_difference_pp=float(point[a]-point[b]),
            percentile_95_interval_pp=np.percentile(rates[:, a]-rates[:, b], [2.5, 97.5]).tolist())
    return result


def stratified_draws(errors, words, strata, population, repetitions, seed):
    """Paired within-stratum draws; inverse-inclusion weights target the full split.

    The same clip indices are used for all models. Groups and stratum sample
    sizes stay fixed. This is a design-conditional approximation, not an IID
    model of the speech corpus or an interval over new speakers/meetings.
    """
    rng = np.random.default_rng(seed)
    totals = np.zeros((repetitions, errors.shape[1]))
    denominators = np.zeros(repetitions)
    point_errors = np.zeros(errors.shape[1])
    point_words = 0.0
    for key in sorted(strata):
        indices = np.asarray(strata[key])
        weight = population[key]/len(indices)
        draw = rng.integers(len(indices), size=(repetitions, len(indices)))
        totals += errors[indices][draw].sum(axis=1)*weight
        denominators += words[indices][draw].sum(axis=1)*weight
        point_errors += errors[indices].sum(axis=0)*weight
        point_words += words[indices].sum()*weight
    return 100*totals/denominators[:, None], 100*point_errors/point_words


def series_draws(errors, words, labels):
    """Enumerate every ordered whole-series bootstrap draw, including repeats."""
    unique = sorted(set(labels))
    group_errors = np.array([errors[np.asarray(labels)==key].sum(axis=0) for key in unique])
    group_words = np.array([words[np.asarray(labels)==key].sum() for key in unique])
    draws = np.array(list(product(range(len(unique)), repeat=len(unique))))
    return 100*group_errors[draws].sum(axis=1)/group_words[draws].sum(axis=1)[:, None]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--replicates', type=int, default=20000)
    parser.add_argument('--seed', type=int, default=20261114)
    args = parser.parse_args()
    if args.replicates < 1000:
        parser.error('Use at least 1000 bootstrap replicates')
    data = ROOT/'data/leaderboard/ami_cleaned'
    manifest_path = data/'manifest_pilot.jsonl'
    rows = [json.loads(s) for s in manifest_path.read_text().splitlines()]
    selection = json.loads((data/'pilot_selection.json').read_text())
    ids = [r['id'] for r in rows]
    if len(set(ids)) != len(rows):
        raise ValueError('Duplicate manifest IDs')
    normalize = EnglishTextNormalizer()
    refs = [tuple(normalize(r['text']).split()) for r in rows]
    words = np.array([len(ref) for ref in refs])
    errors = np.zeros((len(rows), len(MODELS)), dtype=np.int64)
    prediction_hashes = {}
    for col, model in enumerate(MODELS):
        paths = list((args.run_dir/model/'results').glob('*.jsonl'))
        if len(paths) != 1:
            raise ValueError(f'Expected one prediction file: {model}')
        predictions = [json.loads(s) for s in paths[0].read_text().splitlines()]
        keyed = {p['audio_filepath']: p for p in predictions}
        if len(keyed) != len(predictions) or set(keyed) != set(ids):
            raise ValueError(f'Prediction coverage mismatch: {model}')
        for i, row in enumerate(rows):
            prediction = keyed[row['id']]
            if prediction['text'] != row['text']:
                raise ValueError(f'Raw reference mismatch: {row["id"]}')
            alignment = edit_distance(refs[i], tuple(normalize(prediction['pred_text']).split()),
                                      merge_compounds=True)
            errors[i, col] = alignment['ins']+alignment['del']+alignment['sub']
        verified = json.loads((args.run_dir/model/'verified_score.json').read_text())
        if words.sum() != verified['reference_words'] or errors[:, col].sum() != sum(
            verified[k] for k in ['insertions', 'deletions', 'substitutions']):
            raise ValueError(f'Counts disagree with verified score: {model}')
        prediction_hashes[model] = hashlib.sha256(paths[0].read_bytes()).hexdigest()
    population = {(s['meeting'],s['duration_bin']):s['population'] for s in selection['strata']}
    strata = defaultdict(list)
    for i, row in enumerate(rows):
        key = (row['meeting_id'], int(np.searchsorted(selection['duration_boundaries_seconds'],
                                                    row['duration_seconds'], side='right')))
        strata[key].append(i)
    if set(strata) != set(population):
        raise ValueError('Unrepresented source stratum')
    labels = [r['meeting_series_id'] for r in rows]
    observed = 100*errors.sum(axis=0)/words.sum()
    draws, weighted_point = stratified_draws(errors, words, strata, population,
                                            args.replicates, args.seed)
    leave_one_out = {}
    for series in sorted(set(labels)):
        keep = np.asarray(labels) != series
        rates = 100*errors[keep].sum(axis=0)/words[keep].sum()
        leave_one_out[series] = dict(examples_retained=int(keep.sum()),
                                    wer_percent=dict(zip(MODELS,rates.tolist())),
                                    paired_differences_pp={MODELS[a]+' minus '+MODELS[b]:float(rates[a]-rates[b])
                                                           for a,b in PAIRS})
    result = dict(seed=args.seed, replicates=args.replicates, examples=len(rows),
        reference_words=int(words.sum()), observed_unweighted_wer_percent=dict(zip(MODELS,observed.tolist())),
        stratified_clip_bootstrap=dict(
            method='Paired resampling within each fixed meeting-duration stratum; original n_h draws with replacement, full-split weights N_h/n_h; percentile intervals; no finite-population correction.',
            interpretation='Approximate clip-selection uncertainty conditional on the represented benchmark meetings/speakers and sampling design; not new-meeting or new-speaker uncertainty.',
            results=describe(draws, weighted_point)),
        whole_series_sensitivity=dict(
            method='Exact enumeration of all 4^4=256 ordered bootstrap samples of four whole meeting series; identical resampling for every model; repeated meetings/speakers remain together.',
            interpretation='Only four clusters. Descriptive sensitivity ranges, not reliable nominal 95% coverage or a significance test. Treat narrower clip-level intervals alongside this dependence check.',
            results=describe(series_draws(errors,words,labels), observed)),
        leave_one_series_out=leave_one_out,
        provenance=dict(manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
                        prediction_sha256=prediction_hashes,
                        scoring='Upstream EnglishTextNormalizer and kaldialign merge_compounds=True'),
        limitations=[
            'This does not establish a universal sufficient sample size or bound normalization effects not yet measured.',
            'Weighted full-split estimates differ slightly from the reported unweighted pilot scores.',
            'No bootstrap probability is interpreted as the probability that one model is better.',
            'No uncertainty is estimated for published leaderboard figures, whose exact pipeline revisions remain unconfirmed.',
        ])
    (args.run_dir/'uncertainty.json').write_text(json.dumps(result,indent=2)+'\n')
    with (args.run_dir/'utterance_error_counts.jsonl').open('w') as f:
        for i,row in enumerate(rows):
            f.write(json.dumps(dict(id=row['id'],meeting_id=row['meeting_id'],
                meeting_series_id=row['meeting_series_id'],speaker_id=row['speaker_id'],
                reference_words=int(words[i]),errors=dict(zip(MODELS,errors[i].tolist()))))+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
