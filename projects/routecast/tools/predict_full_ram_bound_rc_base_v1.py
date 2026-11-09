"""Complete input-only physical additive baseline with durable path journal."""
import json,subprocess,time,signal
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from bound_indexed_cost import BoundNormalizedRCBase
from prepared_csr import write
from physical_prediction_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_bound_rc_base_prediction_v1_2026-10-09';D.mkdir(exist_ok=False)
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml'
endpoint=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json'
binary=R/'build/routecast_csr_direct'
B=E/'full_ram_native_node_binding_v1_2026-10-09'
proof=E/'full_ram_native_node_binding_verification_v1_2026-10-09/verification.json'
v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
sources=[proof,B/'rr_indexed_data.echo',B/'routecast_node_cost_indices.csv',R/'tools/bound_indexed_cost.py',R/'tools/path_rc.py',Path(__file__),R/'tools/semantic_sketch.py',R/'tools/compact_indexed_sketch.py',R/'tools/prepared_csr.py',R/'tools/physical_prediction_audit.py',R/'tools/rr_graph.py']
bindings={str(p):sha(p) for p in [graph,endpoint,binary,*sources]}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,mode='bound_normalized_rc_base_equal_half_scale1e6',timeout_s=600,
    scope='All 16819 input connections, independent per-source/net shortest paths, canonical cost/hops/edge-ID tie order; Frozen cost round-ties-even(1e6*(serialized RC increment + native indexed base)/(2*normalization)); constant criticality half, all switches buffered, no pressure/history/lookahead/tree prefix. Authenticated native node-index table is input, no target route or per-pin timing labels. Native XML and exact net-union audit, no negotiated congestion/joint route-tree guarantee. Full development family only.'),indent=2)+'\n')
def timeout(*args):raise TimeoutError('frozen 600-second predictor budget exceeded')
signal.signal(signal.SIGALRM,timeout);signal.alarm(600)
start=time.perf_counter();worker=None;status='FAILED';details={}
try:
    g=read_rr_graph(graph);e=json.loads(endpoint.read_text());assert e['graph_sha256']==g.sha256 and len(e['connections'])==16819
    engine=BoundNormalizedRCBase(g,(B/'rr_indexed_data.echo').read_text(),(B/'routecast_node_cost_indices.csv').read_text(),v['identity'],10**6);manifest=write(engine,D/'csr');del engine
    prep=time.perf_counter()-start
    groups=defaultdict(list)
    for row in e['connections']:groups[row['net_id']].append(row)
    worker=subprocess.Popen([str(binary),str(D/'csr'),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    rows=[];occupancy=Counter();visits=0;settled=0;t=time.perf_counter()
    with (D/'net_results.jsonl').open('x') as journal:
        for i,(net,cohort) in enumerate(sorted(groups.items()),1):
            source=cohort[0]['source'];assert all(c['source']==source for c in cohort)
            targets=sorted({c['sink'] for c in cohort})
            worker.stdin.write(' '.join(map(str,[source,*targets]))+'\n');worker.stdin.flush()
            line=worker.stdout.readline();assert line,'worker terminated without response'
            result=json.loads(line);assert not result['budget_exhausted']
            journal.write(json.dumps(dict(net_id=net,source=source,result=result))+'\n');journal.flush()
            touched=set();visits+=result['edge_visits'];settled+=result['settled_nodes']
            for c in cohort:
                path=result['paths'].get(str(c['sink']))
                rows.append({**c,'physical_edge_ids':path,'method':'bound_rc_base' if path is not None else 'failed'})
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
