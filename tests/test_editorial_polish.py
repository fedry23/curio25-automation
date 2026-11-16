"""Editorial entertainment, voice pronunciation and soundtrack regression."""
import json
from pathlib import Path

from curio25.preview import EDITORIAL_ORDER,programme_order,CONCEPTS
from curio25.voice_style import for_speech,vocal_profile
from curio25.soundtrack import RATE,BPM,MELODY,original_music,lively_mix_filter

ROOT=Path(__file__).resolve().parents[1]


def test_fact_order_alternates_topics_without_changing_ids():
    original=json.loads((ROOT/'data/candidates/2026-11-17.json').read_text())['facts']
    result=programme_order(original)
    assert len(EDITORIAL_ORDER)==25 and len(set(EDITORIAL_ORDER))==25
    assert len(result)==25 and set(f['id'] for f in original)==set(f['id'] for f in result)
    categories=[f['category'] for f in result]
    assert all(a!=b for a,b in zip(categories,categories[1:])),categories
    assert len(CONCEPTS)==25


def test_entertaining_narration_stays_bounded_and_not_approved():
    items=json.loads((ROOT/'data/candidates/2026-11-17.json').read_text())['facts']
    words=[len(f['narration'].split()) for f in items]
    assert len(items)==25 and all(22<=w<=35 for w in words)
    assert sum(words)<=740
    assert all(f['review_status']=='pending' for f in items)
    assert sum('¿' in f['narration'] or '¡' in f['narration'] for f in items)>=14
    assert all(f.get('source_url') for f in items)


def test_voice_speech_spelling_keeps_subtitles_pristine():
    phrase="NOAA, Yellowstone y los hermanos Wright"
    spoken=for_speech(phrase)
    assert 'NOAA' not in spoken and 'Wright' not in spoken
    assert 'Yélouston' in spoken
    assert phrase=="NOAA, Yellowstone y los hermanos Wright"
    assert vocal_profile('entusiasta',5,0,3,'¡Increíble!')!=vocal_profile('entusiasta',5,0,3,'Es un dato.')


def test_music_is_rearranged_and_has_ducking(tmp_path):
    assert BPM==116 and len(MELODY)==32
    assert "sidechaincompress" in lively_mix_filter()
    import numpy as np
    import wave
    p=tmp_path/'music.wav'
    original_music(p,2)
    with wave.open(str(p)) as w:
        assert w.getframerate()==RATE
        assert w.getnchannels()==1
        y=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')/32767
    assert len(y)==RATE*2
    assert np.max(np.abs(y))>.13
    assert np.sqrt(np.mean(y*y))>.025
