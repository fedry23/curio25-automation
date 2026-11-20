"""Official OAuth and resumable upload. Publication fails closed."""
import json,os
from pathlib import Path
from datetime import date,datetime,timedelta,timezone
import re
from zoneinfo import ZoneInfo
from .state import connect,restore,export_history,sha,confirm_publication,published_count,production_episode
SCOPES=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.force-ssl']

def authorize():
    from google_auth_oauthlib.flow import InstalledAppFlow
    client=os.environ.get('YOUTUBE_CLIENT_FILE')
    if not client: raise ValueError('Definir YOUTUBE_CLIENT_FILE con OAuth de aplicación de escritorio propio')
    credentials=InstalledAppFlow.from_client_secrets_file(client,SCOPES).run_local_server(port=0,access_type='offline',prompt='consent')
    target=Path(os.environ.get('YOUTUBE_TOKEN_FILE','token.json')); target.write_text(credentials.to_json()); target.chmod(0o600)

def publication_day(episode):
    """A dated episode always targets its own day, not 'tomorrow by accident'."""
    match=re.fullmatch(r"daily-(\d{4}-\d{2}-\d{2})",episode)
    return date.fromisoformat(match.group(1)) if match else None


def publish_at(config,now=None,target_date=None):
    """An exact, future 18:00 Europe/Madrid slot across DST changes.

    Existing callers without target_date keep their next-slot behavior.
    """
    now=now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("La hora actual debe incluir zona horaria")
    zone=ZoneInfo(config['timezone'])
    local=now.astimezone(zone)
    h,m=map(int,config['publish_hour'].split(':'))
    if target_date is None:
        day=local.date()
    else:
        day=date.fromisoformat(target_date) if isinstance(target_date,str) else target_date
        if not isinstance(day,date) or isinstance(day,datetime):
            raise ValueError("Fecha de publicación inválida")
    target=datetime.combine(day,datetime.min.time().replace(hour=h,minute=m),zone)
    if target_date is None and target.astimezone(timezone.utc)<=now.astimezone(timezone.utc)+timedelta(hours=1):
        target=datetime.combine(day+timedelta(days=1),datetime.min.time().replace(hour=h,minute=m),zone)
    if target.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)!=target.replace(tzinfo=None):
        raise ValueError("Hora inexistente por cambio de horario")
    if target.astimezone(timezone.utc)<=now.astimezone(timezone.utc)+timedelta(hours=1):
        raise ValueError("La fecha de publicación ya ha pasado o está demasiado cerca")
    return target.astimezone(timezone.utc).isoformat()

def gate(config,video,metadata):
    if config.get('publication_enabled') is not True: raise PermissionError('Publicación desactivada: falta aprobación del piloto y conexión del canal')
    if metadata.get('preview_only') is True: raise PermissionError('Borrador no publicable')
    digest=sha(video)
    if config.get('approved_episode_sha256')!=digest or metadata.get('sha256')!=digest: raise PermissionError('La aprobación debe corresponder al SHA256 exacto del vídeo')
    if not config.get('channel_id'): raise PermissionError('Falta canal autorizado')
    if not isinstance(metadata.get('contains_synthetic_media'),bool): raise ValueError('Revisar identificación de contenido sintético')

