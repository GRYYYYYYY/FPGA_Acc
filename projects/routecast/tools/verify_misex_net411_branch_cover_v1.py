"""Conflict split cover and exact ordinary leaf certificates, fixed-kept scope only."""
import sys,json
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_window_witness_guided_joint_v20_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());minimum=R/'experiments/misex_net411_failure_minima_v1_2026-10-07';mp=minimum/'receipt.json';vp=minimum/'verification.json';m=json.loads(mp.read_text());v=json.loads(vp.read_text());assert v['rows_verified']==len(m['rows']) and v['ordinary_feasible_failures']==0;bindings={**v['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(mp):sha(mp),str(vp):sha(vp)};assert all(sha(k)==h for k,h in bindings.items());_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');event=json.loads((out/'event.json').read_text());slots={e:s for s,e in enumerate(f['edge_ids'])};leafs=defaultdict(list)
for row in m['rows']:leafs[row['branch_file']].append(row)
def own(records):
 owners=defaultdict(set)
 for rec in records:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
 return owners
rows=[]
for attempt in r['attempts']:
 if attempt['status']!='SEARCH_EXHAUSTED':rows.append(dict(index=attempt['index'],covered=False,reason='Bounded search retained unexplored branches.'));continue
 release=set(attempt['release']);kept=[rec for rec in event['before_records'] if rec['net_id'] not in release];fixed=own(kept);groups=release|{q['net_id'] for q in event['selection']['queries']};branches={frozenset(tuple(x) for x in b['constraints']):b for b in attempt['branches']};assert len(branches)==len(attempt['branches']) and frozenset() in branches;reachable=set();todo=[frozenset()];splits=leaves=0
 while todo:
  constraints=todo.pop()
  if constraints in reachable:continue
  reachable.add(constraints);b=branches[constraints];directory=out/f"attempt{attempt['index']}_branch{b['index']}";bp=directory/'branch.json';assert sha(bp)==r['files'][str(bp)];bindings[str(bp)]=sha(bp);assert json.loads(bp.read_text())['branch']==b
  if b['status']=='LOW_LEVEL_FAILED':
   proofs=leafs[str(bp)];assert proofs and all(not x['ordinary_budget_feasible'] for x in proofs);leaves+=1;continue
  assert b['status']=='SPLIT';node=b['conflict_node'];participants=[]
  for net in sorted(groups):
   file=directory/f'net{net}.json';assert sha(file)==r['files'][str(file)];bindings[str(file)]=sha(file);state=json.loads(file.read_text());assert state['failure'] is None
   if node in own(state['records']).get(net,set()):participants.append(net)
  fixed_other={net for net,ns in fixed.items() if net not in participants and node in ns};assert len(fixed_other)+len(participants)>f['capacities'][node];assert participants
  for net in participants:
   child=constraints|{(net,node)};assert child!=constraints and child in branches;todo.append(child)
  splits+=1
 assert reachable==set(branches);rows.append(dict(index=attempt['index'],covered=True,splits=splits,certified_failure_leaves=leaves,scope='No ordinary scalar-RC budget-feasible joint paths under this exact kept state and release. This excludes tree solutions in the same surrogate, not other releases, budgets or native routing.'));print('COVER',attempt['index'],splits,leaves,flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'branch_cover_verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Conditional split cover with independently certified ordinary leaf minima; XML branch-state audit remains a separate required evidence item.'),indent=2)+'\n')
