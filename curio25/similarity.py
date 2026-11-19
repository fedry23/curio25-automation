"""Conservative lexical near-duplicate screening; not a semantic fact oracle.

Exact normalized matches block a candidate batch. High overlap and explicit
concept keys flag likely paraphrases for editorial review. No automatic approval.
"""
import json
import re
import unicodedata
from pathlib import Path

STOP = set("el la los las un una unos unas de del en a al por para que se su sus es son y o con como mas muy entre sobre aproximadamente alrededor unos unas".split())


def tokens(text):
    clean = ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                    if not unicodedata.combining(c))
    return re.findall(r'[a-z]+|[0-9]+', clean)


def signature(text):
    return ' '.join(tokens(text))


def keywords(text):
    return {w for w in tokens(text) if w not in STOP}


def compare(left, right):
    a, b = left['claim'], right['claim']
    if signature(a)==signature(b):
        return 'exact'
    concept = left.get('concept_key')
    if concept and concept == right.get('concept_key'):
        return 'same_concept'
    x,y=keywords(a),keywords(b)
    if min(len(x),len(y)) >= 4 and len(x & y)/len(x | y) >= .72:
        return 'high_overlap'
    return None


def screen(root, target):
    root=Path(root)
    directory=root/'data/candidates'
    candidates=[]
    catalogue=root/'data/facts.json'
    if catalogue.exists():
        candidates.extend(json.loads(catalogue.read_text(encoding='utf-8')))
    for path in sorted(directory.glob('????-??-??.json')):
        if path.stem == target:
            continue
        candidates.extend(json.loads(path.read_text(encoding='utf-8'))['facts'])
    current=json.loads((directory/(target+'.json')).read_text(encoding='utf-8'))['facts']
    flags=[]
    for fact in current:
        if not isinstance(fact.get('claim'),str) or not signature(fact['claim']):
            raise ValueError('Afirmación vacía: '+fact['id'])
        for previous in candidates:
            reason='same_id' if fact['id']==previous['id'] else compare(fact,previous)
            if reason:
                flags.append({'fact_id':fact['id'],'other_id':previous['id'],'reason':reason})
        candidates.append(fact)
    return flags
