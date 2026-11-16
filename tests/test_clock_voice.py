"""Continuous, safe-area clock and upbeat narrator tests."""
import shutil, subprocess
import pytest
from PIL import Image
from curio25.clock import stopwatch_filters,timecode,clock_report
from curio25.voice_style import vocal_profile
from curio25.layout import CLOCK,FRAME,TITLE,CAPTION_BAND

@pytest.mark.parametrize("elapsed,expected",[
    (0,"00:00"),(1,"00:01"),(59,"00:59"),
    (60,"01:00"),(120,"02:00"),(299,"04:59"),(300,"05:00")
])
def test_timecodes(elapsed,expected):
    assert timecode(elapsed)==expected

def test_clock_has_separate_visual_space():
    assert FRAME.contains(CLOCK)
    assert not CLOCK.intersects(TITLE)
    assert not CLOCK.intersects(CAPTION_BAND)

def test_clock_offsets_do_not_reset_each_scene():
    first=stopwatch_filters(0,300)
    middle=stopwatch_filters(133.75,300)
    assert first!=middle and "133.7500" in middle
    assert "eif" in middle and "sin" in middle

def test_clock_report_25_increasing_scenes():
    scenes=[dict(start=i*12) for i in range(25)]
    report=clock_report(scenes,300)
    assert report["continuous_across_scenes"]
    assert report["scenes"][0]["clock"]=="00:00"
    assert report["scenes"][13]["clock"]=="02:36"
    assert report["last_frames"]=="05:00"
    with pytest.raises(ValueError):
        clock_report(scenes[::-1],300)

def test_voice_profile_variation_without_impersonation():
    chunks=[vocal_profile("alegre",5,j,3) for j in range(3)]
    assert chunks[0]!=chunks[1] and chunks[1]!=chunks[2]
    for settings in chunks:
        assert .9<settings["length_scale"]<=1
        assert .65<=settings["noise_scale"]<=.9
    assert vocal_profile("neutral",1,0,1)=={"length_scale":1.0}
    with pytest.raises(ValueError):
        vocal_profile("xpressvoice",0,0,1)

@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="FFmpeg not installed")
def test_clock_filter_renders_actual_frame(tmp_path):
    target=tmp_path/"clock.png"
    subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i",
        "color=c=black:s=1920x180:d=0.12","-vf",stopwatch_filters(123,300),
        "-frames:v","1","-y",str(target)],check=True,capture_output=True)
    with Image.open(target) as image:
        assert image.size==(1920,180)
