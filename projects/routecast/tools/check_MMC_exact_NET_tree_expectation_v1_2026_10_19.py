"""Exact real-pilot expectation plus independently enumerated parent chains."""
import pathlib,json,hashlib,itertools
from fractions import Fraction
from collections import Counter
from exact_NET_tree_expectation_v1 import expectation
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 parent=R/'experiments/mmc_shortest_NET_tree_ensemble_pilot_v1_2026-10-19';support=parent/'predecessor_support.json';proof=R/'experiments/mmc_shortest_NET_tree_ensemble_pilot_v2_2026-10-19/verification.json';v=json.loads(proof.read_text());assert v['status']=='REAL_NET_16_TREE_SAMPLES_INDEPENDENT_XML_PATH_BUDGET_PARENT_AND_NET_OCCUPANCY_PASS';assert v['bindings'][str(support)]==sha(support)
 j=json.loads(support.read_text());prepared=dict(source=j['source'],sinks=j['sinks'],choices={int(k):tuple(map(tuple,row)) for k,row in j['choices'].items()},distance={int(k):tuple(value) for k,value in j['distance'].items()});result=expectation(prepared,assignment_limit=100000);assert result['parent_assignments']==24
 samplesfile=proof.parent/'samples.json';samples=json.loads(samplesfile.read_text());assert v['bindings'][str(samplesfile)]==sha(samplesfile);support_edges={e for row in prepared['choices'].values() for _,e in row};audited_edges={e for tree in samples for path in tree['paths'].values() for e in path};assert support_edges<=audited_edges
 # Separate implementation: walk each sink's parents, union the visited nodes,
 # without calling the production tree materializer or expectation routines.
 keys=sorted(prepared['choices']);counts=Counter();assignments=0
 for values in itertools.product(*(prepared['choices'][key] for key in keys)):
  parents=dict(zip(keys,values));nodes={prepared['source']};assignments+=1
  for sink in prepared['sinks']:
   cursor=sink;seen=set()
   while cursor!=prepared['source']:
    assert cursor not in seen;seen.add(cursor);nodes.add(cursor);u,eid=parents[cursor];assert eid in audited_edges;assert prepared['distance'][u][1]+1==prepared['distance'][cursor][1];cursor=u
  counts.update(nodes)
 assert assignments==result['parent_assignments'] and all(result['node_probabilities'][n]==Fraction(counts[n],assignments) for n in prepared['distance'])
 try:expectation(prepared,assignment_limit=23)
 except ValueError:pass
 else:raise AssertionError('partial enumeration accepted')
 empirical=Counter(n for tree in samples for n in tree['nodes']);errors={n:Fraction(empirical[n],16)-p for n,p in result['node_probabilities'].items()};bias={n:result['independent_sink_union'][n]-p for n,p in result['node_probabilities'].items()}
 O=R/'experiments/mmc_exact_NET_tree_expectation_v1_2026-10-19';O.mkdir();files=[support,proof,samplesfile,pathlib.Path(__file__).resolve(),R/'tools/exact_NET_tree_expectation_v1.py',R/'tools/shortest_NET_tree_ensemble_v1.py'];output=dict(status='REAL_PILOT_ALL24_PARENT_ASSIGNMENTS_EXACT_EXPECTATION_INDEPENDENTLY_VERIFIED',bindings={str(p):sha(p) for p in files},parent_assignments=assignments,support_edges_covered_by_prior_XML_audit=len(support_edges),node_probabilities={str(n):str(p) for n,p in result['node_probabilities'].items()},independent_sink_union_bias={str(n):str(x) for n,x in bias.items() if x},sample16_errors={str(n):str(x) for n,x in errors.items() if x},sample16_max_absolute_error=str(max(map(abs,errors.values()))),distinct_node_unions=len(result['node_union_counts']),assignment_limit_rejection_verified=True,scope='Exact expectation under uniform independent local parent choices, not uniformly weighted distinct trees. Single NET only; no congestion labels used, no quality or full-design scalability claim. Min-hop restriction and old global-minimum-dual limitations unchanged.')
 with (O/'verification.json').open('x') as f:json.dump(output,f,indent=2);f.write('\n')
 print('EXACT24 PASS max_sampling_error',output['sample16_max_absolute_error'],'independent_union_bias_nodes',len(output['independent_sink_union_bias']),flush=True)
if __name__=='__main__':main()
