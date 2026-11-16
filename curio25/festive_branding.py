"""Original, family-friendly procedural Curio25 ident.

The rendered clip has no audio and lives entirely within the 1792×640 opener
area. It does not draw or replace the programme's separate, real countdown.
"""
from __future__ import annotations

import functools
import json
import math
from pathlib import Path
import random
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH, HEIGHT = 1792, 640
SIZE = (WIDTH, HEIGHT)
SAFE = (40, 40, WIDTH-40, HEIGHT-40)
try:
    from .theme import FONT_BOLD, FONT_REGULAR
except ImportError:
    FONT_BOLD = Path(__file__).resolve().parents[1]/'assets/fonts/Nunito-Black.ttf'
    FONT_REGULAR = Path(__file__).resolve().parents[1]/'assets/fonts/Nunito-SemiBold.ttf'
FONT_PATH = str(FONT_BOLD) if Path(FONT_BOLD).exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REGULAR_PATH = str(FONT_REGULAR) if Path(FONT_REGULAR).exists() else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
INK = '#183153'
TEAL = '#087f91'
ORANGE = '#ff8a3d'
YELLOW = '#ffd84d'
PAPER = '#fffdf5'


def _font(size, bold=True):
    return ImageFont.truetype(FONT_PATH if bold else REGULAR_PATH, size)


def _ease(value):
    value=max(0.0,min(1.0,value))
    return 1-(1-value)**3


def _blend(c1,c2,a):
    return tuple(round(x*(1-a)+y*a) for x,y in zip(c1,c2))


@functools.lru_cache(maxsize=1)
def _background():
    im=Image.new('RGB',SIZE)
    d=ImageDraw.Draw(im)
    for y in range(HEIGHT):
        a=y/(HEIGHT-1)
        d.line((0,y,WIDTH,y),fill=_blend((85,183,255),(53,214,198),a))
    haze=Image.new('RGBA',SIZE)
    hd=ImageDraw.Draw(haze)
    hd.ellipse((-100,-250,1050,500),fill=(222,255,247,104))
    hd.ellipse((1050,200,1950,1050),fill=(4,139,163,45))
    hd.ellipse((880,-240,1550,330),fill=(255,246,181,35))
    return Image.alpha_composite(im.convert('RGBA'),haze.filter(ImageFilter.GaussianBlur(50)))


def _star(draw,xy,radius,color,rotation=0):
    x,y=xy
    points=[]
    for i in range(8):
        angle=rotation+math.pi*i/4
        radius_i=radius if i%2==0 else radius*.28
        points.append((x+math.cos(angle)*radius_i,y+math.sin(angle)*radius_i))
    draw.polygon(points,fill=color)


def _center_text(draw,text,center_y,box,font,fill):
    bounds=draw.textbbox((0,0),text,font=font)
    width=bounds[2]-bounds[0]; height=bounds[3]-bounds[1]
    x=box[0]+(box[2]-box[0]-width)/2-bounds[0]
    y=center_y-height/2-bounds[1]
    draw.text((x,y),text,font=font,fill=fill)
    return (round(x+bounds[0]),round(y+bounds[1]),round(x+bounds[2]),round(y+bounds[3]))


def _contain(inner,outer=SAFE):
    return outer[0]<=inner[0]<=inner[2]<=outer[2] and outer[1]<=inner[1]<=inner[3]<=outer[3]


def brand_layout(kind='intro'):
    """Measured resting-state text boxes; all required copy has a >=40px margin."""
    if kind not in ('intro','outro'):
        raise ValueError('Tipo de clip desconocido')
    scratch=ImageDraw.Draw(Image.new('RGB',SIZE))
    entries=[]
    def measure(name,text,cy,box,size,bold=True):
        bb=_center_text(scratch,text,cy,box,_font(size,bold),INK)
        entries.append(dict(name=name,text=text,box=list(bb),font_size=size))
    if kind=='intro':
        measure('eyebrow','EL RETO DE LA CURIOSIDAD',180,(160,145,1130,219),27)
        measure('brand_word','CURIO',298,(160,220,802,385),151)
        measure('brand_number','25',299,(812,218,1086,385),145)
        measure('subtitle','25 curiosidades en 5 minutos',432,(155,390,1145,475),43,False)
    else:
        measure('eyebrow','CURIO25',180,(160,145,1130,219),36)
        measure('farewell_title','¡Se acabó el tiempo!',285,(155,230,1145,343),80)
        measure('farewell_subtitle','¡Nos vemos mañana!',414,(155,365,1145,465),67)
    measure('challenge_time','05:00',337,(1265,278,1585,403),68)
    measure('challenge_label','MINUTOS' if kind=='intro' else '¡RETO COMPLETO!',411,(1265,380,1585,445),22)
    errors=[e['name']+': texto fuera de la zona segura' for e in entries if not _contain(e['box'])]
    # The animated main card's overshoot never exceeds its reserved safe region.
    return dict(kind=kind,size=list(SIZE),safe=list(SAFE),text_boxes=entries,
                card=[104,104,1190,544],stopwatch=[1218,90,1632,526],
                card_motion_envelope=[83,86,1205,560],passed=not errors,errors=errors)


