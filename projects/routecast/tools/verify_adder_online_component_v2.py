"""Independent exhaustive proof replay rebuilding owners/parents from selections."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_online_small_component_detours_v1_2026-10-09';T=E/'adder_online_component_solve_v2_2026-10-09';D=E/'adder_online_component_verification_v2_2026-10-09';D.mkdir(exist_ok=False);vp=T/'verification.json';v=json.loads(vp.read_text());authority=E/'adder_online_component_v2_propagation_verification_2026-10-09/verification.json';proof=json.loads(authority.read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());bindings={**proof['bindings'],str(authority):sha(authority),**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];inv=None
for step in range(3,4):
 m=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());q={x['connection_id']:x for x in m['connections']};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()};decomp=json.loads((T/'decomposition.json').read_text());domains={int(c):ids for c,ids in decomp['domains'].items()};bank={c:[options[i] for i in domains[c]] for c,options in bank.items()};labels={cid:index for index,cids in enumerate(decomp['components']) for cid in cids};assert set(labels)==set(bank) and sum(map(len,decomp['components']))==len(bank)
 component=json.loads((T/'component_310.json').read_text());result=component['result'];assert result['status']=='FINITE_BANK_EXHAUSTED' and result['selection'] is None
 if inv is None:inv=read(m['inputs']['graph']['path'],m['graph_sha256'])
 node_users=defaultdict(set);parent_users=defaultdict(lambda:defaultdict(set))
 for cid,options in bank.items():
  for option in options:
   path=option['path']
   for n,sw in path:node_users[n].add(cid)
   for (u,_),(n,sw) in zip(path,path[1:]):parent_users[q[cid]['net_id'],n][cid].add((u,sw))
 for node,users in node_users.items():
  if len({q[c]['net_id'] for c in users})>int(inv.physical.nodes[node][1]):assert len({labels[c] for c in users})==1
 for key,users in parent_users.items():
  if len(set.union(*users.values()))>1:assert len({labels[c] for c in users})==1
 bank={c:bank[c] for c in component['connections']}
 leaves=[];forced_count=0
 def reasons(cid,index,selection):
  owners=defaultdict(set);parents=defaultdict(dict)
  for c,i in selection.items():
   net=q[c]['net_id'];path=bank[c][i]['path']
   for n,s in path:owners[n].add(net)
   for (u,_),(n,s) in zip(path,path[1:]):assert n not in parents[net] or parents[net][n]==(u,s);parents[net][n]=(u,s)
  net=q[cid]['net_id'];path=bank[cid][index]['path'];bad=[]
  for n,s in path:
   if len(owners[n]|{net})>int(inv.physical.nodes[n][1]):bad.append(dict(kind='CAPACITY',node=n,owners=sorted(owners[n]|{net})))
  for (u,_),(n,s) in zip(path,path[1:]):
   if n in parents[net] and parents[net][n]!=(u,s):bad.append(dict(kind='PARENT',node=n,net_id=net,existing=list(parents[net][n]),candidate=[u,s]))
  return bad
 def replay(proof,selection):
  nonlocal_dummy=None
  global_dummy=None
  for cid,i in proof['forced']:
   assert cid not in selection;options=[j for j in range(len(bank[cid])) if not reasons(cid,j,selection)];assert options==[i];selection[cid]=i
  if proof['kind']=='DEAD':
   cid=proof['empty_connection'];assert cid not in selection;rejected=[reasons(cid,i,selection) for i in range(len(bank[cid]))];assert all(rejected);leaves.append(dict(empty_connection=cid,forced_assignments=len(selection),candidate_rejection_reasons=rejected));return
  assert proof['kind']=='BRANCH';cid=proof['connection'];assert cid not in selection;options=[j for j in range(len(bank[cid])) if not reasons(cid,j,selection)];assert [child['index'] for child in proof['children']]==options
  for child in proof['children']:replay(child['proof'],{**selection,cid:child['index']})
 replay(result['proof'],{});row=dict(step=step,components=len(decomp['components']),complete_capacity_parent_coupling_partition_pass=True,unsatisfiable_component=component['connections'],finite_bank_exhaustion_independently_proved=True,dead_leaves=leaves);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Independent coupling completeness and three-connection exhaustive proof replay on sound AC residual bank; finite-bank infeasibility only, with original capacities and shared-parent constraints. Not global model infeasibility/native/timing/gain.'),indent=2)+'\n')
