import hashlib,json,sqlite3,os,tempfile,re
from datetime import date
from pathlib import Path

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def connect(path):
    db=sqlite3.connect(path,timeout=30)
    db.executescript('''CREATE TABLE IF NOT EXISTS episodes(id TEXT PRIMARY KEY,status TEXT NOT NULL,sha TEXT,video_id TEXT,upload_uri TEXT);
    CREATE TABLE IF NOT EXISTS used(fact_id TEXT PRIMARY KEY,episode TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS claims(digest TEXT PRIMARY KEY,episode TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS catalog(fact_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS episode_sources(episode TEXT,fact_id TEXT,url TEXT,snapshot_sha256 TEXT,narration_sha256 TEXT,PRIMARY KEY(episode,fact_id));
    CREATE TABLE IF NOT EXISTS episode_profiles(episode TEXT PRIMARY KEY,profile TEXT NOT NULL,decision TEXT NOT NULL);'''); return db

def claim_hash(f): return hashlib.sha256(' '.join(f['claim'].lower().split()).encode()).hexdigest()
def reserve(db,episode,facts):
    if len(facts)!=25 or len({f['id'] for f in facts})!=25 or len({claim_hash(f) for f in facts})!=25: raise ValueError('Se necesitan exactamente 25 datos distintos')
    with db:
        db.execute('INSERT INTO episodes(id,status) VALUES (?,?)',(episode,'reserved'))
        db.executemany('INSERT INTO used VALUES (?,?)',[(f['id'],episode) for f in facts])
        db.executemany('INSERT INTO claims VALUES (?,?)',[(claim_hash(f),episode) for f in facts])
        for f in facts:
            db.execute('INSERT OR REPLACE INTO catalog VALUES (?,?)',(f['id'],json.dumps(f,ensure_ascii=False)))
            db.execute('INSERT INTO episode_sources VALUES (?,?,?,?,?)',(episode,f['id'],f['source_url'],f['source_snapshot_sha256'],hashlib.sha256(f['narration'].encode()).hexdigest()))

