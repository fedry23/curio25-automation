import json,sqlite3
from pathlib import Path
from datetime import datetime,timezone
import pytest
from curio25.render import allocate,stamp
from curio25.state import connect,reserve,export_history,restore,sha
from curio25.youtube import gate,publish_at
from curio25.__main__ import load_facts
ROOT=Path(__file__).resolve().parents[1]

def facts(): return json.loads((ROOT/'data/facts.json').read_text())
def test_source_catalog():
    db=connect(':memory:'); rows=load_facts(ROOT,db)
    assert len(rows)==25
    assert all(len(f['narration'].split())>=25 for f in rows)
    assert all(f['evidence_excerpt'] for f in rows)
def test_25_and_duplicates():
    db=connect(':memory:')
    with pytest.raises(ValueError): reserve(db,'bad',facts()[:24])
    reserve(db,'first',facts())
    with pytest.raises(sqlite3.IntegrityError): reserve(db,'second',facts())
    assert not db.execute("SELECT * FROM episodes WHERE id='second'").fetchall()
def test_claim_duplicate_with_new_id():
    db=connect(':memory:'); reserve(db,'a',facts()); other=facts()
    for f in other: f['id']+='new'
    with pytest.raises(sqlite3.IntegrityError): reserve(db,'b',other)
def test_history_roundtrip(tmp_path):
    db=connect(':memory:'); reserve(db,'a',facts()); path=tmp_path/'history.json'; export_history(db,path)
    fresh=connect(':memory:'); restore(fresh,path)
    assert fresh.execute('SELECT count(*) FROM used').fetchone()[0]==25
    with pytest.raises(ValueError): load_facts(ROOT,fresh)
def test_duration_no_speedup():
    assert sum(allocate([11]*25))==pytest.approx(300)
    with pytest.raises(ValueError): allocate([13]*25)
    with pytest.raises(ValueError): allocate([3]*25)
    with pytest.raises(ValueError): allocate([11]*24)
def test_subtitle_timestamp(): assert stamp(65.123)=='00:01:05,123'
def test_upload_disabled(tmp_path):
    video=tmp_path/'video'; video.write_bytes(b'test')
    with pytest.raises(PermissionError): gate({'publication_enabled':False},video,{})
def test_approval_bound_to_file(tmp_path):
    video=tmp_path/'video'; video.write_bytes(b'test'); config=dict(publication_enabled=True,channel_id='own',approved_episode_sha256=sha(video))
    metadata=dict(sha256=sha(video),contains_synthetic_media=False); gate(config,video,metadata)
    video.write_bytes(b'changed')
    with pytest.raises(PermissionError): gate(config,video,metadata)
@pytest.mark.parametrize('date,hour',[('2026-01-15T12:00:00+00:00',17),('2026-07-15T12:00:00+00:00',16)])
def test_madrid_dst(date,hour):
    result=datetime.fromisoformat(publish_at(dict(timezone='Europe/Madrid',publish_hour='18:00'),datetime.fromisoformat(date)))
    assert result.hour==hour
def test_next_day():
    result=publish_at(dict(timezone='Europe/Madrid',publish_hour='18:00'),datetime(2026,7,15,20,tzinfo=timezone.utc))
    assert result.startswith('2026-07-16T16:00')
def test_commons_rejects_unlicensed(monkeypatch,tmp_path):
    import curio25.sources as sources
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'query':{'pages':{'1':{'imageinfo':[{'extmetadata':{'License':{'value':'all-rights-reserved'}}}]}}}}
    class Session:
        def get(self,*a,**kw): return Response()
    monkeypatch.setattr(sources,'session',lambda:Session())
    with pytest.raises(ValueError): sources.commons_asset('File:unknown.jpg',tmp_path)

