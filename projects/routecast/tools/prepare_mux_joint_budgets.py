"""Construct joint-safe independent connection budgets; retain all fixed moves."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_joint_path_floors_2026-10-06';out=ROOT/'experiments/mux_joint_budgets_2026-10-06';out.mkdir();p=json.loads((parent/'protocol.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');rows=[]
for c in p['cases']:
 w,i=c['width'],c['index'];source=parent/f'w{w}_m{i}.json';data=json.loads(source.read_text());floors={int(cid):Fraction(a['answer']['delay']*10**9,data['scale'])for cid,a in data['answers'].items()};budget=dict(floors);caps=any(f>1 for f in floors.values());violated=any(path['violated']for path in data['paths']);status='NO_JOINT_VECTOR_FROM_DIAGNOSTIC'if caps or violated else'JOINT_VECTOR_CONSTRUCTED'
 if not caps and not violated:
  proposals={}
  for path in data['paths']:
   ids=path['connection_ids'];spare=Fraction(path['old_rr_plus_headroom_ns'])-sum(floors[cid]for cid in ids);assert spare>=0
   for cid in ids:proposals[cid]=min(proposals.get(cid,Fraction(1)),floors[cid]+spare/len(ids),Fraction(1))
  budget=proposals
  assert all(budget[cid]>=floor for cid,floor in floors.items())
  assert all(sum(budget[c]for c in path['connection_ids'])<=Fraction(path['old_rr_plus_headroom_ns'])for path in data['paths'])
 file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(status=status,budgets_ns={str(c):str(b)for c,b in budget.items()}if status=='JOINT_VECTOR_CONSTRUCTED'else{},parent_sha256=sha(source),default_budget_ns='1',policy='Witness floor plus min perpath equal residual-share, cap1ns; every reportedjointsum preserved. Local timing fixed hypothesis, not globalSTA guarantee.'),indent=2)+'\n');rows.append(dict(width=w,index=i,status=status,sha256=sha(file)));print(rows[-1],flush=True)
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],rows=rows,parent_verification_sha256=sha(parent/'verification.json'),source_sha256=sha(Path(__file__)),scope='All12 allocated before any reroute result. Failure to construct from diagnostic vector not independently proven global/path infeasibility.'),indent=2)+'\n')
