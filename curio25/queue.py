"""Editorial FIFO queue shared by the preflight, renderer and coverage monitor.

All 25 facts in a batch must share the same topic and episode title.
No source/image approval is inferred here: curio25.editorial checks those.
"""
from __future__ import annotations

from collections import OrderedDict
from .state import claim_hash


def ready_batches(facts, used_ids=(), past_claims=()):
    """Return complete groups of 25 approved, unused, distinct facts.

    Keep source-file order to make day-to-day selection reproducible.
    Do not mix unrelated topics in one episode, and never silently skip
    an attempted reuse of a previously published/reserved claim.
    """
    used_ids = set(used_ids)
    past_claims = set(past_claims)
    seen_ids = set()
    eligible = []
    seen_claims = set()
    for f in facts:
        fid = f["id"]
        if fid in seen_ids:
            raise ValueError("ID duplicado en el catálogo: " + fid)
        seen_ids.add(fid)
        if fid in used_ids or f.get("review_status") != "verified":
            continue
        claim = claim_hash(f)
        if claim in past_claims:
            raise ValueError("Afirmación repetida con otro identificador: " + fid)
        if claim in seen_claims:
            raise ValueError("Dos afirmaciones duplicadas entre datos nuevos")
        seen_claims.add(claim)
        eligible.append(f)

    grouped = OrderedDict()
    for f in eligible:
        key = (f.get("episode_topic") or "sistema solar", f.get("episode_title") or "")
        grouped.setdefault(key, []).append(f)

    batches = []
    for _, group in grouped.items():
        for start in range(0, (len(group)//25)*25, 25):
            batches.append(group[start:start+25])
    return batches


def next_batch(facts, used_ids=(), past_claims=()):
    batches = ready_batches(facts, used_ids, past_claims)
    return batches[0] if batches else []
