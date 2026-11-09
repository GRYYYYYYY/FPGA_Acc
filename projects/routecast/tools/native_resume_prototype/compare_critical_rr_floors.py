"""Check exact selected-floor parity and retain explicit unqueried coverage/cost scope."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];rows=[];bindings={}
for w,i in ((16,1),(32,3)):
 subset=ROOT/f'experiments/native_resume_critical_rr_floors_w{w}_m{i}_2026-10-07';full=ROOT/f'experiments/native_resume_target_rr_floors_w{w}_m{i}_2026-10-07'
 sr,fr,sv,fv,sp=[json.loads(f.read_text()) for f in (subset/'receipt.json',full/'receipt.json',subset/'verification.json',full/'verification.json',subset/'protocol.json')]
 assert sv['receipt_sha256']==sha(subset/'receipt.json') and fv['receipt_sha256']==sha(full/'receipt.json')
 assert sr['graph_sha256']==fr['graph_sha256'] and sr['scale']==fr['scale']
 assert all(sha(f)==h for f,h in sp['inputs'].items())
 for receipt in (sr,fr):assert all(sha(c['path'])==c['sha256'] for c in receipt['certificates'])
 byid={r['query']['connection_id']:r for r in fr['rows']};selected=set(sp['selection']['selected_connection_ids']);assert selected=={r['query']['connection_id'] for r in sr['rows']}
 for r in sr['rows']:
  original=byid[r['query']['connection_id']];assert r['query']==original['query'] and r['status']==original['status']=='FOUND' and r['minimum_integer']==original['minimum_integer']
 for f in (subset/'receipt.json',full/'receipt.json',subset/'verification.json',full/'verification.json',subset/'protocol.json'):bindings[str(f)]=sha(f)
 rows.append(dict(width=w,index=i,total_targets=len(fr['rows']),selected_targets=len(sr['rows']),unqueried_targets=len(fr['rows'])-len(sr['rows']),subset_sources=len(sr['certificates']),full_sources=len(fr['certificates']),exact_selected_floor_parity=True,subset_total_seconds=sr['total_seconds'],subset_preparation_seconds=sr['preparation_seconds'],subset_query_certificate_seconds=sr['query_and_certificate_seconds'],full_total_seconds=fr['total_seconds'],observed_subset_full_ratio=sr['total_seconds']/fr['total_seconds'],subset_verification_seconds=sv['verification_seconds']))
out=ROOT/'experiments/native_resume_critical_rr_floors_comparison_2026-10-07';out.mkdir(exist_ok=False)
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,verifier_sha256=sha(Path(__file__)),scope='Own last working criticality snapshot replay, not initial pre-route selection or heldout. Full and subset observed on different runs; w32 subset overlapped w16 separate verification. Core floor construction/query/certificate timing excludes snapshot generation and final receipt serialization. No route-quality or full workflow gain.'),indent=2)+'\n');print(rows)
