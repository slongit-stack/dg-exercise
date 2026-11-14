#!/usr/bin/env python3
"""Validate pinned AMI-Cleaned audio and build raw-reference evaluation manifests.

Run from any directory with normExpEnv/bin/python. Audio bytes are preserved.
The test split is evaluation-only, including its smoke-test subset.
"""
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
from importlib.metadata import version

import numpy as np
import pyarrow.parquet as pq
import soundfile as sf

from normalizer import EnglishTextNormalizer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/leaderboard/ami_cleaned'
ID_PATTERN = re.compile(
    r'^AMI_(?P<meeting>[A-Z]+\d+[a-z])_(?P<headset>H\d+)_(?P<speaker>[A-Z0-9]+)_(?P<start>\d+)_(?P<end>\d+)$'
)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def write_manifest(path, rows):
    with path.open('w') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def main():
    provenance = json.loads((OUT / 'download_provenance.json').read_text())
    annotation_path = ROOT / 'data/corpusResources/meetings.xml'
    meeting_annotations = {
        m.attrib['observation']: m for m in ET.parse(annotation_path).getroot().findall('meeting')
    }
    normalize = EnglishTextNormalizer()
    records, excluded = [], []
    seen_ids, audio_hashes = set(), defaultdict(list)
    (OUT / 'audio').mkdir(exist_ok=True)
    for shard in provenance['files']:
        path = ROOT / shard['path']
        # Check provenance before trusting/extracting a locally modified shard.
        sha = hashlib.sha256()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
                sha.update(chunk)
        if sha.hexdigest() != shard['sha256']:
            raise ValueError(f'Shard checksum mismatch: {path}')
        row_number = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=16):
            for item in batch.to_pylist():
                example_id = item['id']
                if example_id in seen_ids:
                    raise ValueError(f'Duplicate example ID: {example_id}')
                seen_ids.add(example_id)
                match = ID_PATTERN.fullmatch(example_id)
                if match is None:
                    raise ValueError(f'Unrecognized ID: {example_id}')
                groups = match.groupdict()
                meeting = meeting_annotations[groups['meeting']]
                speakers = [s for s in meeting.findall('speaker')
                            if s.get('global_name') == groups['speaker']
                            and int(s.get('channel', '-1')) == int(groups['headset'][1:])]
                if len(speakers) != 1:
                    raise ValueError(f'ID disagrees with AMI meeting annotations: {example_id}')
                speaker = speakers[0]
                raw = item['audio']['bytes']
                if not raw:
                    raise ValueError(f'Missing embedded audio: {example_id}')
                audio, rate = sf.read(io.BytesIO(raw), dtype='float32', always_2d=True)
                info = sf.info(io.BytesIO(raw))
                if rate != 16000 or audio.shape[1] != 1 or len(audio) == 0:
                    raise ValueError(f'Unexpected audio format: {example_id}: {info}')
                if not np.isfinite(audio).all():
                    raise ValueError(f'Non-finite samples: {example_id}')
                duration = len(audio) / rate
                if abs(duration - item['audio_length_s']) > 1 / rate + 1e-9:
                    raise ValueError(f'Duration metadata mismatch: {example_id}')
                if not isinstance(item['text'], str):
                    raise ValueError(f'Non-string reference: {example_id}')
                norm = normalize(item['text'])
                eligible = bool(norm.strip()) and norm.strip() != 'ignore time segment in scoring'
                checksum = hashlib.sha256(raw).hexdigest()
                audio_hashes[checksum].append(example_id)
                target = OUT / 'audio' / f'{example_id}.wav'
                if target.exists():
                    if hashlib.sha256(target.read_bytes()).hexdigest() != checksum:
                        raise ValueError(f'Existing audio differs: {target}')
                else:
                    target.write_bytes(raw)
                # ID offsets are recorded as encoded values; their scale and
                # original-timeline interpretation need separate verification.
                record = dict(
                    id=example_id, audio_filepath=str(target.relative_to(ROOT)),
                    text=item['text'], normalized_text=norm,
                    eligible_for_official_scoring=eligible,
                    duration_seconds=duration, sample_rate=rate, channels=info.channels,
                    frames=info.frames, audio_subtype=info.subtype, audio_sha256=checksum,
                    original_audio_path=item['audio']['path'], dataset=item['dataset'],
                    meeting_id=groups['meeting'], speaker_id=groups['speaker'],
                    meeting_series_id=groups['meeting'][:-1],
                    meeting_type=meeting.get('type'), annotation_agent=speaker.get('nxt_agent'),
                    annotation_role=speaker.get('role'),
                    headset_id_from_example_id=groups['headset'],
                    encoded_start=int(groups['start']), encoded_end=int(groups['end']),
                    normalized_reference_words=len(norm.split()),
                    words_per_segment_second=len(norm.split()) / duration,
                    peak_amplitude=float(np.max(np.abs(audio))),
                    rms_amplitude=float(np.sqrt(np.mean(audio.astype('float64') ** 2))),
                    all_zero_audio=bool(not np.any(audio)),
                    source_shard=shard['upstream_path'], source_row=row_number,
                    dataset_revision=provenance['revision'],
                )
                records.append(record)
                if not eligible:
                    excluded.append(example_id)
                row_number += 1
        print(f'Validated {path.name}: {row_number} examples', flush=True)
    if len(records) != 7805:
        raise ValueError(f'Expected 7805 examples, found {len(records)}')
    eligible = [r for r in records if r['eligible_for_official_scoring']]
    by_meeting = defaultdict(list)
    for record in eligible:
        by_meeting[record['meeting_id']].append(record)
    # Deterministic coverage sample: one typical-length example per meeting,
    # plus the global shortest and longest. This is a smoke test, not an
    # unbiased performance estimate or a development set.
    smoke = {}
    for meeting, rows in sorted(by_meeting.items()):
        candidates = [r for r in rows if 2 <= r['duration_seconds'] <= 15] or rows
        chosen = min(candidates, key=lambda r: hashlib.sha256(
            ('normExp-smoke-v1:' + r['id']).encode()).hexdigest())
        smoke[chosen['id']] = chosen
    for chosen in (min(eligible, key=lambda r: r['duration_seconds']),
                   max(eligible, key=lambda r: r['duration_seconds'])):
        smoke[chosen['id']] = chosen
    write_manifest(OUT / 'manifest_all.jsonl', records)
    write_manifest(OUT / 'manifest_test.jsonl', eligible)
    write_manifest(OUT / 'manifest_smoke.jsonl', sorted(smoke.values(), key=lambda r: r['id']))
    durations = [r['duration_seconds'] for r in records]
    report = dict(
        dataset_repo=provenance['repo_id'], dataset_revision=provenance['revision'],
        config='ami_cleaned', split='test', total_examples=len(records),
        eligible_examples=len(eligible), excluded_ids=excluded,
        total_audio_hours=sum(durations) / 3600,
        eligible_audio_hours=sum(r['duration_seconds'] for r in eligible) / 3600,
        normalized_reference_words=sum(r['normalized_reference_words'] for r in eligible),
        duration_percentiles_seconds=dict(zip(['min', 'p25', 'median', 'p75', 'p95', 'max'],
            np.percentile(durations, [0, 25, 50, 75, 95, 100]).tolist())),
        audio_subtypes=dict(Counter(r['audio_subtype'] for r in records)),
        meetings={m: dict(examples=len(rows), audio_hours=sum(r['duration_seconds'] for r in rows)/3600,
                         speakers=sorted({r['speaker_id'] for r in rows}))
                  for m, rows in sorted(by_meeting.items())},
        unique_speakers=len({r['speaker_id'] for r in records}),
        meeting_series=sorted({r['meeting_series_id'] for r in records}),
        annotation_metadata_verification=dict(
            matched_examples=len(records),
            checked_fields=['meeting_id', 'speaker_id', 'headset channel number'],
            source=str(annotation_path.relative_to(ROOT)),
            sha256=hashlib.sha256(annotation_path.read_bytes()).hexdigest(),
        ),
        normalizer_revision=subprocess.check_output(
            ['git', '-C', str(ROOT/'open_asr_leaderboard'), 'rev-parse', 'HEAD'], text=True).strip(),
        dependency_versions={name: version(name) for name in ['pyarrow', 'numpy', 'soundfile', 'regex']},
        duplicate_audio_groups=[ids for ids in audio_hashes.values() if len(ids) > 1],
        all_zero_audio_ids=[r['id'] for r in records if r['all_zero_audio']],
        audio_above_unit_peak_ids=[r['id'] for r in records if r['peak_amplitude'] > 1],
        smoke_examples=len(smoke), smoke_audio_seconds=sum(r['duration_seconds'] for r in smoke.values()),
        local_raw_meetings=sorted(p.name for p in (ROOT/'data/amicorpus').iterdir() if (p/'audio').is_dir()),
        warnings=[
            'Meeting/speaker/channel fields match local AMI meetings.xml; that is a metadata cross-check, not a listening audit.',
            'Only four meeting series are represented; repeated speakers limit independence across the 16 meetings.',
            'Encoded start/end offsets have not been verified against original recordings.',
            'Words per segment second is a reference-density proxy, not active-speech speaking rate.',
            'Audio condition and cleaned-reference provenance require further source documentation.',
            'Current pinned dataset/scoring revisions are not confirmed as the revisions of the supplied leaderboard scores.',
            'No training/development split is prepared; do not fit normalization or term weights on this test split.',
        ],
    )
    write_json(OUT / 'verification.json', report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['meetings', 'warnings']}, indent=2))


if __name__ == '__main__':
    main()
