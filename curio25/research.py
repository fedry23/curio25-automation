"""Archive source evidence and Commons *candidates*; NEVER auto-approve."""
import argparse, hashlib, json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import requests
from .sources import session, plain, ALLOWED

ALLOWED_HOSTS=('noaa.gov','nasa.gov','loc.gov','nps.gov','si.edu')

def safe(url):
    if not isinstance(url,str):return False
    p=urlsplit(url);h=(p.hostname or '').lower()
    return (p.scheme=='https' and p.username is None and p.password is None
            and p.port in (None,443)
            and any(h==host or h.endswith('.'+host) for host in ALLOWED_HOSTS))

def evidence(text,query):
    return ' '.join(query.casefold().split()) in ' '.join(text.casefold().split())

def licensed_candidate(info):
    ext=info.get('extmetadata',{})
    get=lambda key:plain(ext.get(key,{}).get('value','')).strip()
    license_name=get('License').lower()
    if (license_name not in ALLOWED or not get('Artist')
        or info.get('mime') not in ('image/jpeg','image/png','image/webp')):return None
    if not all(str(info.get(k,'')).startswith('https://') for k in ('url','descriptionurl')):return None
    return dict(source=info['descriptionurl'],url=info['url'],thumb=info.get('thumburl'),
                author=get('Artist'),license=license_name,
                license_short=get('LicenseShortName'),license_url=get('LicenseUrl'),
                reviewed=False,approved=False)

def suggestions(sess,query):
    if not query:return []
    p=dict(action='query',format='json',generator='search',gsrsearch=query[:120],
           gsrnamespace=6,gsrlimit=12,prop='imageinfo',
           iiprop='url|extmetadata|mime',iiurlwidth=800)
    r=sess.get('https://commons.wikimedia.org/w/api.php',params=p,timeout=35)
    r.raise_for_status()
    found=[]
    for page in r.json().get('query',{}).get('pages',{}).values():
        for info in page.get('imageinfo',[]):
            obj=licensed_candidate(info)
            if obj:
                obj['file_title']=page.get('title');found.append(obj)
                if len(found)>=3:return found
    return found

def _new_session():
    # No hidden backoff of several minutes if a source or Commons is unavailable.
    s=requests.Session()
    s.headers['User-Agent']='Curio25EvidenceCollector/0.3 (https://github.com/fedry23/curio25-automation)'
    return s

def collect(root,date,out):
    root=Path(root);out=Path(out)
    facts=json.loads((root/'data/candidates'/(date+'.json')).read_text())['facts']
    if len(facts)!=25 or len({f['id'] for f in facts})!=25:
        raise ValueError('Se necesitan 25 candidatos únicos')
    snapdir=out/'snapshots';snapdir.mkdir(parents=True,exist_ok=True)
    urls=sorted({f['source_url'] for f in facts})
    if not all(safe(url) for url in urls):
        raise ValueError('Hay URLs fuera de la lista de instituciones permitidas')

    def fetch_url(url):
        rec={'url':url,'status':'pending'}
        try:
            with _new_session() as s:
                res=s.get(url,timeout=(5,12),allow_redirects=True)
                res.raise_for_status()
            if not safe(res.url):raise ValueError('Redirección insegura')
            if len(res.content)>4_000_000:raise ValueError('Fuente demasiado grande')
            if 'html' not in res.headers.get('Content-Type','').lower():
                raise ValueError('Fuente no HTML')
            txt=plain(res.text)
            if len(txt)<200:raise ValueError('Texto insuficiente')
            name=hashlib.sha256(url.encode()).hexdigest()[:16]+'.txt'
            (snapdir/name).write_text(txt,encoding='utf-8')
            rec.update(status='archived_unreviewed',path='snapshots/'+name,
                       sha256=hashlib.sha256(txt.encode()).hexdigest(),
                       final_url=res.url,archived_at=datetime.now(timezone.utc).isoformat())
        except (ValueError,requests.RequestException,OSError) as exc:
            rec.update(status='fetch_failed',error=str(exc)[:250])
        print('SOURCE',rec['status'],url,flush=True)
        return rec

    # Each worker uses its own connection so timeout/retry behavior is bounded.
    with ThreadPoolExecutor(max_workers=4) as pool:
        srcs=list(pool.map(fetch_url,urls))
    sources=dict(zip(urls,srcs))

    checks=[]
    for fact in facts:
        a=sources[fact['source_url']]
        ok=False
        if a['status']=='archived_unreviewed' and fact.get('evidence_query'):
            txt=(out/a['path']).read_text(encoding='utf-8')
            ok=evidence(txt,fact['evidence_query'])
        checks.append(dict(fact_id=fact['id'],source_url=fact['source_url'],
                           source_sha256=a.get('sha256'),
                           evidence_query=fact.get('evidence_query'),
                           evidence_found=ok,verified=False,media_approved=False,
                           status='pending_human_review' if ok else 'needs_more_research'))

    def find_images(fact):
        try:
            with _new_session() as s:
                result=suggestions(s,fact.get('media_search_query',''))
            print('IMAGES',fact['id'],len(result),flush=True)
            return result
        except (requests.RequestException,ValueError) as exc:
            print('IMAGES FAILED',fact['id'],str(exc)[:120],flush=True)
            return dict(error=str(exc)[:250],matches=[])

    with ThreadPoolExecutor(max_workers=3) as pool:
        media_results=list(pool.map(find_images,facts))
    media={f['id']:images for f,images in zip(facts,media_results)}
    result=dict(date=date,created_at=datetime.now(timezone.utc).isoformat(),
                publication_enabled=False,production_ready=False,
                total=25,sources=list(sources.values()),facts=checks,
                sources_archived=sum(r['status']=='archived_unreviewed' for r in sources.values()),
                evidence_found=sum(r['evidence_found'] for r in checks),approved_facts=0,
                disclaimer='La coincidencia textual NO prueba la afirmación; los archivos Commons NO están aprobados hasta revisar derechos y contenido.')
    (out/'source_report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    (out/'image_suggestions.json').write_text(json.dumps(media,indent=2,ensure_ascii=False)+'\n')
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--episode',required=True);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();r=collect(a.root,a.episode,a.out)
    print(json.dumps({k:r[k] for k in ('sources_archived','evidence_found','approved_facts','production_ready')},ensure_ascii=False))

if __name__=='__main__':main()
