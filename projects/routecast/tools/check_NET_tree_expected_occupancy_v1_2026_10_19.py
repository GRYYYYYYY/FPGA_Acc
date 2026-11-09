"""Exhaustive random reference for exact one-sink DP and real fixed16 policy."""
import pathlib,json,hashlib,random,math
from shortest_NET_tree_ensemble_v1 import prepare
from exact_NET_tree_expectation_v1 import expectation
from NET_tree_expected_occupancy_v1 import single_sink,predict,EXACT_ASSIGNMENT_LIMIT,SAMPLES,SEED
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 rng=random.Random(1019);checks=0;unreachable=0;large=0
 for i in range(300):
  edges=[(k,rng.randrange(7),rng.randrange(7),rng.randrange(4)) for k in range(18)]
  try:p=prepare(edges,0,[6])
  except ValueError:unreachable+=1;continue
  if math.prod(map(len,p['choices'].values()))>100000:large+=1;continue
  exact=expectation(p,assignment_limit=100000)['node_probabilities'];dp=single_sink(p);assert all(dp.get(n,0)==v for n,v in exact.items());checks+=1
 O=R/'experiments/NET_tree_expected_occupancy_core_v1_2026-10-19';O.mkdir();real=R/'experiments/mmc_NET_tree_csr_certified_batch_v2_2026-10-19';proof=real/'independent_global_dual_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='ALL16_REAL_NETS_GLOBAL_LEXICOGRAPHIC_SHORTEST_PATH_DUALS_PASS';rows=[];files=[pathlib.Path(__file__).resolve(),R/'tools/NET_tree_expected_occupancy_v1.py',R/'tools/exact_NET_tree_expectation_v1.py',R/'tools/shortest_NET_tree_ensemble_v1.py',proof]
 for row in v['rows']:
  net=row['net_id'];f=real/f'net_{net}.json';assert v['bindings'][str(f)]==sha(f);j=json.loads(f.read_text());p=dict(source=j['source'],sinks=j['sinks'],choices={int(n):tuple(map(tuple,x)) for n,x in j['choices'].items()},distance={int(n):tuple(x) for n,x in j['distance'].items()});pred=predict(p,net_id=net);assert pred['probabilities'][p['source']]==1 and all(0<x<=1 for x in pred['probabilities'].values());rows.append(dict(net_id=net,mode=pred['mode'],samples=pred['samples'],expected_tree_nodes=str(sum(pred['probabilities'].values()))));files.append(f)
 bindings={str(p):sha(p) for p in files}
 with (O/'verification.json').open('x') as f:json.dump(dict(status='single_sink_DP_matches_exhaustive_and_fixed16_hybrid_policy_exercised',bindings=bindings,random_reachable_exact_checks=checks,random_unreachable=unreachable,random_skipped_large=large,exact_assignment_limit=EXACT_ASSIGNMENT_LIMIT,samples=SAMPLES,seed=SEED,real_NETs=rows,scope='Core/input-only feasibility. Exact single-sink removes sampling noise under local-parent model, not prediction error. Multi-sink samples remain approximate; no target labels used, no full55300NET forecast or quality/time gain.'),f,indent=2);f.write('\n')
 print('PASS',checks,'exact random single-sink cases; real modes', {m:sum(x['mode']==m for x in rows) for m in {x['mode'] for x in rows}},flush=True)
if __name__=='__main__':main()
