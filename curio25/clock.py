"""Curio25's continuous five-minute on-screen stopwatch."""
from __future__ import annotations
from .layout import CLOCK, CAPTION_BAND, VISUAL_SAFE

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def timecode(seconds: float) -> str:
    if seconds < 0 or seconds > 300.5:
        raise ValueError("El reloj admite vídeos de hasta cinco minutos")
    whole = min(300, int(seconds+1e-6))
    return f"{whole//60:02}:{whole%60:02}"


def stopwatch_filters(scene_start: float, target_seconds: float) -> str:
    """Animated FFmpeg overlay, with scene-relative t adjusted to elapsed video."""
    if abs(target_seconds-300)>0.01:
        raise ValueError("Este cronómetro requiere 300 segundos")
    if not 0<=scene_start<301:
        raise ValueError("Inicio de escena fuera de rango")
    assert VISUAL_SAFE.contains(CLOCK) and not CLOCK.intersects(CAPTION_BAND)
    elapsed=f"(t+{scene_start:.4f})"
    display=f"(t+{scene_start:.4f}+0.40)"
    minutes="%{eif\\:floor("+display+"/60)\\:d\\:2}"
    seconds="%{eif\\:mod(floor("+display+"),60)\\:d\\:2}"
    text=minutes+r"\:"+seconds
    angle=f"(2*PI*{elapsed}/300)"
    return (
        f"drawtext=fontfile={FONT}:text='{text}':fontsize=36:"
        "fontcolor=0xffce54:x=1465:y=73,"
        "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
        "text='●':fontsize=20:fontcolor=0x83e9df:"
        f"x='1416+29*sin({angle})-10':y='101-29*cos({angle})-10'"
    )


def clock_report(chapters: list[dict], target_seconds: float) -> dict:
    if abs(target_seconds-300)>0.01 or len(chapters)!=25:
        raise ValueError("El reloj necesita 25 capítulos en cinco minutos")
    starts=[float(c['start']) for c in chapters]
    if abs(starts[0])>0.001 or any(b<=a for a,b in zip(starts,starts[1:])):
        raise ValueError("Tiempo de los capítulos no es creciente")
    if starts[-1]>=target_seconds:
        raise ValueError("Último capítulo fuera del vídeo")
    return dict(duration_seconds=target_seconds,first_frame="00:00",
                last_frames="05:00",continuous_across_scenes=True,
                box=list(CLOCK.tuple()),subtitle_overlap=False,
                scenes=[dict(scene=i+1,offset_seconds=round(s,3),clock=timecode(s))
                        for i,s in enumerate(starts)])
