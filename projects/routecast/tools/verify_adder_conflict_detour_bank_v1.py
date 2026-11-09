"""All expanded candidates independently replayed with XML and Fraction."""
import json
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_conflict_detour_bank_v1_2026-10-09';r=json.loads((D/'verification.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';m=json.loads(ep0.read_text());inv=read(m['inputs']['graph']['path'],m['graph_sha256']);rows=[]
for step in range(4):
 ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';queries={str(q['connection_id']):q for q in json.loads(ep.read_text())['connections']};budgets={str(b['connection_id']):F(*b['exact_delay_s']) for b in json.loads((E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json').read_text())};v=json.loads((D/f'step_{step}.json').read_text());assert set(v['bank'])==set(queries);count=0;detours=0
 for cid,candidates in v['bank'].items():
  q=queries[cid]
  for c in candidates:
   path=c['path'];assert path[0]==[q['source'],None] and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
   rr,cc=inv.classes[inv.node_classes[q['source']]];delay=rr*cc/2
   for (u,_),(n,s) in zip(path,path[1:]):
    assert inv.arc_multiplicities.get((u,n,s))==1 and int(inv.physical.nodes[n][1])>0
    rr,cc=inv.classes[inv.node_classes[n]];sr,td=inv.electrical_switches[s];delay+=(sr+rr/2)*cc+td
   assert delay==F(c['delay_seconds'])<=budgets[cid];count+=1
   if c['origin']=='conflict_detour':assert c['forbidden_node'] not in {n for n,s in path};detours+=1
 rows.append(dict(step=step,all_candidate_physical_fraction_budgets_pass=True,candidates=count,verified_detours=detours))
(D/'candidate_verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in (D/'verification.json',Path(__file__))},rows=rows,scope='Independent all finitebank path audit; no joint route accepted.'),indent=2)+'\n');print(rows)
