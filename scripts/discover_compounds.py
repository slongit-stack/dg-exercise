#!/usr/bin/env python3
"""Discover compound variants from separate, locally available AMI annotations."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from normalizer import EnglishTextNormalizer

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'data/development/compounds'
LEXICON = Path('/usr/share/pocketsphinx/model/en-us/cmudict-en-us.dict')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def segments(path):
    """Keep one speaker per segment; break at sentence punctuation or >1s gap."""
    words, previous_end = [], None
    for node in ET.parse(path).getroot():
        if node.tag != 'w':
            if words:
                yield ' '.join(words)
            words, previous_end = [], None
            continue
        text = node.text or ''
        if node.get('punc') == 'true':
            if any(c in text for c in '.?!;') and words:
                yield ' '.join(words)
                words, previous_end = [], None
            continue
        start = float(node.get('starttime', '0'))
        if previous_end is not None and start-previous_end > 1.0 and words:
            yield ' '.join(words)
            words = []
        words.append(text)
        previous_end = float(node.get('endtime', str(start)))
    if words:
        yield ' '.join(words)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    normalize = EnglishTextNormalizer()
    test = [json.loads(s) for s in (ROOT/'data/leaderboard/ami_cleaned/manifest_test.jsonl').read_text().splitlines()]
    test_series = {r['meeting_series_id'] for r in test}
    meetings_path = ROOT/'data/corpusResources/meetings.xml'
    meetings = list(ET.parse(meetings_path).getroot())
    test_meetings = {r['meeting_id'] for r in test}
    test_speakers = {s.get('global_name') for m in meetings if m.get('observation') in test_meetings for s in m}
    allowed = {m.get('observation') for m in meetings
               if m.get('seen_type') == 'training'
               and m.get('observation')[:-1] not in test_series
               and not ({s.get('global_name') for s in m} & test_speakers)}
    files = sorted(p for p in (ROOT/'data/words').glob('*.words.xml') if p.name.split('.')[0] in allowed)
    if not files:
        raise ValueError('No disjoint training annotations')
    # Vendor lexicon locally so discovery remains reproducible across machines.
    lex_path = OUT/'lexicon_source.dict'
    if not lex_path.exists():
        lex_path.write_bytes(LEXICON.read_bytes())
    lexicon = {re.sub(r'\(\d+\)$', '', s.split()[0]).lower()
               for s in lex_path.read_text().splitlines() if s.strip()}
    lexicon = {w for w in lexicon if re.fullmatch('[a-z]+', w)}
    unigram, bigram = Counter(), Counter()
    examples = defaultdict(list)
    docs = []
    for path in files:
        for i, raw in enumerate(segments(path)):
            tokens = normalize(raw).split()
            if not tokens:
                continue
            doc = dict(id=f'{path.stem}:{i}', meeting_id=path.name.split('.')[0],
                       speaker_agent=path.name.split('.')[1], text=raw, normalized_text=' '.join(tokens))
            docs.append(doc)
            unigram.update(tokens)
            bigram.update(zip(tokens, tokens[1:]))
    candidates = []
    for pair, count in sorted(bigram.items()):
        closed = ''.join(pair)
        if closed in lexicon and unigram[closed] and all(re.fullmatch('[a-z]+', w) for w in pair):
            candidates.append(dict(open=' '.join(pair), closed=closed,
                open_count=count, closed_count=unigram[closed], review_status='pending'))
    wanted = {c['open'] for c in candidates} | {c['closed'] for c in candidates}
    for doc in docs:
        ts = doc['normalized_text'].split()
        forms = set(ts) | {' '.join(p) for p in zip(ts, ts[1:])}
        for form in forms & wanted:
            if len(examples[form]) < 4:
                examples[form].append(dict(id=doc['id'], text=doc['text']))
    for c in candidates:
        c['open_examples'] = examples[c['open']]
        c['closed_examples'] = examples[c['closed']]
    (OUT/'transcripts.jsonl').write_text(''.join(json.dumps(d)+'\n' for d in docs))
    (OUT/'candidates.json').write_text(json.dumps(candidates, indent=2)+'\n')
    provenance = dict(selection='All local word annotations labelled training in AMI meetings.xml, excluding evaluation series and speakers; development use only, not a claimed HF train split.',
        meetings=sorted({p.name.split('.')[0] for p in files}),
        documents=len(docs), normalized_words=sum(unigram.values()), candidates=len(candidates),
        evaluation_series=sorted(test_series), evaluation_speakers=sorted(test_speakers),
        metadata_sha256=sha(meetings_path), evaluation_manifest_sha256=sha(ROOT/'data/leaderboard/ami_cleaned/manifest_test.jsonl'),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
        lexicon_source=str(LEXICON), lexicon_sha256=sha(lex_path),
        transcript_sha256=sha(OUT/'transcripts.jsonl'), script_sha256=sha(Path(__file__)),
        discovery='Both open bigram and closed token observed after upstream normalization; closed token in pinned CMU pronunciation lexicon. No frequency threshold. Break on sentence punctuation, non-word events, or >1s pause; no cross-speaker bigrams.')
    (OUT/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    print(json.dumps({k:provenance[k] for k in ['meetings','documents','normalized_words','candidates']}, indent=2))


if __name__ == '__main__':
    main()
