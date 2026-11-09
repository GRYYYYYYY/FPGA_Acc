"""Independently authenticate full projection trial and candidate source scope."""
import json,sys,math
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NET
D=R/'experiments/native_endpoint_name_set_v1_2026-10-08'
v=json.loads((D/'verification.json').read_text())
assert all(sha(p)==h for p,h in v['bindings'].items())
old=(R/'tools/verify_ultraembedded_mmc_native_cold_v1.py').read_text()
new=(R/'tools/verify_ultraembedded_mmc_native_name_set_v2.py').read_text()
needle="observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()))"
replacement="required_net_names=set(ep['net_names'].values());observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in required_net_names)"
assert old.count(needle)==1 and new==old.replace(needle,replacement)
W=R/'experiments/ultraembedded_mmc_continuous_workflow_v4_2026-10-08'
assert [x['arm'] for x in v['rows']]==['cold','seed']
rows=[]
for row in v['rows']:
 a=row['arm'];native=W/a/'native/mmc';ep=json.loads((W/a/'demand/mmc/endpoints.json').read_text())
 audit=json.loads((native/'physical_audit.json').read_text())
 proof=json.loads((native/'verification.json').read_text())
 assert all(sha(p)==h for p,h in proof['bindings'].items())
 assert proof['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass']
 names={int(m[1]):m[2] for line in (native/'output.route').read_text().splitlines() if (m:=NET.match(line))}
 allowed=set(ep['net_names'].values())
 actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in audit['connections'] if names[q['net_id']] in allowed)
 required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'])
 assert actual==required and sum(required.values())==row['physical_connections']==115572 and row['complete_counter_parity']
 assert all(math.isfinite(row[k]) and row[k]>0 for k in ['baseline_seconds','candidate_seconds'])
 rows.append(dict(row,candidate_over_baseline=row['candidate_seconds']/row['baseline_seconds']))
bindings={**v['bindings'],str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(p)==h for p,h in bindings.items())
(D/'independent_verification_v1.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,complete_counter_and_exact_source_change_pass=True,scope='Full archived endpoint projection only; producer single-order clocks not independently reconstructed; no complete audit runtime or workflow gain proof.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
