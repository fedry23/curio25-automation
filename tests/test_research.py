import pytest
from curio25.research import safe,evidence,licensed_candidate

@pytest.mark.parametrize('url',['https://www.noaa.gov/a','https://science.nasa.gov/a','https://www.nps.gov/a','https://guides.loc.gov/a'])
def test_allowed_sources(url):assert safe(url)

@pytest.mark.parametrize('url',['http://www.noaa.gov','https://www.noaa.gov.evil.org','file:///etc/passwd','https://x:y@noaa.gov/','https://noaa.gov:8443/x'])
def test_reject_urls(url):assert not safe(url)

def test_evidence_match():assert evidence('The  97 percent belongs here','97  PERCENT')

def test_reject_noncommercial():
    assert licensed_candidate({'mime':'image/jpeg','extmetadata':{'License':{'value':'cc-by-nc-4.0'},'Artist':{'value':'Author'}}}) is None

def test_approved_flag_is_always_false():
    x=licensed_candidate({'mime':'image/jpeg','url':'https://upload.wikimedia.org/f.jpg','descriptionurl':'https://commons.wikimedia.org/wiki/F',
    'extmetadata':{'License':{'value':'cc-by-4.0'},'Artist':{'value':'Author'},'LicenseShortName':{'value':'CC BY 4.0'}}})
    assert x and not x['approved'] and not x['reviewed']
