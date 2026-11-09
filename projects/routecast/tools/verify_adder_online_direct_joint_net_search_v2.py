"""Independent physical/Fraction and partial-state replay of joint NET rerouting."""
import json
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_online_direct_joint_net_search_v2_2026-10-09';D=E/'adder_online_direct_joint_net_verification_v2_2026-10-09';D.mkdir(exist_ok=False);rp=B/'verification.json';report=json.loads(rp.read_text());bindings={**report['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());dp=B/'step_3.json';data=json.loads(dp.read_text());ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']};bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);bank={int(c):opts for c,opts in data['bank'].items()};assert set(bank)==set(q)
for cid,options in bank.items():
 assert options
 for option in options:
  path=option['path'];assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink'] and len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[q[cid]['source']]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert delay==F(*option['exact_delay_s']) and delay<=budgets[cid]
def check(state):
 owners=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  assert any(o['path']==path for o in bank[cid]);net=q[cid]['net_id']
  for n,s in path:owners[n].add(net)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
 assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items())
events=0
for attempt in data['attempts']:
 failed=attempt['failed_connection'];released=set(attempt['released_nets']);assert q[failed]['net_id'] in released
 affected=sorted(c for c in q if q[c]['net_id'] in released and c!=failed);assert attempt['affected_connections']==affected
 state={int(c):path for c,path in attempt['initial_state'].items()};assert all(c==failed or q[c]['net_id'] not in released for c in state);check(state)
 for event in attempt['events']:
  assert event['status']=='FOUND';cid=event['connection_id'];assert cid not in state and cid in affected;path=event['path'];assert [inv.physical.arcs[u,v,s] for (u,_),(v,s) in zip(path,path[1:])]==event['physical_edge_ids'];state[cid]=path;check(state);events+=1
 assert attempt['reroute_complete'] and all(c in state for c in affected) and {str(c):path for c,path in state.items()}==attempt['state']
for p in (dp,ep,bp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,candidates=sum(map(len,bank.values())),attempts=len(data['attempts']),found_events=events,partial_capacity_parent_state_replay_pass=True,scope='Every candidate original physical/Fraction budget, each partial joint reroute state unique-NET capacity/sameNET parent, released NET membership and all affected branches. Partial leaf states, not complete route/native acceptance or full graph infeasibility.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
