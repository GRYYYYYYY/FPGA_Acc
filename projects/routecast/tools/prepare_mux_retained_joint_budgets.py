"""Construct joint-safe independent connection budgets; retain all fixed moves."""
import json
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_joint_path_floors_2026-10-06';out=ROOT/'experiments/mux_retained_joint_budgets_2026-10-06';out.mkdir();p=json.loads((parent/'protocol.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');rows=[]
for c in p['cases']:
 w,i=c['width'],c['index'];source=parent/f'w{w}_m{i}.json';data=json.loads(source.read_text());old_ep=json.loads(Path(c['old']).read_text());new_ep=json.loads(Path(c['target']).read_text());old_queries={q['connection_id']:q for q in old_ep['connections']};changed_nets={q['net_id']for q in new_ep['connections']if q!=old_queries[q['connection_id']]};affected={q['connection_id']for q in new_ep['connections']if q['net_id']in changed_nets};old_spec=json.loads(Path(c['budget']).read_text());retained={}
 for x in old_spec['constraints']:
  cid=x['connection_id']
  if cid not in affected:
   value=Fraction(x['old_rr_ns']);assert cid not in retained or retained[cid]==value;retained[cid]=value
 floors={int(cid):Fraction(a['answer']['delay']*10**9,data['scale'])for cid,a in data['answers'].items()};floors.update(retained);budget=dict(floors);caps=any(f>1 for f in floors.values());violated=any(sum(floors[c]for c in path['connection_ids'])>Fraction(path['old_rr_plus_headroom_ns'])for path in data['paths']);status='NO_JOINT_VECTOR_FROM_DIAGNOSTIC'if caps or violated else'JOINT_VECTOR_CONSTRUCTED'
 if not caps and not violated:
  proposals={}
  for path in data['paths']:
   ids=path['connection_ids'];free=[cid for cid in ids if cid in affected];spare=Fraction(path['old_rr_plus_headroom_ns'])-sum(floors[cid]for cid in ids);assert spare>=0
   for cid in ids:
    if cid not in affected:proposals[cid]=floors[cid]
    else:proposals[cid]=min(proposals.get(cid,Fraction(1)),floors[cid]+spare/len(free),Fraction(1))
  budget=proposals
  assert all(budget[cid]>=floor for cid,floor in floors.items())
  assert all(sum(budget[c]for c in path['connection_ids'])<=Fraction(path['old_rr_plus_headroom_ns'])for path in data['paths'])
 file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(status=status,budgets_ns={str(c):str(b)for c,b in budget.items()}if status=='JOINT_VECTOR_CONSTRUCTED'else{},parent_sha256=sha(source),retained_fixed_ns={str(cid):str(v)for cid,v in retained.items()},affected_connection_ids=sorted(affected),default_budget_ns='1',policy='Fixed retained actual old RR; affected witness floor plus min perpath equal residual-share, cap1ns; every reportedjointsum preserved. Local timing fixed hypothesis, not globalSTA guarantee.'),indent=2)+'\n');rows.append(dict(width=w,index=i,status=status,sha256=sha(file)));print(rows[-1],flush=True)
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],rows=rows,parent_verification_sha256=sha(parent/'verification.json'),source_sha256=sha(Path(__file__)),scope='All12 allocated before any reroute result. Failure to construct from diagnostic vector not independently proven global/path infeasibility.'),indent=2)+'\n')
