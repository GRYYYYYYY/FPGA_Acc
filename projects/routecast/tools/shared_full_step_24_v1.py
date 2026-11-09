"""Full independent Fraction/physical/capacity verification of all4 final route states."""
import json
from collections import Counter,defaultdict
from pathlib import Path
from fractions import Fraction as F
from unified_rr_audit_inventory_v2 import read
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_shared_full_stage_7_v1_2026-10-08';r=json.loads((D/'receipt.json').read_text());assert all(sha(f)==h for f,h in r['bindings'].items());inv=None
for step,row in enumerate(r['rows']):
 ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text())
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 v=json.loads((D/f'step_{step}.json').read_text());queries={q['connection_id']:q for q in meta['connections']};budget={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads((E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json').read_text())};audits={x['connection_id']:x for x in v['rows']};assert {int(cid) for cid in v['state']}==set(queries)==set(audits)
 unions=defaultdict(set);parents=defaultdict(dict);fail=[]
 for cidtext,path in v['state'].items():
  cid=int(cidtext);q=queries[cid];source=q['source'];assert path[0]==[source,None] and path[-1][0]==q['sink'];assert len({n for n,s in path})==len(path)
  rr,cc=inv.classes[inv.node_classes[source]];delay=rr*cc/2
  for (u,_),(n,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,n,s))==1 and int(inv.physical.nodes[n][1])>0
   assert n not in parents[q['net_id']] or parents[q['net_id']][n]==(u,s);parents[q['net_id']][n]=(u,s)
   rr,cc=inv.classes[inv.node_classes[n]];sr,td=inv.electrical_switches[s];delay+=(sr+rr/2)*cc+td
  assert delay==F(audits[cid]['delay_seconds']) and budget[cid]==F(audits[cid]['budget_seconds']) and audits[cid]['budget_pass']==(delay<=budget[cid])
  if delay>budget[cid]:fail.append(cid)
  unions[q['net_id']].update(n for n,s in path)
 demand=Counter(n for ns in unions.values() for n in ns);assert {str(n):c for n,c in demand.items()}==v['node_occupancy'];assert all(c<=int(inv.physical.nodes[n][1]) for n,c in demand.items());assert sorted(fail)==v['violation_ids'] and len(fail)==row['remaining_violations']
report=dict(bindings={str(p):sha(p) for p in (D/'receipt.json',Path(__file__),R/'tools/unified_rr_audit_inventory_v2.py')},all2064_final_fraction_physical_capacity_rows_pass=True,remaining_budget_violations=[x['remaining_violations'] for x in r['rows']],scope='Full final state physical arcs/NET parents/uniqueNETcapacity/endpoint and exact independent Fraction recomputation. Does not prove native packedpin reload, global joint infeasibility or user timing/gain.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['remaining_budget_violations'])
