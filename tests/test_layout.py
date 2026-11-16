import json
from pathlib import Path
from PIL import Image
import pytest
from curio25.art import panel,photo_layer
from curio25.layout import (Box,CAPTION_BAND,CAPTION_SAFE,PHOTO,caption_chunks,caption_layout,validate_scene,validate_animations)
from curio25.render import write_ass
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('fact',json.loads((ROOT/'data/facts.json').read_text()),ids=lambda f:f['id'])
def test_every_scene_has_disjoint_visual_and_caption_boxes(fact,tmp_path):
    elements=panel(fact,1,tmp_path/'panel.png')
    captions=[caption_layout(chunk) for chunk in caption_chunks(fact['narration'])]
    report=validate_scene(elements,captions)
    assert report['passed'],report['errors']
    assert all(cue['line_count']<=2 for cue in captions)
    assert all(CAPTION_SAFE.contains(Box(*cue['box'])) for cue in captions)
    assert ' '.join(caption_chunks(fact['narration']))==' '.join(fact['narration'].split())

def test_hard_wrap_splits_long_sentence_without_overflow():
    text='Una curiosidad con explicación precisa y entretenida para todos los públicos. '*8
    chunks=caption_chunks(text)
    assert len(chunks)>2
    assert all(caption_layout(c)['line_count']<=2 for c in chunks)

def test_visual_in_caption_band_is_rejected():
    report=validate_scene([dict(name='bad',box=[100,820,800,940])],[])
    assert not report['passed']

def test_overlap_is_rejected():
    report=validate_scene([dict(name='a',box=[100,100,500,300]),dict(name='b',box=[450,200,600,350])],[])
    assert not report['passed']

def test_animation_cannot_escape_photo():
    assert not validate_animations([dict(name='camera',envelope=list(PHOTO.tuple()),container=list(PHOTO.tuple()))])
    assert validate_animations([dict(name='camera',envelope=[900,320,1850,900],container=list(PHOTO.tuple()))])

def test_ass_has_real_pixel_canvas_and_two_explicit_lines(tmp_path):
    path=tmp_path/'test.ass'; write_ass(path,[(.15,2,['Primera línea','Segunda línea'])]); text=path.read_text()
    assert 'PlayResX: 1920' in text and 'PlayResY: 1080' in text
    assert r'{\an5\pos(960,955)\q2}' in text
    assert r'Primera línea\NSegunda línea' in text
    assert '\a' not in text
    assert '0:00:00.15,0:00:02.00' in text

def test_real_photo_is_fitted_to_its_reserved_box(tmp_path):
    image=tmp_path/'photo.jpg'; Image.new('RGB',(1200,700),'red').save(image)
    f=json.loads((ROOT/'data/facts.json').read_text())[0]
    f.update(media_path=str(image),media_credit='NASA / dominio público')
    elements=panel(f,1,tmp_path/'panel.png'); assert validate_scene(elements,[])['passed']
    result=Image.open(tmp_path/'panel.png'); assert result.getpixel((1000,400))[0]>240
    assert photo_layer(f,tmp_path/'layer.png')
    assert Image.open(tmp_path/'layer.png').size==(PHOTO.width*2,PHOTO.height*2)

def test_ffmpeg_rasterized_caption_stays_in_reserved_band(tmp_path):
    import shutil,subprocess
    from PIL import ImageChops
    if not shutil.which('ffmpeg'): pytest.skip('FFmpeg no disponible')
    base=tmp_path/'base.png'; Image.new('RGB',(1920,1080),'#080f1e').save(base)
    caption=caption_layout('La superficie de Venus tiene una temperatura sorprendente, y su atmósfera retiene muchísimo calor alrededor del planeta.')
    write_ass(tmp_path/'captions.ass',[(0,2,caption['lines'])])
    result=subprocess.run(['ffmpeg','-y','-v','error','-i','base.png','-vf','ass=filename=captions.ass','-frames:v','1','caption.png'],cwd=tmp_path,capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    actual=ImageChops.difference(Image.open(base).convert('RGB'),Image.open(tmp_path/'caption.png').convert('RGB')).getbbox()
    assert actual is not None
    assert CAPTION_SAFE.contains(Box(*actual)),actual
