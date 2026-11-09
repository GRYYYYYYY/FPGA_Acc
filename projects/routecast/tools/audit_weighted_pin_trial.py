"""Independent physical witness/cost/cohort audit; does not rerun predictor."""
import argparse,json
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from net_pressure_sketch import net_union
p=argparse.ArgumentParser();p.add_argument('experiment',type=Path);p.add_argument('--inventory',type=Path);a=p.parse_args();root=a.experiment
receipt=json.loads((root/'receipt.json').read_text())
for file,digest in receipt['input_sha256'].items():assert sha(file)==digest
for file,digest in receipt['artifact_sha256'].items():assert sha(root/file)==digest
for file,digest in receipt['source_sha256'].items():assert sha(root/'source'/file)==digest
inputs=receipt['input_sha256'];find=lambda suffix:next(file for file in inputs if file.endswith(suffix))
g=read_rr_graph(find('rr_graph.xml'));catalog=PinChoiceCatalog(g);bg=json.loads(Path(find('baseline_prediction.json')).read_text());users,demand=net_union(g,bg);rows={str(r['connection_id']):r for r in json.loads(Path(find('rows.json')).read_text())};paths=json.loads((root/'paths.json').read_text());assignment=json.loads((root/'assignment.json').read_text());chosen=assignment['assignment']
assert set(paths)==set(chosen) and len(paths)==receipt['requests']
if a.inventory:
 assert str(a.inventory) in inputs
 inventory=json.loads(a.inventory.read_text());expected={str(cid) for c in inventory['classes'] for cid in c['request_ids']};assert set(paths)==expected
base={};full={};reduced={};alpha=receipt['alpha']
for n,node in g.nodes.items():
 if node.type in {'CHANX','CHANY'} and node.capacity>0:
  loc=dict(node.location);base[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1;c=node.capacity;d=demand.get(n,0)
  full[n]=(alpha*max(0,d-c+1)+c-1)//c;reduced[n]=(alpha*max(0,max(0,d-1)-c+1)+c-1)//c
 else:base[n]=full[n]=reduced[n]=0
count=0;total=0
for cid,result in paths.items():
 row=rows[cid];w=row['path_pin_witness'];net=row['net_id'];own=users[net]
 assert set(result['paths'])==set(result['costs'])
 assert set(map(int,result['paths']))==set(catalog.sinks[w['sink_class']].physical_pins)
 for ptc,path in result['paths'].items():
  witness=catalog.witness(w['source_class'],w['sink_class'],path)
  assert witness['selected_opin_ptc']==row['packed_source']['physical_pin_ptc'] and witness['selected_ipin_ptc']==int(ptc)
  value=sum(base[g.edges[e].sink]+(reduced[g.edges[e].sink] if g.edges[e].sink in own else full[g.edges[e].sink]) for e in path)
  assert value==result['costs'][ptc];count+=1
 sink,ptc=chosen[cid];assert sink==w['sink_class'];total+=result['costs'][str(ptc)]
assert len({tuple(v) for v in chosen.values()})==len(chosen)
assert total==assignment['total_cost']==receipt['optimal_supplied_cost'] and count==receipt['candidates']
from collections import defaultdict
from pin_assignment_optimality import verify
class_costs=defaultdict(dict);class_assignments=defaultdict(dict)
for cid,result in paths.items():
 sink=chosen[cid][0];class_costs[sink][int(cid)]={(sink,int(ptc)):value for ptc,value in result['costs'].items()};class_assignments[sink][int(cid)]=chosen[cid]
optimality={str(sink):verify(costs,class_assignments[sink]) for sink,costs in class_costs.items()}
assert all(r['optimal'] for r in optimality.values())
report={'matching_optimality':optimality,'optimality_verifier_sha256':sha('tools/pin_assignment_optimality.py'),'requests_verified':len(paths),'candidate_paths_and_costs_verified':count,'assigned_cost_verified':total,'full_inventory_verified':bool(a.inventory),'auditor_sha256':sha(__file__),'receipt_sha256':sha(root/'receipt.json'),'scope':'physical paths, fixed source pin, exact frozen costs, complete requested cohort and injectivity; independent residual matching optimality verified; not independent shortest-path or native legality proof'}
(root/'independent_candidate_optimality_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
