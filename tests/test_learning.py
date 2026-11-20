from datetime import date
from curio25.learning import BASELINE, CHALLENGER, collect_peers, decide, assigned_profile, select_for_render
import pytest


class Response:
    def __init__(self, items): self.items=items
    def execute(self): return {'items':self.items}


class PublicAPI:
    def search(self): return self
    def videos(self): return self
    def channels(self): return self
    def list(self, **kw):
        if 'q' in kw:
            lang=kw['relevanceLanguage']
            return Response([{'snippet':{'channelId':lang+str(i)},'id':{'videoId':'v'+lang+str(i)}} for i in range(20)])
        if 'statistics,status' in kw['part']:
            return Response([{'id':v,'snippet':{'channelId':v[1:]},'status':{'privacyStatus':'public'}} for v in kw['id'].split(',')])
        return Response([{'id':kw['id']}])


def test_peer_collection_unique_quota_and_read_only():
    rows=collect_peers(PublicAPI(),'own')
    assert len(rows)==30
    assert len({x['channel']['id'] for x in rows})==30
    assert sum(x['search_language']=='es' for x in rows)==15
    assert sum(x['search_language']=='en' for x in rows)==15


def test_learning_requires_sample_and_can_rollback():
    assert decide([])=='explore'
    def rows(candidate):
        return [{'video_id':str(i)+profile,'profile':profile,'views':200,'retention':retention}
                for profile,retention in [(BASELINE,40),(CHALLENGER,candidate)] for i in range(5)]
    assert decide(rows(44))==CHALLENGER
    assert decide(rows(41))==BASELINE
    assert decide(rows(30))==BASELINE
    assert decide(rows(44)[:5])=='explore'
    assert assigned_profile('daily-2026-11-19','explore')!=assigned_profile('daily-2026-11-20','explore')


def test_disabled_and_error_stay_baseline():
    assert select_for_render({},None,'daily-2026-11-19')==(BASELINE,'disabled')
    assert select_for_render({'learning_enabled':True,'learning_policy_accepted':True},None,'daily-2026-11-19',clients=(object(),object()))==(BASELINE,'unavailable')
