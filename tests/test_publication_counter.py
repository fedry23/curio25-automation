from curio25.state import connect, confirm_publication, published_count, export_history, restore
import pytest

def test_publication_counter(tmp_path):
    db = connect(':memory:')
    db.executemany('INSERT INTO episodes(id,status,video_id) VALUES (?,?,?)', [
        ('pilot','rendered',None), ('daily','scheduled','abc')])
    assert published_count(db) == 0
    video = {'id':'abc','status':{'privacyStatus':'private','uploadStatus':'processed'}}
    assert not confirm_publication(db,'daily',video)
    video['status']['privacyStatus'] = 'public'
    with pytest.raises(ValueError):
        confirm_publication(db,'pilot',video)
    assert confirm_publication(db,'daily',video)
    assert confirm_publication(db,'daily',video)
    assert published_count(db) == 1
    path = tmp_path / 'history.json'
    export_history(db,path)
    restored = connect(':memory:')
    restore(restored,path)
    assert published_count(restored) == 1
