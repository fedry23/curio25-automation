"""Original fixed layout with licensed photography and a separate subtitle band."""
from PIL import Image, ImageDraw, ImageOps
import math,random,hashlib
from .layout import font,fit_text,Box,TITLE,PHOTO,GRAPH,CREDIT,PROGRESS
COLORS={'mercury':'#bdafa5','venus':'#edbc6a','earth':'#32becd','sun':'#ffc546','moon':'#c6d3e5','mars':'#e77754','jupiter':'#dfa986','saturn':'#d9bf83','uranus':'#7be4dd','neptune':'#5688ef','pluto':'#c6a898'}

def _text(d,text,box,size,bold=False,max_lines=2,fill='white',minimum=16,gap=8):
    lines,face,actual,height=fit_text(text,box,size,minimum,max_lines,bold,gap)
    asc,desc=face.getmetrics(); y=box.y1
    for line in lines:
        # Top-anchor uses ascent-aware positioning rather than a guessed baseline.
        d.text((box.x1,y),line,font=face,fill=fill,anchor='lt'); y+=asc+desc+gap
    return dict(box=list(box.tuple()),font_size=actual,line_count=len(lines),text=text)

def panel(f,index,path):
    im=Image.new('RGB',(1920,1080),'#0a1327'); d=ImageDraw.Draw(im); rng=random.Random(f['id']); accent=COLORS.get(f.get('body'), ('#48b7d5','#f4a261','#a18bfa','#7fd5ac','#e9bc70')[int(hashlib.sha256(str(f.get('body','')).encode()).hexdigest()[:4],16)%5])
    for _ in range(150):
        x,y=rng.randrange(64,1856),rng.randrange(48,824); d.ellipse((x,y,x+2,y+2),fill='#3b4965')
    elements=[]
    def record(name,box,**extra): elements.append(dict(name=name,box=list(box.tuple()),**extra))
    d.rounded_rectangle((90,64,370,126),16,fill=accent)
    _text(d,'CURIO / 25',Box(110,76,350,120),32,True,max_lines=1,fill='#0a1327')
    record('brand',Box(90,64,370,126))
    number=Box(1690,65,1820,125); _text(d,f'{index:02}/25',number,34,True,max_lines=1); record('counter',number)
    info=_text(d,f['title'],TITLE,56,True,minimum=42); record('title',TITLE,font_size=info['font_size'],line_count=info['line_count'])
    eyebrow=Box(90,325,840,366); _text(d,'UN DATO, UNA HISTORIA',eyebrow,25,True,max_lines=1,fill=accent); record('eyebrow',eyebrow)
    # Exact photographic box: the frame itself never moves or zooms.
    media=f.get('media_path')
    if media:
        with Image.open(media) as source:
            photo=ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'),(PHOTO.width,PHOTO.height),method=Image.Resampling.LANCZOS)
        im.paste(photo,(PHOTO.x1,PHOTO.y1)); d=ImageDraw.Draw(im)
    else:
        # Explicit fallback for local layout tests and genuinely unavailable assets.
        d.rounded_rectangle(PHOTO.tuple(),20,fill='#17253d')
        cx=(PHOTO.x1+PHOTO.x2)//2; cy=(PHOTO.y1+PHOTO.y2)//2; r=170
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=accent)
        _text(d,'ILUSTRACIÓN ORIGINAL',Box(1000,692,1770,732),23,max_lines=1,fill='#d8e5fa')
    d.rectangle(PHOTO.tuple(),outline='#526885',width=2); record('photograph' if media else 'illustration',PHOTO)
    credit=f.get('media_credit','Ilustración original Curio25 · Sin escala')
    info=_text(d,credit,CREDIT,18,minimum=12,max_lines=2,gap=2,fill='#a9bad3'); record('image_credit',CREDIT,font_size=info['font_size'],line_count=info['line_count'])
    g=f['graphic']; values=g['values']; maximum=max(values) or 1
    for j,(val,label) in enumerate(zip(values[:2],g['labels'][:2])):
        top=390+j*176
        label_box=Box(90,top,840,top+54); info=_text(d,label,label_box,29,minimum=23,max_lines=1,fill='#dbe6fa'); record(f'graph_label_{j}',label_box,font_size=info['font_size'])
        value_box=Box(90,top+66,840,top+148)
        if g['kind'] in ('compare','fraction'):
            d.rounded_rectangle((90,top+66,90+max(8,750*val/maximum),top+96),7,fill=accent if j==0 else '#6783b3')
            _text(d,str(val).replace('.',','),Box(90,top+105,840,top+147),27,True,max_lines=1)
        elif g['kind']=='moons':
            count=2 if j==0 else 1
            for k in range(count): d.ellipse((100+k*90,top+75,144+k*90,top+119),fill=accent)
        elif g['kind']=='layers':
            for k in range(3 if j==0 else 8): d.ellipse((100+k*83,top+75,124+k*83,top+99),outline=accent,width=3)
            _text(d,'Representación conceptual',Box(90,top+112,840,top+148),22,max_lines=1,fill='#9bb0d0')
        else:
            d.line((110,top+93,810,top+93),fill=accent,width=4)
            if f.get('body')=='venus' and j==1: d.polygon([(110,top+93),(130,top+82),(130,top+104)],fill=accent)
            else: d.polygon([(810,top+93),(790,top+82),(790,top+104)],fill=accent)
        record(f'graph_values_{j}',value_box)
    notice=Box(90,757,840,788); _text(d,('NASA Science · Gráfico esquemático · Fuentes en descripción' if not f.get('episode_topic') or f.get('episode_topic')=='sistema solar' else 'Gráfico esquemático · Fuentes y licencias en descripción'),notice,20,minimum=17,max_lines=1,fill='#9bb0d0'); record('source_notice',notice)
    d.rounded_rectangle(PROGRESS.tuple(),5,fill='#26364f'); record('progress',PROGRESS)
    # This entire strip is reserved exclusively for captions. No visual/credit enters it.
    d.rectangle((0,840,1920,1080),fill='#080f1e')
    im.save(path)
    return elements

