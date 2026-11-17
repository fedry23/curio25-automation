"""Zero-dependency safety preflight for Curio25 daily production."""
import argparse
import hashlib
import json
import os
from pathlib import Path
from .queue import next_batch


def digest(fact):
    return hashlib.sha256(" ".join(fact["claim"].lower().split()).encode()).hexdigest()


def assess(root, mode, episode):
    root = Path(root)
    if mode not in ("daily", "review_pilot"):
        raise ValueError("Modo desconocido")
    history = json.loads((root / "data/history.json").read_text(encoding="utf-8"))
    facts = json.loads((root / "data/facts.json").read_text(encoding="utf-8"))
    by_id = {f["id"]: f for f in facts}
    if len(by_id) != len(facts):
        raise ValueError("ID duplicado en el catálogo")
    episodes = {e["id"]: e for e in history["episodes"]}
    used = {row["id"] for row in history["used_facts"]}

    def result(code, message, ready=False, available=0):
        return dict(ready=ready, code=code, message=message, available=available)

    if mode == "review_pilot":
        record = episodes.get(episode)
        if record and record["status"] in ("reserved", "rendered"):
            return result("PILOT_REVIEW", "Revisión del piloto sin volver a consumir datos", True)
        return result("PILOT_UNAVAILABLE", "Piloto inexistente o con subida iniciada")

    uncertain = sorted(e["id"] for e in episodes.values() if
        e["status"] == "uploading" or
        (e["status"] == "reserved" and e["id"] != episode))
    if uncertain:
        return result("RECONCILIATION_REQUIRED",
                      "Conciliar reserva/subida pendiente: " + ", ".join(uncertain))
    existing = episodes.get(episode)
    if existing and existing["status"] != "reserved":
        return result("EPISODE_EXISTS", "Episodio existente; no sobrescribir")

    if existing:
        ids = {row["id"] for row in history["used_facts"] if row["episode"] == episode}
        if len(ids) != 25 or not ids.issubset(by_id):
            raise ValueError("Reserva incompleta o catálogo modificado")
        selected = [f for f in facts if f["id"] in ids]
    else:
        eligible = [f for f in facts if f["id"] not in used
                    and f.get("review_status") == "verified"]
        recorded = {row["digest"] for row in history.get("claims", [])}
        selected = next_batch(facts, used, recorded)
        if len(selected) < 25:
            return result("CATALOG_EXHAUSTED",
                          f"Solo quedan {len(eligible)} datos verificados; hacen falta 25. "
                          "No se renderiza ni publica.", available=len(eligible))

    if len({digest(f) for f in selected}) != 25:
        raise ValueError("Hay dos afirmaciones idénticas")
    if any(f.get("review_status") != "verified" for f in selected):
        raise ValueError("La reserva contiene datos no revisados")

    # Match the renderer's evidence checks before downloading models or packages.
    audit = {a["url"]: a for a in json.loads(
        (root / "data/source_audit.json").read_text(encoding="utf-8"))}
    for f in selected:
        entry = audit.get(f["source_url"])
        if entry is None:
            raise ValueError("Falta auditoría: " + f["id"])
        path = root / entry["path"]
        if not path.is_file():
            raise ValueError("Falta captura de fuente: " + f["id"])
        content = path.read_bytes()
        hashed = hashlib.sha256(content).hexdigest()
        if hashed != entry["sha256"] or hashed != f["source_snapshot_sha256"]:
            raise ValueError("Fuente editada o hash incorrecto: " + f["id"])
        if f["evidence_query"].lower() not in content.decode("utf-8").lower():
            raise ValueError("Evidencia no encontrada: " + f["id"])

    return result("RESUME" if existing else "READY",
                  "25 datos verificados y fuentes intactas", True, 25)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--mode", choices=("daily", "review_pilot"), default="daily")
    p.add_argument("--episode", required=True)
    args = p.parse_args()
    report = assess(args.root, args.mode, args.episode)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fd:
            fd.write("ready=" + str(report["ready"]).lower() + "\n")
            fd.write("reason=" + report["code"] + "\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fd:
            fd.write("### Curio25: " + report["code"] + "\n\n"
                     + report["message"] + "\n\n"
                     "La publicación en YouTube permanece desactivada.\n")
    if not report["ready"]:
        print("::warning title=Curio25 " + report["code"] + "::" + report["message"])


if __name__ == "__main__":
    main()
