"""Subtitles and timestamps: one source of truth for SRT and ASS.

Keep the public imports from curio25.render for backward compatibility.
"""
from pathlib import Path

def stamp(s):
    ms=round(s*1000); return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def ass_stamp(seconds):
    centis=round(seconds*100)
    return f'{centis//360000}:{centis//6000%60:02}:{centis//100%60:02}.{centis%100:02}'

def write_ass(path,cues):
    # Explicit PlayRes prevents libass from scaling a tiny implicit 384x288 canvas.
    header="""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Nunito SemiBold,44,&H00533118,&H00533118,&H50FFFFFF,&H60FFFFFF,0,0,0,0,100,100,0,0,3,10,0,5,90,90,60,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[]
    for start,end,text_lines in cues:
        escaped=[line.replace('\\','\\\\').replace('{','\\{').replace('}','\\}') for line in text_lines]
        text=r'\N'.join(escaped)
        lines.append(rf'Dialogue: 0,{ass_stamp(start)},{ass_stamp(end)},Caption,,0,0,0,,{{\an5\pos(960,955)\q2}}'+text)
    Path(path).write_text(header+'\n'.join(lines)+'\n')


