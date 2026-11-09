"""Frozen regional-repair development trial using audited template candidates."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
from hybrid_repair import repair
from pin_template_trial import spatial
from prediction_metrics import compare
from rr_graph import read_rr_graph


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def freeze(out):
    if out.exists():raise ValueError('choose fresh experiment directory')
    prior=Path('experiments/connectivity_trial_2026-10-04');proto=json.loads((prior/'protocol.json').read_text())
    receipt=json.loads((prior/'receipt.json').read_text());audit=json.loads((prior/'independent_audit.json').read_text())
    if not audit['all_checked_invariants_passed']:raise ValueError('candidate audit did not pass')
    out.mkdir(parents=True);source=out/'source';source.mkdir()
    variants={}
    for name in ('0','1','2','fixed'):
        path=prior/f'refinement_{name}.json'
        if sha(path)!=receipt['artifact_sha256'][path.name]:raise ValueError('candidate artifact identity changed')
        variants[name]={'path':str(path.resolve()),'sha256':sha(path)}
    names=['hybrid_trial.py','hybrid_repair.py','pin_template_trial.py','pin_pools.py','template_sketch.py',
           'prediction_metrics.py','rr_graph.py','rr_occupancy.py','semantic_sketch.py','run_sketch.py','connection_golden.py']
    for name in names:shutil.copyfile(Path(__file__).with_name(name),source/name)
    inputs={k:proto['inputs'][k] for k in ('graph','endpoints','process_labels')}
    raw=Path('experiments/budget_sweep_2026-10-04/rr_length_switch_32920.json')
    inputs['raw_baseline']={'path':str(raw.resolve()),'sha256':sha(raw)}
    protocol={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'fixed diffeq development ablation; no heldout or feedback',
              'inputs':inputs,'candidates':variants,'candidate_audit_sha256':sha(prior/'independent_audit.json'),
              'margin_tiles':1,'repair_stages':['regional failed endpoints grouped by SOURCE','full RR for region misses only'],
              'budget':'full physical node count; no artificial search cutoff','cost':'unchanged rr_length_switch',
              'primary':['complete individual physical-arc coverage','candidate + repair search/witness work','region-filter preprocessing work'],
              'secondary':['312 common spatial utilization bins at native iterations1/13'],
              'source_sha256':{name:sha(Path(__file__).with_name(name)) for name in names},
              'limitations':['region overlap allows long segments to extend outside box','no negotiated congestion/pin assignment/net-tree proof',
                             'candidate refinement/witness construction and graph import costs are not in search counters',
                             'quotient/physical/witness state all retained; no total memory benefit proven','no wall-time speedup claims']}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')


def run(out):
    protocol=json.loads((out/'protocol.json').read_text())
    for name,digest in protocol['source_sha256'].items():
        if sha(Path(__file__).with_name(name))!=digest:raise ValueError('source changed')
    for entry in list(protocol['inputs'].values())+list(protocol['candidates'].values()):
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    graph=read_rr_graph(protocol['inputs']['graph']['path'])
    ep=json.loads(Path(protocol['inputs']['endpoints']['path']).read_text())
    labels=json.loads(Path(protocol['inputs']['process_labels']['path']).read_text())
    native={str(row['iteration']):spatial(graph,row['node_occupancy']) for row in (labels['iterations'][0],labels['iterations'][-1])}
    summaries=[]
    for name,entry in protocol['candidates'].items():
        candidate=json.loads(Path(entry['path']).read_text());result=repair(graph,ep,candidate,protocol['margin_tiles'])
        if result['completed']!=len(ep['connections']):raise AssertionError('repair failed reachable native endpoints')
        result['metrics']={i:compare(spatial(graph,result['node_occupancy']),truth,20) for i,truth in native.items()}
        result['candidate_sha256']=entry['sha256'];result['protocol_sha256']=sha(out/'protocol.json')
        target=out/f'hybrid_{name}.json';target.write_text(json.dumps(result,indent=2)+'\n')
        work=result['repair_work'];candidate_work=result['candidate_work']
        search_witness_visits=(candidate_work.get('edge_visits',0)+candidate_work.get('witness_edge_visits',0)+
                              work.get('regional_edge_visits',0)+work.get('full_edge_visits',0))
        summary={'variant':name,'completed':result['completed'],'requested':result['requested'],'methods':result['methods'],
                 'repair_sources':result['repair_sources'],'repair_work':work,'candidate_work':candidate_work,
                 'combined_search_witness_edge_visits':search_witness_visits,'metrics':result['metrics']}
        summaries.append(summary);print(json.dumps(summary),flush=True)
    raw=json.loads(Path(protocol['inputs']['raw_baseline']['path']).read_text())['payload']['prediction']
    receipt={'protocol_sha256':sha(out/'protocol.json'),'summary':summaries,'raw_full_search_edge_visits':sum(t['edge_visits'] for t in raw['search_traces']),
             'all_reachable_endpoints_completed':True,'artifact_sha256':{p.name:sha(p) for p in out.glob('hybrid_*.json')}}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.output_dir)
    else:run(a.output_dir)