def export_history(db,path):
    data={'episodes':[dict(zip(['id','status','sha','video_id'],r)) for r in db.execute('SELECT id,status,sha,video_id FROM episodes')], 'used_facts':[dict(zip(['id','episode'],r)) for r in db.execute('SELECT * FROM used')], 'claims':[dict(zip(['digest','episode'],r)) for r in db.execute('SELECT * FROM claims')]}
    data['sources']=[dict(zip(['episode','fact_id','url','snapshot_sha256','narration_sha256'],r)) for r in db.execute('SELECT * FROM episode_sources')]
    data['episode_profiles']=[dict(zip(['episode','profile','decision'],r)) for r in db.execute('SELECT episode,profile,decision FROM episode_profiles ORDER BY episode')]
    # Publish a complete JSON snapshot or leave the previous version untouched.
    # A cancelled runner must not leave a half-written history file.
    dest=Path(path)
    fd,tmp=tempfile.mkstemp(prefix='.'+dest.name+'.',suffix='.tmp',dir=dest.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as output:
            output.write(json.dumps(data,indent=2)+'\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp,dest)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def restore(db,path):
    if not Path(path).exists(): return
    data=json.loads(Path(path).read_text())
    with db:
        rank={'reserved':0,'rendered':1,'uploading':2,'scheduled':3,'published':4}
        for e in data['episodes']:
            current=db.execute('SELECT status,sha,video_id FROM episodes WHERE id=?',(e['id'],)).fetchone()
            if e['status'] not in rank or (current and current[0] not in rank): raise ValueError('Estado desconocido; conciliar historial')
            if current:
                if current[1] and e['sha'] and current[1]!=e['sha']: raise ValueError('Hashes de episodio en conflicto; conciliar historial')
                if current[2] and e['video_id'] and current[2]!=e['video_id']: raise ValueError('IDs YouTube en conflicto; conciliar historial')
                if rank[e['status']]>rank[current[0]]:
                    db.execute('UPDATE episodes SET status=?,sha=?,video_id=? WHERE id=?',(e['status'],e['sha'] or current[1],e['video_id'] or current[2],e['id']))
            else: db.execute('INSERT INTO episodes(id,status,sha,video_id) VALUES (?,?,?,?)',tuple(e[k] for k in ['id','status','sha','video_id']))
        for f in data['used_facts']: db.execute('INSERT OR IGNORE INTO used VALUES (?,?)',(f['id'],f['episode']))
        for f in data.get('sources',[]): db.execute('INSERT OR IGNORE INTO episode_sources VALUES (?,?,?,?,?)',tuple(f[k] for k in ['episode','fact_id','url','snapshot_sha256','narration_sha256']))
        for f in data.get('claims',[]): db.execute('INSERT OR IGNORE INTO claims VALUES (?,?)',(f['digest'],f['episode']))
        for p in data.get('episode_profiles',[]):
            existing=db.execute('SELECT profile,decision FROM episode_profiles WHERE episode=?',(p['episode'],)).fetchone()
            pair=(p['profile'],p['decision'])
            if existing and existing!=pair: raise ValueError('Perfil de episodio en conflicto')
            db.execute('INSERT OR IGNORE INTO episode_profiles VALUES (?,?,?)',(p['episode'],*pair))

# Catalog facts remain versioned in JSON; SQLite holds production reservations and snapshots.

def finalize_render(db,episode,facts,video_sha,profile=None,decision=None):
    """Record the exact reviewed script rendered, including edits after a failed attempt."""
    reserved={r[0] for r in db.execute('SELECT fact_id FROM used WHERE episode=?',(episode,))}
    if len(facts)!=25 or {f['id'] for f in facts}!=reserved: raise ValueError('El render no coincide con la reserva')
    if any(f['review_status']!='verified' for f in facts): raise ValueError('Guion sin revisar')
    with db:
        changed=db.execute('UPDATE episodes SET status=?,sha=? WHERE id=? AND status=?',('rendered',video_sha,episode,'reserved')).rowcount
        if changed!=1: raise ValueError('Estado de render incompatible')
        if profile is not None:
            db.execute('INSERT OR REPLACE INTO episode_profiles VALUES (?,?,?)',(episode,profile,decision or 'disabled'))
        for f in facts:
            db.execute('INSERT OR REPLACE INTO catalog VALUES (?,?)',(f['id'],json.dumps(f,ensure_ascii=False)))
            db.execute('INSERT OR REPLACE INTO episode_sources VALUES (?,?,?,?,?)',(episode,f['id'],f['source_url'],f['source_snapshot_sha256'],hashlib.sha256(f['narration'].encode()).hexdigest()))

def begin_revision(db,episode):
    """Explicit editorial revision of an unpublished episode; never consumes facts again."""
    with db:
        row=db.execute('SELECT status,sha FROM episodes WHERE id=?',(episode,)).fetchone()
        if not row or row[0] not in ('reserved','rendered'): raise ValueError('Solo se revisan episodios sin subir; conciliar cualquier carga previa')
        db.execute('UPDATE episodes SET status=?,sha=NULL WHERE id=?',('reserved',episode))


def production_episode(episode):
    match = re.fullmatch(r'daily-(\d{4}-\d{2}-\d{2})', episode)
    if not match:
        return False
    try:
        date.fromisoformat(match.group(1))
    except ValueError:
        return False
    return True


def confirm_publication(db, episode, video, channel_id=None):
    """Count only dated production episodes with a processed public API result."""
    if not production_episode(episode):
        raise ValueError('Solo episodios diarios de producción')
    if channel_id is not None and video.get('snippet', {}).get('channelId') != channel_id:
        raise ValueError('Vídeo de otro canal')
    status = video.get('status', {})
    if status.get('privacyStatus') != 'public' or status.get('uploadStatus') != 'processed':
        return False
    with db:
        # Make the identity/duplicate checks and transition one writer transaction.
        if not db.in_transaction:
            db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT status,video_id FROM episodes WHERE id=?',(episode,)).fetchone()
        if not row or not row[1] or row[1] != video.get('id') or row[0] not in ('scheduled','published'):
            raise ValueError('Publicación no coincide con el historial')
        if db.execute('SELECT 1 FROM episodes WHERE video_id=? AND id<>?', (row[1],episode)).fetchone():
            raise ValueError('ID de YouTube duplicado; conciliar historial')
        db.execute("UPDATE episodes SET status='published' WHERE id=?",(episode,))
    return True


def published_count(db):
    return len({video_id for episode, video_id in db.execute(
        "SELECT id,video_id FROM episodes WHERE status='published' AND video_id IS NOT NULL")
        if production_episode(episode) and video_id})
