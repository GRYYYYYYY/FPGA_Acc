"""Independent complete path, exact delay, shared-parent, capacity and wire audit."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'online_cost_replay_v4_adder_online_leaf_context_search_v1_2026-10-09';T=E/'online_cost_replay_v4_adder_online_component_solve_v5_2026-10-09';D=E/'online_cost_replay_v4_adder_online_full_selection_verification_v1_2026-10-09';D.mkdir(exist_ok=False);vp=T/'verification.json';v=json.loads(vp.read_text());assert v['status']=='FOUND';bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']};bank=json.loads((B/'step_3.json').read_text())['bank'];selection={int(c):i for c,i in v['selection'].items()};assert set(selection)==set(q) and len(q)==516;g=Path(meta['inputs']['graph']['path']);inv=read(g,meta['graph_sha256']);budgetp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(budgetp.read_text())};owners=defaultdict(set);parents=defaultdict(dict);state={};origins=Counter();length={}
for node in ET.parse(g).getroot().find('rr_nodes'):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[int(node.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
for cid,index in selection.items():
 candidate=bank[str(cid)][index];path=candidate['path'];query=q[cid];assert path[0]==[query['source'],None] and path[-1][0]==query['sink'];assert inv.physical.nodes[path[0][0]][0]=='SOURCE' and inv.physical.nodes[path[-1][0]][0]=='SINK';assert len({n for n,s in path})==len(path);net=query['net_id'];r,c=inv.classes[inv.node_classes[query['source']]];delay=r*c/2
 for n,s in path:assert int(inv.physical.nodes[n][1])>0;owners[n].add(net)
 for (u,_),(n,s) in zip(path,path[1:]):
  assert inv.arc_multiplicities.get((u,n,s))==1;r,c=inv.classes[inv.node_classes[n]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td;assert n not in parents[net] or parents[net][n]==(u,s);parents[net][n]=(u,s)
 assert delay==F(*candidate['exact_delay_s']) and delay<=budgets[cid];state[str(cid)]=path;origins[candidate['origin']]+=1
assert all(len(nets)<=int(inv.physical.nodes[n][1]) for n,nets in owners.items());wire=sum(length.get(n,0)*len(nets) for n,nets in owners.items());oldp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_2_state.json';old=json.loads(oldp.read_text())['state'];retained=sum(old[c]==p for c,p in state.items());sp=D/'step_3_state.json';sp.write_text(json.dumps(dict(state=state,wire=wire,node_occupancy={str(n):len(nets) for n,nets in owners.items()}),indent=2)+'\n')
for p in (sp,ep,budgetp,oldp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,step=3,connections=516,complete_original_physical_fraction_capacity_parent_pass=True,model_budget_failures=0,wire=wire,old_paths_equal=retained,selected_origins=dict(origins),native_verified=False,scope='Complete third-step online-produced candidate under supplied target-derived model budgets, no target path candidates. No native packed-pin/FULL/STA, independent timing target, previous-step continuous state, wire nonregression or end-to-end gain claim.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