def photo_layer(f,path):
    """High resolution crop for a camera movement constrained to PHOTO."""
    if not f.get('media_path'): return False
    with Image.open(f['media_path']) as source:
        photo=ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'),(PHOTO.width*2,PHOTO.height*2),method=Image.Resampling.LANCZOS)
        photo.save(path)
    return True

def thumbnail(path, topic='sistema solar', photo_path=None):
    """Topic-aware 16:9 thumbnail using an already approved licensed photograph."""
    im=Image.new('RGB',(1280,720),'#0a1327')
    if photo_path:
        with Image.open(photo_path) as source:
            photo=ImageOps.fit(ImageOps.exif_transpose(source).convert('RGB'),
                               (620,720), method=Image.Resampling.LANCZOS)
        im.paste(photo,(660,0))
    else:
        d=ImageDraw.Draw(im)
        d.ellipse((825,100,1280,555),fill='#385577')
        d.ellipse((780,330,1280,520),outline='#83e9df',width=15)
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,725,720),fill='#101a31')
    d.text((60,38),'CURIO25',font=font(46,True),fill='#83e9df')
    d.text((52,120),'25',font=font(240,True),fill='#ffce54')
    d.text((62,398),'DATOS QUE',font=font(53,True),fill='white')
    d.text((62,470),'TE SORPRENDERÁN',font=font(38,True),fill='white')
    info=Box(62,557,685,653)
    lines,face,size,height=fit_text(str(topic).upper(),info,52,25,max_lines=2,bold=True)
    ascent,descent=face.getmetrics(); y=info.y1
    for line in lines:
        d.text((info.x1,y),line,font=face,fill='#83e9df',anchor='lt')
        y+=ascent+descent+8
    im.save(path)
