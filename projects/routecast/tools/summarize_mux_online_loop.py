"""Bind all twelve outcomes and completed independent audit artifacts."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_online_loop_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==len(p['cases'])==12;assert all(sha(f)==h for f,h in p['sources'].items());rows=[];totals=Counter()
for case,row in zip(p['cases'],r['rows']):
 assert (case['width'],case['index'])==(row['width'],row['index'])
 if row['status']=='PRIOR_ALLOCATION_SKIP':rows.append(row);continue
 work=out/f"w{row['width']}_m{row['index']}";result=work/'result.json';assert sha(result)==row['result_sha256'];data=json.loads(result.read_text());audits={}
 for name in ('control_timing_verification','physical_budget_verification','floor_verification','choice_verification','observation_verification'):
  file=work/(name+'.json');a=json.loads(file.read_text());assert a['result_sha256']==sha(result);audits[name]=sha(file)
  if name=='physical_budget_verification':
   for attempt in a['rows']:totals['path_occurrences']+=attempt['paths'];totals['restricted_path_occurrences']+=attempt['restricted_paths'];totals['budget_violations']+=len(attempt['budget_violations'])
  if name=='choice_verification':totals['option_decisions']+=a['option_decisions']
  if name=='observation_verification':totals['observations']+=a['witnesses'];totals['observation_labels']+=a['finite_labels']
 totals['attempts']+=len(data['result']['trace']);totals['allocations']+=len(data['allocations']);rows.append(dict(**row,audits=audits))
assert totals['budget_violations']==0
(out/'audit_summary.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),source_sha256=sha(Path(__file__)),statuses=dict(Counter(row['status'] for row in rows)),totals=dict(totals),rows=rows,scope='All fixed cohort outcomes and percase independent timing/control/physical/exclusion/shortest-floor/selection/observation audits bound. Path occurrences repeat connections across attempts. No complete route/native FULL/STA, full lifecycle gain or general architecture claim.'),indent=2)+'\n');print(dict(totals));print(dict(Counter(row['status'] for row in rows)))
