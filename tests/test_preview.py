"""Preview smoke tests: isolated history and explicitly unapproved facts."""
import hashlib,json
from PIL import Image
from curio25.preview import CONCEPTS,create_manifest,contact_sheet

def test_concept_count():
    assert len(CONCEPTS)==25

def test_preview_is_not_approved(tmp_path):
    staging=tmp_path/'data/candidates/media-2026-11-17'
    (staging/'images').mkdir(parents=True)
    records=[]
    facts=[]
    for i in range(25):
        photo=staging/'images'/f'{i}.jpg'
        Image.new('RGB',(900,600)).save(photo)
        records.append({
            'fact_id':f'f{i}','file':f'images/{i}.jpg',
            'status':'downloaded_unreviewed',
            'sha256':hashlib.sha256(photo.read_bytes()).hexdigest(),
            'license':'cc0','license_short':'CC0','author':'Autor ejemplo',
            'source':'https://commons.wikimedia.org/'})
        facts.append({'id':f'f{i}','title':f'Dato {i}',
            'review_status':'pending','category':'ciencia',
            'claim':'Una afirmación','narration':'Explicación breve.',
            'source_url':'https://example.org'})
    (staging/'media_report.json').write_text(json.dumps({'records':records}))
    (tmp_path/'data/candidates/2026-11-17.json').write_text(json.dumps({'facts':facts}))
    result=create_manifest(tmp_path,tmp_path/'out')
    assert len(result)==25
    assert all(f['review_status']=='pending' and f['preview_only'] for f in result)
    manifest=json.loads((tmp_path/'out/preview-manifest.json').read_text())
    assert manifest['publishable'] is False
    assert manifest['history_modified'] is False
    assert manifest['images_legally_approved']==0
    contact_sheet(result,tmp_path/'out/sheet.jpg')
    with Image.open(tmp_path/'out/sheet.jpg') as im:
        assert im.size==(1700,1350)

def test_no_upload_import():
    import inspect,curio25.preview
    src=inspect.getsource(curio25.preview)
    assert 'from .youtube import' not in src
    assert 'data/history.json' not in src
