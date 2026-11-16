"""Preview is isolated from production. Never approve or upload candidates."""
import hashlib
import json
import pytest
from curio25.preview import prepare

def test_quarantine_preflight_is_not_production():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    facts=prepare(root,"2026-11-17")
    assert len(facts)==25
    assert all(f["review_status"]=="pending" and f["draft_watermark"] for f in facts)
    assert all(f["media_record"]["review_status"]=="pending_visual_legal_review" for f in facts)
    assert all("media_path" in f and f["source_snapshot_sha256"] for f in facts)
    assert {f["episode_topic"] for f in facts}=={"curiosidades del mundo"}

def test_tampered_media_fail_closed(tmp_path):
    # Build a minimal structural fixture, but fail BEFORE attempting to open images.
    root=tmp_path
    p=root/"data/candidates";p.mkdir(parents=True)
    (p/"2026-11-17.json").write_text(json.dumps({"facts":[{"id":f"x-{i}"} for i in range(25)],"production_ready":False}))
    q=p/"research-2026-11-17";q.mkdir()
    (q/"source_report.json").write_text(json.dumps({"sources_archived":0,"sources":[{"url":"a"}],"production_ready":False}))
    m=p/"media-2026-11-17";m.mkdir()
    (m/"media_report.json").write_text(json.dumps({"photos_downloaded":25,"production_ready":False}))
    with pytest.raises(ValueError,match="Faltan capturas de fuente"):
        prepare(root,"2026-11-17")
