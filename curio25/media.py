"""Explicit, reviewed commercial-rights media inventory, linked to every fact."""
import json
from pathlib import Path
from .state import sha
from .sources import ALLOWED

def attach_media(root,facts):
    root=Path(root); path=root/'data/media/assets.json'
    if not path.exists(): raise ValueError('Falta inventario visual revisado: ejecutar scripts/download_media.py')
    records=json.loads(path.read_text()); mapped={r['body']:r for r in records}
    enriched=[]
    for f in facts:
        record=mapped.get(f['body'])
        if not record or record.get('review_status')!='approved': raise ValueError('Foto sin revisión para '+f['body'])
        if record.get('license') not in ALLOWED or not record.get('author') or not record.get('source'): raise ValueError('Faltan derechos/autor/fuente')
        asset=(root/'data/media'/record['file']).resolve()
        if not asset.is_relative_to((root/'data/media').resolve()): raise ValueError('Ruta visual fuera del inventario')
        if not asset.is_file() or sha(asset)!=record['sha256']: raise ValueError('Foto ausente o modificada: '+f['body'])
        enriched.append(dict(f,media_path=str(asset),media_credit=record['display_credit'],media_record=record))
    return enriched

def credits(records):
    unique={r['source']:r for r in records}
    return '\n'.join(f"{r['body']}: {r['author']} · {r['license_short']}\n{r['source']}" for r in unique.values())
