"""All12 original XML physical endpoints and exact Fraction budget audit."""
import json,time
from collections import Counter
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit_unified_v1 import audit
from unified_rr_audit_inventory_v1 import read as read_inventory
from native_route_ledger_import_compact import physical_paths
from memoized_fraction_path_delay_unified_v1 import FractionPathMemo
R=Path(__file__).resolve().parents[1];N=R/'experiments/retained_seed_session_native_cohort_v2_2026-10-08';D=R/'experiments/unified_inventory_native_cohort_audit_v1_2026-10-08';D.mkdir(exist_ok=False);rp=N/'receipt.json';pp=N/'protocol.json';r=json.loads(rp.read_text());p=json.loads(pp.read_text());assert r['protocol_sha256']==sha(pp)
bindings={**r['bindings'],str(rp):sha(rp),str(pp):sha(pp),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(f)==h for f,h in bindings.items())
assert len(r['rows'])==len(p['plans'])==12;electrical={};inventories={};rows=[];start=time.perf_counter()
for x,plan in zip(r['rows'],p['plans']):
 assert (x['width'],x['index'])==(plan['width'],plan['index']) and all(sha(f)==h for f,h in x['files'].items());bindings.update(x['files'])
 if x['exit_code']!=0:
  rows.append(dict(width=x['width'],index=x['index'],status='NATIVE_FAILURE',budget_admitted=False));continue
 w=N/f'w{x["width"]}_m{x["index"]}';route=w/'output.route';target=json.loads(Path(plan['target']).read_text());budget=json.loads(Path(plan['budget']).read_text());graph=Path(target['inputs']['graph']['path'])
 assert x['loaded_marker'] and x['full_check'] and x['vpr_succeeded']
 key=(str(graph),target['graph_sha256'])
 if key not in inventories:inventories[key]=read_inventory(graph,key[1])
 proof=audit(graph,route,inventories[key]);assert proof['all_printed_branch_arc_switch_and_union_checks_pass'] and proof['overflow_units']==0
 paths=physical_paths(route);observed=Counter((name,path[0][0],path[-1][0]) for name,branches in paths.items() for path in branches)
 expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections']);assert observed==expected
 key=(str(graph),target['graph_sha256'])
 if key not in electrical:electrical[key]=FractionPathMemo(graph,key[1],inventories[key])
 memo=electrical[key];bykey={(target['net_names'][str(q['net_id'])],q['source'],q['sink']):q for q in target['connections']};assert len(bykey)==len(target['connections'])
 delays=[];violations=[]
 with memo.batch():
  for name,branches in paths.items():
   for path in branches:
    q=bykey[name,path[0][0],path[-1][0]]
    delay=memo.delay(path)
    cid=q['connection_id'];limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']));ok=delay*10**9<=limit
    delays.append(dict(connection_id=cid,delay_seconds=str(delay),budget_ns=str(limit),budget_pass=ok))
    if not ok:violations.append(cid)
 assert len(delays)==len(target['connections'])
 out=D/f'w{x["width"]}_m{x["index"]}_original_budget_verification.json';out.write_text(json.dumps(dict(rows=sorted(delays,key=lambda y:y['connection_id']),physical=proof,violation_ids=sorted(violations)),indent=2)+'\n');bindings[str(out)]=sha(out)
 rows.append(dict(width=x['width'],index=x['index'],status='FULL_PHYSICAL_ENDPOINT_PASS',connections=len(delays),budget_safe=len(delays)-len(violations),violation_ids=sorted(violations),budget_admitted=not violations,cpd_ns=x['cpd_ns'],wirelength=x['wirelength']))
 print(x['width'],x['index'],'full physical',len(delays),'budget violations',len(violations),flush=True)
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,rows=rows,full_physical_pass_cases=sum(x['status']=='FULL_PHYSICAL_ENDPOINT_PASS' for x in rows),original_budget_admitted_cases=sum(x['budget_admitted'] for x in rows),audit_component_seconds=time.perf_counter()-start,memo_stats={str(k):dict(v.stats) for k,v in electrical.items()},native_cohort_component_seconds=r['native_cohort_component_seconds'],scope='Actual12 native FULL logs and original XML all printed arcs/types/NET capacity/complete named endpoints, plus all original budget Fraction delays. Seed generation/canonical packedpin/native STA equivalence/full original-input workflow and heldout gain not established. Separate native and audit clocks, never sum as a new prospective workflow.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS cohort physical',report['full_physical_pass_cases'],'budget admitted',report['original_budget_admitted_cases'])
