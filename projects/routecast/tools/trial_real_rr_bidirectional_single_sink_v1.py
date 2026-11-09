"""Complete single-target NET primitive, frozen development price contexts."""
import json,sys,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search
from bidirectional_rc_bridge_v1 import Bidirectional
name=sys.argv[1];assert name in ['xtea','8051','mmc']
P=R/'experiments/resident_radix_count_complete_v4_2026-10-08/protocol.json'
protocol=json.loads(P.read_text());case=next(x for x in protocol['cases'] if x['name']==name)
assert all(sha(p)==h for p,h in protocol['bindings'].items())
reference=R/'experiments/resident_radix_count_complete_v4_2026-10-08'/name
reference_receipt=reference/'receipt.json';reference_data=json.loads(reference_receipt.read_text())
for section in ['bindings','files']:
 for p,h in reference_data[section].items():assert sha(p)==h
admission=R/'experiments/bidirectional_rc_cpp_contract_v1_2026-10-08/verification.json'
proof=json.loads(admission.read_text());assert proof['pass_all']
assert all(sha(p)==h for p,h in proof['bindings'].items())
forward_binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
reverse_binary=R/'experiments/bidirectional_rc_build_v1_2026-10-08/search.so'
inputs=[P,Path(case['endpoint']),admission,forward_binary,reverse_binary,reference_receipt,reference/'round0.json',reference/'round1.json']
bindings={**closure([Path(__file__)]),**{str(p):sha(p) for p in inputs},str(R/'tools/soft_demand_cpp/bidirectional_workspace_v1.cpp'):sha(R/'tools/soft_demand_cpp/bidirectional_workspace_v1.cpp')}
bindings[str(R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp')]=sha(R/'tools/soft_demand_cpp/tree_workspace_radix_stats_v4.cpp')
graph,digest,nodes,f,rc,queries=load_endpoints(case['endpoint']);bindings[str(graph)]=digest
groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
selected={n:qs for n,qs in groups.items() if len({q['sink'] for q in qs})==1}
assert all(len({q['source'] for q in qs})==1 for qs in selected.values())
by_sink=defaultdict(list)
for n,qs in sorted(selected.items()):by_sink[qs[0]['sink']].append((n,qs[0]['source']))
D=R/'experiments/real_rr_bidirectional_single_sink_v1_2026-10-08'/name;D.mkdir(parents=True,exist_ok=False)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scale=rc.scale,graph_sha256=digest,required_single_target_nets=len(selected),required_single_target_connections=sum(map(len,selected.values())),total_original_connections=len(queries),scope='Every single-distinct-SINK NET in fixed known case; multi-target NETs explicitly excluded from this primitive test, not excluded from the eventual full model. Original prior round prices are frozen development replay contexts, not prospective candidate feedback. Single forward-then-bidirectional clocks, setup separately reported, no paired/full-model/workflow gain proof.'),indent=2)+'\n')
forward=Search(f,rc,forward_binary);tick=time.perf_counter();reverse=Bidirectional(f,rc,reverse_binary);reverse_setup=time.perf_counter()-tick
contexts=[('initial',{},0)]
for i in range(2):contexts.append((f'round{i}',{int(n):v for n,v in json.loads((reference/f'round{i}.json').read_text())['prices'].items()},rc.scale//(20*10**9)))
rows=[];files={}
def check(source,sink,slots,raw,objective,prices,weight):
 u=source;seen={u};delay=rc.initial(u);cost=delay
 assert f['capacities'][u]>0
 for slot in slots:
  assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1]
  u=f['dest_ranks'][slot];assert u not in seen and f['capacities'][u]>0;seen.add(u)
  delay+=rc.increments[slot];cost+=rc.increments[slot]+weight*prices.get(u,0)
 assert u==sink and delay==raw and cost==objective
 physical=[f['edge_ids'][e] for e in slots]
 assert rc.path(source,sink,physical)==raw
 return dict(source=source,sink=sink,physical_edge_ids=physical,delay=raw,objective=objective)
for phase,prices,weight in contexts:
 forward.prepare(prices,weight);reverse.prepare(prices,weight);baseline={};tick=time.perf_counter()
 for n,qs in sorted(selected.items()):
  source=qs[0]['source'];sink=qs[0]['sink'];raw,parents,settled=forward.search(source,{sink})
  if sink not in settled:baseline[n]=None;continue
  u=sink;slots=[]
  while u!=source:u,e=parents[u];slots.append(e)
  slots.reverse();cost=raw[sink]+weight*sum(prices.get(f['dest_ranks'][e],0) for e in slots)
  baseline[n]=check(source,sink,slots,raw[sink],cost,prices,weight)
 baseline_seconds=time.perf_counter()-tick;candidate={};tick=time.perf_counter()
 work=[0,0,0,0]
 for n,qs in sorted(selected.items()):
  source,sink=qs[0]['source'],qs[0]['sink'];answer=reverse.search(source,sink)
  candidate[n]=None if answer is None else check(source,sink,answer['slots'],answer['raw'],answer['objective'],prices,weight)
  if answer is not None:
   work=[x+y for x,y in zip(work,answer['scanned_arcs']+answer['settled_nodes'])]
 candidate_seconds=time.perf_counter()-tick
 assert set(baseline)==set(candidate)==set(selected)
 changed=0
 for n in selected:
  a,b=baseline[n],candidate[n];assert (a is None)==(b is None)
  if a is not None:assert a['objective']==b['objective'];changed+=a['physical_edge_ids']!=b['physical_edge_ids']
 p=D/f'{phase}.json';p.write_text(json.dumps(dict(baseline=baseline,candidate=candidate))+'\n');files[str(p)]=sha(p)
 row=dict(phase=phase,complete_nets=len(selected),complete_connections=sum(map(len,selected.values())),candidate_queries=len(selected),candidate_work=work,changed_equal_objective_paths=changed,all_minimum_objectives_equal=True,baseline_seconds=baseline_seconds,candidate_seconds=candidate_seconds)
 rows.append(row);print(json.dumps(row),flush=True)
assert all(sha(p)==h for p,h in bindings.items());forward.close();reverse.close()
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,files=files,rows=rows,bidirectional_setup_seconds=reverse_setup),indent=2)+'\n')
