#!/usr/bin/env python3
"""Recompute and pool pilot metrics across verified, available AMI metadata."""
import argparse
from bisect import bisect_right
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.compound_normalization import DEFAULT_RULES, canonicalize, load_rules
from scripts.domain_metric import weighted_distance
from scripts.score_predictions import score
from scripts.stem_normalization import stem_tokens

ROOT=Path(__file__).resolve().parents[1]
MODELS=['whisper-large-v3','whisper-large-v3-turbo','parakeet']
FIELDS=['meeting_type','meeting_series_id','meeting_id','speaker_id','annotation_role','duration_bin']
METRICS=['official_wer','stem_compound_wer','token_wer','stem_token_wer',
         'domain_wer','stem_domain_wer','custom_compound_wer','custom_token_wer']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def metadata_labels(row,boundaries):
    labels={field:row.get(field) or 'unannotated' for field in FIELDS if field!='duration_bin'}
    labels['duration_bin']=f'Q{bisect_right(boundaries,row["duration_seconds"])+1}'
    return labels


def pool(rows):
    """Pool numerator/denominator, including zero-error rows; never average WERs."""
    errors=sum(r['errors'] for r in rows)
    mass=sum(r['reference_mass'] for r in rows)
    return dict(errors=errors,reference_mass=mass,
                score_percent=100*errors/mass if mass>0 else None)


def ranking_label(scores):
    tiers=[]
    for model in sorted(scores,key=lambda m:(scores[m],m)):
        if tiers and math.isclose(scores[model],scores[tiers[-1][0]],rel_tol=0,abs_tol=1e-10):
            tiers[-1].append(model)
        else:
            tiers.append([model])
    return ' < '.join(' = '.join(tier) for tier in tiers)


def write_tables(result,path):
    lines=['# Pilot performance by metadata', '',
        'All scores are percentages pooled over clips within each group. L = Whisper large-v3; T = turbo; P = Parakeet v3.', '',
        'The official columns use upstream normalization and compound-aware alignment. The stem-weighted columns use stem normalization and weighted token alignment. These are separate policies; differences between those columns do not isolate one change.', '',
        'The CSV/JSON contain all eight metrics, edit-cost components and denominator masses. Groups overlap across fields. Subgroup results are exploratory, with four meeting series and recurring speakers; no significance claims.', '']
    for field,values in result['groups'].items():
        lines.extend(['## '+field,'',
            '| Value | Clips | Words | Minutes | Series | Speakers | Official L | Official T | Official P | Stem-weighted L | Stem-weighted T | Stem-weighted P |',
            '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |'])
        for label,g in values.items():
            cells=[label,str(g['examples']),str(g['reference_words']),f"{g['audio_seconds']/60:.2f}",str(g['series']),str(g['speakers'])]
            cells.extend(f"{g['models'][m][metric]['score_percent']:.2f}" for metric in ['official_wer','stem_domain_wer'] for m in MODELS)
            lines.append('| '+' | '.join(cells)+' |')
        lines.append('')
    path.write_text('\n'.join(lines)+'\n')


def validate_metadata(rows):
    path=ROOT/'data/corpusResources/meetings.xml'
    meetings={m.get('observation'):m for m in ET.parse(path).getroot()}
    missing=defaultdict(int)
    for r in rows:
        meeting=meetings[r['meeting_id']]
        speakers=[s for s in meeting if s.get('global_name')==r['speaker_id']
                  and int(s.get('channel','-1'))==int(r['headset_id_from_example_id'][1:])]
        if len(speakers)!=1:
            raise ValueError('Speaker/channel metadata mismatch: '+r['id'])
        speaker=speakers[0]
        checks=[(r['meeting_series_id'],r['meeting_id'][:-1]),
                (r['meeting_type'],meeting.get('type')),
                (r['annotation_role'],speaker.get('role')),
                (r['annotation_agent'],speaker.get('nxt_agent'))]
        if any(a!=b for a,b in checks):
            raise ValueError('Annotation mismatch: '+r['id'])
        if not math.isclose(r['duration_seconds'],r['frames']/r['sample_rate'],abs_tol=1e-9):
            raise ValueError('Duration/frame mismatch: '+r['id'])
        for field in FIELDS:
            if field!='duration_bin' and not r.get(field):
                missing[field]+=1
    return dict(checked_clips=len(rows),annotation_sha256=sha(path),missing_fields=dict(missing),
                checks='Meeting/series/type, global speaker ID, channel, annotation agent/role, and frame-derived duration; no new listening or waveform audit')