def _paper_card(t,kind='intro'):
    if kind=='outro': return _outro_card(t)
    layer=Image.new('RGBA',SIZE)
    d=ImageDraw.Draw(layer)
    # Tactile offset paper layers and a soft, short shadow.
    shadow=Image.new('RGBA',SIZE)
    sd=ImageDraw.Draw(shadow)
    sd.rounded_rectangle((112,126,1196,554),42,fill=(7,99,120,60))
    layer=Image.alpha_composite(layer,shadow.filter(ImageFilter.GaussianBlur(13)))
    d=ImageDraw.Draw(layer)
    d.rounded_rectangle((100,104,1178,534),42,fill='#ffca70')
    d.rounded_rectangle((112,120,1190,544),42,fill='#b8f1e0')
    d.rounded_rectangle((104,112,1182,536),40,fill=PAPER)
    # Tiny folded corner and colourful paper tab.
    d.polygon([(1130,112),(1182,164),(1130,164)],fill='#e0f4e8')
    d.rounded_rectangle((402,148,888,210),22,fill='#dff7ec')
    _center_text(d,'EL RETO DE LA CURIOSIDAD',180,(153,148,1115,210),_font(27),TEAL)
    # A restrained staged arrival: title first, subtitle after it.
    title_alpha=round(255*_ease((t-.19)/.34))
    title=Image.new('RGBA',SIZE); td=ImageDraw.Draw(title)
    _center_text(td,'CURIO',298,(160,220,802,385),_font(151),INK)
    td.rounded_rectangle((812,219,1086,383),34,fill=YELLOW)
    _center_text(td,'25',299,(812,218,1086,385),_font(145),INK)
    title.putalpha(title.getchannel('A').point(lambda a:round(a*title_alpha/255)))
    layer=Image.alpha_composite(layer,title)
    sub=Image.new('RGBA',SIZE); sd=ImageDraw.Draw(sub)
    _center_text(sd,'25 curiosidades en 5 minutos',432,(155,390,1145,475),_font(43,False),INK)
    sd.rounded_rectangle((398,480,891,487),3,fill='#7bd4c5')
    opacity=_ease((t-.44)/.34)
    sub.putalpha(sub.getchannel('A').point(lambda a:round(a*opacity)))
    layer=Image.alpha_composite(layer,sub)
    # Scale-only reveal around the card centre; never moves the full composition.
    settle=_ease(t/.48)
    scale=.88+.12*settle+.009*math.sin(min(t/.48,1)*math.pi)
    if scale<.9999:
        crop=layer.crop((78,80,1210,570))
        resized=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
        reveal=Image.new('RGBA',SIZE)
        reveal.alpha_composite(resized,(round(644-resized.width/2),round(325-resized.height/2)))
        return reveal
    return layer


