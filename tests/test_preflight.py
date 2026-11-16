"""Safety checks for the daily editorial preflight."""
import hashlib
import json
import pytest
from curio25.preflight import assess


def setup_catalog(tmp_path, total=25, used=(), review="verified"):
    data = tmp_path / "data"
    (data / "snapshots").mkdir(parents=True)
    proof = b"reviewed scientific evidence available"
    (data / "snapshots/source.txt").write_bytes(proof)
    hashed = hashlib.sha256(proof).hexdigest()
    audit = [{"url": "https://example.org/source",
              "path": "data/snapshots/source.txt", "sha256": hashed}]
    facts = [{"id": f"fact-{i}", "claim": f"Unique claim number {i}",
              "review_status": review, "source_url": "https://example.org/source",
              "source_snapshot_sha256": hashed, "evidence_query": "scientific evidence"}
             for i in range(total)]
    history = {"episodes": [], "used_facts": [
        {"id": f"fact-{i}", "episode": "pilot-001"} for i in used], "claims": []}
    (data / "facts.json").write_text(json.dumps(facts))
    (data / "source_audit.json").write_text(json.dumps(audit))
    (data / "history.json").write_text(json.dumps(history))
    return data, history


def save_history(data, history):
    (data / "history.json").write_text(json.dumps(history))


def test_ready_25(tmp_path):
    setup_catalog(tmp_path)
    assert assess(tmp_path, "daily", "next")["code"] == "READY"


@pytest.mark.parametrize("count,used,review", [
    (24, [], "verified"), (25, range(25), "verified"),
    (25, [], "pending"),
])
def test_exhausted_does_not_render(tmp_path, count, used, review):
    setup_catalog(tmp_path, count, used, review)
    r = assess(tmp_path, "daily", "next")
    assert not r["ready"] and r["code"] == "CATALOG_EXHAUSTED"


def test_resume_only_same_reserved_episode(tmp_path):
    data, history = setup_catalog(tmp_path, used=range(25))
    history["episodes"] = [{"id": "next", "status": "reserved"}]
    for row in history["used_facts"]:
        row["episode"] = "next"
    save_history(data, history)
    assert assess(tmp_path, "daily", "next")["code"] == "RESUME"


@pytest.mark.parametrize("status", ["reserved", "uploading"])
def test_ambiguous_state_blocks_new_episode(tmp_path, status):
    data, history = setup_catalog(tmp_path)
    history["episodes"] = [{"id": "previous", "status": status}]
    save_history(data, history)
    assert assess(tmp_path, "daily", "next")["code"] == "RECONCILIATION_REQUIRED"


def test_existing_video_is_never_replaced(tmp_path):
    data, history = setup_catalog(tmp_path)
    history["episodes"] = [{"id": "next", "status": "rendered"}]
    save_history(data, history)
    assert assess(tmp_path, "daily", "next")["code"] == "EPISODE_EXISTS"


def test_manual_revision_only_before_upload(tmp_path):
    data, history = setup_catalog(tmp_path)
    history["episodes"] = [{"id": "pilot-001", "status": "rendered"}]
    save_history(data, history)
    assert assess(tmp_path, "review_pilot", "pilot-001")["ready"]
    history["episodes"][0]["status"] = "scheduled"
    save_history(data, history)
    assert not assess(tmp_path, "review_pilot", "pilot-001")["ready"]


def test_hash_tampering_stops_build(tmp_path):
    data, _ = setup_catalog(tmp_path)
    (data / "snapshots/source.txt").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="Fuente editada"):
        assess(tmp_path, "daily", "next")


def test_duplicate_claim_with_new_id_is_rejected(tmp_path):
    data, history = setup_catalog(tmp_path)
    history["claims"] = [{"digest": hashlib.sha256(b"unique claim number 0").hexdigest(),
                          "episode": "old"}]
    save_history(data, history)
    with pytest.raises(ValueError, match="Afirmación repetida"):
        assess(tmp_path, "daily", "next")
