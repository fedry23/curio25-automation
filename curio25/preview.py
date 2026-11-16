"""Draft-only assembly of the second episode.

No mutation of the production catalogue/history; no YouTube API calls.
Every image and factual statement remains unapproved for publication.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import argparse
import hashlib
import json

CONCEPTS = [
    ("180 KILOS","Corazón de una ballena azul"),
    ("3 CORAZONES","Dos hacia las branquias"),
    ("3.700 MILLAS","Migración en cada trayecto"),
    ("UNIÓN EXTREMA","Solo algunas especies"),
    ("CANTOS COMPLEJOS","Cortejo y territorio"),
    ("97 % DEL AGUA","Está en los océanos"),
    ("200 METROS","Comienza la penumbra"),
    ("UNOS 4 °C","Océano profundo"),
    ("HASTA EL 80 %","Animales bioluminiscentes"),
    ("PREDOMINA EL AZUL","Viaja mejor bajo el agua"),
    ("1844","Primer telegrama público"),
    ("7 MARZO 1876","Patente de Bell"),
    ("10 MARZO 1876","Bell habla con Watson"),
    ("12 SEGUNDOS","Primer vuelo, 120 pies"),
    ("1915","Llamada transcontinental"),
    ("AÑOS SETENTA","Materiales de asientos"),
    ("CMOS","Cámaras actuales"),
    ("RECUBRIMIENTOS","Lentes resistentes"),
    ("MANOS LIBRES","Tecnología espacial"),
    ("PROGRAMA APOLLO","Seguridad alimentaria"),
    ("MÁS DE 10.000","Fenómenos hidrotermales"),
    ("MÁS DE LA MITAD","Géiseres activos conocidos"),
    ("45-50 MILLONES","Años desde las erupciones"),
    ("14.000-32.000 L","Agua por erupción"),
    ("1.840 MILLONES","Antigüedad de las rocas"),
]

def create_manifest(root, out):
    """Build review facts from staged sources and files, never approved records."""
    root = Path(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    facts = json.loads((root / 'data/candidates/2026-11-17.json').read_text(encoding='utf-8'))['facts']
    store = root / 'data/candidates/media-2026-11-17'
    images = json.loads((store / 'media_report.json').read_text(encoding='utf-8'))['records']
    if len(facts) != 25 or len(images) != 25 or len({f['id'] for f in facts}) != 25:
        raise ValueError('Necesitamos 25 datos y 25 fotos únicas')
    media = {record['fact_id']: record for record in images}
    enriched = []
    for i, fact in enumerate(facts):
        record = media.get(fact['id'])
        if not record or record.get('status') != 'downloaded_unreviewed':
            raise ValueError('Foto pendiente: ' + fact['id'])
        path = (store / record['file']).resolve()
        if not path.is_relative_to(store.resolve()) or not path.is_file():
            raise ValueError('Foto ausente o fuera de staging: ' + fact['id'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Hash visual inválido: ' + fact['id'])
        with Image.open(path) as im:
            im.verify()
        if record['license'] not in {'pd','cc0','cc-by-3.0','cc-by-4.0',
                                     'cc-by-sa-3.0','cc-by-sa-4.0'}:
            raise ValueError('Licencia desconocida: ' + fact['id'])
        if fact['review_status'] != 'pending':
            raise ValueError('La previsualización espera candidatos sin aprobar')
        title, detail = CONCEPTS[i]
        enriched.append(dict(
            fact,
            preview_only=True,
            episode_title='25 curiosidades del mundo que te van a sorprender',
            graphic={'kind':'concept','values':[1,1],
                     'labels':['EL DATO','¿QUÉ SIGNIFICA?'],
                     'details':[title,detail]},
            media_path=str(path),
            media_credit=(record['author']+' · '+record['license_short'])[:70],
            media_record=record
        ))
    manifest = {
        'kind':'private_technical_preview',
        'publishable':False,
        'fact_count':25,
        'image_count':25,
        'facts_verified_for_publication':0,
        'images_legally_approved':0,
        'history_modified':False,
        'warning':'BORRADOR NO PUBLICABLE. Falta revisión de datos, imágenes y licencias.',
        'items':[{'fact_id':f['id'],'source':f['source_url'],
                  'image_license':f['media_record']['license'],
                  'image_source':f['media_record']['source'],
                  'image_sha256':f['media_record']['sha256']}
                 for f in enriched],
    }
    (out / 'preview-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return enriched

def contact_sheet(facts, target):
    tile_w, tile_h = 340, 270
    output=Image.new('RGB',(tile_w*5,tile_h*5),'#121a2c')
    draw=ImageDraw.Draw(output)
    regular=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
    bold=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',17)
    for i,fact in enumerate(facts):
        x=(i%5)*tile_w
        y=(i//5)*tile_h
        with Image.open(fact['media_path']) as image:
            preview=ImageOps.fit(ImageOps.exif_transpose(image).convert('RGB'),(tile_w-12,182))
        output.paste(preview,(x+6,y+6))
        draw.rectangle((x+6,y+194,x+tile_w-6,y+tile_h-6),fill='#24354b')
        draw.text((x+13,y+199),f"{i+1:02} · {fact['category'].upper()}",font=bold,fill='#86e4da')
        draw.text((x+13,y+227),fact['title'][:41],font=regular,fill='white')
        draw.text((x+13,y+248),'PENDIENTE DE APROBACIÓN',font=regular,fill='#f4cb83')
    output.save(target,quality=88)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('.'))
    parser.add_argument('--out',type=Path,default=Path('build/review-2026-11-17'))
    parser.add_argument('--contact-only',action='store_true')
    args=parser.parse_args()
    facts=create_manifest(args.root,args.out)
    contact_sheet(facts,args.out/'contact-sheet.jpg')
    print('Mosaico de 25 imágenes generado para revisión',flush=True)
    if not args.contact_only:
        from .render import render
        conf=json.loads((args.root/'config.json').read_text(encoding='utf-8'))
        report=render(args.root,args.out,facts,conf)
        print(json.dumps(dict(report,preview_only=True),ensure_ascii=False))

if __name__=='__main__':
    main()
