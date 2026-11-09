"""Receipt-closed immutable-context reuse ablation; not cold-routing speed."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2];out=R/'experiments/native_live_search_reuse_v3_2026-10-07';control=R/'experiments/native_live_search_stateless_repeat_2026-10-07'
import sys
sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
reuse=json.loads((out/'receipt.json').read_text());fresh=json.loads((control/'receipt.json').read_text())
for r in reuse['rows']+fresh['rows']:
 for key in ('inputs','sources','files'):assert all(sha(p)==h for p,h in r[key].items())
 assert r['canonical']['mismatches']==r['canonical']['fixups']==0 and r['cpd_ns']==4.87739
assert len({r['producer']['candidate_sha256'] for r in reuse['rows']+fresh['rows']})==1
for a,b in zip(reuse['rows'],fresh['rows']):
 for k in ('initial_wire_budget','final_wire','accepted_repair_nets'):assert a['producer'][k]==b['producer'][k]
 assert {Path(p).name:h for p,h in a['producer']['inputs'].items()}=={Path(p).name:h for p,h in b['producer']['inputs'].items()}
rows={}
for name,r in [('reuse',reuse),('stateless',fresh)]:
 rows[name]=dict(sequence_wall_seconds=r['total_seconds'],native_with_producer_seconds=sum(s['native_including_producer_seconds'] for s in r['rows']),producer_seconds=sum(s['producer']['producer_seconds'] for s in r['rows']),individual_native_seconds=[s['native_including_producer_seconds'] for s in r['rows']])
result=dict(rows=rows,sequence_ratio=rows['reuse']['sequence_wall_seconds']/rows['stateless']['sequence_wall_seconds'],native_ratio=rows['reuse']['native_with_producer_seconds']/rows['stateless']['native_with_producer_seconds'],receipts={str(p):sha(p) for p in (out/'receipt.json',control/'receipt.json')},verifier_sha256=sha(__file__),scope='Same known development fixture repeated three times, sequences observed reuse then stateless, no randomization or controlled host load. Server startup and first context construction paid. Per-step final normalization and original FULL/STA retained on both. Isolates immutable context reconstruction cost, not feedback vs native cold routing, changing-placement performance or held-out generalization.')
(out/'context_reuse_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
