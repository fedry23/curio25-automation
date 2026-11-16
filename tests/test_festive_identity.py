"""Integration contracts for the brighter programme without production side effects."""
import inspect,json,math
from pathlib import Path
from PIL import Image,ImageColor,ImageChops
import pytest
from curio25.theme import PALETTE,CATEGORIES,FONT_BOLD,FONT_REGULAR,category_colors,decorative_filters
from curio25.layout import PHOTO,CAPTION_BAND,CLOCK,TITLE,Box
from curio25.art import panel,photo_frame
from curio25.branding import INTRO_SECONDS,OUTRO_SECONDS,programme_lengths
ROOT=Path(__file__).resolve().parents[1]

def luminance(c):
    v=[x/255 for x in ImageColor.getrgb(c)]
    v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
    return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))
def contrast(a,b):
    x,y=sorted([luminance(a),luminance(b)])
    return (y+.05)/(x+.05)

def test_bundled_fonts_and_commercial_license():
    assert FONT_BOLD.exists() and FONT_REGULAR.exists()
    assert 'SIL OPEN FONT LICENSE' in (ROOT/'assets/fonts/OFL-Nunito.txt').read_text()
    assert (ROOT/'assets/fonts/provenance.json').exists()

def test_palette_has_playful_colors_and_readable_ink():
    assert PALETTE['yellow']=='#FFD84D' and PALETTE['pink']=='#FF5FB2'
    assert contrast(PALETTE['ink'],PALETTE['white'])>10
    for key in ['yellow','turquoise','sky','orange','pink','lime']:
        assert contrast(PALETTE['ink'],PALETTE[key])>=4.5
    assert contrast(PALETTE['ink'],PALETTE['violet'])>=3 # large bold counters only

@pytest.mark.parametrize('category',['animales','ciencia','historia','tecnología','naturaleza'])
def test_categories_have_explicit_distinct_pairs(category):
    assert category in CATEGORIES
    name,a,b=category_colors(dict(category=category))
    assert name==category and a!=b

def test_decorations_actually_move_and_stay_in_margins():
    text=decorative_filters(0)
    assert 'sin(t*' in text and decorative_filters(1)!=text
    for box in [Box(4,200,60,270),Box(1860,335,1916,405),Box(4,645,60,715),Box(1860,695,1916,765)]:
        assert not box.intersects(CAPTION_BAND)
        assert all(not box.intersects(content) for content in [PHOTO,TITLE,CLOCK])

def test_animated_photo_has_a_rounded_transparent_frame(tmp_path):
    f=dict(category='animales');p=tmp_path/'frame.png';photo_frame(f,p)
    with Image.open(p) as im:
        assert im.size==(PHOTO.width,PHOTO.height)
        assert im.getpixel((PHOTO.width//2,PHOTO.height//2))[3]==0
        assert im.getpixel((0,0))[3]==255

def test_intro_and_outro_use_existing_five_second_budget():
    assert 2<=INTRO_SECONDS<=2.5
    assert sum(programme_lengths([10]*25))==pytest.approx(300)
    assert INTRO_SECONDS+OUTRO_SECONDS==pytest.approx(5)

def test_renderer_uses_idents_before_clock_and_retains_ducking():
    from curio25.render import render
    s=inspect.getsource(render)
    assert 'render_brand_clip' in s and 'lively_mix_filter()' in s
    assert 'scene_start' in s and 'stopwatch_filters' in s
    assert 'intro_outro_filters(' not in s # old dark opener is never used
    assert 'frame_counts[-1]+=' in s

def test_preview_does_not_call_production_or_youtube():
    import curio25.preview as preview
    s=inspect.getsource(preview)
    assert 'finalize_render' not in s and 'begin_revision' not in s
    assert '.youtube' not in s and 'data/history' not in s

def test_decorative_and_clock_symbols_have_real_glyphs():
    from PIL import ImageFont
    from curio25.clock import stopwatch_filters
    symbols='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    f=ImageFont.truetype(symbols,24)
    for char in ['●','•']:
        a,b=f.getmask(char),f.getmask('\uffff')
        assert (a.size,bytes(a))!=(b.size,bytes(b))
    assert 'fontfile='+symbols in stopwatch_filters(0,300)
    assert 'fontfile='+symbols in decorative_filters(0)

def test_real_nunito_caption_raster_fits_exclusive_band(tmp_path):
    import subprocess
    from curio25.render import write_ass
    from curio25.layout import caption_layout,CAPTION_SAFE
    from curio25.theme import FONT_DIR
    base=tmp_path/'base.png';Image.new('RGB',(1920,1080),'#FFFDF5').save(base)
    text='La curiosidad es una fiesta para toda la familia, con fotografías sorprendentes, letras claras y mucho por descubrir.'
    cue=caption_layout(text)
    write_ass(tmp_path/'captions.ass',[(0,1,cue['lines'])])
    subprocess.run(['ffmpeg','-y','-v','error','-i','base.png','-vf',f"ass=filename=captions.ass:fontsdir='{FONT_DIR}'",'-frames:v','1','out.png'],cwd=tmp_path,check=True,capture_output=True)
    diff=ImageChops.difference(Image.open(base).convert('RGB'),Image.open(tmp_path/'out.png').convert('RGB')).getbbox()
    assert diff and CAPTION_SAFE.contains(Box(*diff))

def test_final_festive_demo_preserves_unapproved_status_and_timing():
    folder=ROOT/'examples/festive-identity'
    if not (folder/'validation.json').exists(): pytest.skip('Requiere preview final')
    report=json.loads((folder/'validation.json').read_text())
    assert 295<=report['duration']<=305 and (report['width'],report['height'])==(1920,1080)
    assert report['decode_errors']==0
    from curio25.state import sha
    assert report['sha256']==sha(folder/'episode.mp4')
    p=json.loads((folder/'preview-manifest.json').read_text())
    assert p['publishable'] is False and p['fact_count']==25
    assert p['facts_verified_for_publication']==p['images_legally_approved']==0
    assert p['history_modified'] is False
    layout=json.loads((folder/'layout-report.json').read_text())
    assert len(layout['scenes'])==25 and layout['passed']
    assert all(c['line_count']<=2 for s in layout['scenes'] for c in s['captions'])
    assert min(c['start'] for c in layout['scenes'][0]['captions'])>=2.4
    last=layout['scenes'][-1]
    assert max(c['end'] for c in last['captions'])<=last['branding']['start']
    assert json.loads((folder/'protected-state.json').read_text())['changed_files']==[]
