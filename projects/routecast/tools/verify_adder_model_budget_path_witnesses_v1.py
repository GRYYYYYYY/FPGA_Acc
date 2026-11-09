"""Complete independent physical paths attain pre-existing model budgets; joint capacity separate."""
import json
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from unified_rr_audit_inventory_v2 import read
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_model_budget_path_witnesses_v1_2026-10-08';D.mkdir(exist_ok=False)
pp=E/'adder_budget_provenance_v1_2026-10-08/verification.json';p=json.loads(pp.read_text());bindings={**p['bindings'],str(pp):sha(pp)};assert all(sha(f)==h for f,h in bindings.items())
rows=[];inv=None
for step in range(4):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json'
 meta=json.loads(ep.read_text());g=Path(meta['inputs']['graph']['path'])
 if inv is None:inv=read(g,meta['graph_sha256'])
 assert inv.digest==meta['graph_sha256']
 edge_by_id={eid:key for key,eid in inv.physical.arcs.items()};assert len(edge_by_id)==inv.physical.edge_count
 bp=E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json';budgets={b['connection_id']:b for b in json.loads(bp.read_text())}
 pred=E/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if step==0 else E/f'adder_tree_2L032_move_sequence_audit_2026-10-06/step_{step}_prediction.json'
 paths=json.loads(pred.read_text())['connections'];queries={q['connection_id']:q for q in meta['connections']}
 assert len(paths)==len(queries)==len(budgets)==516 and {x['connection_id'] for x in paths}==set(queries)
 unions=defaultdict(set);parents=defaultdict(lambda:defaultdict(set));witnesses=[]
 for x in paths:
  q=queries[x['connection_id']];assert all(x[k]==q[k] for k in ('connection_id','net_id','source','sink'))
  source=q['source'];sink=q['sink'];assert inv.physical.nodes[source][0]=='SOURCE' and inv.physical.nodes[sink][0]=='SINK'
  r,c=inv.classes[inv.node_classes[source]];delay=r*c/2;node=source;seen={source};net=q['net_id']
  for eid in x['physical_edge_ids']:
   u,v,s=edge_by_id[eid];assert u==node and v not in seen and inv.arc_multiplicities[u,v,s]==1
   assert int(inv.physical.nodes[v][1])>0
   sr,td=inv.electrical_switches[s];r,c=inv.classes[inv.node_classes[v]];delay+=(sr+r/2)*c+td
   parents[net][v].add((u,s));node=v;seen.add(v)
  assert node==sink and int(inv.physical.nodes[source][1])>0
  limit=F(*budgets[x['connection_id']]['exact_delay_s']);assert delay==limit
  unions[net].update(seen);witnesses.append(dict(connection_id=x['connection_id'],path_delay_seconds=str(delay),budget_seconds=str(limit),path_nodes=len(seen)))
 demand=Counter(n for ns in unions.values() for n in ns)
 overflow={str(n):count-int(inv.physical.nodes[n][1]) for n,count in demand.items() if count>int(inv.physical.nodes[n][1])}
 conflicts=[dict(net_id=net,node=n,parents=sorted(ps)) for net,nodes in parents.items() for n,ps in nodes.items() if len(ps)>1 and inv.physical.nodes[n][0]!='SINK']
 out=D/f'step_{step}_witnesses.json';out.write_text(json.dumps(dict(rows=sorted(witnesses,key=lambda x:x['connection_id']),overflow_nodes=overflow,nonterminal_parent_conflicts=conflicts),indent=2)+'\n')
 for f in (ep,bp,pred,out):bindings[str(f)]=sha(f)
 bindings.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
 row=dict(step=step,connections=516,all_individual_paths_attain_original_model_budget=True,overflow_nodes=len(overflow),overflow_units=sum(overflow.values()),nonterminal_parent_conflicts=len(conflicts));rows.append(row);print(row,flush=True)
assert all(sha(f)==h for f,h in bindings.items())
for n in ('verify_adder_model_budget_path_witnesses_v1.py','unified_rr_audit_inventory_v2.py','path_rc.py','pre_route_endpoints.py'):
 f=R/'tools'/n;bindings[str(f)]=sha(f)
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,total_connections=2064,scope='Physical attaining paths prove individual relaxed feasibility under unchanged pre-existing model budgets, not minimum delay optimality or joint legal routing. Complete uniqueNET capacity and nonterminal parent-conflict diagnostics retained; no user clock/native pin/HDL/unseen-family or gain proof.'),indent=2)+'\n')
