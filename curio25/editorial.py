"""Offline consistency audit for Curio25's versioned editorial catalogue.

This verifies integrity/provenance records, not that real-world claims are true.
Reviewers must still check original sources and image-rights statements.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

# Only licenses whose terms may permit commercial use. Image-specific restrictions
# still require actual editorial review; this list is never proof of permission.
COMMERCIAL_LICENSES = {
    "cc0", "pd", "public domain", "cc-by-4.0", "cc-by-3.0",
    "cc-by-sa-4.0", "cc-by-sa-3.0",
}


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _checksum(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _claim_hash(claim: str):
    return hashlib.sha256(" ".join(claim.lower().split()).encode()).hexdigest()


def _check_url(url: str):
    return isinstance(url, str) and urlsplit(url).scheme == "https" and bool(urlsplit(url).hostname)


def audit(root: Path):
    """Scan every reviewed fact and asset. Raise on the first unsafe inconsistency.

    Facts in data/facts.json may only be marked 'verified' after a source review.
    Pending drafts belong in a separate staging file, not the production catalogue.
    """
    root = Path(root)
    data = root / "data"
    facts = _json(data / "facts.json")
    history = _json(data / "history.json")
    snapshots = _json(data / "source_audit.json")
    assets = _json(data / "media/assets.json")

    if not isinstance(facts, list) or not isinstance(snapshots, list) or not isinstance(assets, list):
        raise ValueError("Catálogo, auditorías y recursos deben ser listas")
    if not isinstance(history, dict):
        raise ValueError("Historial inválido")
    previous_ids = {row["id"] for row in history["used_facts"]}
    previous_claims = {row["digest"] for row in history.get("claims", [])}
    source_by_url = {}
    for source in snapshots:
        url = source.get("url")
        if not _check_url(url) or url in source_by_url:
            raise ValueError("URL de fuente inválida o duplicada")
        path = root / source.get("path", "")
        expected_dir = (data / "snapshots").resolve()
        if not path.resolve().is_relative_to(expected_dir):
            raise ValueError("Captura de fuente fuera de data/snapshots")
        if not path.is_file() or _checksum(path) != source.get("sha256"):
            raise ValueError("Captura de fuente ausente o modificada: " + url)
        source_by_url[url] = (source, path)

    by_fact = {}
    by_body = {}
    for record in assets:
        if record.get("fact_id"):
            if record["fact_id"] in by_fact:
                raise ValueError("Recurso duplicado por fact_id: " + record["fact_id"])
            by_fact[record["fact_id"]] = record
        if record.get("body"):
            if record["body"] in by_body:
                raise ValueError("Recurso duplicado por body: " + record["body"])
            by_body[record["body"]] = record

    seen_ids = set()
    seen_claims = set()
    new_count = 0
    topics = {}
    for fact in facts:
        fid = fact.get("id")
        if not isinstance(fid, str) or not fid or fid in seen_ids:
            raise ValueError("ID de dato duplicado o inválido")
        seen_ids.add(fid)
        if fact.get("review_status") != "verified":
            raise ValueError("Dato sin revisión en catálogo de producción: " + fid)
        claim, narration, title = (fact.get(name) for name in ("claim", "narration", "title"))
        if not all(isinstance(t, str) and t.strip() for t in (claim, narration, title)):
            raise ValueError("Faltan título, afirmación o narración: " + fid)
        chash = _claim_hash(claim)
        if chash in seen_claims:
            raise ValueError("Afirmación duplicada en catálogo: " + fid)
        seen_claims.add(chash)

        if not _check_url(fact.get("source_url")) or fact["source_url"] not in source_by_url:
            raise ValueError("Falta enlace de fuente archivada: " + fid)
        source, path = source_by_url[fact["source_url"]]
        if fact.get("source_snapshot_sha256") != source["sha256"]:
            raise ValueError("Hash de fuente inconsistente: " + fid)
        query = fact.get("evidence_query")
        if not isinstance(query, str) or not query.strip() or query.casefold() not in path.read_text(encoding="utf-8").casefold():
            raise ValueError("Evidencia no encontrada en la captura: " + fid)
        if not fact.get("evidence_excerpt"):
            raise ValueError("Falta extracto de evidencia: " + fid)

        media = by_fact.get(fid) or by_body.get(fact.get("body"))
        if not media or media.get("review_status") != "approved":
            raise ValueError("Falta imagen aprobada: " + fid)
        if media.get("license") not in COMMERCIAL_LICENSES:
            raise ValueError("Imagen sin licencia comercial reconocida: " + fid)
        for name in ("author", "source", "display_credit", "license_short", "file", "sha256"):
            if not media.get(name):
                raise ValueError(f"Falta {name} en imagen: " + fid)
        if not _check_url(media["source"]):
            raise ValueError("La imagen no tiene URL de origen HTTPS: " + fid)
        asset_path = data / "media" / media["file"]
        if not asset_path.resolve().is_relative_to((data / "media").resolve()):
            raise ValueError("Archivo visual fuera del inventario: " + fid)
        if not asset_path.is_file() or _checksum(asset_path) != media["sha256"]:
            raise ValueError("Imagen ausente o modificada: " + fid)

        is_new = fid not in previous_ids
        if is_new:
            new_count += 1
            if chash in previous_claims:
                raise ValueError("Se repite una afirmación ya consumida: " + fid)
            if media.get("fact_id") != fid:
                raise ValueError("Cada dato nuevo necesita una imagen vinculada por fact_id: " + fid)
            topic = fact.get("episode_topic")
            if not isinstance(topic, str) or not topic.strip():
                raise ValueError("Dato nuevo sin episode_topic: " + fid)
            topics[topic] = topics.get(topic, 0) + 1
            if len(narration.split()) < 20 or len(narration.split()) > 65:
                raise ValueError("Narración nueva fuera de rango editorial (20-65 palabras): " + fid)
            if not isinstance(fact.get("graphic"), dict):
                raise ValueError("Falta gráfico específico: " + fid)
    return {
        "ok": True,
        "facts": len(facts),
        "previously_used": len(seen_ids & previous_ids),
        "new_reviewed": new_count,
        "complete_new_batches": new_count // 25,
        "topics": topics,
        "note": "La integridad no certifica hechos ni licencias; requieren revisión editorial independiente.",
    }


def main():
    parser = argparse.ArgumentParser(description="Auditoría editorial offline, sin publicar")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