def upload(root,out,episode,config):
    from googleapiclient.http import MediaFileUpload
    metadata=json.loads((out/'metadata.json').read_text()); gate(config,out/'episode.mp4',metadata)
    from .render import validate
    validate(out/'episode.mp4')
    api=authenticated_api(config)
    db=connect(root/'data/history.sqlite'); restore(db,root/'data/history.json'); row=db.execute('SELECT status,sha,video_id FROM episodes WHERE id=?',(episode,)).fetchone()
    if not row or row[0]!='rendered' or row[1]!=sha(out/'episode.mp4'): raise ValueError('Estado incompatible o subida anterior incierta. Conciliar con YouTube antes de reintentar.')
    request=api.videos().insert(part='snippet,status',notifySubscribers=False,body=dict(snippet=dict(title=metadata['title'],description=metadata['description'],categoryId='27',defaultLanguage='es',defaultAudioLanguage='es'),status=dict(privacyStatus='private',publishAt=publish_at(config,target_date=publication_day(episode)),selfDeclaredMadeForKids=False,containsSyntheticMedia=metadata['contains_synthetic_media'])),media_body=MediaFileUpload(str(out/'episode.mp4'),chunksize=8*1024*1024,resumable=True,mimetype='video/mp4'))
    with db:
        changed=db.execute('UPDATE episodes SET status=? WHERE id=? AND status=? AND sha=?',('uploading',episode,'rendered',sha(out/'episode.mp4'))).rowcount
        if changed!=1: raise ValueError('Otra ejecución ya reservó esta subida')
    export_history(db,root/'data/history.json'); response=None
    try:
        while response is None:
            # An exception may mean the remote upload succeeded. Do not retry.
            progress,response=request.next_chunk(num_retries=0)
            if request.resumable_uri:
                with db: db.execute('UPDATE episodes SET upload_uri=? WHERE id=?',(request.resumable_uri,episode))
        with db: db.execute('UPDATE episodes SET status=?,video_id=?,upload_uri=NULL WHERE id=?',('scheduled',response['id'],episode))
        api.thumbnails().set(videoId=response['id'],media_body=MediaFileUpload(str(out/'thumbnail.jpg'))).execute()
        api.captions().insert(part='snippet',body={'snippet':{'videoId':response['id'],'language':'es','name':'Español','isDraft':False}},media_body=MediaFileUpload(str(out/'captions.srt'),mimetype='application/octet-stream')).execute()
    finally: export_history(db,root/'data/history.json')


def authenticated_api(config):
    """Official OAuth; always verify the configured channel before requests."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    if not config.get('channel_id'):
        raise PermissionError('Falta canal autorizado')
    raw=os.environ.get('YOUTUBE_TOKEN_JSON')
    if raw: credentials=Credentials.from_authorized_user_info(json.loads(raw),SCOPES)
    else: credentials=Credentials.from_authorized_user_file(os.environ.get('YOUTUBE_TOKEN_FILE','token.json'),SCOPES)
    if credentials.expired and credentials.refresh_token: credentials.refresh(Request())
    api=build('youtube','v3',credentials=credentials,cache_discovery=False)
    channels=api.channels().list(part='id',mine=True).execute()['items']
    if config['channel_id'] not in {c['id'] for c in channels}: raise PermissionError('OAuth no corresponde al canal configurado')
    return api


def reconcile(root, config, api=None):
    """Read-only YouTube reconciliation. No insert, update, or retry of uploads."""
    if not config.get('channel_id'):
        raise PermissionError('Falta canal autorizado')
    api = authenticated_api(config) if api is None else api
    db = connect(root/'data/history.sqlite')
    try:
        restore(db,root/'data/history.json')
        rows = [(episode, video_id) for episode, video_id in db.execute(
            "SELECT id,video_id FROM episodes WHERE status='scheduled' AND video_id IS NOT NULL ORDER BY id")
            if production_episode(episode)]
        confirmed, pending = [], []
        for offset in range(0,len(rows),50):
            batch=rows[offset:offset+50]
            result=api.videos().list(part='id,snippet,status',id=','.join(sorted({v for _,v in batch}))).execute()
            by_id={item['id']:item for item in result['items']}
            for episode, video_id in batch:
                video=by_id.get(video_id)
                if video and confirm_publication(db,episode,video,config['channel_id']):
                    confirmed.append(episode)
                else:
                    pending.append(episode)
        return {'confirmed':confirmed,'pending':pending,'published_count':published_count(db)}
    finally:
        try: export_history(db,root/'data/history.json')
        finally: db.close()
