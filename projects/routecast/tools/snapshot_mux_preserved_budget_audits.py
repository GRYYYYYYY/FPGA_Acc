"""Bind only completed cases with all six audits; explicitly report pending cases."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_preserved_budget_online_loop_2026-10-06';names=['control_timing_verification','physical_budget_verification','floor_verification','choice_verification','observation_verification','history_cost_verification'];rows=[];pending=[];policy=Counter();selected=Counter();paths=0
for f in sorted(out.glob('w*_m*/result.json')):
 missing=[n for n in names if not (f.parent/(n+'.json')).exists()]
 if missing:pending.append(dict(case=f.parent.name,missing=missing));continue
 audits={}
 for n in names:
  file=f.parent/(n+'.json');d=json.loads(file.read_text());assert d['result_sha256']==sha(f);audits[n]=sha(file)
  if n=='physical_budget_verification':
   for r in d['rows']:assert not r['budget_violations'];paths+=r['paths']
 d=json.loads(f.read_text());policy.update(a['budget_policy'] for a in d['allocations'] if a['valid']);selected.update(d['allocations'][a['allocation_index']]['budget_policy'] for a in d['attempts']);rows.append(dict(case=f.parent.name,result_sha256=sha(f),audits=audits,status=d['result']['status']))
(out/'audited_snapshot.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),rows=rows,pending_completed_files=pending,valid_allocation_policies=dict(policy),selected_policies=dict(selected),path_occurrences=paths,scope='Available completed-file snapshot with six result-bound audit artifacts only; absent cases/unfinished receipt pending, no full-cohort or native acceptance claim.'),indent=2)+'\n');print(len(rows),paths,dict(policy),dict(selected),'pending',pending)
