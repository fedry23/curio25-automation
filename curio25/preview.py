"""Unpublished 25-fact Curio25 VIDEO PREVIEW from quarantined editorial material.

NO production approval, no upload, no changes to the production fact catalogue,
approved media inventory or history. A conspicuous watermark is compulsory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from .sources import ALLOWED

TOPIC = "curiosidades del mundo"
LABELS = [
    ("Ballena azul", "Un corazón de ~180 kg"),
    ("Branquias: dos corazones", "Cuerpo: un corazón"),
    ("Migración oceánica", "Cerca de 5.955 km por tramo"),
    ("Algunos rapes abisales", "Fusión reproductiva"),
    ("Canto de jorobadas", "Cortejo y territorio"),
    ("Agua oceánica", "Resto del agua terrestre"),
    ("La luz se debilita", "A partir de ~200 metros"),
    ("Temperatura media", "Océano profundo: ~4 °C"),
    ("Bioluminiscentes", "Otros pelágicos"),
    ("Brillo azulado", "Luz que viaja bajo el agua"),
    ("Washington", "Baltimore · 1844"),
    ("Patente del teléfono", "7 de marzo de 1876"),
    ("Bell y Watson", "La llamada de 1876"),
    ("Primer vuelo", "12 s · 120 pies"),
    ("Nueva York", "San Francisco · 1915"),
    ("Espuma viscoelástica", "Investigación aeroespacial"),
    ("Sensor CMOS", "Cámaras de hoy"),
    ("Lentes resistentes", "Recubrimientos espaciales"),
    ("Comunicación manos libres", "Astronautas y auriculares"),
    ("Comida espacial", "Seguridad alimentaria"),
    ("Fenómenos hidrotermales", "Géiseres incluidos"),
    ("Yellowstone", "Más de la mitad de los géiseres"),
    ("Bosques antiguos", "Árboles petrificados"),
    ("Volumen bajo · galones", "Volumen alto · galones"),
    ("Rocas antiquísimas", "Cañón relativamente reciente"),
]
NUMERICAL = {
    2: (2,1),
    6: (97,3),
    9: (80,20),
    21: (10000,500),
    24: (3700,8400),
}


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare(root, episode):
    """Fail closed on missing source / checksum / image; never mark verified."""
    root=Path(root)
    candidate=_read(root/"data/candidates"/(episode+".json"))
    research=root/"data/candidates"/("research-"+episode)
    media_root=root/"data/candidates"/("media-"+episode)
    evidence=_read(research/"source_report.json")
    pictures=_read(media_root/"media_report.json")
    facts=candidate.get("facts", [])
    if (len(facts)!=25 or len({f["id"] for f in facts})!=25
        or candidate.get("production_ready") is True
        or evidence.get("production_ready") is True
        or pictures.get("production_ready") is True):
        raise ValueError("Borrador exige exactamente 25 candidatos separados del catálogo aprobado")
    if evidence.get("sources_archived")!=len(evidence.get("sources", [])):
        raise ValueError("Faltan capturas de fuente")
    if pictures.get("photos_downloaded")!=25:
        raise ValueError("Faltan imágenes de revisión")
    urls={s["url"]:s for s in evidence["sources"]}
    findings={f["fact_id"]:f for f in evidence["facts"]}
    records={r["fact_id"]:r for r in pictures["records"]}
    result=[]
    for ix,f in enumerate(facts):
        fid=f["id"]
        s=urls.get(f["source_url"])
        e=findings.get(fid)
        r=records.get(fid)
        if not s or not e or not r or s["status"]!="archived_unreviewed" or not e["evidence_found"]:
            raise ValueError("Fuente o evidencia incompleta: "+fid)
        if e["source_url"]!=f["source_url"] or e["source_sha256"]!=s["sha256"]:
            raise ValueError("Desajuste entre afirmación y fuente: "+fid)
        snapshot=(research/s["path"]).resolve()
        if not snapshot.is_relative_to((research/"snapshots").resolve()):
            raise ValueError("Ruta de fuente sospechosa: "+fid)
        if hashlib.sha256(snapshot.read_bytes()).hexdigest()!=s["sha256"]:
            raise ValueError("SHA256 de fuente incorrecto: "+fid)
        document=snapshot.read_text(encoding="utf-8").casefold()
        if f["evidence_query"].casefold() not in document:
            raise ValueError("Evidencia textual desaparecida: "+fid)
        if r.get("status")!="downloaded_unreviewed" or r.get("license") not in ALLOWED:
            raise ValueError("Foto de prueba ausente o no apta: "+fid)
        if not all(r.get(k) for k in ("file","source","author","license_short","sha256")):
            raise ValueError("Metadatos de imagen incompletos: "+fid)
        path=(media_root/r["file"]).resolve()
        if not path.is_relative_to((media_root/"images").resolve()):
            raise ValueError("Imagen fuera de cuarentena: "+fid)
        if hashlib.sha256(path.read_bytes()).hexdigest()!=r["sha256"]:
            raise ValueError("Foto editada o SHA256 erróneo: "+fid)
        x,y=LABELS[ix]
        values=NUMERICAL.get(ix+1,(1,1))
        graphic={"kind":"compare" if ix+1 in NUMERICAL else "layers",
                 "values":list(values),"labels":[x,y]}
        # The same renderer is used, but the historical + production state is
        # never touched: prepare() only returns quarantine paths for preview.
        record=dict(r,file="../candidates/media-"+episode+"/"+r["file"])
        record["display_credit"]=str(r["author"])+" · "+str(r["license_short"])
        result.append(dict(
            id=fid,title=f["title"],claim=f["claim"],narration=f["narration"],
            source_url=f["source_url"],source_snapshot_sha256=s["sha256"],
            evidence_query=f["evidence_query"],
            evidence_excerpt=f["evidence_query"],
            episode_topic=TOPIC,
            episode_title="25 curiosidades increíbles del mundo | Curio25",
            body=f["category"],graphic=graphic,
            review_status="pending",
            media_path=str(path),media_record=record,
            media_credit=record["display_credit"],
            draft_watermark=True,
        ))
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--episode",default="2026-11-17")
    p.add_argument("--out",default="build/preview-2026-11-17")
    p.add_argument("--preflight-only",action="store_true")
    args=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    out=(root/args.out).resolve()
    if not out.is_relative_to((root/"build").resolve()):
        raise ValueError("El borrador solo puede guardarse dentro de build/")
    config=_read(root/"config.json")
    if config.get("publication_enabled"):
        raise PermissionError("Borrador bloqueado cuando publicación real está activada")
    facts=prepare(root,args.episode)
    preflight={"episode":args.episode,"candidate_count":len(facts),
               "rights_approved":False,"facts_approved":False,
               "publication_allowed":False,"source":"quarantine"}
    out.mkdir(parents=True,exist_ok=True)
    (out/"PREVIEW-NO-PUBLICAR.json").write_text(
        json.dumps(preflight,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(preflight,ensure_ascii=False),flush=True)
    if args.preflight_only:
        return
    if (out/"episode.mp4").exists():
        raise ValueError("El borrador anterior ya existe: no sobrescribir")
    from .render import render
    from PIL import Image,ImageDraw,ImageFont
    report=render(root,out,facts,config)
    metadata=_read(out/"metadata.json")
    metadata.update(preview_only=True,publication_allowed=False,
                    editorial_status="PENDIENTE DE REVISIÓN",
                    rights_approved=False)
    banner="BORRADOR - NO PUBLICAR. DATOS E IMÁGENES EN REVISIÓN.\n\n"
    metadata["description"]=banner+metadata["description"]
    (out/"metadata.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n")
    (out/"description.txt").write_text(metadata["description"],encoding="utf-8")
    with Image.open(out/"thumbnail.jpg") as im:
        im=im.convert("RGB")
        d=ImageDraw.Draw(im)
        d.rectangle((0,0,1280,94),fill="#9c2637")
        d.text((640,47),"BORRADOR - NO PUBLICAR",fill="white",
               anchor="mm",font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",38))
        im.save(out/"thumbnail.jpg")
    print(json.dumps({"preview_created":True,"duration":report["duration"],
                      "sha256":report["sha256"],"rights_approved":False},ensure_ascii=False))


if __name__=="__main__":
    main()
