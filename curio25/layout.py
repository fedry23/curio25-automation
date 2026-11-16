"""Pixel-based safe areas shared by artwork, subtitles, renderer and checks."""
from dataclasses import dataclass
from pathlib import Path
from PIL import ImageFont
import re

WIDTH, HEIGHT = 1920, 1080
from .theme import FONT_REGULAR,FONT_BOLD
FONT = str(FONT_REGULAR)
BOLD = str(FONT_BOLD)
CAPTION_FONT_SIZE = 44
CAPTION_LINE_GAP = 10
CAPTION_MAX_WIDTH = 1680
CAPTION_CENTER = (960, 955)

@dataclass(frozen=True)
class Box:
    x1: int
    y1: int
    x2: int
    y2: int
    def tuple(self): return (self.x1, self.y1, self.x2, self.y2)
    @property
    def width(self): return self.x2-self.x1
    @property
    def height(self): return self.y2-self.y1
    def contains(self, other):
        return self.x1 <= other.x1 <= other.x2 <= self.x2 and self.y1 <= other.y1 <= other.y2 <= self.y2
    def intersects(self, other):
        return min(self.x2, other.x2)>max(self.x1, other.x1) and min(self.y2, other.y2)>max(self.y1, other.y1)

FRAME=Box(0,0,WIDTH,HEIGHT)
VISUAL_SAFE=Box(64,48,1856,824)
CAPTION_BAND=Box(0,840,1920,1080)
CAPTION_SAFE=Box(90,866,1830,1044)
TITLE=Box(90,160,1820,300)
PHOTO=Box(900,310,1820,758)
GRAPH=Box(90,390,840,742)
CREDIT=Box(900,772,1820,814)
PROGRESS=Box(90,799,840,811)
CLOCK=Box(1360,57,1662,145)

def font(size, bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)

def wrap_pixels(text, face, maximum):
    words=text.split(); lines=[]; line=''
    for word in words:
        if face.getlength(word)>maximum:
            raise ValueError('Palabra demasiado ancha para la caja: '+word)
        candidate=(line+' '+word).strip()
        if face.getlength(candidate)<=maximum: line=candidate
        else: lines.append(line); line=word
    if line: lines.append(line)
    return lines

def fit_text(text, box, maximum_size, minimum_size=16, max_lines=2, bold=False, gap=8):
    for size in range(maximum_size,minimum_size-1,-1):
        face=font(size,bold); lines=wrap_pixels(text,face,box.width)
        asc,desc=face.getmetrics(); height=len(lines)*(asc+desc)+max(0,len(lines)-1)*gap
        if len(lines)<=max_lines and height<=box.height:
            return lines,face,size,height
    raise ValueError(f'Texto no cabe en caja {box.tuple()}: {text}')

def caption_chunks(text):
    """Split before TTS, so every displayed cue has its own measured audio."""
    face=font(CAPTION_FONT_SIZE)
    # Preserve complete sentences wherever they fit; split long ones by measured lines.
    sentences=re.split(r'(?<=[.!?])\s+',text.strip()); chunks=[]
    for sentence in sentences:
        lines=wrap_pixels(sentence,face,CAPTION_MAX_WIDTH)
        for start in range(0,len(lines),2):
            chunks.append(' '.join(lines[start:start+2]))
    return chunks

def caption_layout(text):
    face=font(CAPTION_FONT_SIZE); lines=wrap_pixels(text,face,CAPTION_MAX_WIDTH)
    if len(lines)>2 or not lines: raise ValueError('Subtítulo requiere más de dos líneas o está vacío')
    asc,desc=face.getmetrics(); height=len(lines)*(asc+desc)+(len(lines)-1)*CAPTION_LINE_GAP
    width=max(face.getlength(line) for line in lines)
    box=Box(round(CAPTION_CENTER[0]-width/2)-13, round(CAPTION_CENTER[1]-height/2)-13,
            round(CAPTION_CENTER[0]+width/2)+13,round(CAPTION_CENTER[1]+height/2)+13)
    if not CAPTION_SAFE.contains(box): raise ValueError('Subtítulo fuera de la franja reservada')
    return dict(lines=lines,line_count=len(lines),font_size=CAPTION_FONT_SIZE,box=list(box.tuple()))

def validate_scene(elements,captions):
    errors=[]; boxes=[]
    for element in elements:
        box=Box(*element['box']); boxes.append((element['name'],box))
        if not VISUAL_SAFE.contains(box): errors.append(element['name']+': fuera de área visual segura')
        if box.intersects(CAPTION_BAND): errors.append(element['name']+': invade subtítulos')
    for i,(name,box) in enumerate(boxes):
        for other_name,other_box in boxes[i+1:]:
            if box.intersects(other_box): errors.append(name+': solapa '+other_name)
    for i,cue in enumerate(captions):
        box=Box(*cue['box'])
        if cue['line_count']>2 or not CAPTION_SAFE.contains(box): errors.append(f'caption-{i}: fuera de caja o >2 líneas')
        for name,other in boxes:
            if box.intersects(other): errors.append(f'caption-{i}: solapa {name}')
    return dict(passed=not errors,errors=errors,visual_safe=list(VISUAL_SAFE.tuple()),caption_band=list(CAPTION_BAND.tuple()),elements=elements,captions=captions)

def validate_animations(animations):
    errors=[]
    for item in animations:
        envelope=Box(*item['envelope']); container=Box(*item['container'])
        if not container.contains(envelope) or not VISUAL_SAFE.contains(envelope): errors.append(item['name']+': animación fuera de caja')
        if envelope.intersects(CAPTION_BAND): errors.append(item['name']+': animación invade subtítulos')
    return errors
