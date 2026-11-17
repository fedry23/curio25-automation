"""FFmpeg subprocess, media metadata and final MP4 validation.

No upload logic, editorial state mutation or rendering code lives here.
"""
import json
import re
import subprocess
from .state import sha

def run(args):
    result=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    if result.returncode: raise RuntimeError(result.stderr[-5000:])
    return result.stdout

def probe(path): return json.loads(run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
def duration(path): return float(probe(path)['format']['duration'])

def validate(path,expected=300):
    p=probe(path); video=next(s for s in p['streams'] if s['codec_type']=='video'); audio=next(s for s in p['streams'] if s['codec_type']=='audio')
    if (video['width'],video['height'])!=(1920,1080): raise ValueError('Resolución incorrecta')
    if abs(float(p['format']['duration'])-expected)>5: raise ValueError('Duración fuera de tolerancia')
    run(['ffmpeg','-v','error','-xerror','-err_detect','explode','-i',str(path),'-f','null','-'])
    stats=subprocess.run(['ffmpeg','-hide_banner','-i',str(path),'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True).stderr
    match=re.search(r'max_volume: ([-\d.]+) dB',stats)
    if not match or not -35<float(match[1])<0: raise ValueError('Audio ausente, demasiado bajo o saturado')
    return dict(duration=float(p['format']['duration']),width=video['width'],height=video['height'],audio_codec=audio['codec_name'],max_volume_db=float(match[1]),sha256=sha(path),decode_errors=0)

