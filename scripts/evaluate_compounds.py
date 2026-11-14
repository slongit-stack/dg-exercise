#!/usr/bin/env python3
"""Rescore saved pilot predictions in a normalization × alignment factorial audit."""
import argparse
import hashlib
import json
from pathlib import Path

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer

from compound_normalization import DEFAULT_RULES, canonicalize, load_rules
from score_predictions import score

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['whisper-large-v3', 'whisper-large-v3-turbo', 'parakeet']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--rules', type=Path, default=DEFAULT_RULES)
    args = parser.parse_args()
    rules = load_rules(args.rules)
    config = json.loads(args.rules.read_text())
    candidate_path = ROOT/'data/development/compounds/candidates.json'
    if sha(candidate_path) != config['candidates_sha256']:
        raise ValueError('Development candidates changed since review')
    if sha(candidate_path.parent/'provenance.json') != config['development_provenance_sha256']:
        raise ValueError('Development provenance changed since review')
    manifest_path = ROOT/'data/leaderboard/ami_cleaned/manifest_pilot.jsonl'
    manifest = [json.loads(s) for s in manifest_path.read_text().splitlines()]
    normalize = EnglishTextNormalizer()
    result = dict(rules_version=config['version'], rules_sha256=sha(args.rules),
                  manifest_sha256=sha(manifest_path), rules_count=len(rules), models={})
    for model in MODELS:
        paths = list((args.run_dir/model/'results').glob('*.jsonl'))
        if len(paths) != 1:
            raise ValueError(f'Expected one prediction file for {model}')
        predictions = [json.loads(s) for s in paths[0].read_text().splitlines()]
        checked = score(predictions, manifest)
        verified = json.loads((args.run_dir/model/'verified_score.json').read_text())
        for key in ['insertions','deletions','substitutions','reference_words']:
            if checked[key] != verified[key]:
                raise ValueError(f'Baseline counts changed: {model} {key}')
        variants = {}
        for custom in [False, True]:
            for merge in [False, True]:
                counts = dict(ins=0, sub=0, del_=0, reference_words=0)
                changed_ref = changed_hyp = 0
                affected = []
                for p in predictions:
                    ref = normalize(p['text']).split()
                    hyp = normalize(p['pred_text']).split()
                    nr, nh = canonicalize(ref,rules), canonicalize(hyp,rules)
                    changed_ref += nr != ref
                    changed_hyp += nh != hyp
                    if custom and (nr != ref or nh != hyp):
                        affected.append(dict(id=p['audio_filepath'], reference_before=ref, reference_after=nr,
                                             prediction_before=hyp, prediction_after=nh))
                    a = edit_distance(nr if custom else ref, nh if custom else hyp, merge_compounds=merge)
                    counts['ins'] += a['ins']
                    counts['del_'] += a['del']
                    counts['sub'] += a['sub']
                    counts['reference_words'] += a['ref_len']
                key = ('custom' if custom else 'upstream')+('_compound_alignment' if merge else '_token_alignment')
                variants[key] = dict(**counts, wer_percent=100*(counts['ins']+counts['del_']+counts['sub'])/counts['reference_words'],
                    changed_reference_clips=changed_ref if custom else 0, changed_prediction_clips=changed_hyp if custom else 0)
                if custom and not merge:
                    (args.run_dir/model/'compound_changed_clips.json').write_text(json.dumps(affected,indent=2)+'\n')
        result['models'][model] = dict(predictions_sha256=sha(paths[0]), variants=variants)
    (args.run_dir/'compound_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
