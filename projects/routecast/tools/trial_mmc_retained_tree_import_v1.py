"""All real clean threshold branches imported and independently compared."""
import json,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from criticality_shared_tree_sparse_reference_v3 import Graph
from retained_criticality_tree_seed_v1 import seed
O=R/'experiments/mmc_selective_tree_preflight_v1_2026-10-13';proof=O/'estimator_round0_eligibility_v1.json';v=json.loads(proof.read_text());bindings={**v['bindings'],**closure([Path(__file__)]),str(proof):sha(proof)};assert all(sha(k)==h for k,h in bindings.items())
ep=next(Path(k) for k in bindings if k.endswith('/endpoints.json'));graph,digest,nodes,f,rc,qs=load_endpoints(ep);g=Graph(f,rc.increments,[rc.initial(u) for u in range(len(f['capacities']))]);slots={eid:i for i,eid in enumerate(f['edge_ids'])}
p=R/'experiments/mmc_delayed_history_ablation_v1_2026-10-13/model/round0.json';state=json.loads(p.read_text());ledger={int(k):v for k,v in state['ledger'].items()};groups=defaultdict(list)
for r in state['records']:groups[r['net_id']].append(r)
rows={r['net']:r for r in v['pernet']};tested=kept=0
for net,rs in sorted(groups.items()):
 if len(rs)<16:continue
 selected=[];expected_parent={};expected_arrival={};expected_nodes=set()
 for r in rs:
  u=r['source'];path=[u];delay=rc.initial(u);parents={};arrivals={u:delay};pathslots=[]
  for eid in r['answer']['physical_edge_ids']:
   i=slots[eid];assert f['row_offsets'][u]<=i<f['row_offsets'][u+1];dest=f['dest_ranks'][i];parents[dest]=(u,i);delay+=rc.increments[i];arrivals[dest]=delay;path.append(dest);pathslots.append(i);u=dest
  assert u==r['sink'] and delay==r['answer']['delay'] and delay<=r['budget_integer']
  if any(ledger.get(n,0)>f['capacities'][n] for n in path):continue
  selected.append((r['sink'],pathslots,r['budget_integer']));expected_nodes.update(path)
  for n,parent in parents.items():assert n not in expected_parent or expected_parent[n]==parent;expected_parent[n]=parent
  for n,d in arrivals.items():assert n not in expected_arrival or expected_arrival[n]==d;expected_arrival[n]=d
 assert len(selected)==rows[net]['clean_connections'] and len(expected_nodes)==rows[net]['clean_union_nodes']
 tree=g.tree(rs[0]['source']);actual=seed(tree,selected)
 if not selected:expected_nodes={tree.source};expected_arrival={tree.source:rc.initial(tree.source)}
 assert actual==frozenset(expected_nodes) and tree.parents==expected_parent and tree.arrival==expected_arrival;tested+=1;kept+=len(selected)
assert tested==612 and kept==5167 and all(sha(k)==h for k,h in bindings.items());(O/'retained_tree_import_trial_v1.json').write_text(json.dumps(dict(bindings=bindings,all_real_threshold_clean_paths_imported_with_exact_parents_arrivals_and_union_pass=True,nets=tested,retained_connections=kept,scope='Authenticated real import contract only, no rerouting speed or prediction/native QoR proof.'),indent=2)+'\n');print('PASS real imports',tested,kept,flush=True)
