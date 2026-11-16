from pathlib import Path
import shutil
import subprocess
import json
import pytest
from PIL import ImageChops
from curio25.festive_branding import (SIZE,SAFE,brand_layout,render_frame,render_brand_clip)


def test_intro_required_copy_and_safe_text_boxes():
    layout=brand_layout()
    assert layout['passed'],layout['errors']
    assert layout['size']==[1792,640]
    copy={r['text'] for r in layout['text_boxes']}
    assert {'CURIO','25','25 curiosidades en 5 minutos','05:00'}<=copy
    for item in layout['text_boxes']:
        x1,y1,x2,y2=item['box']
        assert SAFE[0]<=x1<x2<=SAFE[2]
        assert SAFE[1]<=y1<y2<=SAFE[3]


def test_procedural_animation_is_deterministic_and_rgb():
    first=render_frame(.2); later=render_frame(1.6)
    assert first.size==SIZE and first.mode=='RGB'
    assert ImageChops.difference(first,render_frame(.2)).getbbox() is None
    assert ImageChops.difference(first,later).getbbox() is not None


def test_unknown_kind_is_not_generated(tmp_path):
    with pytest.raises(ValueError): render_brand_clip(tmp_path/'unknown.mp4',kind='unknown')
    assert not (tmp_path/'unknown.mp4').exists()


@pytest.mark.parametrize('kind',['intro','outro'])
def test_final_title_boxes_do_not_overlap(kind):
    entries=brand_layout(kind)['text_boxes']
    for i,a in enumerate(entries):
        for b in entries[i+1:]:
            ax1,ay1,ax2,ay2=a['box']; bx1,by1,bx2,by2=b['box']
            assert min(ax2,bx2)<=max(ax1,bx1) or min(ay2,by2)<=max(ay1,by1),(a,b)


def test_intro_encodes_exact_size_duration_without_audio(tmp_path):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): pytest.skip('FFmpeg no disponible')
    report=render_brand_clip(tmp_path/'intro.mp4',seconds=1,fps=12)
    result=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(tmp_path/'intro.mp4')],capture_output=True,text=True,check=True)
    data=json.loads(result.stdout); video=data['streams'][0]
    assert (video['width'],video['height'])==SIZE
    assert len(data['streams'])==1 and video['codec_type']=='video'
    assert float(data['format']['duration'])==pytest.approx(1,abs=.04)
    assert report['frames']==12 and report['audio'] is False
    assert (tmp_path/'poster.png').exists()


def test_outro_exact_copy_and_safe_boxes():
    layout=brand_layout('outro')
    assert layout['passed'],layout['errors']
    assert {'¡Se acabó el tiempo!','¡Nos vemos mañana!'}<={item['text'] for item in layout['text_boxes']}
    for item in layout['text_boxes']:
        x1,y1,x2,y2=item['box']
        assert SAFE[0]<=x1<x2<=SAFE[2]
        assert SAFE[1]<=y1<y2<=SAFE[3]


def test_outro_has_real_animation_and_distinct_design():
    first=render_frame(.2,'outro'); later=render_frame(1.7,'outro')
    assert later.size==SIZE and later.mode=='RGB'
    assert ImageChops.difference(first,later).getbbox() is not None
    assert ImageChops.difference(later,render_frame(1.7,'intro')).getbbox() is not None


def test_outro_keeps_prescribed_duration_and_no_audio(tmp_path):
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'): pytest.skip('FFmpeg no disponible')
    report=render_brand_clip(tmp_path/'outro.mp4',kind='outro',seconds=2.6,fps=25)
    data=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(tmp_path/'outro.mp4')],capture_output=True,text=True,check=True).stdout)
    assert report['frames']==65 and report['seconds']==2.6
    assert len(data['streams'])==1 and data['streams'][0]['codec_type']=='video'
    assert float(data['format']['duration'])==pytest.approx(2.6,abs=.04)
