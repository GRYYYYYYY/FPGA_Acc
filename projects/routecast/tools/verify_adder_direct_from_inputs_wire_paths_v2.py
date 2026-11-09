"""Map actual SAT model to516 physical paths and independently audit whole selection."""
import json
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_direct_from_inputs_wire_paths_verification_v2_2026-10-09'
op=E/'adder_direct_from_inputs_wire_selection_v2_2026-10-09';vp=op/'verification.json';report=json.loads(vp.read_text());bindings={**report['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(f)==h for f,h in bindings.items());D.mkdir(exist_ok=False);doc=json.loads((op/'selection.json').read_text());selected={int(c):i for c,i in doc['selection'].items()}
bp=E/'adder_direct_from_inputs_v2_2026-10-09/result.json';bank={int(c):p for c,p in json.loads(bp.read_text())['bank'].items()};mp=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(mp.read_text());q={x['connection_id']:x for x in meta['connections']};budgetp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(budgetp.read_text())};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);selection={};owners=defaultdict(set);parents=defaultdict(dict);paths={}
for cid,options in bank.items():
 index=selected[cid];assert 0<=index<len(options);selection[cid]=index;option=options[index];path=option['path'];paths[cid]=path;query=q[cid];net=query['net_id'];assert path[0]==[query['source'],None] and path[-1][0]==query['sink'];assert len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
 for n,s in path:owners[n].add(net)
 for (u,_),(v,s) in zip(path,path[1:]):
  assert inv.arc_multiplicities.get((u,v,s))==1;nr,nc=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+nr/2)*nc+td
  assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
 assert delay==F(*option['exact_delay_s']) and delay<=budgets[cid]
assert set(selection)==set(q) and len(selection)==516;assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items());assert {str(c):path for c,path in paths.items()}==doc['paths']
from class_cached_rc_endpoint_context_v1 import load_endpoints
_,_,nodes,_,_,_=load_endpoints(mp);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
initialp=E/'adder_direct_from_inputs_verification_v2_2026-10-09/selection.json';current={int(c):i for c,i in json.loads(initialp.read_text())['selection'].items()}
def audit_choices(choices):
 usage=defaultdict(set);parent=defaultdict(dict)
 for cid,i in choices.items():
  net=q[cid]['net_id'];path=bank[cid][i]['path']
  for n,s in path:usage[n].add(net)
  for (u,_),(n,s) in zip(path,path[1:]):assert n not in parent[net] or parent[net][n]==(u,s);parent[net][n]=(u,s)
 assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in usage.items())
 return sum(length.get(n,0)*len(nets) for n,nets in usage.items())
assert audit_choices(current)==report['initial_geometry']
for event in doc['events']:
 cid=event['connection_id'];assert current[cid]==event['old_index'];assert audit_choices(current)==event['old_cost'];current[cid]=event['new_index'];assert audit_choices(current)==event['new_cost']<event['old_cost']
assert current==selection and audit_choices(current)==report['final_geometry']
p=D/'selection.json';p.write_text(json.dumps(dict(selection=selection,paths=paths),indent=2)+'\n')
for p in (p,op/'selection.json',bp,mp,budgetp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,status='ALL516_PHYSICAL_MODEL_BUDGET_CAPACITY_PARENT_PASS',connections=516,scope='Full selected paths verified; native/canonical STA, retained routes and matched cost still required. Budgets are positive-control target-derived, not independent timing specification.'),indent=2)+'\n');print('ALL516_PHYSICAL_MODEL_BUDGET_CAPACITY_PARENT_PASS')
