"""Candidate research follows new dates; 30-day timeline remains offline."""
import json
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from curio25.candidate_queue import pending_batches
from curio25.calendar import plan, local_datetime


def create_candidate(root, day, count=25):
    folder=root/"data/candidates"
    folder.mkdir(parents=True,exist_ok=True)
    (folder/(day+".json")).write_text(
        json.dumps({"facts":[{"id":f"{day}-{i}","review_status":"pending"}
                              for i in range(count)]}),encoding="utf-8")
    return folder


def test_candidate_research_chooses_oldest_unresearched(tmp_path):
    folder=create_candidate(tmp_path,"2026-11-18")
    create_candidate(tmp_path,"2026-11-19")
    assert pending_batches(tmp_path)==["2026-11-18","2026-11-19"]
    (folder/"research-2026-11-18").mkdir()
    (folder/"research-2026-11-18/source_report.json").write_text("{}")
    assert pending_batches(tmp_path)==["2026-11-19"]
    (folder/"research-2026-11-19").mkdir()
    (folder/"research-2026-11-19/source_report.json").write_text("{}")
    assert pending_batches(tmp_path)==[]


def test_research_does_not_count_image_selection_as_fact_batch(tmp_path):
    folder=create_candidate(tmp_path,"2026-11-18")
    (folder/"media-selection-2026-11-20.json").write_text("{}")
    (folder/"research-2026-11-21.json").write_text("{}")
    assert pending_batches(tmp_path)==["2026-11-18"]


def test_candidate_batch_must_be_complete(tmp_path):
    create_candidate(tmp_path,"2026-11-18",24)
    with pytest.raises(ValueError,match="incompleto"):
        pending_batches(tmp_path)


def test_local_eighteen_stays_eighteen_through_madrid_dst():
    config={"timezone":"Europe/Madrid","publish_hour":"18:00"}
    before=local_datetime(date(2027,3,27),config)
    after=local_datetime(date(2027,3,28),config)
    assert before.hour==after.hour==18
    assert before.utcoffset().total_seconds()==3600
    assert after.utcoffset().total_seconds()==7200
    oct_before=local_datetime(date(2027,10,30),config)
    oct_after=local_datetime(date(2027,10,31),config)
    assert oct_before.hour==oct_after.hour==18
    assert oct_before.utcoffset().total_seconds()==7200
    assert oct_after.utcoffset().total_seconds()==3600


def prepare(root, count=50, status="verified"):
    data=root/"data"
    data.mkdir(parents=True)
    facts=[
        {"id":f"unique-{i}","claim":f"Different story {i}",
         "episode_topic":"curiosidades del mundo",
         "episode_title":"25 datos sorprendentes",
         "review_status":status} for i in range(count)
    ]
    (data/"facts.json").write_text(json.dumps(facts))
    (data/"history.json").write_text(
        json.dumps({"episodes":[],"used_facts":[],"claims":[]}))
    (root/"config.json").write_text(json.dumps({
        "timezone":"Europe/Madrid","publish_hour":"18:00",
        "publication_enabled":False,"channel_id":None}))
    return facts


def test_calendar_allocates_only_approved_batches(tmp_path,monkeypatch):
    from curio25 import coverage
    monkeypatch.setattr(coverage,"audit",lambda _:{"ok":True})
    prepare(tmp_path,50)
    schedule=plan(tmp_path,date(2026,11,18),7)
    assert [x["status"] for x in schedule["slots"]]==[
        "approved_facts_available_for_render"]*2+["missing_approved_facts"]*5
    assert len({x["id_digest"] for x in schedule["slots"][:2]})==2
    assert schedule["publication_enabled"] is False
    assert schedule["youtube_verified_public_uploads"] is None
    assert all(x["publication_authorized"] is False for x in schedule["slots"])
    assert all(x["local"].endswith("+01:00") for x in schedule["slots"])


def test_calendar_never_counts_unapproved_candidates(tmp_path,monkeypatch):
    from curio25 import coverage
    monkeypatch.setattr(coverage,"audit",lambda _:{"ok":True})
    prepare(tmp_path,25,status="pending")
    schedule=plan(tmp_path,date(2026,11,18),2)
    assert all(x["status"]=="missing_approved_facts" for x in schedule["slots"])


def test_existing_schedule_is_only_a_history_record(tmp_path,monkeypatch):
    from curio25 import coverage
    monkeypatch.setattr(coverage,"audit",lambda _:{"ok":True})
    prepare(tmp_path,25)
    data=tmp_path/"data/history.json"
    history=json.loads(data.read_text())
    history["episodes"]=[{"id":"daily-2026-11-18","status":"scheduled","video_id":"not-verified"}]
    data.write_text(json.dumps(history))
    calendar=plan(tmp_path,date(2026,11,18),2)
    assert calendar["slots"][0]["status"]=="recorded_scheduled_not_youtube_verified"
    assert not calendar["slots"][0]["verified_on_youtube"]
    assert calendar["slots"][1]["status"]=="approved_facts_available_for_render"


@pytest.mark.parametrize("value",["18:0","25:00","aa:bb"])
def test_invalid_local_hours_are_rejected(value):
    with pytest.raises(ValueError):
        local_datetime(date(2027,6,1),{
            "timezone":"Europe/Madrid","publish_hour":value})
