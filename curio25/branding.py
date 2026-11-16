"""Original Curio25 five-minute opener and closer; visual-safe overlays."""
from __future__ import annotations
from .layout import VISUAL_SAFE, CAPTION_BAND, CLOCK, Box

INTRO_SECONDS=2.4
OUTRO_SECONDS=2.6

OPEN_AREA=Box(64,160,1856,800)


def programme_lengths(speech_seconds, target=300, intro=INTRO_SECONDS, outro=OUTRO_SECONDS):
    """Leave exact intro/outro room in the existing 300-second programme."""
    from .render import allocate
    if not (0<=intro<=4 and 0<=outro<=4):
        raise ValueError("Intro y outro deben durar entre 0 y 4 segundos")
    result=allocate(speech_seconds,target=target-intro-outro)
    result[0]+=intro
    result[-1]+=outro
    return result


def intro_outro_filters(index, total, scene_seconds, intro=INTRO_SECONDS, outro=OUTRO_SECONDS):
    """FFmpeg overlays do not cover the timer and never enter caption band."""
    if total!=25 or index<0 or index>=total:
        raise ValueError("Se esperan 25 curiosidades")
    assert VISUAL_SAFE.contains(OPEN_AREA) and not OPEN_AREA.intersects(CAPTION_BAND)
    assert not OPEN_AREA.intersects(CLOCK)
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    filters=[]
    if index==0 and intro:
        enable=f"lt(t,{intro:.3f})"
        filters.extend([
            f"drawbox=x=64:y=160:w=1792:h=640:color=0x101d37@0.97:t=fill:enable='{enable}'",
            f"drawtext=fontfile={font}:text='CURIO25':fontsize=108:fontcolor=0xffcf59:x=660:y=262:enable='{enable}'",
            f"drawtext=fontfile={font}:text='25 CURIOSIDADES EN 5 MINUTOS':fontsize=48:fontcolor=white:x=350:y=430:enable='{enable}'",
            f"drawtext=fontfile={font}:text='EMPIEZA EL RELOJ':fontsize=32:fontcolor=0x83e9df:x=755:y=518:enable='{enable}'",
        ])
    if index==total-1 and outro:
        start=scene_seconds-outro
        if start<0:raise ValueError("La outro no cabe al final")
        enable=f"gte(t,{start:.3f})"
        filters.extend([
            f"drawbox=x=64:y=160:w=1792:h=640:color=0x101d37@0.97:t=fill:enable='{enable}'",
            f"drawtext=fontfile={font}:text='SE ACABO EL TIEMPO':fontsize=70:fontcolor=0xffcf59:x=485:y=302:enable='{enable}'",
            f"drawtext=fontfile={font}:text='25 DATOS MAS QUE SABES':fontsize=43:fontcolor=white:x=575:y=432:enable='{enable}'",
            f"drawtext=fontfile={font}:text='NOS VEMOS EN EL SIGUIENTE':fontsize=29:fontcolor=0x83e9df:x=645:y=517:enable='{enable}'",
        ])
    return ",".join(filters)
