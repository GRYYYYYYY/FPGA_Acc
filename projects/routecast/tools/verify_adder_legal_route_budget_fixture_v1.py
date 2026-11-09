"""Full independent Fraction, original physical arcs, shared tree and capacity proof."""
import json
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];D=R/'experiments/adder_legal_route_budget_fixture_v1_2026-10-09';r=json.loads((D/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());inv=None;rows=[]
for plan in r['plans']:
 m=json.loads(Path(plan['endpoints']).read_text());qs={q['connection_id']:q for q in m['connections']};budgets=json.loads(Path(plan['budgets']).read_text());budget={b['connection_id']:b for b in budgets};v=json.loads(Path(plan['state']).read_text());assert len(budget)==len(budgets)==len(qs) and {int(cid) for cid in v['state']}==set(qs)==set(budget)
 if inv is None:inv=read(m['inputs']['graph']['path'],m['graph_sha256'])
 assert inv.digest==m['graph_sha256'];parents=defaultdict(dict);unions=defaultdict(set)
 for cidtext,path in v['state'].items():
  cid=int(cidtext);q=qs[cid];b=budget[cid];assert all(b[k]==q[k] for k in ('net_id','source','sink'));assert path[0]==[q['source'],None] and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
  assert inv.physical.nodes[q['source']][0]=='SOURCE' and inv.physical.nodes[q['sink']][0]=='SINK'
  rr,cc=inv.classes[inv.node_classes[q['source']]];delay=rr*cc/2
  for (u,_),(n,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,n,s))==1 and int(inv.physical.nodes[n][1])>0
   assert n not in parents[q['net_id']] or parents[q['net_id']][n]==(u,s);parents[q['net_id']][n]=(u,s)
   rr,cc=inv.classes[inv.node_classes[n]];sr,td=inv.electrical_switches[s];delay+=(sr+rr/2)*cc+td
  assert delay==F(*b['exact_delay_s']);unions[q['net_id']].update(n for n,s in path)
 demand=Counter(n for ns in unions.values() for n in ns);assert {str(n):c for n,c in demand.items()}==v['node_occupancy'] and all(c<=int(inv.physical.nodes[n][1]) for n,c in demand.items())
 rows.append(dict(step=plan['step'],connections=len(qs),all_original_arc_fraction_budget_parent_capacity_pass=True,known_joint_model_feasible=True))
assert all(sha(p)==h for p,h in r['bindings'].items())
out=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__),R/'tools/unified_rr_audit_inventory_v2.py')},rows=rows,scope='Independent known feasible positive control; budgets equal native witness model delays by construction. Not independent prediction or original-budget success, STA/userclock/gain.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(rows)
