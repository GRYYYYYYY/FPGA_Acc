"""Independent live-search physical endpoint/edge/owner/budget and input closure."""
import sys,json
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from nonzero_rc_endpoint_context import load_endpoints
import os
out=R/('experiments/native_live_search_reuse_v3_2026-10-07/step_'+os.environ['ROUTECAST_REUSE_STEP']);r=json.loads((out/'receipt.json').read_text())
for key in ('inputs','sources','files'):assert all(sha(p)==h for p,h in r[key].items())
ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());_,_,nodes,f,rc,qs=load_endpoints(ep);arcs={(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in qs)
rows=[];norm=lambda paths:{n:Counter(ps) for n,ps in paths.items() if ps}
for path in (out/'native/live.route',out/'native/candidate.route',out/'native/tx.attempt0.after.route',out/'canonical/design.route'):
 paths=physical_paths(path);assert Counter((n,p[0][0],p[-1][0]) for n,seq in paths.items() for p in seq)==expected;occ=Counter()
 for name,seq in paths.items():
  union=set()
  for p in seq:
   assert all((u,v,sw) in arcs for (u,_),(v,sw) in zip(p,p[1:]));union.update(u for u,_ in p)
  occ.update(union)
 assert all(v<=f['capacities'][n] for n,v in occ.items());rows.append(dict(path=str(path),endpoints=len(qs),all_arcs_valid=True,zero_capacity_overflow=True))
 if path.name=='candidate.route':candidate=norm(paths)
 if path.name=='design.route' or path.name=='tx.attempt0.after.route':assert norm(paths)==candidate
assert r['canonical']['mismatches']==r['canonical']['fixups']==0 and r['canonical']['cpd_ns']==r['cpd_ns']==4.87739
assert r['producer']['final_wire']<=r['producer']['initial_wire_budget']
assert norm(physical_paths(out/'native/live.route'))!=candidate
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(__file__),rows=rows,live_search_changes_physical_paths=True,canonical_paths_equal_candidate=True,scope='Known single development fixture; all four routes independently checked, original canonical FULL/STA zero fixups/mismatches. Timing performance/generalization not inferred.'),indent=2)+'\n');print('PASS',len(qs),'x',len(rows))
