"""Future YouTube slots are exact and remain blocked without explicit permission."""
from datetime import datetime,timezone,date
import pytest

from curio25.youtube import publish_at,publication_day


def test_episode_date_is_carried_to_video_schedule():
    assert publication_day('daily-2027-03-28')==date(2027,3,28)
    assert publication_day('pilot-001') is None
    assert publication_day('daily-2027-03-28-extra') is None


def test_a_scheduled_week_in_madrid_keeps_exact_18_local():
    cfg={'timezone':'Europe/Madrid','publish_hour':'18:00'}
    now=datetime(2027,3,20,12,tzinfo=timezone.utc)
    result=[datetime.fromisoformat(publish_at(cfg,now,target_date=date(2027,3,d)))
            for d in range(25,31)]
    assert result[0].hour==17
    assert result[1].hour==17
    assert all(x.hour==16 for x in result[3:])
    assert len(set(result))==6


def test_cannot_silently_move_yesterday_episode_to_tomorrow():
    cfg={'timezone':'Europe/Madrid','publish_hour':'18:00'}
    now=datetime(2027,3,30,20,tzinfo=timezone.utc)
    with pytest.raises(ValueError,match='pasado|cerca'):
        publish_at(cfg,now,target_date=date(2027,3,29))


def test_default_remains_next_valid_slot():
    cfg={'timezone':'Europe/Madrid','publish_hour':'18:00'}
    now=datetime(2026,11,17,21,tzinfo=timezone.utc)
    assert publish_at(cfg,now).startswith('2026-11-18T17:00')


def test_naive_now_is_not_accepted():
    with pytest.raises(ValueError,match='zona horaria'):
        publish_at({'timezone':'Europe/Madrid','publish_hour':'18:00'},
                   datetime(2026,11,17,20))
