from curio25.state import connect, confirm_publication, published_count, export_history, restore
import pytest

def test_publication_counter(tmp_path):
    db = connect(':memory:')
    db.executemany('INSERT INTO episodes(id,status,video_id) VALUES (?,?,?)', [
        ('pilot','rendered',None), ('daily-2026-11-19','scheduled','abc')])
    assert published_count(db) == 0
    video = {'id':'abc','status':{'privacyStatus':'private','uploadStatus':'processed'}}
    assert not confirm_publication(db,'daily-2026-11-19',video)
    video['status']['privacyStatus'] = 'public'
    with pytest.raises(ValueError):
        confirm_publication(db,'pilot',video)
    assert confirm_publication(db,'daily-2026-11-19',video)
    assert confirm_publication(db,'daily-2026-11-19',video)
    assert published_count(db) == 1
    path = tmp_path / 'history.json'
    export_history(db,path)
    restored = connect(':memory:')
    restore(restored,path)
    assert published_count(restored) == 1


def test_pilot_and_duplicate_never_count():
    db=connect(':memory:')
    db.executemany('INSERT INTO episodes(id,status,video_id) VALUES (?,?,?)',[
        ('pilot-001','published','pilot'),
        ('daily-2026-11-19','scheduled','same'),
        ('daily-2026-11-20','scheduled','same')])
    assert published_count(db)==0
    video={'id':'same','snippet':{'channelId':'channel'},'status':{'privacyStatus':'public','uploadStatus':'processed'}}
    with pytest.raises(ValueError):
        confirm_publication(db,'daily-2026-11-19',video,'other')
    with pytest.raises(ValueError):
        confirm_publication(db,'daily-2026-11-19',video,'channel')
    assert published_count(db)==0


def test_reconcile_uses_read_only_api_and_persists(tmp_path):
    from curio25.youtube import reconcile
    from unittest.mock import Mock
    (tmp_path/'data').mkdir()
    db=connect(tmp_path/'data/history.sqlite')
    with db:
        db.executemany('INSERT INTO episodes(id,status,video_id) VALUES (?,?,?)',[
            ('daily-2026-11-19','scheduled','public'),
            ('daily-2026-11-20','scheduled','private'),
            ('daily-2026-11-21','uploading',None),
            ('pilot-001','scheduled','pilot')])
    db.close()
    api=Mock()
    api.videos.return_value.list.return_value.execute.return_value={'items':[
        {'id':'public','snippet':{'channelId':'channel'},'status':{'privacyStatus':'public','uploadStatus':'processed'}},
        {'id':'private','snippet':{'channelId':'channel'},'status':{'privacyStatus':'private','uploadStatus':'processed'}}]}
    report=reconcile(tmp_path,{'channel_id':'channel'},api)
    assert report=={'confirmed':['daily-2026-11-19'],'pending':['daily-2026-11-20'],'published_count':1}
    api.videos.return_value.list.assert_called_once_with(part='id,snippet,status',id='private,public')
    api.videos.return_value.insert.assert_not_called()
    restored=connect(':memory:')
    restore(restored,tmp_path/'data/history.json')
    assert published_count(restored)==1
    assert reconcile(tmp_path,{'channel_id':'channel'},api)['published_count']==1
