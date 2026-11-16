"""Explicit, reviewed commercial-rights media inventory, linked to every fact."""
import json
from pathlib import Path
from .state import sha
from .sources import ALLOWED

def attach_media(root,facts):
    root=Path(root); path=root/'data/media/assets.json'
    if not path.exists(): raise ValueError('Falta inventario visual revisado: ejecutar scripts/download_media.py')
    records=json.loads(path.read_text()); by_fact={r['fact_id']:r for r in records if r.get('fact_id')}; by_body={r.get('body',r.get('fact_id','recurso')):r for r in records if r.get('body')}
    enriched=[]
    for f in facts:
        record=by_fact.get(f.get('id')) or by_body.get(f.get('body'))
        if not record or record.get('review_status')!='approved': raise ValueError('Foto sin revisión para '+str(f.get('id') or f.get('body')))
        if record.get('license') not in ALLOWED or not record.get('author') or not record.get('source'): raise ValueError('Faltan derechos/autor/fuente')
        asset=(root/'data/media'/record['file']).resolve()
        if not asset.is_relative_to((root/'data/media').resolve()): raise ValueError('Ruta visual fuera del inventario')
        if not asset.is_file() or sha(asset)!=record['sha256']: raise ValueError('Foto ausente o modificada: '+str(f.get('id') or f.get('body')))
        enriched.append(dict(f,media_path=str(asset),media_credit=record['display_credit'],media_record=record))
    return enriched

def credits(records):
    unique={r['source']:r for r in records}
    return '\n'.join(f"{r.get('body') or r.get('fact_id','recurso')}: {r['author']} · {r['license_short']}\n{r['source']}" for r in unique.values())
