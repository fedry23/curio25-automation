"""New subjects should not inherit solar-system labels or generic images."""
import hashlib
import json
from PIL import Image
import pytest
from curio25.art import panel,thumbnail
from curio25.layout import validate_scene
from curio25.media import attach_media
from curio25.render import episode_identity


def fact(name='anfibios'):
    return {
        'id':'nature-001','body':'frog','title':'Una curiosidad de anfibios',
        'episode_topic':name,'claim':'Prueba de identidad de tema',
        'graphic':{'kind':'compare','values':[2,1],'labels':['A','B']}
    }


def test_non_solar_metadata_has_correct_title():
    topic,title=episode_identity([fact() for _ in range(25)])
    assert topic=='anfibios' and 'anfibios' in title and 'sistema solar' not in title


def test_non_solar_requires_explicit_topic():
    row=fact();del row['episode_topic']
    with pytest.raises(ValueError,match='episode_topic'):
        episode_identity([row]*25)


def test_mixed_topics_rejected():
    with pytest.raises(ValueError,match='mismo tema'):
        episode_identity([fact('anfibios'),fact('ingeniería')])


def test_subject_specific_approved_image_and_safe_layout(tmp_path):
    image_dir=tmp_path/'data/media';image_dir.mkdir(parents=True)
    img=image_dir/'frog.png';Image.new('RGB',(900,600),'green').save(img)
    sha=hashlib.sha256(img.read_bytes()).hexdigest()
    record={'fact_id':'nature-001','file':'frog.png','sha256':sha,'license':'pd',
            'author':'Curio25 test','source':'https://example.org/frog',
            'display_credit':'Ilustración de prueba · PD','license_short':'Public domain',
            'review_status':'approved'}
    (image_dir/'assets.json').write_text(json.dumps([record]))
    enriched=attach_media(tmp_path,[fact()])
    assert enriched[0]['media_record']['fact_id']=='nature-001'
    elements=panel(enriched[0],1,tmp_path/'panel.png')
    assert validate_scene(elements,[])['passed']
    thumbnail(tmp_path/'thumbnail.jpg',topic='anfibios',photo_path=str(img))
    assert Image.open(tmp_path/'thumbnail.jpg').size==(1280,720)


def test_unreviewed_image_is_blocked(tmp_path):
    image_dir=tmp_path/'data/media';image_dir.mkdir(parents=True)
    (image_dir/'assets.json').write_text(json.dumps([dict(fact_id='nature-001',review_status='pending')]))
    with pytest.raises(ValueError,match='sin revisión'):
        attach_media(tmp_path,[fact()])
