#!/usr/bin/env python3
"""Download the pinned leaderboard AMI-Cleaned shards and verify LFS SHA-256s."""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/leaderboard/ami_cleaned'
REPO = 'hf-audio/open-asr-leaderboard'
REVISION = 'de79e57adf9983993bcc72586d7313460825f5eb'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(
        f'https://huggingface.co/api/datasets/{REPO}/revision/{REVISION}', timeout=60
    ) as response:
        metadata = json.load(response)
    if metadata['sha'] != REVISION:
        raise ValueError('Resolved dataset revision differs from requested revision')
    (OUT / 'dataset_info.json').write_text(json.dumps(metadata, indent=2) + '\n')
    with urllib.request.urlopen(
        f'https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/README.md', timeout=60
    ) as response:
        (OUT / 'upstream_README.md').write_bytes(response.read())
    url = f'https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/ami_cleaned'
    with urllib.request.urlopen(url, timeout=60) as response:
        files = json.load(response)
    files = [f for f in files if f['path'].endswith('.parquet')]
    if len(files) != 3:
        raise ValueError(f'Expected three shards, found {len(files)}')
    records = []
    for entry in files:
        target = OUT / 'shards' / Path(entry['path']).name
        target.parent.mkdir(exist_ok=True)
        expected = entry['lfs']['oid']
        if not target.exists():
            partial = target.with_suffix('.parquet.partial')
            print(f'Downloading {entry["path"]}: {entry["size"]:,} bytes', flush=True)
            with urllib.request.urlopen(
                f'https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{entry["path"]}',
                timeout=120,
            ) as response, partial.open('wb') as f:
                shutil.copyfileobj(response, f, length=8 * 1024 * 1024)
            if partial.stat().st_size != entry['size'] or digest(partial) != expected:
                raise ValueError(f'Download verification failed: {partial}')
            partial.replace(target)
        actual = digest(target)
        if actual != expected or target.stat().st_size != entry['size']:
            raise ValueError(f'Checksum/size mismatch: {target}')
        records.append(dict(path=str(target.relative_to(ROOT)), size=target.stat().st_size,
                            sha256=actual, upstream_path=entry['path']))
        print(f'Verified {target.name}', flush=True)
    (OUT / 'download_provenance.json').write_text(json.dumps(
        dict(repo_id=REPO, revision=REVISION, files=records), indent=2) + '\n')


if __name__ == '__main__':
    main()
