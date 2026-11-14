#!/usr/bin/env python3
"""Project entry point: inspect/restore the replay bundle or plan/run CPU replay."""
import argparse
from datetime import datetime,timezone
import hashlib
import io
import json
import os
from pathlib import Path,PurePosixPath
import shlex
import shutil
import subprocess
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[1]
SAVED=ROOT/'results/pilot/20261114T195638016516Z'
UPSTREAM_REVISION='c21a412f2dd7cbe3af658d69fbf3d0dd536a264e'
STAGES=['summarize_pilot','analyze_uncertainty','evaluate_compounds','evaluate_stemming',
        'evaluate_domain_metric','characterize_performance','render_four_metric_tables']


def bundle_entries():
    manifest=json.loads((ROOT/'artifacts/pilot_replay_manifest.json').read_text())
    path=ROOT/'artifacts'/manifest['archive']
    if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['archive_sha256']:
        raise ValueError('Replay archive checksum mismatch')
    expected={e['path']:e for e in manifest['files']}
    entries=[]
    with tarfile.open(path,'r:gz') as archive:
        for member in archive:
            relative=PurePosixPath(member.name)
            if not member.isfile() or relative.is_absolute() or '..' in relative.parts or member.name not in expected:
                raise ValueError('Unexpected/unsafe archive member: '+member.name)
            payload=archive.extractfile(member).read()
            entry=expected.pop(member.name)
            if len(payload)!=entry['bytes'] or hashlib.sha256(payload).hexdigest()!=entry['sha256']:
                raise ValueError('Input checksum mismatch: '+member.name)
            target=ROOT.joinpath(*relative.parts)
            if not target.resolve().is_relative_to(ROOT):
                raise ValueError('Restore path escapes workspace')
            entries.append((target,payload))
    if expected:
        raise ValueError('Archive missing declared members')
    return entries


def restore(entries):
    # Check all conflicts before making any writes. Existing equal files are fine.
    for path,payload in entries:
        if path.exists() and (not path.is_file() or path.read_bytes()!=payload):
            raise ValueError(f'Restore would replace a different file: {path}')
    for path,payload in entries:
        if not path.exists():
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(payload)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['inspect','restore','replay'])
    parser.add_argument('--output',type=Path,help='New output directory for replay; saved pilot is never overwritten')
    parser.add_argument('--dry-run',action='store_true',help='Print replay commands without executing them')
    args=parser.parse_args()
    if args.action in ['inspect','restore']:
        entries=bundle_entries()
        if args.action=='restore':
            restore(entries)
        print(f'Verified {len(entries)} archive members'+('; restored missing files' if args.action=='restore' else '; no files changed'))
        return
    output=(args.output or ROOT/'results/replay'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')).resolve()
    if output==SAVED.resolve() or output.exists() or output.is_relative_to(SAVED.resolve()):
        parser.error('Use a new output directory outside the saved pilot')
    commands=[[sys.executable,str(ROOT/'scripts'/f'{stage}.py'),str(output)] for stage in STAGES]
    if args.dry_run:
        print(f'Copy saved pilot to {output}')
        for cmd in commands:
            print(shlex.join(cmd))
        return
    revision=subprocess.check_output(['git','-C',str(ROOT/'open_asr_leaderboard'),'rev-parse','HEAD'],text=True).strip()
    if revision!=UPSTREAM_REVISION:
        parser.error('Upstream checkout revision differs from the pinned version')
    if not SAVED.is_dir():
        parser.error('Restore the replay bundle first')
    output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(SAVED,output)
    environment=dict(os.environ,PYTHONPATH=str(ROOT/'open_asr_leaderboard'))
    for cmd in commands:
        print(shlex.join(cmd),flush=True)
        subprocess.run(cmd,cwd=ROOT,env=environment,check=True)
    print(f'CPU replay complete: {output}')


if __name__=='__main__':
    main()
