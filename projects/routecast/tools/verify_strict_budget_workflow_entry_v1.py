"""Authenticate receipt and replay skip with subprocess launch forbidden."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from strict_budget_workflow_entry_v1 import execute
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/strict_budget_workflow_entry_v1_2026-10-08'
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text())
assert r['protocol_sha256']==sha(D/'protocol.json')
assert p['source_sha256']==sha(R/'tools/strict_budget_workflow_entry_v1.py')
assert p['gate_source_sha256']==sha(R/'tools/certified_budget_execution_gate_v1.py')
assert r['candidate_launched'] is False and r['candidate_exit_code'] is None
assert r['candidate_quality_accepted'] is False and not (D/'candidate.log').exists()
assert {b['connection_id'] for b in p['preflight']['blockers']}=={785,1637}
bindings=p['preflight']['bindings']
assert all(sha(path)==digest for path,digest in bindings.items())
base=R/'experiments/branch_budget_admission_census_v1_2026-10-08'
c=next(c for c in json.loads((base/'protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
with tempfile.TemporaryDirectory(prefix='routecast-strict-entry-') as tmp:
    with patch('strict_budget_workflow_entry_v1.subprocess.run',side_effect=AssertionError('Candidate must not launch')) as launch:
        replay=execute(base/'w32_m2_admission.json',base/'verification.json',c['target'],c['budget'],p['command'],p['cwd'],Path(tmp)/'replay')
        assert launch.call_count==0 and replay['candidate_launched'] is False
        assert replay['decision']==r['decision']
report=dict(bindings={**bindings,str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))},
            authenticated_actual_skip=True,independent_launch_interception_calls=0,
            all_original_budgets_unchanged=True,
            real_feasible_continue_workflow_verified=False,
            scope='Actual strict entry plus replay with subprocess.run forbidden. '
                  'Proves candidate not launched on this certified infeasible case; '
                  'does not prove continue branch or full end-to-end performance.')
with (D/'verification.json').open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
print('PASS: authenticated real skip and zero intercepted candidate launches')
