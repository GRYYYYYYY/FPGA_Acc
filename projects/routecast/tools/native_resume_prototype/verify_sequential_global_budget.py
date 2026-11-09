"""Independent physical-path replacement and endpoint replay of native diagnostic."""
import json,sys,re
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from nonzero_rc_endpoint_context import load_endpoints
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_resume_sequential_global_budget_2026-10-07';b=R/'experiments/native_resume_sequential_adder_step3_workflow_2026-10-07';d=R/'experiments/native_resume_sequential_adder_conditional_2026-10-07'
r=json.loads((o/'receipt.json').read_text());p=json.loads((o/'protocol.json').read_text());assert r['protocol_sha256']==sha(o/'protocol.json');assert all(sha(f)==h for f,h in {**r['files'],**p['inputs'],**p['sources']}.items())
ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());_,_,nodes,f,rc,qs=load_endpoints(ep);arc={eid:(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1]) for eid in [f['edge_ids'][s]]}
norm=lambda path:{n:Counter(ps) for n,ps in physical_paths(path).items() if ps};old=norm(b/'exchange_canonical/design.route');new=norm(o/'canonical/design.route');assert old.keys()==new.keys()
condition=json.loads((d/'receipt.json').read_text());selected=set(r['selected_nets']);assert selected
for name in new:
 if name not in selected:assert new[name]==old[name]
for row in condition['rows']:
 if row['net'] not in selected:continue
 predicted=[]
 for x in row['records']:
  q=x['query'];path=[(q['source'],None)];u=q['source']
  for eid in x['physical_edge_ids']:
   previous,v,sw=arc[eid];assert previous==u;path.append((v,sw));u=v
  assert u==q['sink'];predicted.append(tuple(path))
 assert Counter(predicted)==new[row['net']]
assert new==norm(o/'native/design.route')
expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in qs);actual=Counter((n,path[0][0],path[-1][0]) for n,paths in new.items() for path,count in paths.items() for _ in range(count));assert expected==actual
union={n:{u for path in paths for u,_ in path} for n,paths in new.items()};occ=Counter(u for us in union.values() for u in us);assert all(v<=f['capacities'][u] for u,v in occ.items())
for logname in ('native/native.log','canonical/reload.log'):
 text=(o/logname).read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text
 assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==r['cpd_ns'];assert int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1])==r['wirelength']
assert r['wirelength']<=r['budget'] and r['canonical']['fixups']==r['canonical']['mismatches']==0
result=dict(receipt_sha256=sha(o/'receipt.json'),verifier_sha256=sha(Path(__file__)),selected_nets=sorted(selected),unchanged_unselected_nets=len(new)-len(selected),verified_endpoints=len(qs),zero_capacity_overflow=True,exact_conditioned_paths_native_preserved=True,native_cpd_ns=r['cpd_ns'],native_wirelength=r['wirelength'],scope='Independent physical endpoint, full path and ownership replay; native FULL/STA evidence. Not an independent native timing engine or complete pipeline cost experiment.')
(o/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
