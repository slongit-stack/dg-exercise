#!/usr/bin/env python3
"""Summarize verified pilot outputs, subgroup counts, and runtime projections."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

from kaldialign import edit_distance
from normalizer import EnglishTextNormalizer

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'data/leaderboard/ami_cleaned'


def read(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    args = parser.parse_args()
    selection = json.loads((DATA/'pilot_selection.json').read_text())
    manifest = {r['id']: r for r in read(DATA/'manifest_pilot.jsonl')}
    config = json.loads((args.run_dir/'configuration.json').read_text())
    published = {r['model_id']: r['dataset_wer_percent']['ami_cleaned']
                 for r in json.loads((ROOT/'configs/leaderboard_reference.json').read_text())['models']}
    normalize = EnglishTextNormalizer()
    summary = dict(run_dir=str(args.run_dir), configuration=config,
                   pilot_selection=selection, models={}, limitations=[
                       'Preliminary pilot accuracy, not full-split leaderboard reproduction.',
                       'Only four meeting series; no claim of statistical significance.',
                       'Inference projections assume the same batch size, backend, and hardware; exclude data preparation, loading, warmup and scoring.',
                       'Duration/example/word scaling are sensitivity checks, not confidence bounds.',
                       'GPU memory samples are device-wide at one-second intervals; actual peaks can be missed.',
                   ])
    for key in config['selected_models']:
        work = args.run_dir/key
        score = json.loads((work/'verified_score.json').read_text())
        status = json.loads((work/'status.json').read_text())
        if status['returncode'] != 0 or score['examples'] != len(manifest):
            raise ValueError(f'Incomplete run: {key}')
        groups = defaultdict(lambda: dict(ins=0, dele=0, sub=0, words=0, examples=0))
        predictions = list((work/'results').glob('*.jsonl'))
        if len(predictions) != 1:
            raise ValueError(f'Expected one prediction manifest: {key}')
        for prediction in read(predictions[0]):
            row = manifest[prediction['audio_filepath']]
            counts = edit_distance(tuple(normalize(row['text']).split()),
                                   tuple(normalize(prediction['pred_text']).split()), merge_compounds=True)
            for field in ['meeting_id', 'meeting_series_id', 'speaker_id']:
                group = groups[(field, row[field])]
                for target, source in [('ins','ins'),('dele','del'),('sub','sub'),('words','ref_len')]:
                    group[target] += counts[source]
                group['examples'] += 1
        subgroup_scores = {}
        for (field, group_id), counts in sorted(groups.items()):
            subgroup_scores.setdefault(field, {})[group_id] = dict(
                counts, wer_percent=100*(counts['ins']+counts['dele']+counts['sub'])/counts['words'])
        for field in subgroup_scores:
            groups_for_field = subgroup_scores[field].values()
            if sum(g['words'] for g in groups_for_field) != score['reference_words']:
                raise ValueError(f'Subgroup reference counts disagree: {key}/{field}')
            for group_count, score_count in [('ins','insertions'),('dele','deletions'),('sub','substitutions')]:
                if sum(g[group_count] for g in subgroup_scores[field].values()) != score[score_count]:
                    raise ValueError(f'Subgroup errors disagree: {key}/{field}')
        telemetry = []
        with (work/'gpu_samples.csv').open() as f:
            for row in csv.reader(f):
                if len(row) == 4:
                    try:
                        telemetry.append([float(x.strip()) for x in row[1:]])
                    except ValueError:
                        pass
        seconds = score['recorded_inference_seconds']
        estimates = {metric: seconds*selection['full'][metric]/selection['pilot'][metric]
                     for metric in ['audio_seconds', 'examples', 'reference_words']}
        summary['models'][key] = dict(
            score=score, run_status=status,
            published_full_ami_cleaned_wer_percent=published[config['models'][key]['model_id']],
            projected_full_inference_seconds_by_scaling=estimates,
            sampled_device_peak_memory_mib=max((r[0] for r in telemetry), default=None),
            sampled_device_total_memory_mib=max((r[1] for r in telemetry), default=None),
            gpu_samples=len(telemetry), subgroups=subgroup_scores,
        )
        print(f'{key}: WER={score["wer_percent"]:.2f}%, inference={seconds:.2f}s, '
              f'pilot wall={status["wall_seconds_including_setup"]:.1f}s, '
              f'full inference projection={estimates["audio_seconds"]/60:.2f} min')
    (args.run_dir/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')


if __name__ == '__main__':
    main()
