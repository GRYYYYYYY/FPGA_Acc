"""Independent all-path/endpoints/owner-capacity and native-state pilot closure."""
import sys,json,re
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from nonzero_rc_endpoint_context import load_endpoints
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_route_transaction_v2_2026-10-07';r=json.loads((o/'receipt.json').read_text());p=json.loads((o/'protocol.json').read_text());assert r['protocol_sha256']==sha(o/'protocol.json');assert all(sha(f)==h for f,h in r['inputs'].items());b=R/'build/native_route_transaction_v2_2026-10-07';br=json.loads((b/'receipt.json').read_text());bp=json.loads((b/'protocol.json').read_text());assert br['protocol_sha256']==sha(b/'protocol.json') and br['binary_sha256']==sha(b/'routecast_transaction_vpr');assert bp['source_sha256']==sha(R/'tools/native_route_transaction/hook_v2.cpp') and all(sha(f)==h for f,h in bp['inputs_sha256'].items())
ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());_,_,nodes,fields,rc,qs=load_endpoints(ep);arcs={(u,fields['dest_ranks'][s],fields['switch_ids'][s]) for u in range(len(nodes)) for s in range(fields['row_offsets'][u],fields['row_offsets'][u+1])};expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in qs);rows=[]
for row in r['rows']:
 assert all(sha(f)==h for f,h in row['files'].items());w=o/row['case'];paths=physical_paths(w/'tx.after.route');actual=Counter((n,ps[0][0],ps[-1][0]) for n,seq in paths.items() for ps in seq);assert actual==expected;occ=Counter()
 for n,seq in paths.items():
  union=set()
  for ps in seq:
   for (u,_),(v,sw) in zip(ps,ps[1:]):assert (u,v,sw) in arcs
   union.update(u for u,_ in ps)
  occ.update(union)
 assert all(v<=fields['capacities'][n] for n,v in occ.items());log=(w/'run.log').read_text();assert 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log
 if row['case']!='commit':assert (w/'tx.before.route').read_bytes()==(w/'tx.after.route').read_bytes()
 rows.append(dict(case=row['case'],endpoints=len(qs),zero_capacity_overflow=True,all_arcs_native_physical_ids_valid=True,rollback_serialized_bytes_exact=row['case']!='commit',native_cpd_ns=row['cpd_ns']))
assert {x['case'] for x in rows}=={'commit','forced_rollback','malformed_late_net'}
(o/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(o/'receipt.json'),build_receipt_sha256=sha(b/'receipt.json'),verifier_sha256=sha(Path(__file__)),endpoint_sha256=sha(ep),rows=rows,scope='Independent exact endpoint/physical arc/owner-capacity checks; original native FULL/STA supplies timing. Move-owned tree/context rollback paths exact for two tested failures. Not all globals, arbitrary exceptions, typed epoch/graph request validation, concurrency or complete pipeline speed proof.'),indent=2)+'\n');print(rows)
