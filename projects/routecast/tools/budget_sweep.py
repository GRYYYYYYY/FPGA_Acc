"""Frozen development-only budget sweep, resumable from verified artifacts."""
import argparse
from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import time
from evaluate_sketch import evaluate
from rr_graph import read_rr_graph
from run_sketch import predict


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(path)


def freeze(output):
    if (output/'protocol.json').exists():raise ValueError('protocol already exists; do not overwrite')
    previous=Path('experiments/pre_route_endpoints_2026-10-04')
    info=json.loads((previous/'protocol.json').read_text())['cases']['diffeq']
    graph=info['inputs']['graph']['path']; endpoints=previous/'diffeq_endpoints.json'; labels=previous/'diffeq_aligned_labels.json'
    counts=json.loads(Path('experiments/rr_frontend_2026-10-04/diffeq_audit.json').read_text())
    output.mkdir(parents=True,exist_ok=True);source=output/'source';source.mkdir()
    names=['budget_sweep.py','evaluate_sketch.py','prediction_metrics.py','rr_graph.py','rr_occupancy.py',
           'run_sketch.py','semantic_sketch.py','connection_golden.py']
    sources={}
    for name in names:
        p=Path(__file__).with_name(name);sources[name]=sha(p);shutil.copyfile(p,source/name)
    reuse={}
    for mode in ('rr_hop','rr_length_switch'):
        p=previous/f'diffeq_{mode}_prediction.json';r=json.loads(p.read_text())
        if r['endpoints_sha256']!=sha(endpoints):raise ValueError('reused endpoints mismatch')
        if any(sources[n]!=d for n,d in r['source_sha256'].items()):raise ValueError('reuse code identity mismatch')
        reuse[mode]={'path':str(p.resolve()),'sha256':sha(p)}
    protocol={'schema':'ROUTECAST_BUDGET_SWEEP_V1','frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'scope':'development diffeq only, no heldout or performance claim','modes':['rr_hop','rr_length_switch'],
              'budgets':[1024,4096,16384,counts['node_count']],
              'inputs':{name:{'path':str(Path(p).resolve()),'sha256':sha(p)} for name,p in [('graph',graph),('endpoints',endpoints),('labels',labels)]},
              'source_sha256':sources,'reuse_4096':reuse,'evaluation':'unchanged resource/spatial scopes and top-k from prior protocol; all failures included',
              'invariants':['completed connection IDs are nested as budget increases','completed count equals requested minus failure count','at graph-node-count budget all native-label endpoints are reachable','4096 artifacts must match frozen SHA and predictor code'],
              'limitations':['single design/fixed architecture','static cost and SOURCE-tree sketch, not negotiated congestion routing','labels are final occupancy, not routability or routing difficulty','top-k tie limitations remain','wall times not controlled or repeated']}
    write(output/'protocol.json',protocol)


def run(output):
    proto=json.loads((output/'protocol.json').read_text())
    for name,digest in proto['source_sha256'].items():
        if sha(Path(__file__).with_name(name))!=digest:raise ValueError(f'code changed: {name}')
    for entry in proto['inputs'].values():
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    graph=read_rr_graph(proto['inputs']['graph']['path'])
    endpoints=json.loads(Path(proto['inputs']['endpoints']['path']).read_text())
    labels=json.loads(Path(proto['inputs']['labels']['path']).read_text());rows=[]
    requested={r['connection_id'] for r in endpoints['connections']}
    for mode in proto['modes']:
        previous_completed=set()
        for budget in proto['budgets']:
            target=output/f'{mode}_{budget}.json'
            if target.exists():
                record=json.loads(target.read_text())
                if (record['protocol_sha256']!=sha(output/'protocol.json') or record['mode']!=mode or record['budget']!=budget):
                    raise ValueError('unverified resume artifact')
                if record['record_sha256']!=hashlib.sha256(json.dumps(record['payload'],sort_keys=True).encode()).hexdigest():
                    raise ValueError('resume payload identity mismatch')
                payload=record['payload']
            else:
                begin=time.monotonic()
                if budget==4096:
                    entry=proto['reuse_4096'][mode]
                    if sha(entry['path'])!=entry['sha256']:raise ValueError('reuse artifact changed')
                    prediction=json.loads(Path(entry['path']).read_text());reused=True
                else:
                    prediction=predict(graph,endpoints,mode,budget);reused=False
                metrics=evaluate(graph,prediction,labels,endpoints)
                payload={'prediction':prediction,'metrics':metrics,'reused':reused,
                         'driver_wall_s':time.monotonic()-begin}
                record={'protocol_sha256':sha(output/'protocol.json'),'mode':mode,'budget':budget,'payload':payload,
                        'record_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}
                write(target,record)
            prediction=payload['prediction'];metrics=payload['metrics']
            failed={r['connection_id'] for r in prediction['failures']};completed=requested-failed
            if not previous_completed<=completed:raise AssertionError('completion nonmonotonic')
            if prediction['connections_completed']!=len(completed):raise AssertionError('count mismatch')
            if budget==len(graph.nodes) and failed:raise AssertionError('full budget still missing native reachable endpoints')
            previous_completed=completed
            row={'mode':mode,'budget':budget,'completed':len(completed),'requested':len(requested),
                 'failures_by_reason':dict(Counter(r['reason'] for r in prediction['failures'])),
                 'settled_nodes':sum(r['settled_nodes'] for r in prediction['search_traces']),
                 'edge_visits':sum(r['edge_visits'] for r in prediction['search_traces']),
                 'resource_spearman':metrics['resource_utilization']['spearman'],
                 'spatial_spearman':metrics['spatial_segment_utilization']['spearman'],
                 'spatial_mae':metrics['spatial_segment_utilization']['mae'],
                 'spatial_precision_at_k':metrics['spatial_segment_utilization']['precision_at_k'],
                 'predicted_overflow_nodes':metrics['predicted_overflow_nodes'],'reused':payload['reused']}
            rows.append(row);print(json.dumps(row),flush=True)
    write(output/'receipt.json',{'protocol_sha256':sha(output/'protocol.json'),'summary':rows,'all_invariants_passed':True,
          'artifact_sha256':{f'{m}_{b}.json':sha(output/f'{m}_{b}.json') for m in proto['modes'] for b in proto['budgets']},
          'completed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.output_dir)
    else:run(a.output_dir)
