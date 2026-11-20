import argparse,json,logging
from pathlib import Path
from .state import connect,reserve,restore,export_history,finalize_render,begin_revision,published_count,production_episode
from .render import render
ROOT=Path(__file__).resolve().parents[1]
def load_facts(root,db):
    all_facts=json.loads((root/'data/facts.json').read_text()); used={r[0] for r in db.execute('SELECT fact_id FROM used')}
    from .queue import next_batch
    past={r[0] for r in db.execute('SELECT digest FROM claims')}
    facts=next_batch(all_facts,used,past)
    if len(facts)!=25: raise ValueError(f'Solo quedan {len(facts)} datos revisados. Añadir 25 nuevos; nunca repetir ni inventar.')
    validate_facts(root,facts)
    return facts

def validate_facts(root,facts):
    # Retrieval is evidence, never automatic approval of a factual claim.
    from .state import sha
    if len(facts)!=25 or any(f['review_status']!='verified' for f in facts): raise ValueError('Reserva sin 25 datos revisados')
    audits=json.loads((root/'data/source_audit.json').read_text())
    for f in facts:
        a=next(a for a in audits if a['url']==f['source_url']); path=root/a['path']
        if sha(path)!=a['sha256'] or f['source_snapshot_sha256']!=a['sha256']: raise ValueError('Fuente modificada')
        if f['evidence_query'].lower() not in path.read_text().lower(): raise ValueError('Evidencia ausente')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('command',choices=['build','revise','validate','upload','auth','reconcile']); parser.add_argument('--episode',default='pilot-001'); parser.add_argument('--out',default='build/pilot-001'); args=parser.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s')
    root=ROOT; out=(root/args.out).resolve(); config=json.loads((root/'config.json').read_text())
    if args.command=='auth':
        from .youtube import authorize
        authorize(); return
    if args.command=='validate':
        from .render import validate
        print(json.dumps(validate(out/'episode.mp4'),indent=2)); return
    if args.command=='upload':
        from .youtube import upload
        upload(root,out,args.episode,config); return
    if args.command=='reconcile':
        from .youtube import reconcile
        print(json.dumps(reconcile(root,config),ensure_ascii=False,indent=2)); return
    db=connect(root/'data/history.sqlite'); restore(db,root/'data/history.json')
    if args.command=='revise':
        begin_revision(db,args.episode); export_history(db,root/'data/history.json')
    existing=db.execute('SELECT status FROM episodes WHERE id=?',(args.episode,)).fetchone()
    if existing:
        if existing[0]!='reserved': raise ValueError('Episodio ya generado o publicado; no sobrescribir')
        ids={r[0] for r in db.execute('SELECT fact_id FROM used WHERE episode=?',(args.episode,))}
        facts=[f for f in json.loads((root/'data/facts.json').read_text()) if f['id'] in ids]
    else:
        facts=load_facts(root,db); reserve(db,args.episode,facts); export_history(db,root/'data/history.json')
    validate_facts(root,facts)
    try:
        from .media import attach_media
        visual_facts=attach_media(root,facts)
        render_config=dict(config)
        if production_episode(args.episode):
            render_config['confirmed_publications_at_render']=published_count(db)
        report=render(root,out,visual_facts,render_config)
        finalize_render(db,args.episode,facts,report['sha256'])
    finally: export_history(db,root/'data/history.json')
    print(json.dumps(report,indent=2))
if __name__=='__main__': main()