def _outro_card(t):
    """Same tactile paper identity, with a yellow/fuchsia celebration accent."""
    layer=Image.new('RGBA',SIZE)
    shadow=Image.new('RGBA',SIZE); sd=ImageDraw.Draw(shadow)
    sd.rounded_rectangle((112,126,1196,554),42,fill=(7,99,120,60))
    layer=Image.alpha_composite(layer,shadow.filter(ImageFilter.GaussianBlur(13)))
    d=ImageDraw.Draw(layer)
    d.rounded_rectangle((100,104,1178,534),42,fill=YELLOW)
    d.rounded_rectangle((112,120,1190,544),42,fill='#ffafd5')
    d.rounded_rectangle((104,112,1182,536),40,fill=PAPER)
    d.polygon([(1130,112),(1182,164),(1130,164)],fill='#ffe3ef')
    d.rounded_rectangle((483,144,807,211),24,fill='#ff5fb2')
    _center_text(d,'CURIO25',180,(160,145,1130,219),_font(36),INK)
    title=Image.new('RGBA',SIZE); td=ImageDraw.Draw(title)
    # Underline arrives with the headline; it never flashes or covers the copy.
    td.rounded_rectangle((243,332,1047,345),6,fill=YELLOW)
    _center_text(td,'¡Se acabó el tiempo!',285,(155,230,1145,343),_font(80),INK)
    opacity=_ease((t-.12)/.34)
    title.putalpha(title.getchannel('A').point(lambda a:round(a*opacity)))
    layer=Image.alpha_composite(layer,title)
    sub=Image.new('RGBA',SIZE); sd=ImageDraw.Draw(sub)
    _center_text(sd,'¡Nos vemos mañana!',414,(155,365,1145,465),_font(67),INK)
    sd.rounded_rectangle((447,484,843,491),3,fill='#ff5fb2')
    opacity=_ease((t-.39)/.38)
    sub.putalpha(sub.getchannel('A').point(lambda a:round(a*opacity)))
    layer=Image.alpha_composite(layer,sub)
    scale=.90+.10*_ease(t/.42)
    if scale<.9999:
        crop=layer.crop((78,80,1210,570))
        resized=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS)
        reveal=Image.new('RGBA',SIZE)
        reveal.alpha_composite(resized,(round(644-resized.width/2),round(325-resized.height/2)))
        return reveal
    return layer


def _celebration(t):
    layer=Image.new('RGBA',SIZE); d=ImageDraw.Draw(layer); rng=random.Random(2526)
    palette=['#ffd84d','#ff5fb2','#7a6cff','#fffdf5','#b8ef55']
    elapsed=max(0,t-.12)
    # Two continuous, gravity-led ribbon bursts behind the card, not a flash.
    for side in (0,1):
        for j in range(24):
            speed=rng.uniform(170,370); angle=rng.uniform(-1.42,-.35)
            vx=math.cos(angle)*speed*(1 if side==0 else -1)
            vy=math.sin(angle)*speed
            x=(90 if side==0 else WIDTH-90)+vx*elapsed
            y=570+vy*elapsed+70*elapsed*elapsed
            r=6+j%5; a=j+t*1.7; ux,uy=math.cos(a)*r,math.sin(a)*r; vx2,vy2=-uy*.4,ux*.4
            d.polygon([(x-ux-vx2,y-uy-vy2),(x+ux-vx2,y+uy-vy2),(x+ux+vx2,y+uy+vy2),(x-ux+vx2,y-uy+vy2)],fill=palette[j%len(palette)])
    return layer


def _stopwatch(t,kind='intro'):
    layer=Image.new('RGBA',SIZE); d=ImageDraw.Draw(layer)
    cx,cy,r=1425,330,174
    # A little orbit of short rays gives this the feel of a friendly challenge.
    ray_alpha=round(160*_ease((t-.08)/.45))
    for j in range(12):
        a=math.tau*j/12
        if abs(math.sin(a))>.72: continue
        inner=r+24; outer=r+37+3*math.sin(t*2+j)
        d.line((cx+math.cos(a)*inner,cy+math.sin(a)*inner,cx+math.cos(a)*outer,cy+math.sin(a)*outer),fill=(255,252,224,ray_alpha),width=6)
    d.rounded_rectangle((1395,101,1455,170),15,fill=INK)
    d.rounded_rectangle((1379,90,1471,125),13,fill='#fff1af',outline=INK,width=6)
    d.rounded_rectangle((1554,184,1610,213),10,fill='#eaffe9',outline=INK,width=5)
    d.ellipse((cx-r+8,cy-r+15,cx+r+8,cy+r+15),fill=(5,109,132,50))
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=ORANGE if kind=='intro' else '#ff5fb2',outline=INK,width=7)
    d.ellipse((cx-r+18,cy-r+18,cx+r-18,cy+r-18),fill='#fff6cd',outline='#ffd475',width=8)
    for j in range(12):
        a=math.tau*j/12-math.pi/2
        inner=137 if j%3==0 else 143; outer=151
        d.line((cx+math.cos(a)*inner,cy+math.sin(a)*inner,cx+math.cos(a)*outer,cy+math.sin(a)*outer),fill=INK,width=5 if j%3==0 else 3)
    # Decorative moving hand remains well above the time label.
    angle=-math.pi/2+.12*math.sin(t*1.3)
    d.line((cx,cy-51,cx+math.cos(angle)*81,cy-51+math.sin(angle)*81),fill=TEAL,width=8)
    d.ellipse((cx-9,cy-60,cx+9,cy-42),fill=TEAL)
    _center_text(d,'05:00',337,(1265,278,1585,403),_font(68),INK)
    _center_text(d,'MINUTOS' if kind=='intro' else '¡RETO COMPLETO!',411,(1265,380,1585,445),_font(22),TEAL)
    # Slide less than 22px and fade in; the timer remains inside its safe envelope.
    opacity=_ease((t-.12)/.38)
    layer.putalpha(layer.getchannel('A').point(lambda a:round(a*opacity)))
    shifted=Image.new('RGBA',SIZE)
    shifted.alpha_composite(layer,(0,round(18*(1-opacity))))
    return shifted


