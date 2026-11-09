"""Budget-preserving searches avoiding certified local-capacity core nodes."""
import json,time
from pathlib import Path
from collections import Counter
from fractions import Fraction as F
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from native_bounded_wire_search_v1 import NativeBoundedSearch
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_local_capacity_detours_v4_2026-10-09';D.mkdir(exist_ok=False);vp=E/'adder_full871_local_capacity_v1_2026-10-09/verification.json';v=json.loads(vp.read_text());bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};_,_,nodes,f,rc,_=load_endpoints(ep);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);bankp=E/'adder_local_capacity_detours_v3_2026-10-09/step_3.json';bank={int(c):o for c,o in json.loads(bankp.read_text())['bank'].items()};events=[];added=0;start=time.perf_counter()
for cid in v['connection_ids']:
 for blocked in [[n] for n in v['node_ids']]+[v['node_ids']]:
  query=q[cid]
  if query['source'] in blocked or query['sink'] in blocked:continue
  scaled=budgets[cid]*rc.scale;limit=scaled.numerator//scaled.denominator;answer=search.query(query['source'],query['sink'],limit,{n:f['capacities'][n] for n in blocked},set(),{},1000000,sum(length.values())+1);event=dict(connection_id=cid,blocked_nodes=blocked,integer_budget=limit,**answer);events.append(event)
  if answer['status']!='FOUND':continue
  path=[[query['source'],None]];u=query['source']
  for eid in answer['physical_edge_ids']:
   source,n,sw=edge[eid];assert source==u;path.append([n,sw]);u=n
  assert not set(blocked)&{n for n,s in path};event['path']=path
  if not any(o['path']==path for o in bank[cid]):
   delay=F(answer['delay'],rc.scale);bank[cid].append(dict(path=path,origin='LOCAL_CAPACITY_NODE_AVOIDANCE',exact_delay_s=[delay.numerator,delay.denominator]));added+=1
p=D/'step_3.json';p.write_text(json.dumps(dict(bank={str(c):o for c,o in bank.items()},events=events),indent=2)+'\n');search.close()
for p in (p,ep,bp,bankp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,new_candidates=added,candidates=sum(map(len,bank.values())),queries=len(events),status_counts=dict(Counter(e['status'] for e in events)),search_seconds=time.perf_counter()-start,scope='Node-avoidance candidate search only; no complete choice or full graph infeasibility claim. NO_STRICT_IMPROVEMENT is scoped to exact bounded query.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
