#!/usr/bin/env python3
"""Build a deterministic allowlisted bundle of public text-only replay inputs."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[1]
RUN='results/pilot/20261114T195638016516Z'


def main():
    selected=[
        'data/leaderboard/ami_cleaned/manifest_pilot.jsonl',
        'data/leaderboard/ami_cleaned/pilot_selection.json',
        'data/corpusResources/meetings.xml',
        'data/LICENCE.txt','data/CCBY4.0.txt','data/00README_MANUAL.txt',
        'data/background/brown/brown.zip','data/background/brown/README',
        'data/background/brown/provenance.json',
    ]
    for directory in ['data/development/compounds','data/development/domain_metric']:
        selected.extend(str(p.relative_to(ROOT)) for p in (ROOT/directory).iterdir() if p.is_file())
    selected.extend(str(p.relative_to(ROOT)) for p in (ROOT/RUN).rglob('*')
                    if p.is_file() and p.suffix in {'.json','.jsonl','.csv','.md'})
    entries=[]
    out=ROOT/'artifacts'
    out.mkdir(exist_ok=True)
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w') as archive:
        for relative in sorted(set(selected)):
            path=ROOT/relative
            if path.is_symlink():
                raise ValueError('Symlinks are not valid replay inputs')
            payload=path.read_bytes()
            entries.append(dict(path=relative,bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest()))
            info=tarfile.TarInfo(relative)
            info.size=len(payload)
            info.mode=0o644
            archive.addfile(info,io.BytesIO(payload))
    target=out/'pilot_replay_inputs.tar.gz'
    with target.open('wb') as f:
        with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as zipped:
            zipped.write(buffer.getvalue())
    manifest=dict(format_version=1,archive=target.name,
        archive_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        purpose='Public text-only CPU replay inputs and saved results; no waveforms, model weights, credentials, or application settings.',
        files=entries)
    (out/'pilot_replay_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'{len(entries)} files; {target.stat().st_size/1024/1024:.2f} MiB compressed')


if __name__=='__main__':
    main()
