"""Independent candidate-support removal certificate replay."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v10pair0_adder_online_proof_expand_v1_2026-10-09';T=E/'online_cost_replay_v10pair0_adder_online_bank_propagation_v1_2026-10-09';D=E/'online_cost_replay_v10pair0_adder_online_bank_propagation_verification_v1_2026-10-09';D.mkdir(exist_ok=False);vp=T/'verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];inv=None
for step in range(3,4):
 meta=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());queries={q['connection_id']:q for q in meta['connections']};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()};doc=json.loads((T/f'step_{step}.json').read_text());assert doc['joint_policy']=='DEFER_TO_CAPACITY_PARENT_COMPONENT_SOLVER' and 'joint' not in doc;original_path=E/f'adder_online_bank_propagation_v1_2026-10-09/step_{step}.json';original=json.loads(original_path.read_text());assert doc['propagation']==original['propagation'];bindings[str(original_path)]=sha(original_path);proof=doc['propagation'];domains={c:set(range(len(v))) for c,v in bank.items()};checks=0;kinds=set()
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
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
