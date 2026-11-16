import json
from pathlib import Path
import pytest
from curio25.state import sha

ROOT=Path(__file__).resolve().parents[1]
def test_complete_photographic_episode_layout():
    out=ROOT/'build/pilot-002' if (ROOT/'build/pilot-002/metadata.json').exists() else ROOT/'examples/pilot-002'
    if not (out/'metadata.json').exists(): pytest.skip('Requiere render de piloto fotográfico completo')
    report=json.loads((out/'layout-report.json').read_text()); metadata=json.loads((out/'metadata.json').read_text())
    assert report['passed'] and len(report['scenes'])==25
    assert all(s['photograph'] and s['passed'] and not s['errors'] for s in report['scenes'])
    assert all(not s['whole_frame_motion'] for s in report['scenes'])
    cues=[c for s in report['scenes'] for c in s['captions']]
    assert len(cues)>=70 and max(c['line_count'] for c in cues)<=2
    assert all(c['box'][1]>=866 and c['box'][3]<=1044 for c in cues)
    assert metadata['sha256']==sha(out/'episode.mp4')
    assert len(metadata['description'])<=5000
    assert all(s['original_media']['license']=='pd' for s in json.loads((out/'assets.json').read_text()) if s.get('fact_id'))
    for cue in (out/'captions.srt').read_text().strip().split('\n\n'):
        assert len(cue.splitlines()[2:])<=2
