"""Fixed text-only English Snowball policy, independent of the other transcript."""
from functools import lru_cache
from importlib.metadata import version
import re

import snowballstemmer

PACKAGE_VERSION = '3.0.1'
if version('snowballstemmer') != PACKAGE_VERSION:
    raise RuntimeError(f'Expected snowballstemmer=={PACKAGE_VERSION}')
_STEMMER = snowballstemmer.stemmer('english')


@lru_cache(maxsize=100000)
def stem_token(token):
    return _STEMMER.stemWord(token) if re.fullmatch('[a-z]+', token) else token


def stem_tokens(tokens):
    return [stem_token(token) for token in tokens]
