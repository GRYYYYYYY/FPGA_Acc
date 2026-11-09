"""Full graph field parity against separate physical and Fraction XML readers."""
import json,time
from pathlib import Path
from unified_rr_audit_inventory_v1 import read
from buffered_rc_node_classes import read as electrical_read
from native_route_audit_cache import snapshot,clear_cache
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/unified_rr_audit_inventory_v1_2026-10-08';D.mkdir(exist_ok=False)
p=R/'experiments/retained_seed_session_native_cohort_v2_2026-10-08/protocol.json'
plans=json.loads(p.read_text())['plans'];seen=set();rows=[];bindings={str(p):sha(p)}
for plan in plans:
 target=json.loads(Path(plan['target']).read_text());g=Path(target['inputs']['graph']['path']);digest=target['graph_sha256']
 if str(g) in seen:continue
 seen.add(str(g));assert sha(g)==digest;bindings[str(g)]=digest
 start=time.perf_counter();u=read(g,digest);ut=time.perf_counter()-start
 clear_cache();start=time.perf_counter();a=snapshot(g,digest);ids,classes,switches,h=electrical_read(g);rt=time.perf_counter()-start
 assert dict(u.physical.nodes)==dict(a.nodes)
 assert u.physical.duplicate_nodes==a.duplicate_nodes
 assert dict(u.physical.arcs)==dict(a.arcs)
 assert u.physical.switches==a.switches and u.physical.edge_count==a.edge_count
 assert u.node_classes==tuple(ids) and u.classes==tuple(classes)
 assert dict(u.electrical_switches)==switches and u.digest==h
 try:u.physical.nodes[0]=('broken','0')
 except TypeError:pass
 else:raise AssertionError('Mutable inventory')
 try:read(g,'0'*64)
 except ValueError:pass
 else:raise AssertionError('Stale epoch accepted')
 rows.append(dict(graph=str(g),nodes=len(ids),edges=a.edge_count,unified_seconds=ut,separate_readers_seconds=rt))
 print(rows[-1],flush=True)
assert len(rows)==3 and all(sha(k)==v for k,v in bindings.items())
for name in ('unified_rr_audit_inventory_v1.py','verify_unified_rr_audit_inventory_v1.py','buffered_rc_node_classes.py','native_route_audit_cache.py','path_rc.py','pre_route_endpoints.py'):
 f=R/'tools'/name;bindings[str(f)]=sha(f)
report=dict(bindings=bindings,rows=rows,all_three_full_graph_field_parity=True,scope='Full physical inventory and exact electrical class/switch parity on three developed mux RR graphs; serial single observations, no complete route audit, paired speedup, heldout or budget admission claim. Unified reader rejects duplicate/noncontiguous IDs by electrical contract; not a drop-in physical-only parser for arbitrary graphs.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
