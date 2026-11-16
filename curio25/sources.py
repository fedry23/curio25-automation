import hashlib, html, json, re, time
from pathlib import Path
from datetime import datetime, timezone
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def session():
    s=requests.Session(); s.headers['User-Agent']='Curio25/0.1 (educational audit)'
    s.mount('https://', HTTPAdapter(max_retries=Retry(total=4,backoff_factor=2,status_forcelist=[429,500,502,503,504],respect_retry_after_header=True)))
    return s

def plain(raw):
    raw=re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '',raw,flags=re.S|re.I)
    return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>',' ',raw)))

def snapshot(root):
    root=Path(root); facts=json.loads((root/'data/facts.json').read_text()); s=session(); reports=[]
    for url in sorted({f['source_url'] for f in facts}):
        r=s.get(url,timeout=45); r.raise_for_status(); text=plain(r.text)
        name=hashlib.sha256(url.encode()).hexdigest()[:16]+'.txt'
        (root/'data/snapshots').mkdir(parents=True,exist_ok=True); (root/'data/snapshots'/name).write_text(text)
        reports.append(dict(url=url,path='data/snapshots/'+name,sha256=hashlib.sha256(text.encode()).hexdigest(),retrieved_at=datetime.now(timezone.utc).isoformat())); time.sleep(.3)
    (root/'data/source_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
    for f in facts:
        rec=next(r for r in reports if r['url']==f['source_url']); txt=(root/rec['path']).read_text(); m=re.search(re.escape(f['evidence_query']),txt,re.I)
        print(f['id'],f['title'], ':',txt[max(0,m.start()-100):m.end()+220] if m else 'NO MATCH')

ALLOWED={'cc0','pd','public domain','cc-by-4.0','cc-by-sa-4.0','cc-by-3.0','cc-by-sa-3.0'}
def commons_asset(title,directory):
    s=session(); r=s.get('https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',titles=title,prop='imageinfo',iiprop='url|extmetadata'),timeout=45); r.raise_for_status()
    info=next(iter(r.json()['query']['pages'].values()))['imageinfo'][0]; meta=info['extmetadata']; get=lambda k: plain(meta.get(k,{}).get('value',''))
    license_id=get('License').lower()
    if license_id not in ALLOWED or not get('Artist') or not get('LicenseShortName'): raise ValueError('Licencia comercial o autor no verificables')
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True); response=s.get(info['url'],timeout=60); response.raise_for_status()
    digest=hashlib.sha256(response.content).hexdigest(); path=directory/(digest+Path(info['url']).suffix); path.write_bytes(response.content)
    record=dict(file=path.name,sha256=digest,author=get('Artist'),license=license_id,license_url=get('LicenseUrl'),title=title,source=info['descriptionurl'],changes='Encuadre y rótulos',retrieved_at=datetime.now(timezone.utc).isoformat())
    path.with_suffix('.license.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)); return record

if __name__=='__main__': snapshot(Path(__file__).resolve().parents[1])
