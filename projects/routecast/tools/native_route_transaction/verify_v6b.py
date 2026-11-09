"""Independent live no-op export/commit endpoint and owner-capacity check."""
import sys,json
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from nonzero_rc_endpoint_context import load_endpoints
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_route_transaction_v6b_2026-10-07';receipt=json.loads((o/'receipt.json').read_text())
for row in receipt['rows']:assert all(sha(p)==h for p,h in row['files'].items())
ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());_,_,nodes,fields,rc,qs=load_endpoints(ep)
arcs={(u,fields['dest_ranks'][s],fields['switch_ids'][s]) for u in range(len(nodes)) for s in range(fields['row_offsets'][u],fields['row_offsets'][u+1])}
expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in qs)
w=o/'live_noop';paths=physical_paths(w/'tx.attempt0.after.route');assert Counter((n,p[0][0],p[-1][0]) for n,seq in paths.items() for p in seq)==expected
occ=Counter()
for n,seq in paths.items():
 union=set()
 for p in seq:
  assert all((u,v,sw) in arcs for (u,_),(v,sw) in zip(p,p[1:]));union.update(u for u,_ in p)
 occ.update(union)
assert all(v<=fields['capacities'][n] for n,v in occ.items())
(o/'verification.json').write_text(json.dumps(dict(endpoints=len(qs),zero_capacity_overflow=True,all_arcs_valid=True,receipt_sha256=sha(o/'receipt.json'),verifier_sha256=sha(__file__),scope='No-op live producer only; no incremental algorithm or speed evidence.'),indent=2)+'\n');print('PASS',len(qs))
