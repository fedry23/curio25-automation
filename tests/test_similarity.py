import json
from curio25.similarity import compare, screen


def test_punctuation_case_accents():
    assert compare({'claim':'¡La Luna gira!'}, {'claim':'la luna GÍRA'})=='exact'


def test_explicit_concept_flags_paraphrase():
    assert compare({'claim':'El animal vive mucho','concept_key':'animal:longevity'},
                   {'claim':'Supera varias décadas','concept_key':'animal:longevity'})=='same_concept'


def test_related_but_different_claims():
    assert compare({'claim':'El pulpo tiene tres corazones'},
                   {'claim':'El pulpo tiene sangre azul'}) is None


def test_high_overlap_reorder():
    assert compare({'claim':'El sonido viaja más rápido bajo agua marina'},
                   {'claim':'Bajo agua marina el sonido viaja rápido'})=='high_overlap'


def test_archive_cross_batch_and_catalogue(tmp_path):
    folder=tmp_path/'data/candidates'
    folder.mkdir(parents=True)
    (tmp_path/'data/facts.json').write_text(json.dumps([{'id':'old','claim':'El coral es un animal'}]))
    (folder/'2026-11-18.json').write_text(json.dumps({'facts':[{'id':'draft','claim':'La Luna gira'}]}))
    (folder/'2026-11-19.json').write_text(json.dumps({'facts':[{'id':'new','claim':'El coral es un animal!'}, {'id':'new2','claim':'La luna gira.'}]}))
    assert screen(tmp_path,'2026-11-19')==[
        {'fact_id':'new','other_id':'old','reason':'exact'},
        {'fact_id':'new2','other_id':'draft','reason':'exact'}]
