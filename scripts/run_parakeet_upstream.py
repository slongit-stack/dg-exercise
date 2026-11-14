#!/usr/bin/env python3
"""Run upstream Parakeet evaluation with an explicitly pinned Hub revision.

Upstream's Parakeet CLI lacks a model-revision option. Its exporter also replaces
the child environment, losing writable-cache settings. This wrapper pins the
download and preserves the parent environment alongside exporter overrides;
audio preparation, inference, and export implementation remain upstream.
"""
import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace


def run_with_environment(*args, **kwargs):
    if 'env' in kwargs:
        kwargs['env'] = dict(os.environ, **kwargs['env'])
    return subprocess.run(*args, **kwargs)


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--model-revision', required=True)
    args, remaining = parser.parse_known_args()
    root = Path(__file__).resolve().parents[1]
    path = root/'open_asr_leaderboard/soundsgoodai/run_eval.py'
    spec = importlib.util.spec_from_file_location('upstream_parakeet_eval', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    download = module.snapshot_download

    def pinned_download(repo_id, *positional, **kwargs):
        kwargs['revision'] = args.model_revision
        return download(repo_id, *positional, **kwargs)

    module.snapshot_download = pinned_download
    module.subprocess = SimpleNamespace(run=run_with_environment)
    sys.argv = [str(path), *remaining]
    module.main()


if __name__ == '__main__':
    main()