def metric_counts(ref,hyp,stem_ref,stem_hyp,rules,weights):
    custom_ref,custom_hyp=canonicalize(ref,rules),canonicalize(hyp,rules)
    result={}
    for name,rr,hh,merge in [
        ('official_wer',ref,hyp,True),('stem_compound_wer',stem_ref,stem_hyp,True),
        ('token_wer',ref,hyp,False),('stem_token_wer',stem_ref,stem_hyp,False),
        ('custom_compound_wer',custom_ref,custom_hyp,True),
        ('custom_token_wer',custom_ref,custom_hyp,False)]:
        a=edit_distance(rr,hh,merge_compounds=merge)
        result[name]=dict(errors=a['total'],reference_mass=a['ref_len'],
                          insertion_cost=a['ins'],deletion_cost=a['del'],substitution_cost=a['sub'])
    for name,rr,hh,w in [('domain_wer',ref,hyp,weights['upstream']),
                         ('stem_domain_wer',stem_ref,stem_hyp,weights['stemmed'])]:
        a=weighted_distance(rr,hh,w)
        result[name]=dict(errors=a['weighted_errors'],reference_mass=a['reference_weight'],
                          insertion_cost=a['insertion_cost'],deletion_cost=a['deletion_cost'],substitution_cost=a['substitution_cost'])
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    args=parser.parse_args()
    data=ROOT/'data/leaderboard/ami_cleaned'
    manifest_path=data/'manifest_pilot.jsonl'
    manifest=read(manifest_path)
    selection=json.loads((data/'pilot_selection.json').read_text())
    if sha(manifest_path)!=selection['pilot_manifest_sha256']:
        raise ValueError('Pilot manifest changed')
    if len({r['id'] for r in manifest})!=len(manifest):
        raise ValueError('Duplicate manifest IDs')
    bounds=selection['duration_boundaries_seconds']
    normalize=EnglishTextNormalizer()
    reliability=validate_metadata(manifest)
    stemming=json.loads((args.run_dir/'stemming_analysis.json').read_text())
    domain=json.loads((args.run_dir/'domain_metric_analysis.json').read_text())
    compounds=json.loads((args.run_dir/'compound_analysis.json').read_text())
    for prior in [stemming,domain,compounds]:
        if prior['manifest_sha256']!=sha(manifest_path):
            raise ValueError('Prior analysis uses different manifest')
    weights={}
    weight_hashes={}
    for variant in ['upstream','stemmed']:
        path=ROOT/'data/development/domain_metric'/(variant+'_weights.json')
        weight_hashes[variant]=sha(path)
        if weight_hashes[variant]!=domain['weight_sha256'][variant]:
            raise ValueError('Weights differ from prior analysis')
        weights[variant]=json.loads(path.read_text())['weights']
    if sha(DEFAULT_RULES)!=compounds['rules_sha256']:
        raise ValueError('Compound rules differ from prior analysis')
    rules=load_rules()
    grouped=defaultdict(list)
    for row in manifest:
        for field,label in metadata_labels(row,bounds).items():
            grouped[(field,label)].append(row)
    groups={field:{} for field in FIELDS}
    for (field,label),rows in sorted(grouped.items()):
        groups[field][label]=dict(examples=len(rows),audio_seconds=sum(r['duration_seconds'] for r in rows),
            reference_words=sum(r['normalized_reference_words'] for r in rows),
            meetings=len({r['meeting_id'] for r in rows}),series=len({r['meeting_series_id'] for r in rows}),
            speakers=len({r['speaker_id'] for r in rows}),models={})
    pooled={}
    prediction_hashes={}
    for model in MODELS:
        paths=list((args.run_dir/model/'results').glob('*.jsonl'))
        if len(paths)!=1:
            raise ValueError('Expected one prediction file: '+model)
        prediction_hashes[model]=sha(paths[0])
        for prior in [stemming,domain,compounds]:
            if prior['models'][model]['predictions_sha256']!=prediction_hashes[model]:
                raise ValueError('Predictions changed since prior analysis')
        predictions=read(paths[0])
        baseline=score(predictions,manifest)
        verified=json.loads((args.run_dir/model/'verified_score.json').read_text())
        for key in ['insertions','deletions','substitutions','reference_words']:
            if baseline[key]!=verified[key]:
                raise ValueError('Verified baseline mismatch')
        keyed={p['audio_filepath']:p for p in predictions}
        perclip={}
        audit=[]
        for row in manifest:
            hyp=normalize(keyed[row['id']]['pred_text']).split()
            ref=normalize(row['text']).split()
            if len(ref)!=row['normalized_reference_words']:
                raise ValueError('Reference normalization drift')
            metrics=metric_counts(ref,hyp,stem_tokens(ref),stem_tokens(hyp),rules,weights)
            perclip[row['id']]=metrics
            audit.append(dict(id=row['id'],labels=metadata_labels(row,bounds),metrics=metrics))
        pooled[model]={metric:pool([d[metric] for d in perclip.values()]) for metric in METRICS}
        expected={
            'official_wer':verified['wer_percent'],
            'stem_compound_wer':stemming['models'][model]['variants']['stemmed_compound_alignment']['wer_percent'],
            'token_wer':domain['models'][model]['variants']['upstream']['token_wer_percent'],
            'stem_token_wer':domain['models'][model]['variants']['stemmed']['token_wer_percent'],
            'domain_wer':domain['models'][model]['variants']['upstream']['weighted_wer_percent'],
            'stem_domain_wer':domain['models'][model]['variants']['stemmed']['weighted_wer_percent'],
            'custom_compound_wer':compounds['models'][model]['variants']['custom_compound_alignment']['wer_percent'],
            'custom_token_wer':compounds['models'][model]['variants']['custom_token_alignment']['wer_percent']}
        for metric,value in expected.items():
            if not math.isclose(pooled[model][metric]['score_percent'],value,abs_tol=1e-9):
                raise ValueError('Recomputed score differs: '+metric)
        for (field,label),rows in grouped.items():
            groups[field][label]['models'][model]={}
            for metric in METRICS:
                cells=[perclip[r['id']][metric] for r in rows]
                stats=pool(cells)
                for component in ['insertion_cost','deletion_cost','substitution_cost']:
                    stats[component]=sum(c[component] for c in cells)
                groups[field][label]['models'][model][metric]=stats
        for field in FIELDS:
            if sum(g['examples'] for g in groups[field].values())!=len(manifest):
                raise ValueError('Groups do not partition the sample')
            for metric in METRICS:
                for key in ['errors','reference_mass']:
                    actual=sum(g['models'][model][metric][key] for g in groups[field].values())
                    if not math.isclose(actual,pooled[model][metric][key],abs_tol=1e-8):
                        raise ValueError('Group totals do not reconcile')
        (args.run_dir/model/'characterization_clip_counts.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in audit))
    ranking_counts={}
    for field,values in groups.items():
        ranking_counts[field]={}
        for metric in METRICS:
            orders=defaultdict(list)
            for label,g in values.items():
                label_order=ranking_label({m:g['models'][m][metric]['score_percent'] for m in MODELS})
                orders[label_order].append(label)
            ranking_counts[field][metric]=dict(orders)
    result=dict(pooled=pooled,groups=groups,ranking_groups=ranking_counts,reliability=reliability,
        provenance=dict(manifest_sha256=sha(manifest_path),selection_sha256=sha(data/'pilot_selection.json'),
            prediction_sha256=prediction_hashes,weight_sha256=weight_hashes,compound_rules_sha256=sha(DEFAULT_RULES),
            source_sha256=sha(Path(__file__))),
        duration_bin_boundaries_seconds=bounds,
        duration_bin_policy='Full eligible split quartiles frozen before pilot inference; bisect_right (boundary enters next bin)',
        interpretation='Descriptive pooled pilot subgroup scores; no significance tests, no adjustment for multiple comparisons, no causal interpretation. Four series; repeated speakers. Roles and meeting type confounded with speaker/series. No new inferred metadata.')
    (args.run_dir/'performance_characterization.json').write_text(json.dumps(result,indent=2)+'\n')
    write_tables(result,args.run_dir/'performance_characterization.md')
    with (args.run_dir/'performance_characterization.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=['field','value','examples','reference_words','audio_seconds','series','speakers','model','metric','errors','reference_mass','score_percent','insertion_cost','deletion_cost','substitution_cost'])
        writer.writeheader()
        for field,values in groups.items():
            for label,g in values.items():
                common={k:g[k] for k in ['examples','reference_words','audio_seconds','series','speakers']}
                for model,scores in g['models'].items():
                    for metric,stats in scores.items():
                        writer.writerow(dict(field=field,value=label,**common,model=model,metric=metric,**stats))
    print('Verified and characterized',len(manifest),'clips;',sum(len(v) for v in groups.values()),'groups;',len(METRICS),'metrics')


if __name__=='__main__':
    main()
