"""Full4 route serialization using exact pin-index identities from original native traces."""
import json,re,xml.etree.ElementTree as ET,time,sys
from pathlib import Path
from collections import Counter,defaultdict
from serialization_rr_inventory_v1 import SerializationInventory
from native_route_ledger_import_compact import physical_paths
from audit_native_route import NET,NODE
from stream_native_route_audit_cached import audit
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from serialize_shared_inventory import serialize
E=R/'experiments';B=E/'adder_capacity_budget_multinet_wire_guard_v3_2026-10-08';D=E/'adder_multinet_wire_guard_shared_serialization_v2_2026-10-08';D.mkdir(exist_ok=False)
v=json.loads((B/'verification.json').read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings={**v['bindings'],str(B/'verification.json'):sha(B/'verification.json')};rows=[];inventory=None;start=time.perf_counter()
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());g=Path(meta['inputs']['graph']['path']);place=Path(meta['inputs']['place']['path']);
 if inventory is None:inventory=SerializationInventory(g,meta['graph_sha256'])
 inventory.validate(g,meta['graph_sha256']);lookup={edge:i for i,edge in enumerate(inventory.edges)}
 original=g.with_name('design.route') if step==0 else E/f'native_resume_all_inventory_adder_step{step}_cold_2026-10-07/first/output.route';nets=[];current=None
 for line in original.read_text().splitlines():
  n=NET.match(line)
  if n:current=dict(net_id=int(n[1]),name=n[2],pins=[]);nets.append(current)
  m=NODE.match(line)
  if m and m[2] in ('SOURCE','SINK'):
   loc=inventory.nodes[int(m[1])][1];index=0 if m[2]=='SOURCE' else int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);pin=dict(index=index,x=int(loc.get('xlow')),y=int(loc.get('ylow')),layer=int(loc.get('layer','0')),**{'class':int(loc.get('ptc'))})
   if pin not in current['pins']:current['pins'].append(pin)
 identity=D/f'step_{step}_identity.jsonl';identity.write_text(''.join(json.dumps(n)+'\n' for n in nets))
 state=json.loads((B/f'step_{step}.json').read_text())['state'];records=[];expected=defaultdict(list)
 for q in meta['connections']:
  path=state[str(q['connection_id'])];ids=[lookup[u,n,s] for (u,_),(n,s) in zip(path,path[1:])];records.append(dict(q,answer=dict(physical_edge_ids=ids)));expected[meta['net_names'][str(q['net_id'])]].append(tuple(tuple(x) for x in path))
 text,pins=serialize(dict(records=records),ep,identity,place,inventory);out=D/f'step_{step}.route';out.write_text(text)
 actual=physical_paths(out);assert {name:Counter(paths) for name,paths in actual.items()}=={name:Counter(paths) for name,paths in expected.items()}
 proof=audit(g,out);assert proof['overflow_units']==0 and len(proof['connections'])==516
 for f in (ep,g,place,original,identity,out,B/f'step_{step}.json'):bindings[str(f)]=sha(f)
 row=dict(step=step,connections=len(pins),full_paths_equal=True,physical_capacity_pass=True,native_reload_verified=False);rows.append(row);print(row,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
for extra in (R/'tools/serialization_rr_inventory_v1.py',R/'tools/native_resume_prototype/serialize_shared_inventory.py'):
 bindings[str(extra)]=sha(extra)
for n in ('serialize_adder_multinet_wire_guard_shared_v2.py','serialize_live_native_candidate.py','native_route_ledger_import_compact.py','stream_native_route_audit_cached.py','audit_native_route.py','pre_route_endpoints.py'):
 p=R/'tools'/n;bindings[str(p)]=sha(p)
(D/'verification.json').write_text(json.dumps(dict(component_seconds=time.perf_counter()-start,bindings=bindings,rows=rows,scope='All2064 candidate branches serialized, exact original native trace site/class/SINK pin-index identities and complete physical paths preserved, full arc/NETcapacity audit. Native trace identity is not independent packednet reload proof; no native STA/HDL/quality or runtime gain claim.'),indent=2)+'\n')
