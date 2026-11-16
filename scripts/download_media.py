"""Restore approved photographic assets without silently approving upstream changes."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from curio25.sources import session
root=Path(__file__).resolve().parents[1]/'data/media'
for record in json.loads((root/'assets.json').read_text()):
    target=root/record['file']
    if not target.exists():
        r=session().get(record['download_url'],timeout=90); r.raise_for_status()
        if hashlib.sha256(r.content).hexdigest()!=record['sha256']: raise ValueError('El recurso ha cambiado; requiere revisión: '+record['body'])
        target.write_bytes(r.content)
    if hashlib.sha256(target.read_bytes()).hexdigest()!=record['sha256']: raise ValueError('Foto modificada: '+record['body'])
print('Fotografías comerciales aprobadas e íntegras')
