"""Independent exhaustive proof replay rebuilding owners/parents from selections."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v2_adder_online_detour_bank_v1_2026-10-09';T=E/'online_cost_replay_v2_adder_online_bank_joint_v1_2026-10-09';D=E/'online_cost_replay_v2_adder_online_bank_joint_verification_v1_2026-10-09';D.mkdir(exist_ok=False);vp=T/'verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[];inv=None
for step in range(1,4):
 m=json.loads((E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json').read_text());q={x['connection_id']:x for x in m['connections']};bank={int(c):p for c,p in json.loads((B/f'step_{step}.json').read_text())['bank'].items()};result=json.loads((T/f'step_{step}.json').read_text());assert result['status']=='FINITE_BANK_EXHAUSTED' and result['selection'] is None
 if inv is None:inv=read(m['inputs']['graph']['path'],m['graph_sha256'])
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
 replay(result['proof'],{});row=dict(step=step,finite_bank_exhaustion_independently_proved=True,dead_leaves=leaves);rows.append(row);print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Independent forced-domain and exhaustive-child proof replay for finite bank only, with original capacities and shared-parent constraints. Not global model infeasibility/native/timing/gain.'),indent=2)+'\n')
