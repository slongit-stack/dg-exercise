#!/usr/bin/env python3
"""Export exact manifest examples as a local HF dataset for upstream runners."""
import argparse
import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/leaderboard/ami_cleaned'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=SOURCE/'manifest_smoke.jsonl')
    parser.add_argument('--output', type=Path, default=SOURCE/'hf_smoke')
    parser.add_argument('--purpose', default='Inference smoke test; not a representative performance estimate.')
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.manifest.read_text().splitlines() if line.strip()]
    ids = [r['id'] for r in rows]
    if not rows or len(set(ids)) != len(ids):
        raise ValueError('Manifest must contain at least one example and unique IDs')
    if len({r['dataset_revision'] for r in rows}) != 1:
        raise ValueError('Cannot mix source revisions')
    selected, schema = {}, None
    for shard in sorted({r['source_shard'] for r in rows}):
        wanted = {r['source_row']: r for r in rows if r['source_shard'] == shard}
        source = SOURCE/'shards'/Path(shard).name
        parquet = pq.ParquetFile(source)
        schema = parquet.schema_arrow
        offset = 0
        for batch in parquet.iter_batches(batch_size=16):
            positions = [index-offset for index in wanted if offset <= index < offset+len(batch)]
            if positions:
                for item in batch.take(pa.array(positions)).to_pylist():
                    selected[item['id']] = item
            offset += len(batch)
    if set(selected) != set(ids):
        raise ValueError('Manifest IDs do not match the referenced source rows')
    for row in rows:
        item = selected[row['id']]
        if item['text'] != row['text']:
            raise ValueError(f'Reference mismatch: {row["id"]}')
        if hashlib.sha256(item['audio']['bytes']).hexdigest() != row['audio_sha256']:
            raise ValueError(f'Audio mismatch: {row["id"]}')
    table = pa.Table.from_pylist([selected[i] for i in ids], schema=schema)
    destination = args.output/'ami_cleaned'/'test-00000-of-00001.parquet'
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix('.parquet.tmp')
    pq.write_table(table, temporary, compression='zstd')
    temporary.replace(destination)
    (args.output/'README.md').write_text(
        '---\nconfigs:\n- config_name: ami_cleaned\n  data_files:\n'
        '  - split: test\n    path: ami_cleaned/test-*.parquet\n---\n\n'
        'Local evaluation subset of hf-audio/open-asr-leaderboard (AMI-Cleaned).\n'
        'Original audio bytes and raw references are preserved. See provenance.json.\n'
    )
    (args.output/'provenance.json').write_text(json.dumps(dict(
        source_repo='hf-audio/open-asr-leaderboard',
        source_revision=rows[0]['dataset_revision'],
        source_manifest_sha256=hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        examples=len(rows), ids=ids,
        parquet_sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
        purpose=args.purpose,
    ), indent=2)+'\n')
    print(f'Exported {len(rows)} examples to {args.output}')


if __name__ == '__main__':
    main()
