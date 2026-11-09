"""Certify relaxed minima using edge inequalities plus attaining paths, not another search."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);out=ROOT/f'experiments/branch_budget_cohort_rr_floors_w{w}_m{i}_2026-10-08';start=time.perf_counter();r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(f)==h for f,h in p['inputs'].items());ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';_,digest,nodes,f,rc,queries=load_endpoints(ep);assert digest==r['graph_sha256'] and rc.scale==r['scale'] and all(v>=0 for v in rc.increments)
assert {q['connection_id'] for q in queries}=={x['query']['connection_id'] for x in r['rows']} and len(queries)==len(r['rows'])
byid={q['connection_id']:q for q in queries};certs={};checks=0
for file in r['certificates']:
 assert sha(file['path'])==file['sha256'];c=json.loads(Path(file['path']).read_text());source=c['source'];assert source==file['source'];assert source not in certs;certs[source]=c
 assert c['clip'] is not None # This experiment requires complete coverage; retain failures in producer otherwise.
 clip=c['clip'];pot={int(n):v for n,v in c['potentials'].items()};assert pot.get(source,clip)==rc.initial(source)
 for u,value in pot.items():
  assert 0<=value<clip and f['capacities'][u]>0
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if f['capacities'][v]<=0:continue
   assert pot.get(v,clip)<=value+rc.increments[slot];checks+=1
 # Nodes at clipped value trivially satisfy all outgoing inequalities since weights are nonnegative.
 c['decoded']=pot
edges={eid:slot for slot,eid in enumerate(f['edge_ids'])}
for row in r['rows']:
 q=row['query'];assert q==byid[q['connection_id']] and row['status']=='FOUND';c=certs[q['source']];value=c['decoded'].get(q['sink'],c['clip']);assert value==row['minimum_integer'];assert rc.path(q['source'],q['sink'],row['physical_edge_ids'])==value
 assert f['capacities'][q['source']]>0 and all(f['capacities'][f['dest_ranks'][edges[eid]]]>0 for eid in row['physical_edge_ids'])
result=dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),connections=len(queries),certificates=len(certs),nontrivial_edge_inequalities=checks,verification_seconds=time.perf_counter()-start,scope='Exact integer clipped potentials prove no positive-capacity path has lower additive buffered delay; every target has an attaining physical path. Shared XML/RC loader; independent optimality proof, not native shared-tree STA or joint capacity feasibility.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(w,result['connections'],'certified',result['verification_seconds'],flush=True)
