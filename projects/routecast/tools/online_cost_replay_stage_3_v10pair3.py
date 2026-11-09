"""Independent Fraction and unique-NET ownership replay of every online retry."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v10pair3_adder_online_conflict_branch_v1_2026-10-09';D=E/'online_cost_replay_v10pair3_adder_online_conflict_branch_verification_v1_2026-10-09';D.mkdir(exist_ok=False);p=B/'verification.json';r=json.loads(p.read_text());bindings={**r['bindings'],str(p):sha(p),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());inv=None;rows=[]
for step in range(3,4):
 meta=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());q={x['connection_id']:x for x in meta['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads((E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json').read_text())};old={int(c):p for c,p in json.loads((E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step-1}_state.json').read_text())['state'].items()};doc=json.loads((B/f'step_{step}.json').read_text())
 if inv is None:inv=read(meta['inputs']['graph']['path'],meta['graph_sha256'])
 checked=0;witnesses=0
 def checkpath(event):
  cid=event['connection_id'];path=event['path'];assert not ({n for n,sw in path}&set(attempt['bans'].get(str(q[cid]['net_id']),[])));assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink'] and len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[q[cid]['source']]];delay=r*c/2;ids=[]
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;ids.append(inv.physical.arcs[u,v,s]);r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert ids==event['physical_edge_ids'] and delay<=budgets[cid]
 def inventory(state):
  owners=defaultdict(set);parents=defaultdict(dict)
  for cid,path in state.items():
   net=q[cid]['net_id'];assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink']
   for n,s in path:owners[n].add(net)
   for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
  assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items());return owners,parents
 for attempt in doc['attempts']:
  nets=set(attempt['released_nets']);state={c:path for c,path in old.items() if q[c]['net_id'] not in nets};owners,parents=inventory(state)
  for event in attempt['events']:
   if event['status']!='FOUND':continue
   checkpath(event);assert event['connection_id'] not in state;state[event['connection_id']]=event['path'];net=q[event['connection_id']]['net_id']
   for n,s in event['path']:
    owners[n].add(net);assert len(owners[n])<=int(inv.physical.nodes[n][1])
   for (u,_),(v,s) in zip(event['path'],event['path'][1:]):
    assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
   checked+=1
  rebuilt_owners,rebuilt_parents=inventory(state);assert dict(rebuilt_owners)==dict(owners) and dict(rebuilt_parents)==dict(parents)
  witness=attempt.get('capacity_relaxed_witness')
  if witness and witness['status']=='FOUND':
   checkpath(witness);net=q[witness['connection_id']]['net_id'];blocked=set()
   for n,s in witness['path'][1:]:
    others=owners[n]-{net}
    if len(others)>=int(inv.physical.nodes[n][1]):blocked.update(others)
   assert sorted(blocked-nets)==witness['external_old_nets'] and sorted(blocked&nets)==witness['already_staged_nets'];witnesses+=1
   if attempt.get('action')=='SPLIT_NET_NODE_CONFLICT':
    node=attempt['split_node'];others=owners[node]-{net};assert len(others)>=int(inv.physical.nodes[node][1]) and set(attempt['split_owners'])==others|{net}
 assert not doc['committed'] and doc['state'] is None;rows.append(dict(step=step,attempts=len(doc['attempts']),generated_paths_independent_fraction_capacity_parent_pass=checked,diagnostic_witnesses_fraction_owner_replay_pass=witnesses,stop_reason=doc['stop_reason'],no_candidate_published=True));print(rows[-1],flush=True)
reference=json.loads((E/'adder_online_conflict_branch_verification_v1_2026-10-09/verification.json').read_text());assert rows==[row for row in reference['rows'] if row['step']==3]
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Independent every retry original physical/Fraction budget, incremental partial shared parent/capacity with full end-of-attempt rebuild parity and witness owner/split membership/NET-node ban replay. No complete candidate/native/gain/global infeasibility proof.'),indent=2)+'\n')
