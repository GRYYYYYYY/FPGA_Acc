"""Lazy filtering ablation: exact paths must match frozen eager artifacts."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
from hybrid_repair import repair
from lazy_region_search import LazyRegionalSearch
from rr_graph import read_rr_graph


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def freeze(out):
    if out.exists():raise ValueError('fresh output directory required')
    prior=Path('experiments/hybrid_repair_2026-10-04');proto=json.loads((prior/'protocol.json').read_text())
    receipt=json.loads((prior/'receipt.json').read_text());out.mkdir(parents=True);source=out/'source';source.mkdir()
    names=['lazy_repair_trial.py','lazy_region_search.py','hybrid_repair.py','rr_graph.py','rr_occupancy.py','semantic_sketch.py','connection_golden.py']
    for n in names:shutil.copyfile(Path(__file__).with_name(n),source/n)
    eager={}
    for name in proto['candidates']:
        p=prior/f'hybrid_{name}.json'
        if sha(p)!=receipt['artifact_sha256'][p.name]:raise ValueError('eager artifact changed')
        eager[name]={'path':str(p.resolve()),'sha256':sha(p)}
    frozen={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'inputs':{k:proto['inputs'][k] for k in ('graph','endpoints')},
            'candidates':proto['candidates'],'eager_artifacts':eager,'margin_tiles':proto['margin_tiles'],
            'source_sha256':{n:sha(Path(__file__).with_name(n)) for n in names},
            'primary_invariant':'same connection-by-connection physical edge IDs/methods and total node occupancy as eager',
            'work_metrics':['region membership node tests','adjacency filter probes','regional/full search edge visits'],
            'scope':'fixed diffeq development repair stage only, no wall-time or hardware claim'}
    (out/'protocol.json').write_text(json.dumps(frozen,indent=2)+'\n')


def run(out):
    proto=json.loads((out/'protocol.json').read_text())
    for n,d in proto['source_sha256'].items():
        if sha(Path(__file__).with_name(n))!=d:raise ValueError('source changed')
    for entry in list(proto['inputs'].values())+list(proto['candidates'].values())+list(proto['eager_artifacts'].values()):
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    graph=read_rr_graph(proto['inputs']['graph']['path']);ep=json.loads(Path(proto['inputs']['endpoints']['path']).read_text());summaries=[]
    for name,entry in proto['candidates'].items():
        candidate=json.loads(Path(entry['path']).read_text());eager=json.loads(Path(proto['eager_artifacts'][name]['path']).read_text())
        result=repair(graph,ep,candidate,proto['margin_tiles'],search_type=LazyRegionalSearch)
        serialized=json.loads(json.dumps(result))
        if serialized['connections']!=eager['connections'] or serialized['node_occupancy']!=eager['node_occupancy'] or serialized['methods']!=eager['methods']:
            raise AssertionError('lazy filtering changed selected physical paths or occupancy')
        for key in ('regional_settled_nodes','regional_edge_visits','full_settled_nodes','full_edge_visits'):
            if result['repair_work'].get(key,0)!=eager['repair_work'].get(key,0):raise AssertionError('search work changed')
        result['eager_sha256']=proto['eager_artifacts'][name]['sha256'];result['protocol_sha256']=sha(out/'protocol.json')
        target=out/f'lazy_{name}.json';target.write_text(json.dumps(result,indent=2)+'\n')
        summary={'variant':name,'completed':result['completed'],'identical_paths_and_occupancy':True,
                 'eager_region_node_tests':eager['repair_work'].get('region_node_tests',0),
                 'lazy_region_node_tests':result['repair_work'].get('region_node_tests',0),
                 'eager_filter_probes':eager['repair_work'].get('adjacency_filter_probes',0),
                 'lazy_filter_probes':result['repair_work'].get('adjacency_filter_probes',0),
                 'repair_work':result['repair_work']}
        summaries.append(summary);print(json.dumps(summary),flush=True)
    receipt={'protocol_sha256':sha(out/'protocol.json'),'summary':summaries,'all_exact_equivalence_checks_passed':True,
             'artifact_sha256':{p.name:sha(p) for p in out.glob('lazy_*.json')}}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.output_dir)
    else:run(a.output_dir)
