"""Frozen development ablation: pin-only vs pin+channel quotient, no route feedback."""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import datetime
from connection_golden import Result
from pin_pools import build_pools, PinDemand
from prediction_metrics import compare
from rr_graph import read_rr_graph
from template_sketch import estimate


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def spatial(graph,values):
    capacities=defaultdict(int);demand=defaultdict(Fraction)
    for nid,node in graph.nodes.items():
        if node.type not in {'CHANX','CHANY'} or node.capacity==0:continue
        loc=dict(node.location)
        for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
            for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
                key=f'{x},{y},{node.type},{node.segment_id}'
                capacities[key]+=node.capacity;demand[key]+=values.get(str(nid),0)
    return {k:float(demand[k]/v) for k,v in capacities.items()}


def freeze(out):
    if out.exists():raise ValueError('choose a new output directory')
    out.mkdir(parents=True);sources=out/'source';sources.mkdir()
    base=Path('experiments/pre_route_endpoints_2026-10-04/protocol.json')
    case=json.loads(base.read_text())['cases']['diffeq']
    paths={'graph':Path(case['inputs']['graph']['path']),
           'endpoints':Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json'),
           'process_labels':Path('experiments/native_iteration_capture_2026-10-04/process_labels.json'),
           'raw_baseline':Path('experiments/budget_sweep_2026-10-04/rr_length_switch_32920.json')}
    names=['pin_template_trial.py','pin_pools.py','template_sketch.py','prediction_metrics.py','semantic_sketch.py',
           'rr_graph.py','rr_occupancy.py','run_sketch.py','connection_golden.py']
    for n in names:shutil.copyfile(Path(__file__).with_name(n),sources/n)
    protocol={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'diffeq development ablation only',
              'variants':['pin_pool_only','pin_and_channel_pools'],'cost':'unchanged rr_length_switch',
              'budget':'full quotient node count, require completion of all endpoints',
              'inputs':{k:{'path':str(p.resolve()),'sha256':sha(p)} for k,p in paths.items()},
              'source_sha256':{n:sha(Path(__file__).with_name(n)) for n in names},
              'primary_metrics':['common physical tile/type/segment spatial utilization Spearman/MAE first and final native iteration'],
              'secondary':['matching common-scope raw full-budget baseline','active pin-class pressure vs summed IPIN overflow','pin-demand vs native SINK occupancy equality at all iterations'],
              'limitations':['quotient permits impossible physical track-to-exit combinations','distinct-net template touch may undercount multiple tracks of same net','uniform fraction is a relaxation, not an assigned route','pin pool pressure cannot prove Hall/connectivity feasibility','single design/seed; no feedback/heldout/hardware claim']}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')


def run(out):
    protocol=json.loads((out/'protocol.json').read_text())
    for n,d in protocol['source_sha256'].items():
        if sha(Path(__file__).with_name(n))!=d:raise ValueError('code changed')
    for entry in protocol['inputs'].values():
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    inputs={k:json.loads(Path(v['path']).read_text()) for k,v in protocol['inputs'].items() if k!='graph'}
    graph=read_rr_graph(protocol['inputs']['graph']['path']);ep=inputs['endpoints'];labels=inputs['process_labels']
    if ep['graph_sha256']!=graph.sha256 or labels['graph_sha256']!=graph.sha256:raise ValueError('graph identity mismatch')
    pools,owner=build_pools(graph);pool_demand=PinDemand(pools)
    for r in ep['connections']:
        if pool_demand.update(r['connection_id'],1,r['net_id'],r['sink'])!=Result.COMMITTED:raise ValueError('pool rejected input')
    if pool_demand.demand!=pool_demand.rebuild():raise AssertionError('pool rebuild mismatch')
    active={sid for sid,d in pool_demand.demand.items() if d}
    mismatches=[]
    for row in labels['iterations']:
        mismatch={sid for sid in pools if pool_demand.demand[sid]!=row['node_occupancy'].get(str(sid),0)}
        if mismatch:mismatches.append({'iteration':row['iteration'],'classes':sorted(mismatch)})
    if mismatches:raise AssertionError(f'endpoint/native class demand mismatch: {mismatches}')
    pool_rows=[]
    for sid in sorted(active):
        pool=pools[sid];pressure=pool_demand.pressure(sid)
        ips={nid for ids in pool.physical_pins.values() for nid in ids}
        # Sum physical IPIN excess is unambiguous only for this no-facet-duplicate cohort.
        if any(len(ids)>1 for ids in pool.physical_pins.values()):raise ValueError('label physical-facet net union needed')
        pool_rows.append({'sink':sid,'capacity':pool.capacity,'distinct_net_demand':pool_demand.demand[sid],
                          'pressure':[pressure.numerator,pressure.denominator],
                          'first_ipin_overflow_nodes':sum(str(n) in labels['iterations'][0]['node_overflow'] for n in ips),
                          'first_ipin_overflow_mass':sum(labels['iterations'][0]['node_overflow'].get(str(n),0) for n in ips)})
    (out/'pin_demand_audit.json').write_text(json.dumps({'graph_sha256':graph.sha256,'pools':len(pools),'active_pools':len(active),
        'all_iteration_sink_demand_matches':True,'active_pool_overflow_count':sum(r['distinct_net_demand']>r['capacity'] for r in pool_rows),
        'physical_ipin_overflow_nodes_first':sum(r['first_ipin_overflow_nodes'] for r in pool_rows),'pool_rows':pool_rows},indent=2)+'\n')
    raw=inputs['raw_baseline']['payload']['prediction']
    native={str(row['iteration']):spatial(graph,row['node_occupancy']) for row in (labels['iterations'][0],labels['iterations'][-1])}
    summaries=[{'variant':'raw_full_budget','completed':raw['connections_completed'],
                'metrics':{i:compare(spatial(graph,raw['node_occupancy']),t,20) for i,t in native.items()}}]
    for variant in protocol['variants']:
        result=estimate(graph,ep,variant=='pin_and_channel_pools')
        if result['prediction']['connections_completed']!=len(ep['connections']):raise AssertionError('quotient path missing')
        (out/f'{variant}_prediction.json').write_text(json.dumps(result,indent=2)+'\n')
        expected={nid:Fraction(*v) for nid,v in result['channel_expected_demand'].items()}
        metrics={i:compare(spatial(graph,expected),t,20) for i,t in native.items()}
        summary={'variant':variant,'completed':result['prediction']['connections_completed'],
                 'template_nodes':result['template_nodes'],'template_edges':result['template_edges'],'metrics':metrics}
        summaries.append(summary);print(json.dumps(summary),flush=True)
    receipt={'protocol_sha256':sha(out/'protocol.json'),'summary':summaries,'all_assertions_passed':True,
             'artifact_sha256':{p.name:sha(p) for p in out.glob('*.json')},
             'claim_boundary':'same physical spatial scopes across models; quotient feasibility is not physical feasibility'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
    if a.freeze:freeze(a.output_dir)
    else:run(a.output_dir)
