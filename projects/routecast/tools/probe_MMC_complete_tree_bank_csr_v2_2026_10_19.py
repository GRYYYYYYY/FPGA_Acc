"""Preselected five-NET integration bank: one deterministic tree per support."""
import json,pathlib,hashlib,time
from array import array
from MMC_zero_node_RC_shared_CSR_v1 import load
from shortest_NET_tree_csr_certified_v2 import prepare_csr
from shortest_NET_tree_ensemble_v1 import materialize
from coupled_NET_tree_candidates_csr_v2 import CSRIndex,tree_candidate,select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 O.mkdir(exist_ok=False);D=R/'experiments/mmc_conflict_node_detour_v1_2026-10-19';G=R/'experiments/mmc_conflict_group_remaining_detours_v1_2026-10-19';A=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';proofs=[D/'independent_verification_v1.json',G/'independent_verification_v1.json',R/'experiments/coupled_NET_tree_candidates_csr_core_v2_2026-10-19/verification.json'];bindings={str(p):sha(p) for p in proofs+[graph,pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_csr_v2.py',R/'tools/coupled_NET_tree_candidates_v1.py',R/'tools/shortest_NET_tree_ensemble_v1.py',R/'tools/shortest_NET_tree_csr_certified_v2.py']}
 for proof in proofs:
  for p,h in json.loads(proof.read_text())['bindings'].items():assert sha(pathlib.Path(p))==h
 write(O/'protocol.json',dict(bindings=bindings,NETs=[1395,1400,1404,1754,2925],policy='Exactly one tree per original/blocked shortest support; select lexicographically first physical parent for every support node. Fixed five known-development NETs. No native labels or candidate count tuning.',budget='Per-sink original minimum floor and node646275-deleted minimum upper bound; diagnostic allowance only, not admitted routing policy.',scope='Isolated five-NET finite bank with zero external occupancy. Any feasible choice is not a full MMC route.'))
 offsets,dest,cost,caps,kinds,graphseconds=load(graph);start=time.monotonic();index=CSRIndex(offsets,dest,cost,caps,kinds);indexseconds=time.monotonic()-start;cert=json.loads((A/'results.json').read_text())['cases'][0]['certificate'];old={a['net_id']:a for a in cert['owners']};banks={};rows=[]
 for net in [1395,1400,1404,1754,2925]:
  root=D if net in old else G;floors={int(s):lab[0] for s,lab in json.loads((root/f'net_{net}_original_sink_labels.json').read_text()).items()};budgets={int(s):lab[0] for s,lab in json.loads((root/f'net_{net}_blocked_sink_labels.json').read_text()).items()};banks[net]=[]
  for mode in ['original','blocked']:
   if net in old:
    a=old[net]
    if mode=='original':p=dict(source=a['source'],sinks=a['sinks'],choices={int(v):tuple(map(tuple,ps)) for v,ps in a['support_choices'].items()},distance={int(v):tuple(d) for v,d in a['support_distance'].items()})
    else:
     local=array('I',caps);local[646275]=0;p=prepare_csr(offsets,dest,cost,local,kinds,a['source'],a['sinks'])
     for key in ['potential_cost','potential_hops']:assert p[key].tobytes()==(D/f'net_{net}_blocked_{key}.bin').read_bytes()
   else:
    raw=json.loads((G/f'net_{net}_{mode}_support.json').read_text());p=dict(source=raw['source'],sinks=raw['sinks'],choices={int(v):tuple(map(tuple,ps)) for v,ps in raw['choices'].items()},distance={int(v):tuple(d) for v,d in raw['distance'].items()})
   start=time.monotonic();tree=materialize(p,{v:min(ps) for v,ps in p['choices'].items()});candidate=tree_candidate(index,p['source'],tree['paths'],floors,budgets)
   assert candidate['nodes']==tree['nodes'] and candidate['edge_ids']==tree['edge_ids']
   if mode=='blocked':assert 646275 not in candidate['nodes']
   banks[net].append(candidate);out=dict(net_id=net,mode=mode,source=p['source'],paths=tree['paths'],sink_floors=floors,sink_budgets=budgets,sink_costs=candidate['sink_costs'],unique_nodes=sorted(candidate['nodes']),unique_edges=sorted(candidate['edge_ids']),excess=candidate['excess']);write(O/f'net_{net}_{mode}.json',out);rows.append(dict(net_id=net,mode=mode,sinks=len(floors),unique_nodes=len(candidate['nodes']),excess=candidate['excess'],materialize_and_admit_seconds=time.monotonic()-start));print(rows[-1],flush=True)
 result=select(banks,index.capacities,max_states=100000);write(O/'results.json',dict(status='TEN_COMPLETE_REAL_NET_TREES_CSR_ADMITTED',graph_load_seconds=graphseconds,index_build_seconds=indexseconds,rows=rows,isolated_five_NET_selection=result,independent_XML_audit_pending=True));print(result,flush=True)
if __name__=='__main__':main()
