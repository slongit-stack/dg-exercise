#!/usr/bin/env python3
"""Render the report's four-score view from the existing characterization JSON."""
import argparse
import csv
import json
from pathlib import Path

METRICS=[('token_wer','WER'),('stem_token_wer','Stem WER'),
         ('domain_wer','Domain WER'),('stem_domain_wer','Stem + domain WER')]
MODELS=['whisper-large-v3','whisper-large-v3-turbo','parakeet']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    args=parser.parse_args()
    data=json.loads((args.run_dir/'performance_characterization.json').read_text())
    lines=['# Performance by metadata: four-score view','',
           'All scores are percentages. Each uses Hugging Face English normalization and token-level alignment. L = Whisper large-v3; T = turbo; P = Parakeet v3. Scores pool edit costs and reference mass within each group.','']
    for field,groups in data['groups'].items():
        lines.extend(['## '+field,''])
        for metric,label in METRICS:
            lines.extend(['### '+label,'',
                '| Group | Clips | Words | Minutes | Series | Speakers | L | T | P |',
                '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |'])
            for name,g in groups.items():
                cells=[name,str(g['examples']),str(g['reference_words']),f"{g['audio_seconds']/60:.2f}",str(g['series']),str(g['speakers'])]
                cells.extend(f"{g['models'][m][metric]['score_percent']:.2f}%" for m in MODELS)
                lines.append('| '+' | '.join(cells)+' |')
            lines.append('')
    (args.run_dir/'performance_four_metrics.md').write_text('\n'.join(lines)+'\n')
    with (args.run_dir/'performance_characterization.csv').open() as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames
        rows=[r for r in reader if r['metric'] in dict(METRICS)]
    with (args.run_dir/'performance_four_metrics.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f'Rendered four-score tables and {len(rows)} CSV rows')


if __name__=='__main__':
    main()