def test_complete_pilot_artifacts():
    out=next((ROOT/p for p in ['build/pilot-002','examples/pilot-002','build/pilot-001'] if (ROOT/p/'metadata.json').exists()),ROOT/'build/pilot-002')
    if not (out/'metadata.json').exists(): pytest.skip('Se ejecuta tras el render completo')
    metadata=json.loads((out/'metadata.json').read_text()); script=json.loads((out/'script.json').read_text())
    assert metadata['sha256']==sha(out/'episode.mp4')
    assert len(script)==len(metadata['chapters'])==25
    starts=[c['start'] for c in metadata['chapters']]
    assert starts[0]==0 and all(b>a for a,b in zip(starts,starts[1:]))
    assert min(b-a for a,b in zip(starts,starts[1:]))>=10
    assert len(metadata['title'])<=100 and len(metadata['description'])<=5000
    cues=(out/'captions.srt').read_text().split('\n\n')
    assert len(cues)>=70
    assert len(json.loads((out/'assets.json').read_text()))==26
    assert json.loads((ROOT/'config.json').read_text())['publication_enabled'] is False

def test_resumed_reservation_requires_review():
    from curio25.__main__ import validate_facts
    rows=facts(); rows[0]['review_status']='pending'
    with pytest.raises(ValueError): validate_facts(ROOT,rows)

def test_source_hash_cannot_be_swapped():
    from curio25.__main__ import validate_facts
    rows=facts(); rows[0]['source_snapshot_sha256']='wrong'
    with pytest.raises(ValueError): validate_facts(ROOT,rows)

def test_official_scopes_include_caption_upload():
    from curio25.youtube import SCOPES
    assert 'https://www.googleapis.com/auth/youtube.force-ssl' in SCOPES

def test_edited_reserved_script_records_final_provenance():
    import hashlib
    from curio25.state import finalize_render
    db=connect(':memory:'); original=facts(); reserve(db,'edited',original)
    rendered=facts(); rendered[0]['narration']+=' Explicación revisada antes de finalizar.'
    finalize_render(db,'edited',rendered,'video-final-sha')
    saved=db.execute('SELECT narration_sha256 FROM episode_sources WHERE episode=? AND fact_id=?',('edited',rendered[0]['id'])).fetchone()[0]
    assert saved==hashlib.sha256(rendered[0]['narration'].encode()).hexdigest()
    payload=json.loads(db.execute('SELECT payload FROM catalog WHERE fact_id=?',(rendered[0]['id'],)).fetchone()[0])
    assert payload['narration']==rendered[0]['narration']
    assert db.execute('SELECT status,sha FROM episodes').fetchone()==('rendered','video-final-sha')

def test_finalize_rejects_different_reservation():
    from curio25.state import finalize_render
    db=connect(':memory:'); reserve(db,'a',facts()); other=facts(); other[0]['id']='other'
    with pytest.raises(ValueError): finalize_render(db,'a',other,'new-sha')
    assert db.execute('SELECT status FROM episodes').fetchone()[0]=='reserved'

@pytest.mark.parametrize('advanced',['uploading','scheduled'])
def test_restore_preserves_advanced_upload_state(tmp_path,advanced):
    db=connect(':memory:'); reserve(db,'a',facts())
    with db: db.execute("UPDATE episodes SET status='rendered',sha='same-sha' WHERE id='a'")
    path=tmp_path/'history.json'; export_history(db,path); saved=json.loads(path.read_text()); saved['episodes'][0]['status']=advanced
    if advanced=='scheduled': saved['episodes'][0]['video_id']='existing-video'
    path.write_text(json.dumps(saved)); restore(db,path)
    assert db.execute("SELECT status FROM episodes WHERE id='a'").fetchone()[0]==advanced

def test_restore_rejects_conflicting_video_hash(tmp_path):
    db=connect(':memory:'); reserve(db,'a',facts())
    with db: db.execute("UPDATE episodes SET status='rendered',sha='original' WHERE id='a'")
    path=tmp_path/'history.json'; export_history(db,path); saved=json.loads(path.read_text()); saved['episodes'][0]['sha']='different'; path.write_text(json.dumps(saved))
    with pytest.raises(ValueError): restore(db,path)
    assert db.execute('SELECT sha FROM episodes').fetchone()[0]=='original'
