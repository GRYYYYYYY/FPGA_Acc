"""Independent full weighted witness/cost and assignment audit after completion."""
import json
from pathlib import Path
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from net_pressure_sketch import net_union
from pin_commit_validation import validate
from pin_assignment_optimality import verify
from pre_route_endpoints import sha
out=Path('experiments/alu4_full_weighted_pin_trial_2026-10-05');receipt=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());assert receipt['protocol_sha256']==sha(out/'protocol.json')
for p,h in protocol['input_sha256'].items():assert sha(p)==h
for name,h in receipt['artifact_sha256'].items():assert sha(out/name)==h
bg=json.loads(Path('experiments/alu4_transfer_2026-10-05/prediction.json').read_text());ep=json.loads(Path('experiments/alu4_validation_capture_2026-10-05/endpoints.json').read_text());eq=json.loads(Path('experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json').read_text());inventory=json.loads(Path('experiments/alu4_pin_conflict_inventory_2026-10-05/receipt.json').read_text());g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');catalog=PinChoiceCatalog(g);users,demand=net_union(g,bg);rows={r['connection_id']:r for r in bg['connections']};paths=json.loads((out/'paths.json').read_text());assignment=json.loads((out/'assignment.json').read_text());selected={cid for c in inventory['classes'] for cid in c['request_ids']};assert set(map(int,paths))==selected==set(map(int,assignment['assignment']));assert len(selected)==2331-8
checks={r['cid']:r for r in eq['checks']};span={}
for n,node in g.nodes.items():
 loc=dict(node.location);span[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
count=0;chosen_cost=0
for cid in sorted(selected):
 row=rows[cid];q=paths[str(cid)];allowed=set(checks[cid]['physical_members']);assert set(map(int,q['paths']))==allowed
 original=catalog.witness(row['source'],row['sink'],row['physical_edge_ids'])
 for ptc,path in q['paths'].items():
  w=catalog.witness(row['source'],row['sink'],path);assert w['selected_ipin_ptc']==int(ptc) and w['selected_opin_ptc']==original['selected_opin_ptc']
  total=0
  for eid in path:
   n=g.edges[eid].sink;node=g.nodes[n];outside=demand.get(n,0)-int(n in users[row['net_id']]);cap=node.capacity
   penalty=(256*max(0,outside-cap+1)+cap-1)//cap if node.type in {'CHANX','CHANY'} and cap>0 else 0
   total+=span[n]+penalty
  assert total==q['costs'][ptc];count+=1
 _,ptc=assignment['assignment'][str(cid)];chosen_cost+=q['costs'][str(ptc)]
validate(assignment['assignment'],paths,eq['checks'],ep['connections']);assert chosen_cost==assignment['total_cost']==receipt['optimal_supplied_cost'];assert count==92920
optimality=[]
for cls in inventory['classes']:
 costs={cid:{(cls['sink_class'],int(ptc)):v for ptc,v in paths[str(cid)]['costs'].items()} for cid in cls['request_ids']}
 chosen={cid:assignment['assignment'][str(cid)] for cid in cls['request_ids']}
 checked=verify(costs,chosen);assert checked['optimal']
 optimality.append({'sink_class':cls['sink_class'],**checked})
assert len(optimality)==109 and sum(x['total_cost'] for x in optimality)==chosen_cost
result={'class_optimality':optimality,'protocol_sha256':sha(out/'protocol.json'),'paths_sha256':sha(out/'paths.json'),'assignment_sha256':sha(out/'assignment.json'),'audit_source_sha256':sha(__file__),'witnesses_checked':count,'requests_checked':len(selected),'all_physical_pins_and_supplied_costs_exact':True,'assignment_valid':True,'scope':'Feasible supplied-cost assignment and candidate witnesses; Independent residual-cycle optimality on supplied additive candidates only; not joint channel/tree/native timing proof'};(out/'library_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
