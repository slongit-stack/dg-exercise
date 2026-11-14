"""Conservative, frozen text-only compound canonicalization after upstream normalization."""
import json
from pathlib import Path

from normalizer import EnglishTextNormalizer

DEFAULT_RULES = Path(__file__).resolve().parents[1]/'configs/normalization/compounds_v1.json'


def load_rules(path=DEFAULT_RULES):
    config = json.loads(path.read_text())
    pairs = {}
    for rule in config['rules']:
        pair = tuple(rule['open'].split())
        closed = rule['closed']
        if len(pair) != 2 or ''.join(pair) != closed or pair in pairs:
            raise ValueError(f'Invalid or duplicate rule: {rule}')
        pairs[pair] = closed
    # Prevent cascades: the closed output must never itself be an input token.
    if set(pairs.values()) & {t for p in pairs for t in p}:
        raise ValueError('Cascading rules would make canonicalization non-idempotent')
    return pairs


def canonicalize(tokens, rules):
    out, i = [], 0
    while i < len(tokens):
        pair = tuple(tokens[i:i+2])
        if pair in rules:
            out.append(rules[pair])
            i += 2
        else:
            out.append(tokens[i])
            i += 1
    return out


def normalize_compounds(text, rules):
    return canonicalize(EnglishTextNormalizer()(text).split(), rules)
