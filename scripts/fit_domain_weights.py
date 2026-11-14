#!/usr/bin/env python3
"""Fit and freeze development-only domain contrast weights for two text policies."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

from normalizer import EnglishTextNormalizer
from domain_metric import fit_weights
from stem_normalization import stem_tokens

ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    data=ROOT/'data/development/compounds'
    path=data/'transcripts.jsonl'
    provenance=json.loads((data/'provenance.json').read_text())
    if sha(path)!=provenance['transcript_sha256']:
        raise ValueError('Development transcript hash mismatch')
    docs=[json.loads(line) for line in path.read_text().splitlines()]
    if {d['meeting_id'] for d in docs}!=set(provenance['meetings']):
        raise ValueError('Development meeting coverage mismatch')
    archive=ROOT/'data/background/brown/brown.zip'
    normalize=EnglishTextNormalizer()
    background=[]
    with ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            if re.fullmatch(r'brown/c[a-z]\d\d',name):
                text=' '.join(w.rsplit('/',1)[0] for w in z.read(name).decode('ascii').split())
                background.append(normalize(text).split())
        (archive.parent/'README').write_bytes(z.read('brown/README'))
    if len(background)!=500:
        raise ValueError('Expected 500 Brown documents')
    out=ROOT/'data/development/domain_metric'
    out.mkdir(parents=True,exist_ok=True)
    policy=json.loads((ROOT/'configs/domain_metric_v1.json').read_text())
    for variant in ['upstream','stemmed']:
        transform=stem_tokens if variant=='stemmed' else list
        meetings=defaultdict(list)
        for d in docs:
            meetings[d['meeting_id']].extend(transform(d['normalized_text'].split()))
        series={meeting:meeting[:-1] for meeting in meetings}
        exclusions=set(transform(policy['boost_exclusions']))
        fit=fit_weights(meetings,[transform(t) for t in background],series,exclusions)
        result=dict(version='domain-contrast-v1',normalization=variant,**fit,
                    development_sha256=sha(path),development_provenance_sha256=sha(data/'provenance.json'),
                    background_sha256=sha(archive),background_url='https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/brown.zip',
                    source_sha256={p.name:sha(p) for p in [Path(__file__),ROOT/'scripts/domain_metric.py']},
                    policy_sha256=sha(ROOT/'configs/domain_metric_v1.json'))
        (out/(variant+'_weights.json')).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        top=sorted(fit['weights'],key=lambda t:(-fit['weights'][t],t))[:25]
        print(variant, 'boosted terms',len(fit['weights']),[(t,round(fit['weights'][t],3)) for t in top])


if __name__=='__main__':
    main()
