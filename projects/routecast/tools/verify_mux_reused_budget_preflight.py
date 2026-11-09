"""Reused probe parity with frozen fresh-context early-exit observations."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_reused_budget_preflight_2026-10-06';base=ROOT/'experiments/mux_budget_preflight_early_exit_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items())and all(sha(f)==h for c in p['cases']for f,h in c['inputs'].items());rows=[]
keys=('query','budget_units','minimum_units','feasible','expanded','discovered')
for row in r['rows']:
 w=row['width'];file=out/f'w{w}.json';assert sha(file)==row['sha256'];data=json.loads(file.read_text());fresh=json.loads((base/f'w{w}.json').read_text());assert all(data[k]for k in ('restored_endpoint_identity','restored_all_buffers_history_ledger','exceptional_exit_restored'))
 for probe in data['probes']:
  result=probe['result'];assert result['affected']==fresh['affected'];assert result['status']=='REJECT_BUDGET_CANDIDATE_USE_NATIVE_COLD';assert result['observations']==[{k:o[k]for k in keys}for o in fresh['observations']]
 rows.append(dict(width=w,probe_seconds=row['probe_seconds'],setup_seconds=row['setup_seconds'],fresh_observation_parity=True,rejection_and_exception_restoration=True))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Six speculative probes of three native-seeded incumbent contexts; not successful accepted-state transition, concurrency/durability or end-to-end speedup.'),indent=2)+'\n');print(rows)
