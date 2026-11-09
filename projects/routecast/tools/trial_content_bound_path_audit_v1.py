"""Real chain cached validation versus uncached full rebuild and stale-input rejection."""
import json,time,copy
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from content_bound_path_audit_v1 import PathAudit
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'content_bound_path_audit_v1_2026-10-09';D.mkdir(exist_ok=False)
g=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/rr_graph.xml';audit=PathAudit(g,sha(g));inv=audit.inventory;bindings=closure([Path(__file__)]);bindings[str(g)]=sha(g)
rows=[]
for step,prefix in enumerate(('fresh_history_workflow_v1','history_step2_v1','history_step3_v1'),1):
 sp=E/f'{prefix}_stage_2_2026-10-09/result.json';qp=E/f'{prefix}_stage_6_2026-10-09/verification.json';authority=json.loads(qp.read_text());assert all(sha(p)==h for p,h in authority['bindings'].items())
 ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json'
 paths={int(cid):p for cid,p in json.loads(sp.read_text())['paths'].items()};q={x['connection_id']:x for x in json.loads(ep.read_text())['connections']};budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())}
 before=(audit.hits,audit.misses);tick=time.perf_counter();actual=audit.validate(paths,q,budgets);seconds=time.perf_counter()-tick
 # Uncached independent traversal of every original arc and delay.
 owners=defaultdict(set);parents=defaultdict(set)
 for cid,path in paths.items():
  query=q[cid];assert path[0]==[query['source'],None] and path[-1][0]==query['sink']
  assert len({n for n,s in path})==len(path)
  r,c=inv.classes[inv.node_classes[path[0][0]]];delay=r*c/2
  for n,s in path:owners[n].add(query['net_id'])
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1
   r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td;parents[query['net_id'],v].add((u,s))
  assert delay<=budgets[cid]
 assert all(len(ns)<=int(inv.physical.nodes[n][1]) for n,ns in owners.items()) and all(len(ps)==1 for ps in parents.values())
 assert actual==dict(connections=516,unique_net_node_uses=sum(map(len,owners.values())))
 rows.append(dict(step=step,hits=audit.hits-before[0],misses=audit.misses-before[1],validation_seconds=seconds))
 for p in (sp,qp,ep,bp):bindings[str(p)]=sha(p)
rejections=[]
def reject(label,fn):
 try:fn()
 except (AssertionError,ValueError,KeyError):rejections.append(label)
 else:raise AssertionError('Invalid input accepted: '+label)
cid=next(iter(paths));bad=copy.deepcopy(q);bad[cid]['sink']=-1
reject('changed_endpoint',lambda:audit.validate(paths,bad,budgets))
badbudget=dict(budgets);badbudget[cid]=F(-1)
reject('tightened_budget_cached_path',lambda:audit.validate(paths,q,badbudget))
badpath=copy.deepcopy(paths);badpath[cid].append(badpath[cid][0])
reject('repeated_node_path',lambda:audit.validate(badpath,q,budgets))
badpath=copy.deepcopy(paths);badpath[cid][1][1]=999999
reject('changed_switch',lambda:audit.validate(badpath,q,budgets))
single=paths[cid];capacity_queries={i:dict(source=single[0][0],sink=single[-1][0],net_id=i) for i in (0,1)}
assert any(int(inv.physical.nodes[n][1])==1 for n,s in single)
reject('global_capacity_despite_cached_paths',lambda:audit.validate({0:single,1:single},capacity_queries,{0:F(1),1:F(1)}))
prior_digest=audit.digest;audit.digest='0'*64
reject('graph_digest_changed',lambda:audit.validate(paths,q,budgets));audit.digest=prior_digest
before=audit.misses;audit.validate(paths,q,budgets);assert audit.misses==before
assert all(sha(p)==h for p,h in bindings.items())
report=dict(bindings=bindings,rows=rows,rejections=rejections,certificate_count=len(audit.certificates),scope='Real three-step accepted path validation matches uncached original-inventory full rebuild; immutable graph-bound physical/delay cache only. Endpoints/budgets/NET capacity/parent rechecked every call, no native/STA cache or whole workflow speedup claim.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='bindings'},flush=True)
