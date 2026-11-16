"""Editorial catalogue regression tests; synthetic fixtures are not published."""
import hashlib
import json

import pytest
from curio25.editorial import audit


def _digest(blob):
    return hashlib.sha256(blob).hexdigest()


def _fixture(tmp_path, *, used=False):
    data = tmp_path / "data"
    (data / "media").mkdir(parents=True)
    (data / "snapshots").mkdir()
    proof = b"Primary scientific fact and explicit number: 42"
    photo = b"sample-image-bytes"
    (data / "snapshots" / "source.txt").write_bytes(proof)
    (data / "media" / "picture.png").write_bytes(photo)
    fact = {
        "id": "science-001", "title": "Dato concreto", "claim": "Un hecho comprobado",
        "narration": "Este dato explica un fenómeno curioso de forma original con una descripción "
                     "comprensible para distintos públicos y un humor muy ligero que no altera los hechos.",
        "source_url": "https://example.org/research",
        "source_snapshot_sha256": _digest(proof),
        "review_status": "verified", "evidence_excerpt": "scientific fact",
        "evidence_query": "scientific fact", "episode_topic": "curiosidades del mundo",
        "body": "research", "graphic": {"kind": "compare", "values": [42, 1], "labels": ["Dato", "Referencia"]},
    }
    source = {
        "url": fact["source_url"], "path": "data/snapshots/source.txt",
        "sha256": _digest(proof),
    }
    record = {
        "fact_id": fact["id"], "file": "picture.png", "sha256": _digest(photo),
        "author": "Example Author", "source": "https://example.org/image",
        "display_credit": "Example Author · CC0", "license_short": "CC0",
        "license": "cc0", "review_status": "approved",
    }
    history = {"used_facts": [], "claims": [], "episodes": []}
    if used:
        history["used_facts"].append({"id": fact["id"], "episode": "pilot"})
        history["claims"].append({"digest": _digest(fact["claim"].lower().encode()), "episode": "pilot"})
    def write():
        (data / "facts.json").write_text(json.dumps([fact]))
        (data / "source_audit.json").write_text(json.dumps([source]))
        (data / "media/assets.json").write_text(json.dumps([record]))
        (data / "history.json").write_text(json.dumps(history))
    write()
    return data, fact, record, write


def test_real_project_catalogue_is_structurally_audited():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    report = audit(root)
    assert report["ok"] and report["facts"] >= 25
    assert report["complete_new_batches"] == report["new_reviewed"] // 25


def test_approved_new_fact_passes(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    assert audit(tmp_path)["new_reviewed"] == 1


def test_reviewer_cannot_mark_pending_as_production(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    fact["review_status"] = "pending"
    write()
    with pytest.raises(ValueError, match="sin revisión"):
        audit(tmp_path)


def test_tampered_evidence_stops_build(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    (data / "snapshots/source.txt").write_text("An unrelated claim")
    with pytest.raises(ValueError, match="Captura de fuente ausente o modificada"):
        audit(tmp_path)


def test_unapproved_or_noncommercial_image_is_blocked(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    rec["license"] = "cc-by-nc"
    write()
    with pytest.raises(ValueError, match="licencia comercial"):
        audit(tmp_path)


def test_image_must_match_sha(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    (data / "media/picture.png").write_bytes(b"changed")
    with pytest.raises(ValueError, match="Imagen ausente o modificada"):
        audit(tmp_path)


def test_new_fact_must_have_own_media_id(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    rec.pop("fact_id")
    rec["body"] = fact["body"]
    write()
    with pytest.raises(ValueError, match="vinculada por fact_id"):
        audit(tmp_path)


def test_new_fact_requires_topic(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    fact.pop("episode_topic")
    write()
    with pytest.raises(ValueError, match="episode_topic"):
        audit(tmp_path)


def test_previous_claim_new_id_must_be_rejected(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    history = json.loads((data / "history.json").read_text())
    history["claims"] = [{"digest": _digest(fact["claim"].lower().encode()), "episode": "earlier"}]
    (data / "history.json").write_text(json.dumps(history))
    with pytest.raises(ValueError, match="repite una afirmación"):
        audit(tmp_path)


def test_legitimate_used_fact_does_not_require_new_topic(tmp_path):
    data, fact, rec, write = _fixture(tmp_path, used=True)
    fact.pop("episode_topic")
    rec.pop("fact_id")
    rec["body"] = fact["body"]
    write()
    assert audit(tmp_path)["previously_used"] == 1


def test_directory_escape_is_blocked(tmp_path):
    data, fact, rec, write = _fixture(tmp_path)
    rec["file"] = "../../outside.png"
    write()
    with pytest.raises(ValueError, match="fuera del inventario"):
        audit(tmp_path)
