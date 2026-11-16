import pytest
from curio25.stage_media import url_allowed,metadata
def test_url_guard():
    assert url_allowed('https://upload.wikimedia.org/wikipedia/commons/1/1/p.jpg')
    for url in ('https://evil.com/img.jpg','https://upload.wikimedia.org.evil.com/a','file:///tmp/x','http://upload.wikimedia.org/a'):
        assert not url_allowed(url)
def test_licenses_never_auto_approve():
    rec=dict(mime='image/jpeg',descriptionurl='https://commons.wikimedia.org/wiki/File:X.jpg',
        url='https://upload.wikimedia.org/wikipedia/commons/x.jpg',
        extmetadata=dict(License=dict(value='cc-by-sa-4.0'),Artist=dict(value='Author'),LicenseShortName=dict(value='CC BY-SA 4.0')))
    item=dict(fact_id='curio-20261117-01',file_title='File:X.jpg')
    m=metadata(item,rec);assert m['review_status']=='pending_visual_legal_review'
    rec['extmetadata']['License']['value']='cc-by-nc-4.0'
    with pytest.raises(ValueError,match='Sin autor'):
        metadata(item,rec)
