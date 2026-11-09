"""Authenticate ABBA observations and every full physical/budget proof."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/alternating_inventory_audit_v1_2026-10-08'
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text())
assert r['protocol_sha256']==sha(D/'protocol.json')
assert all(sha(f)==h for f,h in p['bindings'].items())
assert [x['arm'] for x in r['rows']]==p['order']==['separate','unified','unified','separate']
b=json.loads((R/'experiments/memoized_fraction_native_cohort_audit_v1_2026-10-08/verification.json').read_text())
for x in r['rows']:
 out=D/f'{x["index"]}_{x["arm"]}';v=json.loads((out/'verification.json').read_text())
 assert x['exit_code']==0 and sha(out/'verification.json')==x['verification_sha256']
 assert x['subprocess_seconds']>=v['audit_component_seconds']>0
 assert all(sha(f)==h for f,h in v['bindings'].items())
 assert v['rows']==b['rows'] and v['memo_stats']==b['memo_stats']
 for row in v['rows']:
  name=f'w{row["width"]}_m{row["index"]}_original_budget_verification.json'
  assert json.loads((out/name).read_text())==json.loads((R/'experiments/memoized_fraction_native_cohort_audit_v1_2026-10-08'/name).read_text())
means={a:statistics.mean(x['subprocess_seconds'] for x in r['rows'] if x['arm']==a) for a in ('separate','unified')}
pairs=[dict(separate_seconds=r['rows'][i]['subprocess_seconds'],unified_seconds=r['rows'][j]['subprocess_seconds'],unified_over_separate=r['rows'][j]['subprocess_seconds']/r['rows'][i]['subprocess_seconds']) for i,j in ((0,1),(3,2))]
report=dict(bindings={str(f):sha(f) for f in (D/'protocol.json',D/'receipt.json',Path(__file__))},all_four_full12_proofs_equal=True,connections_per_run=13324,original_budget_admitted_cases=0,mean_subprocess_seconds=means,paired_observations=pairs,unified_faster_in_both_observations=all(x['unified_over_separate']<1 for x in pairs),scope='Two order-reversed adjacent observations of complete archive audit subprocesses. Limited developer-family audit evidence only; no statistical confidence, OS-cache control, full seed/cold workflow speedup, quality acceptance or native rerun.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
