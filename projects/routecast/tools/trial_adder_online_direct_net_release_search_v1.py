"""Conflict-proof guided new paths and finite bank joint selection, no target paths."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from finite_route_bank_solver_v1 import solve
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_online_direct_leaf_owner_expand_v1_2026-10-09';D=E/'adder_online_direct_net_release_search_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();vp=E/'adder_online_direct_leaf_owner_component_verification_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);cap=f['capacities'];rows=[]
step=3;ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};bank={int(c):p for c,p in json.loads((B/'step_3.json').read_text())['bank'].items()};T=E/'adder_online_direct_leaf_owner_components_v1_2026-10-09';decomp=json.loads((T/'decomposition.json').read_text());domains={int(c):p for c,p in decomp['domains'].items()};baseline={};leaves=[];attempts=[];added=0
for index in range(len(decomp['components'])):
 component=json.loads((T/f'component_{index}.json').read_text())
 if component['result']['status']=='FOUND':baseline.update({int(c):domains[int(c)][i] for c,i in component['result']['selection'].items()})
 elif component['result']['status']=='FINITE_BANK_EXHAUSTED':
  def walk(proof,selection):
   selection={**selection,**{cid:domains[cid][i] for cid,i in proof['forced']}}
   if proof['kind']=='DEAD':leaves.append((proof['empty_connection'],selection));return
   for child in proof['children']:walk(child['proof'],{**selection,proof['connection']:domains[proof['connection']][child['index']]})
  walk(component['result']['proof'],{})
original={c:list(options) for c,options in bank.items()}
for index,(cid,selection) in enumerate(leaves):
 selection={**baseline,**selection};net=q[cid]['net_id'];owners=defaultdict(set);parents={};kept=set()
 for c,i in selection.items():
  path=original[c][i]['path'];nnet=q[c]['net_id']
  if nnet==net:continue
  for n,sw in path:owners[n].add(nnet)
  if nnet==net:
   kept.update(n for n,sw in path)
   for (u,_),(n,sw) in zip(path,path[1:]):assert n not in parents or parents[n]==(u,sw);parents[n]=(u,sw)
 outside=Counter({n:len(nets-{net}) for n,nets in owners.items()});query=q[cid];value=budgets[cid]*rc.scale;answer=search.query(query['source'],query['sink'],value.numerator//value.denominator,outside,kept,parents,1000000,sum(length.values())+1);event=dict(leaf=index,connection_id=cid,selection=selection,**answer);attempts.append(event)
 if answer['status']!='FOUND':continue
 path=[[query['source'],None]];u=query['source']
 for eid in answer['physical_edge_ids']:source,n,sw=edge[eid];assert source==u;path.append([n,sw]);u=n
 event['path']=path
 if not any(c['path']==path for c in bank[cid]):
  delay=F(answer['delay'],rc.scale);bank[cid].append(dict(path=path,origin='DIRECT_FULL_NET_RELEASE_SEARCH',exact_delay_s=[delay.numerator,delay.denominator]));added+=1
p=D/'step_3.json';p.write_text(json.dumps(dict(bank={str(c):p for c,p in bank.items()},attempts=attempts),indent=2)+'\n');bindings[str(p)]=sha(p);search.close();assert all(sha(p)==h for p,h in bindings.items());row=dict(step=3,leaves=len(leaves),new_candidates=added,status_counts=dict(Counter(x['status'] for x in attempts)));(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=[row],scope='Actual budget-preserving physical searches under full solved-component background and failing-branch partial selections. Candidate not complete fullroute; no target paths/native/timing/gain claim.'),indent=2)+'\n');print(row,flush=True)
