"""Endpoint-only shared rooted RC trees; overuse is measured demand, not a legal route."""
import sys,json,time,heapq
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from soft_demand_cpp_bridge_v1 import Search

def predict(endpoint,floorfile,output):
 begin=time.perf_counter();endpoint=Path(endpoint).resolve();floorfile=Path(floorfile).resolve();out=Path(output).resolve();out.mkdir();bindings={**closure([Path(__file__)]),str(endpoint):sha(endpoint),str(floorfile):sha(floorfile)};bindings.update({v['path']:v['sha256'] for v in json.loads(endpoint.read_text())['inputs'].values()});graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(floorfile.read_text())};groups=defaultdict(list);binary=R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so';contract=R/'experiments/soft_demand_cpp_contract_v1_2026-10-07/verification.json';proof=json.loads(contract.read_text());assert proof['actual_python_block_random_cases']==200 and proof['bindings'][str(binary)]==sha(binary);bindings.update({str(binary):sha(binary),str(contract):sha(contract),str(R/'tools/soft_demand_cpp/tree_v1.cpp'):sha(R/'tools/soft_demand_cpp/tree_v1.cpp')});setup_tick=time.perf_counter();search=Search(f,rc,binary);search.prepare({},0);cpp_setup_seconds=time.perf_counter()-setup_tick;cpp_search_seconds=0.0
 for q in queries:groups[q['net_id']].append(q)
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='C++ zero-price early multi-target search, original RC budgets and deterministic parent tie semantics retained; original Python clipped full-field search is the reference. Endpoint-only shortest rooted single-parent tree per NET. Positive-capacity physical graph; no cross-NET hard-cap rejection. Report unique-NET demand and explicit capacity overflow; not a legal joint route or checkpoint. Counting ablation uses the exact same paths but independent connection charge. No native labels in prediction inputs; full original endpoint scope.',required_connections=len(queries)),indent=2)+'\n');records=[];owners={};independent=Counter();failures=[]
 for net,qs in sorted(groups.items()):
  assert len({q['source'] for q in qs})==1;src=qs[0]['source'];budgets={q['connection_id']:max(rc.scale//10**9,(3*floors[q['source'],q['sink']]+1)//2) for q in qs};cap=max(budgets.values())+1;tick=time.perf_counter();d,parents,settled=search.search(src,{q['sink'] for q in qs});cpp_search_seconds+=time.perf_counter()-tick
  owned=set()
  for q in sorted(qs,key=lambda q:q['connection_id']):
   if q['sink'] not in settled or d[q['sink']]>budgets[q['connection_id']]:failures.append(dict(query=q,status='BUDGET_UNREACHABLE'));continue
   u=q['sink'];path=[];used={u}
   while u!=src:
    previous,e=parents[u];path.append(f['edge_ids'][e]);u=previous;assert u not in used;used.add(u)
   path.reverse();assert rc.path(src,q['sink'],path)==d[q['sink']];owned.update(used);independent.update(used);records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=path,delay=d[q['sink']]),budget_integer=budgets[q['connection_id']],floor_integer=floors[src,q['sink']]))
  owners[net]=owned
 ledger=Counter(n for owned in owners.values() for n in owned);overflow=sum(max(0,c-f['capacities'][n]) for n,c in ledger.items());candidate=dict(status='COMPLETE_DEMAND_SKETCH' if not failures else 'INCOMPLETE_DEMAND_SKETCH',records=records,ledger=dict(ledger),independent_connection_ledger=dict(independent),completed_connections=len(records),required_connections=len(queries),failure=failures[0] if failures else None,failures=failures,overflow_units=overflow,overflow_nodes=sum(c>f['capacities'][n] for n,c in ledger.items()),eligible_for_legal_route_commit=False,graph_sha256=digest,scope='Complete endpoint demand estimate with possible cross-NET overuse; no route acceptance.')
 (out/'sketch.json').write_text(json.dumps(candidate)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,total_paid_prediction_seconds=time.perf_counter()-begin,cpp_setup_seconds=cpp_setup_seconds,cpp_search_seconds=cpp_search_seconds,completed=len(records),required=len(queries),overflow_units=overflow,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');return {k:candidate[k] for k in ('status','completed_connections','required_connections','overflow_units','overflow_nodes')}
if __name__=='__main__':print(json.dumps(predict(*sys.argv[1:])),flush=True)
