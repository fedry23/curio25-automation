import json
from pathlib import Path
import pytest
from curio25.media import attach_media
from curio25.state import connect,reserve,begin_revision
ROOT=Path(__file__).resolve().parents[1]

def test_every_fact_has_reviewed_real_image():
    facts=json.loads((ROOT/'data/facts.json').read_text())
    rows=attach_media(ROOT,facts)
    assert len(rows)==25
    assert len({r['media_path'] for r in rows})>=11
    assert all(r['media_record']['license']=='pd' for r in rows)

def test_unknown_or_unlicensed_subject_is_blocked():
    with pytest.raises(ValueError): attach_media(ROOT,[dict(body='unknown')])

def test_revision_does_not_consume_facts_again():
    facts=json.loads((ROOT/'data/facts.json').read_text());db=connect(':memory:');reserve(db,'a',facts)
    with db: db.execute("UPDATE episodes SET status='rendered',sha='old' WHERE id='a'")
    begin_revision(db,'a')
    assert db.execute('SELECT status,sha FROM episodes').fetchone()==('reserved',None)
    assert db.execute('SELECT count(*) FROM used').fetchone()[0]==25

@pytest.mark.parametrize('status',['uploading','scheduled'])
def test_cannot_revise_uploaded_or_ambiguous_episode(status):
    db=connect(':memory:')
    with db: db.execute('INSERT INTO episodes(id,status) VALUES (?,?)',('a',status))
    with pytest.raises(ValueError): begin_revision(db,'a')
