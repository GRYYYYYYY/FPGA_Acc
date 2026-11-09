"""Authenticate complete diagnostic coverage and retain all timing outcomes."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
D=R/'experiments/mmc_ordered_owned_search_pool_v1_2026-10-10';vp=D/'verification.json'
v=json.loads(vp.read_text());assert v['complete_all_initial_and_two_feedback_primary_requests_equal']
for section in ['bindings','files']:assert all(sha(p)==h for p,h in v[section].items())
endpoint=next(Path(p) for p in v['bindings'] if p.endswith('/endpoints.json'))
rp=next(Path(p) for p in v['bindings'] if p.endswith('/seed/model/mmc/receipt.json'))
queries=json.loads(endpoint.read_text())['connections'];r=json.loads(rp.read_text());counts={}
for q in queries:counts[q['net_id']]=counts.get(q['net_id'],0)+1
assert len(queries)==v['required_connections']==115572
assert len(v['epochs'])==3
rows=[]
for i,row in enumerate(v['epochs']):
 nets=sorted(counts) if i==0 else r['rounds'][i-1]['affected_nets']
 assert row['epoch']==i and row['nets']==len(nets) and row['connection_requests']==sum(counts[n] for n in nets)
 assert row['requested_delays_parents_settled_equal']
 a=row['serial_search_snapshot_hash_seconds'];b=row['pool_search_snapshot_hash_seconds'];assert a>0 and b>0
 rows.append(dict(row,pool_to_serial_ratio=b/a,pool_minus_serial_seconds=b-a))
a=sum(x['serial_search_snapshot_hash_seconds'] for x in rows);b=sum(x['pool_search_snapshot_hash_seconds'] for x in rows)
bindings={**closure([Path(__file__)]),str(vp):sha(vp)}
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,complete_original_NET_and_connection_phase_coverage_authenticated=True,rows=rows,total_NET_searches=sum(x['nets'] for x in rows),total_connection_requests=sum(x['connection_requests'] for x in rows),sum_disjoint_phase_serial_seconds=a,sum_disjoint_phase_pool_seconds=b,pool_to_serial_ratio=b/a,observed_all_phases_faster=all(x['pool_to_serial_ratio']<1 for x in rows),observed_sum_faster=b<a,scope='Full development requested-path diagnostic coverage at archived prices/schedule. Timing includes snapshot/hash, fixed serial-first order, not stable causal throughput or fresh model fullworkflow timing. Small v2 interruption cleanup proof does not replace this v1 fullgraph result. Default unchanged; integration requires its own fresh complete state/event and independent audits.')
(D/'comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
