#!/usr/bin/env python3
"""Audit development conflations, then rescore the frozen pilot without inference."""
import argparse
from collections import Counter, defaultdict
from importlib.metadata import version
import hashlib
import json
from pathlib import Path

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer

from score_predictions import score
from stem_normalization import stem_tokens, stem_token

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['whisper-large-v3', 'whisper-large-v3-turbo', 'parakeet']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def counts(ref, hyp, merge):
    a = edit_distance(ref,hyp,merge_compounds=merge)
    return dict(insertions=a['ins'],deletions=a['del'],substitutions=a['sub'],reference_words=a['ref_len'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    args = parser.parse_args()
    policy = ROOT/'configs/normalization/stemming_v1.json'
    config = json.loads(policy.read_text())
    if config['package_version'] != version('snowballstemmer'):
        raise ValueError('Stemmer version differs from policy')
    development = ROOT/'data/development/compounds/transcripts.jsonl'
    provenance = json.loads((development.parent/'provenance.json').read_text())
    if sha(development) != provenance['transcript_sha256']:
        raise ValueError('Development transcript hash mismatch')
    vocabulary = Counter()
    for line in development.read_text().splitlines():
        vocabulary.update(json.loads(line)['normalized_text'].split())
    groups = defaultdict(list)
    for token,n in sorted(vocabulary.items()):
        groups[stem_token(token)].append(dict(token=token,count=n))
    collisions = {s:items for s,items in sorted(groups.items()) if len(items)>1}
    audit = dict(policy=config,policy_sha256=sha(policy),development_sha256=sha(development),
        vocabulary_size=len(vocabulary),changed_token_occurrences=sum(n for t,n in vocabulary.items() if stem_token(t)!=t),
        normalized_token_occurrences=sum(vocabulary.values()),collision_groups=len(collisions),groups=collisions)
    (development.parent/'stemming_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    normalize = EnglishTextNormalizer()
    manifest_path = ROOT/'data/leaderboard/ami_cleaned/manifest_pilot.jsonl'
    manifest = [json.loads(s) for s in manifest_path.read_text().splitlines()]
    result = dict(policy=config,policy_sha256=sha(policy),manifest_sha256=sha(manifest_path),
        development_audit_sha256=sha(development.parent/'stemming_audit.json'),
        source_sha256={p.name:sha(p) for p in [Path(__file__),ROOT/'scripts/stem_normalization.py']},
        packages={name:version(name) for name in ['snowballstemmer','kaldialign','regex']},models={})
    for model in MODELS:
        paths = list((args.run_dir/model/'results').glob('*.jsonl'))
        if len(paths)!=1:
            raise ValueError(f'Expected one prediction file: {model}')
        predictions = [json.loads(s) for s in paths[0].read_text().splitlines()]
        baseline = score(predictions,manifest)
        verified = json.loads((args.run_dir/model/'verified_score.json').read_text())
        for key in ['insertions','deletions','substitutions','reference_words']:
            if baseline[key]!=verified[key]:
                raise ValueError(f'Baseline mismatch: {model} {key}')
        totals = {}
        records = []
        for p in predictions:
            ref,hyp = normalize(p['text']).split(),normalize(p['pred_text']).split()
            sr,sh = stem_tokens(ref),stem_tokens(hyp)
            row = dict(id=p['audio_filepath'],reference_before=ref,reference_after=sr,
                       prediction_before=hyp,prediction_after=sh,scores={})
            for label,rr,hh in [('upstream',ref,hyp),('stemmed',sr,sh)]:
                for merge in [False,True]:
                    name=label+('_compound_alignment' if merge else '_token_alignment')
                    c=counts(rr,hh,merge)
                    row['scores'][name]=c
                    if name not in totals:
                        totals[name]=Counter()
                    totals[name].update(c)
            records.append(row)
        variants={}
        for name,c in totals.items():
            variants[name]=dict(c,wer_percent=100*(c['insertions']+c['deletions']+c['substitutions'])/c['reference_words'])
        result['models'][model]=dict(predictions_sha256=sha(paths[0]),variants=variants,
            changed_reference_clips=sum(r['reference_before']!=r['reference_after'] for r in records),
            changed_prediction_clips=sum(r['prediction_before']!=r['prediction_after'] for r in records))
        (args.run_dir/model/'stemming_clip_audit.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (args.run_dir/'stemming_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
