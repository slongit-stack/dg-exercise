#!/usr/bin/env python3
"""Evaluate frozen development-derived weighted WER on saved pilot predictions."""
from collections import Counter
import hashlib
import json
import argparse
from pathlib import Path

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer

from domain_metric import weighted_distance
from score_predictions import score
from stem_normalization import stem_tokens

ROOT=Path(__file__).resolve().parents[1]
MODELS=['whisper-large-v3','whisper-large-v3-turbo','parakeet']


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    args=parser.parse_args()
    manifest_path=ROOT/'data/leaderboard/ami_cleaned/manifest_pilot.jsonl'
    manifest=[json.loads(s) for s in manifest_path.read_text().splitlines()]
    policy_path=ROOT/'configs/domain_metric_v1.json'
    fits={}
    fit_hashes={}
    development=ROOT/'data/development/compounds/transcripts.jsonl'
    for variant in ['upstream','stemmed']:
        path=ROOT/'data/development/domain_metric'/(variant+'_weights.json')
        fit=json.loads(path.read_text())
        if fit['policy_sha256']!=sha(policy_path) or fit['development_sha256']!=sha(development):
            raise ValueError('Weights do not match frozen policy/development input')
        if fit['background_sha256']!=sha(ROOT/'data/background/brown/brown.zip'):
            raise ValueError('Background input changed since fitting')
        if fit['source_sha256']['domain_metric.py']!=sha(ROOT/'scripts/domain_metric.py'):
            raise ValueError('Metric implementation changed since fitting')
        if any(not 1<w<=4 for w in fit['weights'].values()):
            raise ValueError('Boosted weights outside declared range')
        fits[variant]=fit
        fit_hashes[variant]=sha(path)
    normalize=EnglishTextNormalizer()
    vocabulary=set()
    for line in development.read_text().splitlines():
        vocabulary.update(json.loads(line)['normalized_text'].split())
    result=dict(version='domain-contrast-v1',policy=json.loads(policy_path.read_text()),
                policy_sha256=sha(policy_path),manifest_sha256=sha(manifest_path),weight_sha256=fit_hashes,
                scoring_revision=json.loads((ROOT/'configs/ami_cleaned.json').read_text())['scoring_repository_revision'],
                source_sha256={p.name:sha(p) for p in [Path(__file__),ROOT/'scripts/domain_metric.py',ROOT/'scripts/stem_normalization.py']},models={})
    for model in MODELS:
        paths=list((args.run_dir/model/'results').glob('*.jsonl'))
        if len(paths)!=1:
            raise ValueError(f'Expected one prediction file for {model}')
        predictions=[json.loads(s) for s in paths[0].read_text().splitlines()]
        checked=score(predictions,manifest)
        verified=json.loads((args.run_dir/model/'verified_score.json').read_text())
        for key in ['insertions','deletions','substitutions','reference_words']:
            if checked[key]!=verified[key]:
                raise ValueError(f'Baseline mismatch: {model} {key}')
        variants={}
        audits={p['audio_filepath']:dict(id=p['audio_filepath'],variants={}) for p in predictions}
        for variant,fit in fits.items():
            weights=fit['weights']
            transform=stem_tokens if variant=='stemmed' else list
            dev_vocab=set(transform(sorted(vocabulary)))
            totals=Counter()
            contributions=Counter()
            for p in predictions:
                ref=transform(normalize(p['text']).split())
                hyp=transform(normalize(p['pred_text']).split())
                weighted=weighted_distance(ref,hyp,weights)
                ordinary=edit_distance(ref,hyp,merge_compounds=False)
                row=dict(**weighted,token_errors=ordinary['total'],reference_words=len(ref),
                         reference_boosted_tokens=sum(t in weights for t in ref),
                         prediction_boosted_tokens=sum(t in weights for t in hyp),
                         reference_oov_tokens=sum(t not in dev_vocab for t in ref),
                         prediction_oov_tokens=sum(t not in dev_vocab for t in hyp),
                         hypothesis_words=len(hyp))
                totals.update(row)
                contributions.update(t for t in ref if t in weights)
                audits[p['audio_filepath']]['variants'][variant]=row
            variants[variant]=dict(totals,
                weighted_wer_percent=100*totals['weighted_errors']/totals['reference_weight'],
                token_wer_percent=100*totals['token_errors']/totals['reference_words'],
                boosted_reference_terms=[dict(token=t,count=n,weight=weights[t]) for t,n in contributions.most_common(30)])
        result['models'][model]=dict(predictions_sha256=sha(paths[0]),official_baseline_wer_percent=checked['wer_percent'],variants=variants)
        (args.run_dir/model/'domain_metric_clip_counts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in audits.values()))
    (args.run_dir/'domain_metric_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
