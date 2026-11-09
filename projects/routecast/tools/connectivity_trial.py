"""Development ablation of switch-witness lifting / partition refinement."""
import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import json
from pathlib import Path
import shutil
from connection_golden import Result
from pin_template_trial import spatial
from prediction_metrics import compare
from rr_graph import read_rr_graph
from rr_occupancy import Occupancy
from semantic_sketch import Sketch
from template_sketch import quotient
from template_connectivity import Lifter, refine


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def construct(graph,endpoints,rounds):
    coarse,mapping,_=quotient(graph,True)
    pooled,mapping,members,performed,is_stable=refine(graph,coarse,mapping,rounds)
    sketch=Sketch(pooled,'rr_length_switch',len(pooled.nodes));lifter=Lifter(graph,pooled,mapping)
    ledger=Occupancy(graph);groups=defaultdict(list);rows=[];search_work=Counter()
    for row in endpoints['connections']:groups[row['source']].append(row)
    for source,connections in sorted(groups.items()):
        result=sketch.search(mapping[source],{mapping[r['sink']] for r in connections})
        search_work['settled_nodes']+=result.settled_nodes;search_work['edge_visits']+=result.edge_visits
        lifted={}
        for row in connections:
            sink=row['sink'];path=result.paths.get(mapping[sink])
            if path is None:raise AssertionError('native reachable endpoints missing from quotient')
            if sink not in lifted:lifted[sink]=lifter.lift(source,sink,path)
            lifted_result=lifted[sink]
            if lifted_result.edge_ids is not None:
                if ledger.update(row['connection_id'],1,row['net_id'],source,sink,lifted_result.edge_ids)!=Result.COMMITTED:
                    raise AssertionError('physical witness rejected by ledger')
            rows.append({**row,'quotient_edge_ids':path,'physical_edge_ids':lifted_result.edge_ids,
                         'failed_at':lifted_result.failed_at,'frontier_sizes':lifted_result.frontier_sizes,
                         'witness_edge_visits':lifted_result.physical_edge_visits})
        search_work['witness_edge_visits']+=sum(r.physical_edge_visits for r in lifted.values())
    if ledger.occupancy!=ledger.rebuild():raise AssertionError('lifted physical demand mismatch')
    failures=[r for r in rows if r['physical_edge_ids'] is None]
    if is_stable and failures:raise AssertionError('fixed-point quotient path cannot be lifted')
    return {'physical_graph_sha256':graph.sha256,'quotient_graph_sha256':pooled.sha256,'requested_rounds':rounds,
            'performed_rounds':performed,'stable_partition':is_stable,'nodes':len(pooled.nodes),'edges':len(pooled.edges),
            'requested_connections':len(rows),'lifted_connections':len(rows)-len(failures),
            'failures_by_step':dict(Counter(r['failed_at'] for r in failures)),'connections':rows,
            'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'work':dict(search_work),
            'scope':'exact individual RR switch/arc paths; no joint net capacity, VPR route-tree or closure guarantee'}


def freeze(out):
    if out.exists():raise ValueError('choose fresh protocol/output directory')
    out.mkdir(parents=True);source=out/'source';source.mkdir()
    prior=json.loads(Path('experiments/pin_template_trial_2026-10-04/protocol.json').read_text())
    inputs={k:prior['inputs'][k] for k in ('graph','endpoints','process_labels')}
    names=['connectivity_trial.py','template_connectivity.py','template_sketch.py','pin_pools.py','pin_template_trial.py',
           'prediction_metrics.py','rr_graph.py','rr_occupancy.py','semantic_sketch.py','run_sketch.py','connection_golden.py']
    for n in names:shutil.copyfile(Path(__file__).with_name(n),source/n)
    protocol={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'diffeq development, no heldout or feedback claim',
              'inputs':inputs,'refinement_rounds':[0,1,2,None],'stable_variant':'refine to outgoing-signature fixed point',
              'cost':'unchanged rr_length_switch','budget':'all quotient nodes','source_sha256':{n:sha(Path(__file__).with_name(n)) for n in names},
              'primary':['individual physical path lift coverage','template graph nodes/edges'],
              'secondary':['common physical spatial utilization Spearman/MAE at native iterations1/13'],
              'failure_rule':'no fallback; failed lifts contribute zero occupancy, never dropped from requested cohort',
              'invariants':['every lifted arc projects to selected template switch/edge','fixed point has no lift failures','capacity ledger equals independent rebuild'],
              'limitations':['physical arc path is not jointly legal routing','no congestion-driven pin assignment','single design/seed','refinement may erase structural compression','partial-depth coverage need not be monotone']}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')


def run(out):
    protocol=json.loads((out/'protocol.json').read_text())
    for name,digest in protocol['source_sha256'].items():
        if sha(Path(__file__).with_name(name))!=digest:raise ValueError('code changed')
    for entry in protocol['inputs'].values():
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    graph=read_rr_graph(protocol['inputs']['graph']['path'])
    endpoints=json.loads(Path(protocol['inputs']['endpoints']['path']).read_text())
    if endpoints['graph_sha256']!=graph.sha256:raise ValueError('endpoints graph mismatch')
    labels=json.loads(Path(protocol['inputs']['process_labels']['path']).read_text())
    summaries=[]
    for rounds in protocol['refinement_rounds']:
        name='fixed' if rounds is None else str(rounds)
        result=construct(graph,endpoints,rounds)
        metrics={str(row['iteration']):compare(spatial(graph,result['node_occupancy']),spatial(graph,row['node_occupancy']),20)
                 for row in (labels['iterations'][0],labels['iterations'][-1])}
        result['metrics']=metrics
        target=out/f'refinement_{name}.json';target.write_text(json.dumps(result,indent=2)+'\n')
        summary={k:result[k] for k in ('requested_rounds','performed_rounds','stable_partition','nodes','edges','lifted_connections','requested_connections','failures_by_step')}
        summary['metrics']=metrics;summaries.append(summary);print(json.dumps(summary),flush=True)
    receipt={'protocol_sha256':sha(out/'protocol.json'),'summary':summaries,'all_invariants_passed':True,
             'artifact_sha256':{p.name:sha(p) for p in out.glob('refinement_*.json')}}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.output_dir)
    else:run(a.output_dir)
