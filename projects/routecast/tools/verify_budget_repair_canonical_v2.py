"""Independent authentication and original XML physical/path chain for canonical repair."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_cached import audit
R=Path(__file__).resolve().parents[1];D=R/'experiments/budget_repair_canonical_v2_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(f)==h for f,h in r['bindings'].items())
c=r['canonical'];assert c['exit_code']==0 and c['mismatches']==c['fixups']==0 and all(sha(f)==h for f,h in c['files'].items())
prior=R/'experiments/budget_repair_reconciled_dump_v1_2026-10-08/verification.json';v=json.loads(prior.read_text());assert all(sha(f)==h for f,h in v['bindings'].items())
original=prior.parent/'reconciled.route';route=D/'canonical/design.route';norm=lambda f:Counter((name,path) for name,paths in physical_paths(f).items() for path in paths)
assert norm(original)==norm(route) and sum(norm(route).values())==1929
log=D/'canonical/reload.log';text=log.read_text();assert 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text
assert int(re.findall(r'Found (\d+) mismatches',text)[-1])==int(re.findall(r'Fixed (\d+) routing traces',text)[-1])==0
assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==c['cpd_ns']==c['expected_cpd_ns']
graph=Path(c['command'][c['command'].index('--read_rr_graph')+1]);physical=audit(graph,route);assert physical['overflow_units']==0 and len(physical['connections'])==1929
assert v['budget_violation_connection_ids']==[785,1637] and not v['changed_physical_connection_ids']
bindings={**r['bindings'],**c['files'],str(rp):sha(rp),str(prior):sha(prior),str(original):sha(original),str(Path(__file__)):sha(Path(__file__)),str(graph):sha(graph)}
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,all1929_paths_and_original_xml_physical_checks_pass=True,pin_mismatches=0,trace_fixups=0,cpd_ns=c['cpd_ns'],budget_safe_connections=1927,budget_violation_connection_ids=[785,1637],physical=physical,scope='Budget proof inherited via exact entire physical path equality to authenticated Fraction post-sync proof. Second canonical load zero-fixup; first reconciliation counters remain 8/4, no original HDL equivalence/full-budget/time-QoR gain.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS independent canonical 1929 paths; overflow0; pin counters0; 1927 budgets inherited by exact path equality')
