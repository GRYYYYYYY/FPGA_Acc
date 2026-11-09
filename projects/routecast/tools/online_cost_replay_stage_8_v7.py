"""Joint finite-bank capacity and shared-parent solving with proof artifact."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from finite_route_bank_solver_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v7_adder_online_detour_bank_v1_2026-10-09';D=E/'online_cost_replay_v7_adder_online_bank_joint_v1_2026-10-09';D.mkdir(exist_ok=False);vp=B/'bounds_verification_v2.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];inv=None;start=time.perf_counter()
for step in range(1,4):
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';m=json.loads(ep.read_text());q={x['connection_id']:x for x in m['connections']};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()}
 if inv is None:inv=read(m['inputs']['graph']['path'],m['graph_sha256'])
 cap={n:int(c) for n,(kind,c) in inv.physical.nodes.items()};result=solve(bank,q,cap,max_nodes=100000);p=D/f'step_{step}.json';p.write_text(json.dumps(result,indent=2)+'\n');bindings[str(p)]=sha(p);row=dict(step=step,status=result['status'],visited_nodes=result['visited_nodes']);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Finite bank exact capacity/shared-parent DFS; outcome requires independent proof replay. No allpathspace infeasibility/native acceptance/timing target/gain claim.'),indent=2)+'\n')
