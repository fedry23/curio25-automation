"""Checks for 2.4 s intro + 2.6 s outro, lively narration and musical ducking."""
import shutil
import subprocess
import wave

import numpy as np
import pytest

from curio25.branding import INTRO_SECONDS, OUTRO_SECONDS, programme_lengths, intro_outro_filters
from curio25.soundtrack import original_music, lively_mix_filter
from curio25.voice_style import vocal_profile


def test_intro_outro_do_not_extend_five_minutes():
    scenes=programme_lengths([10.5]*25)
    assert len(scenes)==25
    assert sum(scenes)==pytest.approx(300)
    assert scenes[0]>scenes[1] and scenes[-1]>scenes[-2]
    assert INTRO_SECONDS+OUTRO_SECONDS==pytest.approx(5)


def test_intro_outro_graphics_are_in_separate_scenes_and_safe():
    first=intro_outro_filters(0,25,14,INTRO_SECONDS,OUTRO_SECONDS)
    middle=intro_outro_filters(12,25,12,INTRO_SECONDS,OUTRO_SECONDS)
    last=intro_outro_filters(24,25,15,INTRO_SECONDS,OUTRO_SECONDS)
    assert "CURIO25" in first and "25 CURIOSIDADES" in first
    assert middle==""
    assert "SE ACABO EL TIEMPO" in last
    assert "gte(t,12.400)" in last
    with pytest.raises(ValueError):
        programme_lengths([10]*25,intro=5)


def test_enthusiastic_voice_remains_in_safe_range():
    outputs=[vocal_profile("entusiasta",0,i,3) for i in range(3)]
    assert len({tuple(sorted(x.items())) for x in outputs})==3
    assert all(.90 <= x["length_scale"]<=1.0 for x in outputs)
    assert all(.70 <= x["noise_scale"]<=.85 for x in outputs)


def test_original_music_is_audible_and_unique(tmp_path):
    path=tmp_path/"fun.wav"
    original_music(path,2)
    with wave.open(str(path)) as f:
        assert f.getframerate()==22050
        assert f.getnchannels()==1
        raw=np.frombuffer(f.readframes(f.getnframes()),dtype="<i2").astype(np.float64)/32767
    assert np.max(np.abs(raw)) > .13
    assert np.sqrt(np.mean(raw**2)) > .025
    assert np.std(raw[:11025]-raw[11025:22050]) > .01


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="No FFmpeg")
def test_dynamic_music_ducking_ffmpeg_runs(tmp_path):
    out=tmp_path/"mixed.wav"
    cmd=["ffmpeg","-v","error","-y","-f","lavfi","-i",
         "sine=frequency=330:sample_rate=22050:duration=1.3",
         "-f","lavfi","-i","sine=frequency=550:sample_rate=22050:duration=1.3",
         "-filter_complex",lively_mix_filter(),"-map","[a]",str(out)]
    p=subprocess.run(cmd,text=True,capture_output=True,timeout=40)
    assert p.returncode==0,p.stderr


@pytest.mark.skipif(not shutil.which("ffmpeg"),reason="No FFmpeg")
def test_intro_outro_overlay_rasterizes(tmp_path):
    for idx in (0,24):
        filters=intro_outro_filters(idx,25,12,INTRO_SECONDS,OUTRO_SECONDS)
        out=tmp_path/f"{idx}.png"
        cmd=["ffmpeg","-v","error","-y","-f","lavfi","-i",
             "color=c=black:s=1920x1080:r=25:d=1",
             "-vf",filters,"-frames:v","1",str(out)]
        run=subprocess.run(cmd,text=True,capture_output=True,timeout=20)
        assert run.returncode==0,run.stderr
        assert out.exists()
