"""Post-terminal full-cohort independent topology and net-union audit.

Run only after the authoritative exec handle returns exit zero. Does not launch
or recover the predictor. The handle status is external evidence, not receipt
existence or a caller-provided status inferred from files.
"""
import json,collections
from pathlib import Path
from prepared_csr import read,sha,U64
out=Path('experiments/clma_cpp_predecessor_full_2026-10-04')
csr=Path('experiments/clma_prepared_csr_2026-10-04/csr')
reference=Path('experiments/clma_full_goal_astar_2026-10-04/prediction.json')
protocol=json.loads((out/'protocol.json').read_text());receipt=json.loads((out/'receipt.json').read_text());inputs=protocol['inputs']
assert sha(out/'protocol.json')==receipt['protocol_sha256']
assert sha(out/'results.json')==receipt['results_sha256']
assert sha(out/'main.cpp')==receipt['source_sha256']==inputs['source']
assert sha(out/'driver.py')==receipt['driver_sha256']==inputs['driver']
assert sha('build/routecast_csr_predecessor')==inputs['binary']
assert sha(reference)==inputs['reference']=='e162fd20f6cd70bb2b713c57d5b607569c3d7889b596012aafa355c8958de68a'
assert sha(csr/'manifest.json')==inputs['manifest']
ref=json.loads(reference.read_text());manifest,fields=read(csr,ref['physical_graph_sha256'],'6b51650f3ac0ba59b39ee3b556cfa201c336691a0a88721ac21437ea0ecd36f6')
groups={}
for c in ref['connections']:groups.setdefault(c['net_id'],[]).append(c)
results=json.loads((out/'results.json').read_text())
assert [r['net_id'] for r in results]==sorted(groups)
assert len(groups)==receipt['nets']==4809
# Invert CSR slots to raw-edge endpoints, preserving physical node IDs.
sources=[None]*manifest['edges'];destinations=[None]*manifest['edges'];costs=[None]*manifest['edges']
for rank,source in enumerate(fields['node_ids']):
 for slot in range(fields['row_offsets'][rank],fields['row_offsets'][rank+1]):
  eid=fields['edge_ids'][slot];sources[eid]=source;destinations[eid]=fields['node_ids'][fields['dest_ranks'][slot]];costs[eid]=fields['costs'][slot]
capacity=dict(zip(fields['node_ids'],fields['capacities']));occupancy=collections.Counter();connections=0;edge_visits=0;settled=0
for record in results:
 cs=groups[record['net_id']];result=record['result'];assert not result['budget_exhausted']
 assert set(result['paths'])=={str(c['sink']) for c in cs}
 touched=set()
 for c in cs:
  path=result['paths'][str(c['sink'])];assert path==c['physical_edge_ids']
  node=c['source'];visited={node};touched.add(node)
  for eid in path:
   assert type(eid) is int and 0<=eid<manifest['edges']
   assert sources[eid]==node and costs[eid]!=U64
   node=destinations[eid];assert capacity[node]>0 and node not in visited
   visited.add(node);touched.add(node)
  assert node==c['sink'];connections+=1
 occupancy.update(touched);edge_visits+=result['edge_visits'];settled+=result['settled_nodes']
assert connections==receipt['connections']==13458
assert dict(occupancy)=={int(k):v for k,v in ref['node_occupancy'].items()}
audit={'receipt_sha256':sha(out/'receipt.json'),'all_input_source_binary_result_hashes_verified':True,'nets':len(groups),'connections':connections,'canonical_paths_exact':True,'every_raw_arc_enabled_contiguous_simple_and_positive_destination_capacity':True,'unique_net_node_occupancy_exact':True,'occupied_nodes':len(occupancy),'edge_visits':edge_visits,'settled_nodes':settled,'audit_source_sha256':sha(__file__),'scope':'full clma host additive consumer only; requires separately observed terminal exit0, not HLS/quality/acceleration evidence'}
(out/'completion_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps(audit),flush=True)
