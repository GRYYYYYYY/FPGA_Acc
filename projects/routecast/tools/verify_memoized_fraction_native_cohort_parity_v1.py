"""All scientific rows/proofs unchanged plus bounded cache and graph-epoch tests."""
import json,tempfile
from pathlib import Path
from memoized_fraction_path_delay_v1 import FractionPathMemo
from native_route_ledger_import_compact import physical_paths
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'memoized_fraction_native_cohort_audit_v1_2026-10-08';N=E/'retained_seed_session_native_cohort_v2_2026-10-08'
vp=D/'verification.json';oldp=N/'verification.json';v=json.loads(vp.read_text());old=json.loads(oldp.read_text())
bindings={**v['bindings'],str(vp):sha(vp),str(oldp):sha(oldp),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/memoized_fraction_path_delay_v1.py'):sha(R/'tools/memoized_fraction_path_delay_v1.py')}
assert all(sha(p)==h for p,h in old['bindings'].items());assert v['rows']==old['rows']
for row in v['rows']:
 w,i=row['width'],row['index'];a=D/f'w{w}_m{i}_original_budget_verification.json';b=N/f'w{w}_m{i}/original_budget_verification.json'
 assert json.loads(a.read_text())==json.loads(b.read_text());bindings[str(b)]=sha(b)
plan=json.loads((N/'protocol.json').read_text())['plans'][0];target=json.loads(Path(plan['target']).read_text());graph=Path(target['inputs']['graph']['path']);paths=[path for branches in physical_paths(N/'w8_m0/output.route').values() for path in branches];a,b=paths[:2];assert a!=b
memo=FractionPathMemo(graph,target['graph_sha256'],max_paths=1)
with memo.batch():
 x=memo.delay(a);assert memo.delay(a)==x;memo.delay(b);assert memo.delay(a)==x
assert memo.stats==dict(hits=1,misses=3,evictions=2)
try:memo.delay(a)
except ValueError:pass
else:raise AssertionError('Unauthenticated lookup allowed')
with memo.batch():
 for bad in ([],[(a[0][0],0)],[(a[0][0],None),(a[0][0],0)]):
  try:memo.delay(bad)
  except ValueError:pass
  else:raise AssertionError('Invalid path cached')
 assert memo.delay(a)==x
with tempfile.TemporaryDirectory(prefix='routecast-fraction-cache-') as tmp:
 p=Path(tmp)/'graph.xml';data=graph.read_bytes();p.write_bytes(data);copy=FractionPathMemo(p,sha(p))
 try:
  with copy.batch():
   copy.delay(a);p.write_bytes(data+b'\n')
 except ValueError as e:assert 'changed during audit' in str(e)
 else:raise AssertionError('Mid-batch graph change accepted')
 p.write_bytes(data)
 with copy.batch():assert copy.delay(a)==x
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,all12_scientific_budget_rows_and_physical_proofs_equal=True,total_connections=sum(x['connections'] for x in v['rows']),memo_stats=v['memo_stats'],observed_memo_audit_seconds=v['audit_component_seconds'],reference_audit_seconds=old['audit_component_seconds'],bounded_cache_eviction_pass=True,invalid_path_rejected=True,graph_mutation_rejected_and_recovered=True,scope='Exact row/physical proof parity over full12 archives plus one-node cache limit, invalid paths and controlled temporary graph mutation. Reference Fraction helper shared electrical loader; no new native/canonical/full-workflow or replicated paired gain.')
(D/'parity_verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','memo_stats')});print(v['memo_stats'])
