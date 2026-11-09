"""Authenticate complete shared-context replay and all semantic state parity."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_persistent_repair_context_2026-10-06'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');r=read(out/'receipt.json');replay=Path(r['replay_root'])
assert sha(out/'protocol.json')==r['protocol_sha256'] and sha(root/'tools/trial_ex5p_persistent_repair_context.py')==r['source_sha256']
assert r['one_context_four_stages'] and r['calls']=={'load':4,'native':4}
assert [x['stage'] for x in r['stages']]==p['stages']
for name,h in p['sources'].items():assert sha(root/'tools'/name)==sha(replay/'tools'/name)==h
for row in r['stages']:
 directory=row['stage']+'_2026-10-06';folder=replay/'experiments'/directory;a=read(folder/'receipt.json');b=read(root/'experiments'/directory/'receipt.json');v=read(folder/'verification.json')
 assert sha(folder/'receipt.json')==row['receipt_sha256']==v['receipt_sha256']
 assert sha(folder/'verification.json')==row['verification_sha256']
 keys=[k for k in b if not k.endswith('_sha256') and not k.endswith('_seconds')]
 assert row['semantic_keys']==keys and all(a[k]==b[k] for k in keys)
 assert row['workflow_s']>0 and row['audit_s']>0
final=read(replay/'experiments/ex5p_budget_repair_2026-10-06/receipt.json')
assert final['completed_connections']==final['required_connections']==1916 and final['failure'] is None
result={'receipt_sha256':sha(out/'receipt.json'),'all_semantic_events_and_states_equal':True,'independent_stage_XML_audits_authenticated':True,'complete_connections':1916,'workflow_with_initialization_s':r['workflow_with_initialization_s'],'audit_s':r['audit_s'],'scope':'Complete four-stage development repair parity, including mutable history/demand transitions; native import/canonical/fallback excluded. Stage ledgers reconstructed between stages, not unified production transactions or prospective speed proof.'};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
