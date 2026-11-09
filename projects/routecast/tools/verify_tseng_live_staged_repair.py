"""Authenticate complete no-repair outcome against independent incremental audit."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_live_staged_repair_2026-10-06'
r=json.loads((out/'receipt.json').read_text());v=json.loads((out/'incremental_verification.json').read_text());summary=json.loads((out/'summary.json').read_text());p=json.loads((out/'protocol.json').read_text())
assert v['receipt_sha256']==sha(out/'incremental.json')
assert (out/'receipt.json').read_bytes()==(out/'incremental.json').read_bytes()
assert r['failure'] is None and r['status']=='COMPLETE_CANDIDATE' and r['completed_connections']==r['required_connections']==v['accepted_paths_checked']==1234
assert summary['live_state_restored'] and not summary['repair_invoked'] and summary['receipt_sha256']==sha(out/'receipt.json')
assert all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items()) and all(sha(f)==h for f,h in p['inputs_sha256'].items())
v.update(receipt_sha256=sha(out/'receipt.json'),complete_candidate=True,scope='Complete no-repair staged candidate independently XML-audited; native acceptance pending. Live restoration asserted by authenticated trial, no concurrent publication proof.')
(out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print('verified complete1234 staged candidate,197 rerouted cohort')
