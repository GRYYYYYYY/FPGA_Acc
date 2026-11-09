"""Independent complete-owner release/staged restoration and clipped potential proof replay."""
import json
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
R=Path(__file__).resolve().parents[1];D=R/'experiments/critical_owner_transaction_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);_,_,nodes,f,rc,queries=load_endpoints(Path(case['target']));assert rc.scale==r['scale'];byid={q['connection_id']:q for q in queries};budget=json.loads(Path(case['budget']).read_text());base={int(cid):tuple(tuple(x) for x in p) for cid,p in json.loads((R/'experiments/budget_occupied_branch_repair_v1_2026-10-08/receipt.json').read_text())['state'].items()}
protocol=json.loads((D/'protocol.json').read_text());assert [x['plan'] for x in r['rows']]==protocol['plans'] and len(r['rows'])==4
checks=stages=0
for row in r['rows']:
 plan=row['plan'];released={q['connection_id'] for q in queries if q['net_id']==plan['owner']};assert released==set(plan['released_connections']);state={cid:p for cid,p in base.items() if cid not in released|{plan['critical']}};sequence=[plan['critical'],*plan['restore_order']];assert len(plan['restore_order'])==len(released) and set(plan['restore_order'])==released
 def frame():
  union=defaultdict(set);parents=defaultdict(dict)
  for cid,p in state.items():
   q=byid[cid];assert p[0]==(q['source'],None) and p[-1][0]==q['sink'] and len({n for n,s in p})==len(p);union[q['net_id']].update(n for n,s in p)
   for (u,_),(v,s) in zip(p,p[1:]):assert v not in parents[q['net_id']] or parents[q['net_id']][v]==(u,s);parents[q['net_id']][v]=(u,s)
  ledger=Counter(n for p in union.values() for n in p);assert all(v<=f['capacities'][n] for n,v in ledger.items());return union,parents,ledger
 for ordinal,e in enumerate(row['events']):
  cid=e['connection_id'];assert cid==sequence[ordinal] and cid not in state;q=byid[cid];union,parents,ledger=frame();outside=ledger.copy();outside.subtract(union[q['net_id']]);fixed=parents[q['net_id']];assert outside[q['source']]<f['capacities'][q['source']]
  limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9*rc.scale;ceiling=limit.numerator//limit.denominator;assert e['budget_integer_ceiling']==ceiling
  cp=Path(e['certificate']);assert sha(cp)==e['certificate_sha256'];c=json.loads(cp.read_text());clip=c['clip'];pot={int(n):v for n,v in c['potentials'].items()};assert pot.get(q['source'],clip)==min(rc.initial(q['source']),clip)
  for u,value in pot.items():
   assert 0<=value<clip and outside[u]<f['capacities'][u]
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot]
    if outside[v]>=f['capacities'][v] or (v in fixed and fixed[v]!=(u,f['switch_ids'][slot])):continue
    assert pot.get(v,clip)<=value+rc.increments[slot];checks+=1
  stages+=1
  if e['status']=='STAGED':
   path=tuple(tuple(x) for x in e['path']);assert len(path)-1==len(e['physical_edge_ids']);assert rc.path(q['source'],q['sink'],e['physical_edge_ids'])==e['delay_integer']==clip<=ceiling;u=q['source']
   for (v,s),eid in zip(path[1:],e['physical_edge_ids']):
    slots=[i for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if f['edge_ids'][i]==eid];assert len(slots)==1;i=slots[0];assert (f['dest_ranks'][i],f['switch_ids'][i])==(v,s) and outside[v]<f['capacities'][v] and (v not in fixed or fixed[v]==(u,s));u=v
   state[cid]=path;frame()
  else:assert e['status']=='NO_CONSTRAINED_BUDGET_PATH' and clip==ceiling+1 and pot.get(q['sink'],clip)==clip and ordinal==len(row['events'])-1
 if row['transaction_complete']:assert len(row['events'])==len(sequence) and set(state)==set(base);frame()
 else:assert row['events'][-1]['status']=='NO_CONSTRAINED_BUDGET_PATH';state=dict(base)
 assert row['state']=={str(cid):[list(x) for x in p] for cid,p in state.items()} and not row['published']
assert all(sha(p)==h for p,h in r['bindings'].items())
report=dict(receipt_sha256=sha(rp),verifier_sha256=sha(Path(__file__)),all_four_complete_owner_transactions_replay_pass=True,stages=stages,edge_inequalities=checks,complete_connections=1929,scope='Shared XML electrical loader; independent all-stage physical/budget/parent/occupancy/clipped-potential and full release/restore/rollback replay. No global CPD/native acceptance or publication.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
