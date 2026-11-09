"""Compare all old-route state/edges/exact delay with original full CSR importer."""
import json,time
from fractions import Fraction
from pathlib import Path
from dataclasses import replace
from types import MappingProxyType
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from unified_rr_audit_inventory_v2 import read
from direct_retained_route_import_v1 import load
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/direct_retained_route_import_v1_2026-10-08';D.mkdir(exist_ok=False)
p=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';cases=json.loads(p.read_text())['cases'];rows=[];bindings={str(p):sha(p)}
for w in (8,16,32):
 ep=Path(next(c['old'] for c in cases if c['width']==w));meta=json.loads(ep.read_text());g=Path(meta['inputs']['graph']['path']);route=g.with_name('design.route')
 start=time.perf_counter();_,h,nodes,f,rc,q=load_endpoints(ep);a=load_complete(route,meta,nodes,f,rc);at=time.perf_counter()-start
 start=time.perf_counter();inv=read(g,h);b=load(route,meta,inv);bt=time.perf_counter()-start
 assert a[0]==b[0]
 ar={x['connection_id']:dict(connection_id=x['connection_id'],delay_seconds=str(Fraction(x['delay_integer'],rc.scale)),physical_edge_ids=x['physical_edge_ids']) for x in a[1]}
 assert ar=={x['connection_id']:x for x in b[1]}
 assert b[2]['overflow_units']==0
 path=next(iter(b[0].values()));key=(path[0][0],path[1][0],path[1][1]);counts=dict(inv.arc_multiplicities);counts[key]=2
 try:load(route,meta,replace(inv,arc_multiplicities=MappingProxyType(counts)))
 except ValueError as e:assert 'Nonunique' in str(e)
 else:raise AssertionError('Duplicate required arc accepted')
 assert load(route,meta,inv)[1]==b[1]
 bindings.update({str(ep):sha(ep),str(route):sha(route),**{v['path']:v['sha256'] for v in meta['inputs'].values()}})
 row=dict(width=w,connections=len(q),complete_state_exact_delays_edges_equal=True,reference_build_import_seconds=at,direct_inventory_import_seconds=bt,capacity_overflow=0,duplicate_arc_rejected_and_recovered=True);rows.append(row);print(row,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
for n in ('verify_direct_retained_route_import_v1.py','direct_retained_route_import_v1.py','unified_rr_audit_inventory_v2.py','stream_native_route_audit_unified_v1.py','class_cached_rc_endpoint_context_v1.py','load_complete_route_state_v1.py','native_route_ledger_import_compact.py','path_rc.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All three developed old routes complete state/physical edge IDs/exact Fraction delay parity and complete physical audit. No mutable optimization ledger export or native packed pin proof. Own authenticated inventory construction assumed; controlled in-memory multiplicity rejection. Reference-first single clocks, no fullworkflow speedup or original-budget acceptance.'),indent=2)+'\n')
