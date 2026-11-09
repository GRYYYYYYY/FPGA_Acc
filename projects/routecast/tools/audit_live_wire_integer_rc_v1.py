"""Every native response path: original Fraction RC versus current exact lattice sum."""
import json,sys,time
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/sha_resident_known_source_seed_complete_workflow_v1_2026-10-10';D=R/'experiments/live_wire_integer_rc_contract_v1_2026-10-10';D.mkdir();proof=json.loads((S/'wire_transaction_verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());ep=S/'seed/demand/sha1/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);byid={q['connection_id']:q for q in queries};slots={e:i for i,e in enumerate(f['edge_ids'])};wire=S/'seed/native/sha1/wire.jsonl';paths=[]
for l in wire.read_text().splitlines():
 row=json.loads(l)
 if 'receive' not in row:continue
 x=row['receive'].split()
 if x[0]!='Q':continue
 cid,delay,count=map(int,x[1:4]);p=list(map(int,x[4:]));assert count==len(p);q=byid[cid];paths.append((q,delay,p))
assert len(paths)==17176
begin=time.perf_counter()
for q,delay,path in paths:assert rc.path(q['source'],q['sink'],path)==delay
fraction_seconds=time.perf_counter()-begin;edge_count=0;begin=time.perf_counter()
for q,delay,path in paths:
 u=q['source'];total=rc.initial(u);seen={u}
 for eid in path:
  slot=slots[eid];assert f['row_offsets'][u]<=slot<f['row_offsets'][u+1];u=f['dest_ranks'][slot];assert u not in seen;seen.add(u);total+=rc.increment(slot);edge_count+=1
 assert u==q['sink'] and total==delay
integer_seconds=time.perf_counter()-begin;bindings={str(p):sha(p) for p in [Path(__file__),S/'wire_transaction_verification.json',ep,graph,wire,R/'tools/class_cached_integer_rc_v1.py',R/'tools/integer_rc_context.py',R/'tools/csr_exact_buffered_rc.py']};assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,all17176_original_Fraction_and_exact_integer_path_costs_equal=True,physical_edges_checked=edge_count,fraction_cost_only_seconds=fraction_seconds,integer_cost_with_topology_cycle_checks_seconds=integer_seconds,scope='Complete archived current-wire controlled arithmetic contract. Fraction then integer sequential single clocks; graph parse/encoding/manifest/native acquisition outside component clocks. No live pipeline/timegain proof and no independent audit waiver.'),indent=2)+'\n');print('ALL17176 RC PARITY',edge_count,fraction_seconds,integer_seconds)
