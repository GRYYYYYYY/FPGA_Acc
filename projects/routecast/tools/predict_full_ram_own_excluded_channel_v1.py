"""Complete input-only physical additive baseline with durable path journal."""
import json,subprocess,time,signal
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from frozen_pressure_sketch import FrozenPressureSketch
from prepared_csr import write
from physical_prediction_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_own_excluded_channel_prediction_v1_2026-10-09';D.mkdir(exist_ok=False)
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
endpoint=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json'
binary=R/'build/routecast_net_pressure_v1'
background=E/'full_ram_length_switch_prediction_v1_2026-10-09/prediction.json'
sources=[R/'tools/csr_consumer/net_pressure_main_v1.cpp',background,R/'tools/frozen_pressure_sketch.py',Path(__file__),R/'tools/semantic_sketch.py',R/'tools/compact_indexed_sketch.py',R/'tools/prepared_csr.py',R/'tools/physical_prediction_audit.py',R/'tools/rr_graph.py']
bindings={str(p):sha(p) for p in [graph,endpoint,binary,*sources]}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,mode='own_excluded_channel_pressure_alpha256',timeout_s=600,
    scope='All 16819 input connections; one frozen predictor-only background pass, alpha256 channel penalty ceil(256*max(0,old demand-capacity+1)/capacity), queried net unique-node ownership excluded from background; no evolving occupancy or negotiated routing; independent per-source/net shortest paths, canonical cost/hops/edge-ID tie order; no target route or indexed-cost labels. Native XML and exact net-union audit, no negotiated congestion/joint route-tree guarantee. Full development family only.'),indent=2)+'\n')
def timeout(*args):raise TimeoutError('frozen 600-second predictor budget exceeded')
signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
start=time.perf_counter();worker=None;status='FAILED';details={}
try:
    g=read_rr_graph(graph);e=json.loads(endpoint.read_text());assert e['graph_sha256']==g.sha256 and len(e['connections'])==16819
    bg=json.loads(background.read_text());assert bg['physical_graph_sha256']==g.sha256
    engine=FrozenPressureSketch(g,{int(n):v for n,v in bg['node_occupancy'].items()},g.sha256,256,len(g.nodes));manifest=write(engine,D/'csr');del engine
    from array import array
    demand={int(n):v for n,v in bg['node_occupancy'].items()}
    reduction=[]
    for n in sorted(g.nodes):
        node=g.nodes[n];cap=node.capacity;d=demand.get(n,0)
        def penalty(x):return (256*max(0,x-cap+1)+cap-1)//cap
        reduction.append(penalty(d)-penalty(d-1) if cap>0 and node.type in {'CHANX','CHANY'} and d>0 else 0)
    import sys
    payload=array('Q',reduction)
    if sys.byteorder!='little':payload.byteswap()
    (D/'csr/own_reduction.bin').write_bytes(payload.tobytes())
    own_nodes=defaultdict(set)
    for c in bg['connections']:
        own_nodes[c['net_id']].add(c['source'])
        own_nodes[c['net_id']].update(g.edges[eid].sink for eid in c['physical_edge_ids'])
    owner_counts=Counter(n for nodes in own_nodes.values() for n in nodes)
    assert {str(n):v for n,v in owner_counts.items()}==bg['node_occupancy']
    prep=time.perf_counter()-start
    groups=defaultdict(list)
    for row in e['connections']:groups[row['net_id']].append(row)
    worker=subprocess.Popen([str(binary),str(D/'csr'),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    rows=[];occupancy=Counter();visits=0;settled=0;t=time.perf_counter()
    with (D/'net_results.jsonl').open('x') as journal:
        for i,(net,cohort) in enumerate(sorted(groups.items()),1):
            source=cohort[0]['source'];assert all(c['source']==source for c in cohort)
            targets=sorted({c['sink'] for c in cohort})
            worker.stdin.write(' '.join(map(str,[source,*targets]))+' | '+' '.join(map(str,sorted(own_nodes[net])))+'\n');worker.stdin.flush()
            line=worker.stdout.readline();assert line,'worker terminated without response'
            result=json.loads(line);assert not result['budget_exhausted']
            journal.write(json.dumps(dict(net_id=net,source=source,result=result))+'\n');journal.flush()
            touched=set();visits+=result['edge_visits'];settled+=result['settled_nodes']
            for c in cohort:
                path=result['paths'].get(str(c['sink']))
                rows.append({**c,'physical_edge_ids':path,'method':'own_excluded_channel_pressure_alpha256' if path is not None else 'failed'})
                if path is not None:
                    touched.add(source)
                    for eid in path:touched.add(g.edges[eid].sink)
            occupancy.update(touched)
            if i%250==0:print(i,len(rows),flush=True)
    worker.stdin.close();assert worker.wait()==0
    query=time.perf_counter()-t;methods=Counter(c['method'] for c in rows)
    prediction=dict(physical_graph_sha256=g.sha256,connections=rows,node_occupancy={str(n):v for n,v in occupancy.items()},requested=len(rows),completed=len(rows)-methods['failed'],methods=dict(methods))
    (D/'prediction.json').write_text(json.dumps(prediction)+'\n')
    t=time.perf_counter();checked=audit(g,e,prediction);audit_s=time.perf_counter()-t
    details=dict(preparation_s=prep,query_ledger_s=query,independent_path_audit_s=audit_s,edge_visits=visits,settled_nodes=settled,completed=prediction['completed'],requested=len(rows),audit=checked,csr_context_sha256=manifest['context_sha256'])
    status='COMPLETE_AUDITED_PREDICTION'
except Exception as error:
    details=dict(error=repr(error));print(details,flush=True)
finally:
    signal.alarm(0)
    if worker is not None and worker.poll() is None:worker.kill();worker.wait()
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,status=status,details=details,total_seconds=time.perf_counter()-start,admitted_as_unseen_family=False,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()}),indent=2)+'\n')
print(status,details,flush=True)
