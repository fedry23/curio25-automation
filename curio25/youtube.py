"""Official OAuth and resumable upload. Publication fails closed."""
import json,os,random,time
from pathlib import Path
from datetime import datetime,timedelta,timezone
from zoneinfo import ZoneInfo
from .state import connect,restore,export_history,sha
SCOPES=['https://www.googleapis.com/auth/youtube.upload','https://www.googleapis.com/auth/youtube.force-ssl']

def authorize():
    from google_auth_oauthlib.flow import InstalledAppFlow
    client=os.environ.get('YOUTUBE_CLIENT_FILE')
    if not client: raise ValueError('Definir YOUTUBE_CLIENT_FILE con OAuth de aplicación de escritorio propio')
    credentials=InstalledAppFlow.from_client_secrets_file(client,SCOPES).run_local_server(port=0,access_type='offline',prompt='consent')
    target=Path(os.environ.get('YOUTUBE_TOKEN_FILE','token.json')); target.write_text(credentials.to_json()); target.chmod(0o600)

def publish_at(config,now=None):
    now=now or datetime.now(timezone.utc); zone=ZoneInfo(config['timezone']); local=now.astimezone(zone); h,m=map(int,config['publish_hour'].split(':'))
    target=local.replace(hour=h,minute=m,second=0,microsecond=0)
    if target<=local+timedelta(hours=1): target+=timedelta(days=1)
    # Reject non-existent local clock times around DST transitions.
    if target.astimezone(timezone.utc).astimezone(zone).replace(fold=target.fold)!=target: raise ValueError('Hora inexistente por cambio de horario')
    return target.astimezone(timezone.utc).isoformat()

def gate(config,video,metadata):
    if config.get('publication_enabled') is not True: raise PermissionError('Publicación desactivada: falta aprobación del piloto y conexión del canal')
    digest=sha(video)
    if config.get('approved_episode_sha256')!=digest or metadata.get('sha256')!=digest: raise PermissionError('La aprobación debe corresponder al SHA256 exacto del vídeo')
    if not config.get('channel_id'): raise PermissionError('Falta canal autorizado')
    if not isinstance(metadata.get('contains_synthetic_media'),bool): raise ValueError('Revisar identificación de contenido sintético')

def upload(root,out,episode,config):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
    metadata=json.loads((out/'metadata.json').read_text()); gate(config,out/'episode.mp4',metadata)
    from .render import validate
    validate(out/'episode.mp4')
    raw=os.environ.get('YOUTUBE_TOKEN_JSON')
    if raw: credentials=Credentials.from_authorized_user_info(json.loads(raw),SCOPES)
    else: credentials=Credentials.from_authorized_user_file(os.environ.get('YOUTUBE_TOKEN_FILE','token.json'),SCOPES)
    if credentials.expired and credentials.refresh_token: credentials.refresh(Request())
    api=build('youtube','v3',credentials=credentials,cache_discovery=False)
    channels=api.channels().list(part='id',mine=True).execute()['items']
    if config['channel_id'] not in {c['id'] for c in channels}: raise PermissionError('OAuth no corresponde al canal configurado')
    db=connect(root/'data/history.sqlite'); restore(db,root/'data/history.json'); row=db.execute('SELECT status,sha,video_id FROM episodes WHERE id=?',(episode,)).fetchone()
    if not row or row[0]!='rendered' or row[1]!=sha(out/'episode.mp4'): raise ValueError('Estado incompatible o subida anterior incierta. Conciliar con YouTube antes de reintentar.')
    request=api.videos().insert(part='snippet,status',notifySubscribers=False,body=dict(snippet=dict(title=metadata['title'],description=metadata['description'],categoryId='27',defaultLanguage='es',defaultAudioLanguage='es'),status=dict(privacyStatus='private',publishAt=publish_at(config),selfDeclaredMadeForKids=False,containsSyntheticMedia=metadata['contains_synthetic_media'])),media_body=MediaFileUpload(str(out/'episode.mp4'),chunksize=8*1024*1024,resumable=True,mimetype='video/mp4'))
    with db:
        changed=db.execute('UPDATE episodes SET status=? WHERE id=? AND status=? AND sha=?',('uploading',episode,'rendered',sha(out/'episode.mp4'))).rowcount
        if changed!=1: raise ValueError('Otra ejecución ya reservó esta subida')
    export_history(db,root/'data/history.json'); response=None
    try:
        failures=0
        while response is None:
            try:
                progress,response=request.next_chunk(num_retries=0)
                if request.resumable_uri:
                    with db: db.execute('UPDATE episodes SET upload_uri=? WHERE id=?',(request.resumable_uri,episode))
                failures=0
            except (HttpError,OSError) as exc:
                status=getattr(getattr(exc,'resp',None),'status',None)
                if status and status not in [429,500,502,503,504]: raise
                failures+=1
                if failures>6: raise
                time.sleep(min(60,2**failures+random.random()))
        with db: db.execute('UPDATE episodes SET status=?,video_id=?,upload_uri=NULL WHERE id=?',('scheduled',response['id'],episode))
        api.thumbnails().set(videoId=response['id'],media_body=MediaFileUpload(str(out/'thumbnail.jpg'))).execute()
        api.captions().insert(part='snippet',body={'snippet':{'videoId':response['id'],'language':'es','name':'Español','isDraft':False}},media_body=MediaFileUpload(str(out/'captions.srt'),mimetype='application/octet-stream')).execute()
    finally: export_history(db,root/'data/history.json')
