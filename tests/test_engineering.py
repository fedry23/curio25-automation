"""Safe engineering refactor: API compatibility and state durability."""
import json
import os
from pathlib import Path
import pytest

from curio25 import render
from curio25 import captions,video_io,episode_meta
from curio25.state import connect,export_history,reserve


def test_public_render_api_remains_compatible():
    assert render.stamp is captions.stamp
    assert render.write_ass is captions.write_ass
    assert render.validate is video_io.validate
    assert render.episode_identity is episode_meta.episode_identity
    assert render.run is video_io.run
    assert render.probe is video_io.probe
    assert render.duration is video_io.duration


def test_caption_formats_are_stable(tmp_path):
    assert render.stamp(65.123)=='00:01:05,123'
    file=tmp_path/'captions.ass'
    render.write_ass(file,[(.15,2,['Primera línea','Segunda línea'])])
    raw=file.read_text()
    assert 'PlayResX: 1920' in raw and r'Primera línea\NSegunda línea' in raw


def test_atomic_history_roundtrip(tmp_path):
    db=connect(':memory:')
    facts=json.loads((Path(__file__).resolve().parents[1]/'data/facts.json').read_text())
    reserve(db,'atomic-case',facts)
    path=tmp_path/'history.json'
    export_history(db,path)
    first=path.read_bytes()
    assert json.loads(first)['episodes'][0]['status']=='reserved'
    export_history(db,path)
    assert path.read_bytes()==first
    assert not list(tmp_path.glob('.history.json.*.tmp'))


def test_failed_history_serialization_leaves_previous_intact(monkeypatch,tmp_path):
    from curio25 import state
    db=connect(':memory:')
    path=tmp_path/'history.json'
    path.write_text('{"valid": true}\n')
    original=path.read_bytes()
    def fail(*args,**kwargs):
        raise ValueError('artificial serialization failure')
    monkeypatch.setattr(state.json,'dumps',fail)
    with pytest.raises(ValueError,match='artificial'):
        state.export_history(db,path)
    assert path.read_bytes()==original
    assert not list(tmp_path.glob('.history.json.*.tmp'))


def test_metadata_still_rejects_mixed_topics():
    with pytest.raises(ValueError,match='tema de episodio'):
        episode_meta.episode_identity([
          dict(body='frog',episode_topic='animales'),
          dict(body='frog',episode_topic='tecnología')
        ])
