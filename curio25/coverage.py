"""Offline stock and annual publishing readiness, never fictional success."""
from __future__ import annotations
import argparse
import calendar
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path

from .editorial import audit
from .queue import ready_batches


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def candidate_count(root):
    found=set()
    for path in sorted((root/"data/candidates").glob("*.json")):
        try:
            doc=read_json(path)
        except (OSError, ValueError):
            continue
        if not isinstance(doc,dict) or not isinstance(doc.get("facts"),list):
            continue
        for fact in doc["facts"]:
            if isinstance(fact,dict) and fact.get("id") and fact.get("review_status")!="verified":
                found.add(fact["id"])
    return len(found)


def forecast(root, today=None, minimum_days=30):
    root=Path(root)
    today=today or datetime.now(timezone.utc).date()
    if not 1<=minimum_days<=365:
        raise ValueError("La reserva mínima debe ser entre 1 y 365 días")
    facts=read_json(root/"data/facts.json")
    history=read_json(root/"data/history.json")
    config=read_json(root/"config.json")
    used={f["id"] for f in history.get("used_facts",[])}
    past={r["digest"] for r in history.get("claims",[])}
    defect=None
    try:
        audit(root)
        batches=ready_batches(facts,used,past)
    except (ValueError,TypeError,KeyError,OSError) as exc:
        batches=[]
        defect=str(exc)[:500]

    days=len(batches)
    annual=366 if calendar.isleap(today.year) else 365
    state="BLOCKED" if defect else "CRITICAL" if days<7 else "AT_RISK" if days<minimum_days else "BUFFERED"
    return {
        "date_utc": today.isoformat(),
        "status":state,
        "catalogue_integrity_ok":defect is None,
        "catalogue_error":defect,
        "annual_goal_episodes":annual,
        "annual_goal_unique_facts":25*annual,
        "facts_per_episode":25,
        "confirmed_ready_batches":days,
        "confirmed_ready_facts":days*25,
        "unreviewed_candidate_facts":candidate_count(root),
        "used_fact_ids":len(used),
        "minimum_buffer_days":minimum_days,
        "recommended_buffer_days":60,
        "missing_facts_to_minimum_buffer":max(0,25*(minimum_days-days)),
        "weekly_replenishment_facts":175,
        "youtube_channel_connected":bool(config.get("channel_id")),
        "youtube_publication_enabled":config.get("publication_enabled") is True,
        "recorded_scheduled_uploads":sum(e.get("status")=="scheduled" for e in history.get("episodes",[])),
        "confirmed_public_uploads":None,
        "can_guarantee_annual_publications":False,
        "warning":"El informe no consulta YouTube; un borrador no es un episodio aprobado. Los cron pueden retrasarse y servicios externos fallar."
    }


def markdown(r):
    lines=[
        "## Curio25 - reserva editorial para 365 publicaciones",
        "",
        "**Fecha UTC:** "+r["date_utc"],
        "**Estado:** "+r["status"],
        "**Episodios realmente listos:** "+str(r["confirmed_ready_batches"]),
        "**Hechos aprobados en lotes de 25:** "+str(r["confirmed_ready_facts"]),
        "**Candidatos sin aprobar:** "+str(r["unreviewed_candidate_facts"]),
        "**Faltan para 30 días de reserva:** "+str(r["missing_facts_to_minimum_buffer"])+" hechos",
        "**Objetivo del año:** "+str(r["annual_goal_episodes"])+" vídeos / "+str(r["annual_goal_unique_facts"])+" datos",
        "**YouTube conectado:** "+str(r["youtube_channel_connected"]),
        "**Publicación activada:** "+str(r["youtube_publication_enabled"]),
        "**Integridad del catálogo:** "+str(r["catalogue_integrity_ok"]),
    ]
    if r["catalogue_error"]:
        lines.append("**Error de integridad:** "+r["catalogue_error"])
    lines.extend(["", "**Importante:** los candidatos pendientes no cuentan. No se verifica la publicación pública sin acceso OAuth."])
    return "  \n".join(lines)+"\n"


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--out",type=Path,default=Path("build/annual-coverage"))
    parser.add_argument("--date",type=date.fromisoformat,default=None)
    args=parser.parse_args()
    report=forecast(args.root,args.date)
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"coverage.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    summary=markdown(report)
    (args.out/"coverage.md").write_text(summary,encoding="utf-8")
    print(json.dumps({"status":report["status"],"ready_days":report["confirmed_ready_batches"],
        "candidates":report["unreviewed_candidate_facts"],"shortfall":report["missing_facts_to_minimum_buffer"]},ensure_ascii=False))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"],"a",encoding="utf-8") as handle:
            handle.write("status="+report["status"]+"\n")
            handle.write("ready_days="+str(report["confirmed_ready_batches"])+"\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as handle:
            handle.write(summary)


if __name__=="__main__":
    main()
