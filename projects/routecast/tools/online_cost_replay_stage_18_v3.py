"""Independent candidate-support removal certificate replay."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v3_adder_online_small_component_detours_v1_2026-10-09';T=E/'online_cost_replay_v3_adder_online_component_solve_v2_2026-10-09';D=E/'online_cost_replay_v3_adder_online_component_v2_propagation_verification_2026-10-09';D.mkdir(exist_ok=False);vp=T/'verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];inv=None
for step in range(3,4):
 meta=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());queries={q['connection_id']:q for q in meta['connections']};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()};proof=json.loads((T/'propagation.json').read_text());doc={};domains={c:set(range(len(v))) for c,v in bank.items()};checks=0;kinds=set()
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 from fractions import Fraction as F
 budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads((E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json').read_text())}
 for cid,candidates in bank.items():
  for candidate in candidates:
   path=candidate['path'];q=queries[cid];assert path[0]==[q['source'],None] and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path);assert not set(candidate.get('forbidden_nodes',[]))&{n for n,s in path};r,c=inv.classes[inv.node_classes[q['source']]];delay=r*c/2
   for (u,_),(n,sw) in zip(path,path[1:]):
    assert inv.arc_multiplicities.get((u,n,sw))==1;r,c=inv.classes[inv.node_classes[n]];sr,td=inv.electrical_switches[sw];delay+=(sr+r/2)*c+td
   assert delay==F(*candidate['exact_delay_s']) and delay<=budgets[cid]
 for deletion in proof['removals']:
  a,i,b=deletion['connection'],deletion['index'],deletion['blocker'];assert a!=b and i in domains[a] and set(deletion['blocker_domain'])==domains[b] and domains[b];path=bank[a][i]['path'];net=queries[a]['net_id']
  for j in domains[b]:
   other=bank[b][j]['path'];othernet=queries[b]['net_id'];conflict=False
   if net!=othernet:
    for node in {n for n,s in path}&{n for n,s in other}:
     if int(inv.physical.nodes[node][1])<2:conflict=True;kinds.add('CAPACITY')
   else:
    parents={v:(u,s) for (u,_),(v,s) in zip(path,path[1:])}
    for (u,_),(node,s) in zip(other,other[1:]):
     if node in parents and parents[node]!=(u,s):conflict=True;kinds.add('PARENT')
   assert conflict;checks+=1
  domains[a].remove(i)
 assert {str(c):sorted(d) for c,d in domains.items()}==proof['domains']
 if proof['status']=='FINITE_BANK_BINARY_CONFLICT':assert not domains[proof['empty_connection']]
 else:assert proof['status']=='ARC_CONSISTENT' and all(domains.values())
 row=dict(step=step,propagation_status=proof['status'],verified_deletions=len(proof['removals']),verified_incompatible_pairs=checks,conflict_kinds=sorted(kinds),finite_bank_infeasibility_proved=proof['status']=='FINITE_BANK_BINARY_CONFLICT',joint_status=doc.get('joint',{}).get('status'));rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Every binary support-removal replay from original capacities/shared-parent paths. Empty domain proves finite bank infeasible only; nonempty domains or subsequent joint search require separate proof, no global/timing/native/gain conclusion.'),indent=2)+'\n')
