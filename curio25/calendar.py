"""A read-only 30-day scheduling preview; never authorizes uploading.

The timetable is calculated in the destination timezone so summer/winter
offset changes don't move the public release hour. It only allocates unused
facts that already passed the audited production catalogue.
"""
from __future__ import annotations
import argparse
from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from .coverage import forecast, read_json
from .queue import ready_batches


def local_datetime(day, config):
    if not isinstance(day,date) or isinstance(day,datetime):
        raise TypeError("Se espera una fecha local")
    zone=ZoneInfo(config["timezone"])
    parts=config["publish_hour"].split(":")
    if len(parts)!=2 or any(not p.isdigit() or len(p)!=2 for p in parts):
        raise ValueError("Hora de publicación inválida: HH:MM")
    hour,minute=map(int,parts)
    target=datetime.combine(day,time(hour=hour,minute=minute),zone)
    returned=target.astimezone(timezone.utc).astimezone(zone)
    if returned.replace(tzinfo=None)!=target.replace(tzinfo=None):
        raise ValueError("Hora local inexistente por cambio de horario")
    if returned.fold!=target.fold:
        raise ValueError("Hora local ambigua por cambio de horario")
    return target


def plan(root, first_day=None, days=30):
    root=Path(root)
    if not 1<=days<=60:
        raise ValueError("Se permiten planes de 1 a 60 días")
    config=read_json(root/"config.json")
    zone=ZoneInfo(config["timezone"])
    today=datetime.now(timezone.utc).astimezone(zone).date()
    first_day=first_day or today+timedelta(days=1)
    if not isinstance(first_day,date):
        first_day=date.fromisoformat(first_day)

    report=forecast(root,today=first_day)
    fact_batches=[]
    history=read_json(root/"data/history.json")
    if report["catalogue_integrity_ok"]:
        facts=read_json(root/"data/facts.json")
        used={f["id"] for f in history.get("used_facts",[])}
        past={f["digest"] for f in history.get("claims",[])}
        fact_batches=ready_batches(facts,used,past)

    episodes={e["id"]:e for e in history.get("episodes",[])}
    idx=0
    slots=[]
    for shift in range(days):
        day=first_day+timedelta(days=shift)
        local=local_datetime(day,config)
        ident="daily-"+day.isoformat()
        rec=episodes.get(ident)
        slot={
            "episode_id": ident, "date":day.isoformat(),
            "local":local.isoformat(),
            "utc":local.astimezone(timezone.utc).isoformat(),
            "youtube_video_id": None,
            "verified_on_youtube":False,
            "publication_authorized":False,
        }
        if rec is not None:
            slot["status"]="recorded_"+rec["status"]+"_not_youtube_verified"
            slot["youtube_video_id"]=rec.get("video_id")
        elif idx<len(fact_batches):
            batch=fact_batches[idx]
            idx+=1
            ids=[f["id"] for f in batch]
            slot.update(
                status="approved_facts_available_for_render",
                topic=batch[0].get("episode_topic") or "sistema solar",
                fact_count=25,
                id_digest=hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()
            )
        else:
            slot["status"]="missing_approved_facts"
        slots.append(slot)
    return {
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "timezone":str(zone),
        "local_publish_hour":config["publish_hour"],
        "days":days,
        "first_day":first_day.isoformat(),
        "publication_enabled":config.get("publication_enabled") is True,
        "auto_upload_enabled":False,
        "youtube_verified_public_uploads":None,
        "unassigned_approved_batches":len(fact_batches)-idx,
        "slots":slots,
        "warning":"Calendario SOLO informativo. No acredita permisos, vídeos renderizados ni subidas a YouTube.",
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,default=Path("."))
    parser.add_argument("--out",type=Path,default=Path("build/annual-coverage/calendar.json"))
    parser.add_argument("--start",type=date.fromisoformat,default=None)
    parser.add_argument("--days",type=int,default=30)
    args=parser.parse_args()
    document=plan(args.root,args.start,args.days)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(document,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    states={}
    for slot in document["slots"]:
        states[slot["status"]]=states.get(slot["status"],0)+1
    print(json.dumps({"days":document["days"],"statuses":states},ensure_ascii=False))


if __name__=="__main__":
    main()
