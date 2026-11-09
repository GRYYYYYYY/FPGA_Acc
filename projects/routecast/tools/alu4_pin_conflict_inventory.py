import json
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
rowsfile=Path('experiments/alu4_packed_pin_witness_2026-10-05/rows.json');eqfile=Path('experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json');inputs={str(p):sha(p) for p in (rowsfile,eqfile)}
rows=json.loads(rowsfile.read_text());eq=json.loads(eqfile.read_text());checks={r['cid']:r for r in eq['checks']};assert set(checks)=={r['connection_id'] for r in rows}
groups=defaultdict(list)
for r in rows:groups[r['path_pin_witness']['sink_class']].append(r)
classes=[]
for sink,requests in sorted(groups.items()):
 pins=defaultdict(list)
 for r in requests:pins[r['path_pin_witness']['selected_ipin_ptc']].append(r)
 collisions={p:users for p,users in pins.items() if len(users)>1}
 if not collisions:continue
 allowed={tuple(checks[r['connection_id']]['physical_members']) for r in requests};assert len(allowed)==1
 members=next(iter(allowed));assert len(requests)<=len(members)
 assert all(checks[r['connection_id']]['equivalent']=='full' for r in requests)
 classes.append({'sink_class':sink,'request_ids':sorted(r['connection_id'] for r in requests),'requests':len(requests),'physical_pins':len(members),'overloaded_request_pins':len(collisions),'overuse_request_units':sum(len(u)-1 for u in collisions.values()),'overloaded_unique_net_pins':sum(len({r['net_id'] for r in u})>1 for u in pins.values()),'overuse_unique_net_units':sum(max(0,len({r['net_id'] for r in u})-1) for u in pins.values())})
assert all(sha(p)==h for p,h in inputs.items());out=Path('experiments/alu4_pin_conflict_inventory_2026-10-05');out.mkdir();(out/'source.py').write_text(Path(__file__).read_text())
receipt={'all_requests':len(rows),'all_sink_classes':len(groups),'conflict_classes':len(classes),'repair_requests':sum(c['requests'] for c in classes),'weighted_candidate_upper_count':sum(c['requests']*c['physical_pins'] for c in classes),'overloaded_unique_net_pins':sum(c['overloaded_unique_net_pins'] for c in classes),'overuse_unique_net_units':sum(c['overuse_unique_net_units'] for c in classes),'all_conflict_classes_explicit_full_equivalence':True,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'classes':classes,'scope':'complete baseline selected-pin conflict inventory; class capacity is only necessary, reachable matching and joint channel feasibility unproven'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ('classes','input_sha256','source_sha256')}))
