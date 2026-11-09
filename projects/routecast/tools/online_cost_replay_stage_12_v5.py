"""Propagate current online bank before further finite joint search."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from finite_route_bank_arc_consistency_v1 import propagate
from finite_route_bank_solver_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v5_adder_online_proof_expand_v1_2026-10-09';D=E/'online_cost_replay_v5_adder_online_bank_propagation_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'online_cost_replay_v5_adder_online_proof_expand_verification_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];inv=None
for step in range(1,4):
 meta=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());q={x['connection_id']:x for x in meta['connections']};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()}
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 cap={n:int(c) for n,(kind,c) in inv.physical.nodes.items()};result=propagate(bank,q,cap);out=dict(propagation=result)
 if result['status']=='ARC_CONSISTENT':
  domains={int(c):v for c,v in result['domains'].items()};filtered={c:[bank[c][i] for i in domains[c]] for c in bank};joint=solve(filtered,q,cap,max_nodes=100000);out['joint']=joint
  if joint['status']=='FOUND':out['original_selection']={str(c):domains[c][i] for c,i in joint['selection'].items()}
 p=D/f'step_{step}.json';p.write_text(json.dumps(out,indent=2)+'\n');bindings[str(p)]=sha(p);row=dict(step=step,status=result['status'],removed_candidates=len(result['removals']),empty_connection=result['empty_connection'],joint_status=out.get('joint',{}).get('status'));rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Binary capacity/shared-parent support propagation on online finite bank; delete proof requires independent replay. Arc consistency alone not full feasibility; no allpaths/native/timing/gain claim.'),indent=2)+'\n')
