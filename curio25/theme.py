"""Curio25 Fiesta: original visual tokens, commercially usable bundled OFL fonts."""
from pathlib import Path
import math, random
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
FONT_DIR=ROOT/'assets/fonts'
FONT_REGULAR=FONT_DIR/'Nunito-SemiBold.ttf'
FONT_BOLD=FONT_DIR/'Nunito-Black.ttf'
PALETTE=dict(yellow='#FFD84D',turquoise='#35D6C6',sky='#55B7FF',orange='#FF8A3D',pink='#FF5FB2',violet='#7A6CFF',lime='#B8EF55',white='#FFFFFF',ink='#183153')
CATEGORIES={
 'animales':('turquoise','lime'), 'ciencia':('sky','violet'),
 'historia':('yellow','orange'), 'tecnología':('sky','pink'),
 'naturaleza':('lime','turquoise'), 'geografía':('turquoise','sky'),
 'cuerpo humano':('pink','orange'), 'espacio':('violet','sky'),
}
def category_colors(fact):
    name=str(fact.get('category') or ('espacio' if fact.get('body') else 'ciencia')).lower()
    keys=CATEGORIES.get(name,('sky','violet'))
    return name,PALETTE[keys[0]],PALETTE[keys[1]]

def gradient(size,top=(236,249,255),bottom=(255,245,223)):
    im=Image.new('RGB',size);d=ImageDraw.Draw(im)
    for y in range(size[1]):
        a=y/max(1,size[1]-1)
        d.line((0,y,size[0],y),fill=tuple(round(x*(1-a)+z*a) for x,z in zip(top,bottom)))
    return im

def festive_background(seed=25):
    im=gradient((1920,1080)); d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((-240,-340,700,200),fill=(53,214,198,55));d.ellipse((1500,80,2200,760),fill=(85,183,255,55))
    d.ellipse((-200,680,550,1280),fill=(255,216,77,65));d.ellipse((1200,720,2120,1320),fill=(255,95,178,30))
    rng=random.Random(str(seed))
    for i in range(23):
        x=rng.randint(20,1900);y=rng.randint(15,825);r=rng.randint(4,12)
        color=list(PALETTE.values())[i%7]
        d.ellipse((x-r,y-r,x+r,y+r),outline=color,width=2)
    return im

def card(d,box,fill='white',accent=None,radius=28,shadow=8):
    x1,y1,x2,y2=box
    d.rounded_rectangle((x1+4,y1+shadow,x2+4,y2+shadow),radius,fill='#DCE6EE')
    d.rounded_rectangle(box,radius,fill=fill,outline=accent,width=3 if accent else 1)

def decorative_filters(scene=0):
    """Small actual floating animations in margins only; never on text or captions."""
    # Each envelope is disjoint from the content and reserved lower caption strip.
    colors=['0x35D6C6','0xFF5FB2','0xFFD84D','0x7A6CFF']
    parts=[]
    for j,(x,y) in enumerate([(8,215),(1864,350),(8,660),(1864,710)]):
        parts.append(f"drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:text='●':fontsize=36:fontcolor={colors[(j+scene)%4]}:x='{x}+3*sin(t*1.2+{j})':y='{y}+10*sin(t*1.7+{j})'")
    return ','.join(parts)
