"""Authenticate actual accepted chain and independently verify old-path lineage."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'history_three_step_lineage_v1_2026-10-09'
prefixes=['fresh_history_workflow_v1','history_step2_v1','history_step3_v1']
rows=[];bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
def read(p):
 data=json.loads(p.read_text());bindings[str(p)]=sha(p)
 for name,digest in data.get('bindings',{}).items():
  assert sha(name)==digest,name
  assert name not in bindings or bindings[name]==digest
  bindings[name]=digest
 return data
prior=None
for step,prefix in enumerate(prefixes,1):
 accepted=read(E/f'{prefix}_stage_6_2026-10-09/verification.json')
 workflow=read(E/f'{prefix}_2026-10-09/verification.json')
 read(E/f'{prefix}_2026-10-09/independent_verification.json')
 selection=E/f'{prefix}_stage_2_2026-10-09/result.json';state=read(selection)['paths']
 assert len(state)==516
 row=accepted['rows'][0];assert row['step']==step
 assert workflow['quality']==[row]
 count=None
 if prior is not None:
  old=read(prior)['paths'];bank=read(E/f'{prefix}_stage_1_2026-10-09/result.json')['bank'];count=0
  for cid,options in bank.items():
   for option in options:
    if option['origin']=='ELIGIBLE_ACTUAL_OLD_ROUTE':assert option['path']==old[cid];count+=1
  for index in (0,1,2):
   receipt=read(E/f'{prefix}_stage_{index}_2026-10-09/verification.json')
   assert receipt['bindings'][str(prior)]==sha(prior)
 rows.append(dict(step=step,quality=row,eligible_old_candidates_equal_prior=count,individually_measured_workflow_seconds=workflow['workflow_seconds']))
 prior=selection
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,rows=rows,sum_wire_delta_across_placements=sum(row['quality']['wire_delta'] for row in rows),scope='Three individually measured fresh accepted routing steps, prior selection lineage authenticated. Summed wire deltas concern different placements, not one design wirelength. No single three-step outer timer, sameStore commits, matched cold timing, independent timing target or acceleration claim.')
D.mkdir(exist_ok=False);(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(dict(rows=rows,sum_wire_delta_across_placements=report['sum_wire_delta_across_placements']),flush=True)
