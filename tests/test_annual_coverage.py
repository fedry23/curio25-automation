"""Readiness for 365 episodes, without confusing candidates with approved stock."""
import json
from datetime import date
from pathlib import Path
import pytest

from curio25.queue import ready_batches,next_batch
from curio25.state import claim_hash
from curio25.coverage import forecast,markdown


def sample(count=50,alternate=False):
    out=[]
    for i in range(count):
        topic='animales' if (i%2==0 if alternate else i<count//2) else 'ciencia'
        out.append(dict(id=f'dato-{i:04}',claim=f'Unique claim {i}',
                        episode_topic=topic,review_status='verified'))
    return out


def test_topics_are_grouped_without_mix():
    batches=ready_batches(sample(50,True))
    assert len(batches)==2
    assert all(len(batch)==25 for batch in batches)
    assert all(len({f['episode_topic'] for f in batch})==1 for batch in batches)
    assert next_batch(sample(50,True))==batches[0]


def test_two_incomplete_topics_are_not_an_episode():
    assert ready_batches(sample(40,True))==[]


def test_used_facts_and_duplicate_claims_never_return():
    facts=sample(75)
    used={f['id'] for f in facts[:25]}
    batches=ready_batches(facts,used)
    assert not any(f['id'] in used for b in batches for f in b)
    with pytest.raises(ValueError,match='Afirmación repetida'):
        ready_batches(facts,past_claims={claim_hash(facts[0])})


def test_pending_not_eligible():
    facts=sample(25)
    facts[0]['review_status']='pending'
    assert not next_batch(facts)


def fixture(root,facts,candidates=()):
    data=root/'data'
    (data/'candidates').mkdir(parents=True)
    (data/'facts.json').write_text(json.dumps(facts))
    (data/'history.json').write_text(json.dumps(
        {'used_facts':[],'claims':[],'episodes':[]}))
    (root/'config.json').write_text(json.dumps({
        'channel_id':None,'publication_enabled':False}))
    if candidates:
        (data/'candidates/2026-11-17.json').write_text(json.dumps(
            {'facts':list(candidates)}))


def test_forecast_2026_and_shortage(tmp_path,monkeypatch):
    from curio25 import coverage
    fixture(tmp_path,sample(50,True),[
        dict(id='pending-1',review_status='pending'),
        dict(id='pending-2',review_status='pending')])
    monkeypatch.setattr(coverage,'audit',lambda root:{'ok':True})
    r=forecast(tmp_path,date(2026,11,17))
    assert r['annual_goal_episodes']==365
    assert r['annual_goal_unique_facts']==9125
    assert r['confirmed_ready_batches']==2
    assert r['missing_facts_to_minimum_buffer']==700
    assert r['unreviewed_candidate_facts']==2
    assert r['status']=='CRITICAL'
    assert r['confirmed_public_uploads'] is None
    assert r['youtube_publication_enabled'] is False
    assert 'Candidatos sin aprobar' in markdown(r)


def test_leap_year_366(tmp_path,monkeypatch):
    from curio25 import coverage
    fixture(tmp_path,sample(25))
    monkeypatch.setattr(coverage,'audit',lambda root:{'ok':True})
    r=forecast(tmp_path,date(2028,1,1))
    assert r['annual_goal_episodes']==366
    assert r['annual_goal_unique_facts']==9150


def test_corrupt_approval_blocks_stock_count(tmp_path,monkeypatch):
    from curio25 import coverage
    fixture(tmp_path,sample(50))
    def fail(root):
        raise ValueError('Imagen sin licencia')
    monkeypatch.setattr(coverage,'audit',fail)
    report=forecast(tmp_path,date(2026,11,17))
    assert report['status']=='BLOCKED'
    assert report['confirmed_ready_batches']==0
    assert 'licencia' in report['catalogue_error']


def test_real_repository_no_pilot_reuse():
    root=Path(__file__).resolve().parents[1]
    result=forecast(root,date(2026,11,17))
    assert result['confirmed_ready_facts']%25==0
    assert result['annual_goal_unique_facts']==9125
    assert result['can_guarantee_annual_publications'] is False
