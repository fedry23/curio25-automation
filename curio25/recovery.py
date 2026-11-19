"""Durable, render-only reservations. Never start or retry YouTube uploads."""
import argparse
import json
from pathlib import Path
from .state import connect, restore, reserve, export_history, production_episode
from .preflight import assess
from .queue import next_batch
from .editorial import audit


def choose_episode(root, requested):
    if not production_episode(requested):
        raise ValueError('Identificador diario inválido')
    history = json.loads((Path(root)/'data/history.json').read_text(encoding='utf-8'))
    records = history['episodes']
    if any(e['status']=='uploading' for e in records):
        raise ValueError('Subida incierta: no reintentar ni generar otro episodio')
    pending = [e for e in records if e['status']=='reserved']
    if not pending:
        return requested
    if len(pending)!=1:
        raise ValueError('Varias reservas pendientes: conciliar antes de continuar')
    record = pending[0]
    ident = record['id']
    if not production_episode(ident) or ident>requested or record.get('video_id') or record.get('sha'):
        raise ValueError('Reserva no apta para recuperación automática')
    return ident


def prepare(root, episode):
    """A durable reservation before video rendering. Restart reuses exactly it."""
    root = Path(root)
    if choose_episode(root, episode)!=episode:
        raise ValueError('Recuperar primero la reserva anterior')
    report = assess(root, 'daily', episode)
    if not report['ready']:
        raise ValueError(report['code']+': '+report['message'])
    audit(root)
    db = connect(root/'data/history.sqlite')
    try:
        restore(db,root/'data/history.json')
        db.execute('BEGIN IMMEDIATE')
        try:
            if db.execute("SELECT 1 FROM episodes WHERE status='uploading'").fetchone():
                raise ValueError('Subida incierta en SQLite')
            existing = db.execute('SELECT status FROM episodes WHERE id=?',(episode,)).fetchone()
            if existing:
                if existing[0]!='reserved':
                    raise ValueError('Episodio ya renderizado o enviado')
                ids = [r[0] for r in db.execute('SELECT fact_id FROM used WHERE episode=?',(episode,))]
                if len(ids)!=25:
                    raise ValueError('Reserva incompleta')
                db.commit()
            else:
                facts = json.loads((root/'data/facts.json').read_text(encoding='utf-8'))
                used = {r[0] for r in db.execute('SELECT fact_id FROM used')}
                claims = {r[0] for r in db.execute('SELECT digest FROM claims')}
                batch = next_batch(facts,used,claims)
                if len(batch)!=25:
                    raise ValueError('No hay 25 datos aprobados')
                reserve(db,episode,batch)
                ids = [f['id'] for f in batch]
                db.commit()
        except Exception:
            db.rollback()
            raise
        export_history(db,root/'data/history.json')
        return {'episode':episode,'fact_count':len(ids),'status':'reserved','publication_attempted':False}
    finally:
        db.close()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=('choose','prepare'))
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--episode',required=True)
    a=p.parse_args()
    if a.command=='choose':
        print(choose_episode(a.root,a.episode))
    else:
        print(json.dumps(prepare(a.root,a.episode),ensure_ascii=False))


if __name__=='__main__':
    main()
