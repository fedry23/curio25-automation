"""Download nominated Commons files to quarantine; no automatic approval."""
import argparse,io,json,hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlsplit
import requests
from PIL import Image
from .sources import ALLOWED,plain
EXT={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp'}

def url_allowed(url):
    u=urlsplit(url or '')
    return u.scheme=='https' and u.hostname=='upload.wikimedia.org' and not u.username and not u.password and u.port in (None,443)

def field(meta,key):
    return plain(meta.get(key,{}).get('value','')).strip()

def metadata(item,info):
    m=info.get('extmetadata',{});license=field(m,'License').lower()
    author=field(m,'Artist');origin=info.get('descriptionurl','');mime=info.get('mime')
    download=info.get('thumburl') or info.get('url')
    if license not in ALLOWED or not author or not origin.startswith('https://commons.wikimedia.org/') or mime not in EXT:
        raise ValueError('Sin autor/licencia comercial/origen/formato')
    if not url_allowed(download):raise ValueError('URL imagen insegura')
    return dict(fact_id=item['fact_id'],title=item['file_title'],source=origin,
                author=author,license=license,license_short=field(m,'LicenseShortName'),
                license_url=field(m,'LicenseUrl'),download_url=download,mime=mime,
                review_status='pending_visual_legal_review',
                rights_note='Revisar derechos en España; CC BY-SA exige atribución y obligaciones de adaptación',
                changes='Fotografía a recortar y animar; indicar cambios en créditos')

def get(item,out):
    ident=item['fact_id'];title=item['file_title']
    try:
        if not ident.startswith('curio-') or not title.startswith('File:'):raise ValueError('Selección inválida')
        with requests.Session() as s:
            s.headers['User-Agent']='Curio25MediaAudit/0.3 (fedry23/curio25-automation)'
            r=s.get('https://commons.wikimedia.org/w/api.php',
                params=dict(action='query',format='json',titles=title,prop='imageinfo',iiprop='url|mime|extmetadata',iiurlwidth=1050),timeout=(5,25))
            r.raise_for_status()
            page=next(iter(r.json()['query']['pages'].values()))
            info=page['imageinfo'][0];rec=metadata(item,info)
            image=s.get(rec['download_url'],timeout=(5,30));image.raise_for_status()
        blob=image.content
        if not blob or len(blob)>6000000:raise ValueError('Imagen vacía o demasiado grande')
        with Image.open(io.BytesIO(blob)) as img:
            img.verify()
        with Image.open(io.BytesIO(blob)) as img:
            if img.width<550 or img.height<300:raise ValueError('Resolución insuficiente')
            rec.update(width=img.width,height=img.height)
        path=out/'images'/(ident+EXT[rec['mime']]);path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(blob)
        rec.update(file='images/'+path.name,sha256=hashlib.sha256(blob).hexdigest(),
                   status='downloaded_unreviewed',bytes=len(blob))
        print('MEDIA',ident,rec['status'],rec['width'],rec['height'],flush=True)
        return rec
    except (Exception) as exc:
        print('MEDIA',ident,'failed',str(exc)[:150],flush=True)
        return dict(fact_id=ident,title=title,status='failed',error=str(exc)[:200],
                    review_status='pending_visual_legal_review')

def stage(root,episode,out):
    root=Path(root);out=Path(out)
    selection=json.loads((root/'data/candidates'/('media-selection-'+episode+'.json')).read_text())['photos']
    if len(selection)!=25 or len({s['fact_id'] for s in selection})!=25:raise ValueError('Se requieren 25 imágenes únicas')
    out.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        result=list(pool.map(lambda x:get(x,out),selection))
    summary=dict(date=episode,production_ready=False,publication_enabled=False,
                photos_downloaded=sum(x['status']=='downloaded_unreviewed' for x in result),
                photos_approved=0,rights_approved=0,records=result,
                warning='Los ficheros descargados NO están aprobados: revisar contenido, licencia, autor y derechos territoriales.')
    (out/'media_report.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n')
    return summary

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--episode',required=True);p.add_argument('--out',type=Path,required=True)
    x=p.parse_args();r=stage(x.root,x.episode,x.out)
    print(json.dumps({k:r[k] for k in ('photos_downloaded','photos_approved','production_ready')}))
if __name__=='__main__':main()