def render_frame(time_seconds,kind='intro'):
    """Generate one deterministic RGB frame, useful for visual regression tests."""
    if kind not in ('intro','outro'): raise ValueError('Tipo de clip desconocido')
    t=max(0,float(time_seconds)); frame=_background().copy(); decor=Image.new('RGBA',SIZE); d=ImageDraw.Draw(decor)
    rng=random.Random(2525)
    # Sparse confetti, smooth velocities, no flashing or changing full-screen luminance.
    palette=['#ffd84d','#fff9e9','#ff8a3d','#ff5fb2','#7a6cff','#b8ef55','#35d6c6']
    for j in range(60):
        x=rng.uniform(48,WIDTH-48); start_y=rng.uniform(44,HEIGHT-44)
        y=44+(start_y-44+t*(11+j%4*5))%(HEIGHT-88)
        x+=7*math.sin(t*1.5+j)
        radius=rng.randrange(6,12); angle=j*.9+t*(.35 if j%2 else -.3)
        color=palette[j%len(palette)]
        if j%4==0: _star(d,(x,y),radius+3,color,angle)
        else:
            ux,uy=math.cos(angle)*radius,math.sin(angle)*radius
            vx,vy=-math.sin(angle)*radius*.4,math.cos(angle)*radius*.4
            d.polygon([(x-ux-vx,y-uy-vy),(x+ux-vx,y+uy-vy),(x+ux+vx,y+uy+vy),(x-ux+vx,y-uy+vy)],fill=color)
    for j in range(10):
        x=70+j*178+14*math.sin(j+t*.6); y=65+(j*117)%510-5*math.sin(t+j); radius=12+j%3*8
        d.ellipse((x-radius,y-radius,x+radius,y+radius),outline=(255,255,255,95),width=3)
    # Large sparkles sit away from the required copy.
    for x,y,r in [(70,218,19),(1661,131,21),(1208,561,17),(1670,507,24),(294,579,15)]:
        _star(d,(x,y),r*(.95+.05*math.sin(t*2+x)),(255,251,219,235))
    frame=Image.alpha_composite(frame,decor)
    if kind=='outro': frame=Image.alpha_composite(frame,_celebration(t))
    frame=Image.alpha_composite(frame,_paper_card(t,kind))
    frame=Image.alpha_composite(frame,_stopwatch(t,kind))
    return frame.convert('RGB')


def render_brand_clip(path,kind='intro',seconds=2.4,fps=25):
    """Encode the silent 1792×640 RGB-composed opener and its measured layout.

    The caller composites it at x64/y160; this function never touches episode
    state, audio, publication settings or the separate 300-second programme.
    """
    if kind not in ('intro','outro'): raise ValueError('Tipo de clip desconocido')
    if not 1<=seconds<=4 or not 12<=fps<=60: raise ValueError('Duración/FPS del clip fuera de límites')
    report=brand_layout(kind)
    if not report['passed']: raise ValueError(str(report['errors']))
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    command=['ffmpeg','-y','-v','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{WIDTH}x{HEIGHT}','-framerate',str(fps),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(path)]
    process=subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    frames=round(seconds*fps)
    try:
        for number in range(frames): process.stdin.write(render_frame(number/fps,kind).tobytes())
        process.stdin.close(); error=process.stderr.read().decode(); status=process.wait()
    except Exception:
        process.kill(); process.wait(); raise
    if status: raise RuntimeError(error[-4000:])
    render_frame(min(1.5,seconds-.1),kind).save(path.parent/'poster.png')
    report.update(seconds=frames/fps,fps=fps,frames=frames,audio=False,design='Original Curio25 procedural artwork')
    (path.parent/f'{kind}-layout.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report
