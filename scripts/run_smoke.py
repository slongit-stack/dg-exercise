#!/usr/bin/env python3
"""Run selected models sequentially on a verified local smoke or pilot dataset."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT/'open_asr_leaderboard'


def command(key, config, batch_size, warmup_steps, stage='smoke'):
    model = config['models'][key]
    dataset = str(ROOT/f'data/leaderboard/ami_cleaned/hf_{stage}')
    if key == 'parakeet':
        return [str(ROOT/'normExpParakeetEnv/bin/python'),
                str(ROOT/'scripts/run_parakeet_upstream.py'),
                '--model-revision', model['revision'],
                '--model-id', model['model_id'], '--report-name', model['model_id']+' (fast-gpu-asr)',
                '--model-family', 'parakeet', '--checkpoint-file', 'parakeet-tdt-0.6b-v3.nemo',
                '--dataset-path', dataset, '--dataset', 'ami_cleaned', '--split', 'test',
                '--batch-size', str(batch_size), '--workers', '1', '--beam', '6',
                '--precision', 'fp16', '--decoder-type', 'transducer_modified_beam_search',
                '--min-audio-seconds', '0.1', '--opt-audio-seconds', '10', '--max-audio-seconds', '40',
                '--optimization-level', '5', '--warmup-steps', str(warmup_steps),
                '--engine-cache', str(ROOT/'data/cache/parakeet_engines'), '--device', '0']
    return [str(ROOT/'normExpWhisperEnv/bin/python'), str(UPSTREAM/'transformers/run_eval.py'),
            '--model_id', model['model_id'], '--revision', model['revision'],
            '--dataset_path', dataset, '--dataset', 'ami_cleaned', '--split', 'test',
            '--batch_size', str(batch_size), '--device', '0', '--dtype', 'bfloat16',
            '--attn_implementation', 'sdpa', '--warmup_steps', str(warmup_steps)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['smoke', 'pilot'], default='smoke')
    parser.add_argument('--models', nargs='+', choices=['whisper-large-v3', 'whisper-large-v3-turbo', 'parakeet'],
                        default=['whisper-large-v3', 'whisper-large-v3-turbo', 'parakeet'])
    parser.add_argument('--batch-size', type=int, default=2)
    parser.add_argument('--warmup-steps', type=int, default=1)
    parser.add_argument('--run-dir', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.batch_size < 1 or args.warmup_steps < 0 or len(set(args.models)) != len(args.models):
        parser.error('Use positive batch size, nonnegative warmups, and distinct models')
    config = json.loads((ROOT/'configs/inference_smoke.json').read_text())
    if args.stage == 'pilot':
        config['purpose'] = 'Frozen stratified evaluation pilot for runtime estimation and preliminary accuracy'
    if args.dry_run:
        for key in args.models:
            print(shlex.join(command(key, config, args.batch_size, args.warmup_steps, args.stage)))
        return
    revision = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != config['scoring_revision']:
        parser.error('Upstream revision differs from the configured scoring revision')
    dataset_provenance = ROOT/f'data/leaderboard/ami_cleaned/hf_{args.stage}/provenance.json'
    smoke_manifest = ROOT/f'data/leaderboard/ami_cleaned/manifest_{args.stage}.jsonl'
    provenance = json.loads(dataset_provenance.read_text())
    if provenance['source_manifest_sha256'] != hashlib.sha256(smoke_manifest.read_bytes()).hexdigest():
        parser.error('Subset manifest changed; rerun scripts/export_hf_subset.py')
    parquet = dataset_provenance.parent/'ami_cleaned/test-00000-of-00001.parquet'
    if hashlib.sha256(parquet.read_bytes()).hexdigest() != provenance['parquet_sha256']:
        parser.error('Local dataset checksum mismatch')
    gpu = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total',
                          '--format=csv,noheader'], capture_output=True, text=True)
    if gpu.returncode:
        parser.exit(1, 'GPU preflight failed; no inference was started.\n'+gpu.stderr+gpu.stdout)
    run = (args.run_dir or ROOT/f'results/{args.stage}'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')).resolve()
    run.mkdir(parents=True, exist_ok=False)
    (run/'configuration.json').write_text(json.dumps(dict(
        config, batch_size=args.batch_size, warmup_steps=args.warmup_steps,
        stage=args.stage,
        selected_models=args.models, gpu=gpu.stdout.strip(), subset_provenance=provenance,
    ), indent=2)+'\n')
    env = dict(os.environ, PYTHONPATH=str(UPSTREAM), HF_HOME=str(ROOT/'data/cache/huggingface'),
               HF_DATASETS_CACHE=str(ROOT/'data/cache/datasets'),
               HF_HUB_CACHE=str(ROOT/'data/cache/huggingface/hub'),
               HF_MODULES_CACHE=str(ROOT/'data/cache/huggingface/modules'),
               XDG_CACHE_HOME=str(ROOT/'data/cache'), CUPY_CACHE_DIR=str(ROOT/'data/cache/cupy'),
               PYTHONUNBUFFERED='1')
    for key in args.models:
        work = run/key
        work.mkdir()
        cmd = command(key, config, args.batch_size, args.warmup_steps, args.stage)
        (work/'command.json').write_text(json.dumps(cmd, indent=2)+'\n')
        packages = subprocess.check_output([cmd[0], '-m', 'pip', 'list', '--format=json'], text=True)
        (work/'packages.json').write_text(packages)
        print(f'Running {key}; log: {work/"inference.log"}', flush=True)
        started = time.perf_counter()
        with (work/'inference.log').open('w') as log, (work/'gpu_samples.csv').open('w') as telemetry:
            monitor = subprocess.Popen(
                ['nvidia-smi', '--query-gpu=timestamp,memory.used,memory.total,utilization.gpu',
                 '--format=csv,noheader,nounits', '-l', '1'],
                stdout=telemetry, stderr=subprocess.STDOUT)
            try:
                result = subprocess.run(cmd, cwd=work, env=env, stdout=log, stderr=subprocess.STDOUT)
            finally:
                monitor.terminate()
                monitor.wait(timeout=10)
        (work/'status.json').write_text(json.dumps(dict(
            returncode=result.returncode, wall_seconds_including_setup=time.perf_counter()-started,
        ), indent=2)+'\n')
        if result.returncode:
            parser.exit(1, f'{key} failed; inspect {work/"inference.log"}\n')
        predictions = list((work/'results').glob('*.jsonl'))
        if len(predictions) != 1:
            parser.exit(1, f'Expected one prediction manifest in {work/"results"}\n')
        subprocess.run([sys.executable, str(ROOT/'scripts/score_predictions.py'), str(predictions[0]),
                        '--manifest', str(smoke_manifest),
                        '--output', str(work/'verified_score.json')], env=env, check=True)
    print(f'{args.stage.capitalize()} completed: {run}')


if __name__ == '__main__':
    main()
